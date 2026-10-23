import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from secrets import randbelow, token_urlsafe
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db
from models import TentativaLogin, Usuario
from esquema import (
    ConfirmarEmailRequest,
    EsqueciSenhaRequest,
    ExcluirContaRequest,
    RedefinirSenhaRequest,
    UsuarioCreate,
    UsuarioResponse,
    UsuarioUpdateMe,
)
from seguranca.seguranca import gerar_hash_senha, verificar_senha
from autenticacao import criar_token, obter_usuario_logado
from dados_sensiveis import (
    criptografar_cpf,
    criptografar_telefone,
    indice_cpf,
)
from servicos.email import (
    enviar_email_codigo_recuperacao,
    enviar_email_confirmacao_cadastro,
)


router = APIRouter(
    tags=["Usuários"]
)

_HASH_SENHA_INEXISTENTE = gerar_hash_senha(token_urlsafe(32))
LIMITE_TENTATIVAS = 5
JANELA_TENTATIVAS = timedelta(minutes=15)
RETENCAO_TENTATIVAS = timedelta(days=1)
EXPIRACAO_CODIGO_OTP = timedelta(minutes=15)


def _agora_utc_sem_fuso() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _gerar_codigo_otp() -> str:
    return f"{randbelow(1_000_000):06d}"


def _hash_codigo_otp(codigo: str) -> str:
    return hashlib.sha256(f"otp:{codigo.strip()}".encode("utf-8")).hexdigest()


def _chave_controle(prefixo: str, valor: str) -> str:
    return hashlib.sha256(
        f"{prefixo}:{valor}".encode("utf-8")
    ).hexdigest()


def _chave_cliente_login(request: Request) -> str:
    endereco = request.client.host if request.client else "desconhecido"
    return _chave_controle("login-ip", endereco)


def _chave_conta_login(email: str) -> str:
    return _chave_controle("login-email", email.strip().lower())


def _chave_cliente_cadastro(request: Request) -> str:
    endereco = request.client.host if request.client else "desconhecido"
    return _chave_controle("cadastro-ip", endereco)


def _chave_cliente_redefinicao(request: Request) -> str:
    endereco = request.client.host if request.client else "desconhecido"
    return _chave_controle("redefinir-ip", endereco)


def _chave_conta_redefinicao(email: str) -> str:
    return _chave_controle("redefinir-email", email.strip().lower())


def _obter_tentativa(
    db: Session,
    chave_cliente: str,
) -> TentativaLogin | None:
    return (
        db.query(TentativaLogin)
        .filter(TentativaLogin.chave_cliente == chave_cliente)
        .with_for_update()
        .first()
    )


def _verificar_limites(
    db: Session,
    chaves_cliente: tuple[str, ...],
) -> None:
    agora = _agora_utc_sem_fuso()
    db.query(TentativaLogin).filter(
        TentativaLogin.inicio_janela < agora - RETENCAO_TENTATIVAS
    ).delete(synchronize_session=False)
    db.commit()

    for chave_cliente in chaves_cliente:
        tentativa = _obter_tentativa(db, chave_cliente)
        if tentativa is None:
            continue

        if tentativa.bloqueado_ate and tentativa.bloqueado_ate > agora:
            segundos = max(
                1,
                int((tentativa.bloqueado_ate - agora).total_seconds()),
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Muitas tentativas. Tente novamente mais tarde.",
                headers={"Retry-After": str(segundos)},
            )

        if agora - tentativa.inicio_janela >= JANELA_TENTATIVAS:
            tentativa.tentativas = 0
            tentativa.inicio_janela = agora
            tentativa.bloqueado_ate = None
    db.commit()


def _registrar_tentativa(
    db: Session,
    chaves_cliente: tuple[str, ...],
) -> bool:
    agora = _agora_utc_sem_fuso()
    bloqueado = False
    for chave_cliente in chaves_cliente:
        tentativa = _obter_tentativa(db, chave_cliente)
        if tentativa is None:
            try:
                with db.begin_nested():
                    tentativa = TentativaLogin(
                        chave_cliente=chave_cliente,
                        tentativas=1,
                        inicio_janela=agora,
                    )
                    db.add(tentativa)
                    db.flush()
                db.commit()
                continue
            except IntegrityError:
                tentativa = _obter_tentativa(db, chave_cliente)
                if tentativa is None:
                    raise

        if agora - tentativa.inicio_janela >= JANELA_TENTATIVAS:
            tentativa.tentativas = 0
            tentativa.inicio_janela = agora
            tentativa.bloqueado_ate = None

        tentativa.tentativas += 1
        if tentativa.tentativas >= LIMITE_TENTATIVAS:
            tentativa.bloqueado_ate = agora + JANELA_TENTATIVAS
        bloqueado = bloqueado or tentativa.bloqueado_ate is not None
        db.commit()
    return bloqueado


def _limpar_tentativas(
    db: Session,
    chaves_cliente: tuple[str, ...],
) -> None:
    for chave_cliente in chaves_cliente:
        tentativa = _obter_tentativa(db, chave_cliente)
        if tentativa is not None:
            db.delete(tentativa)
    db.commit()


# =========================================================
# CRIAR USUÁRIO (COM ENVIO DE E-MAIL DE CONFIRMAÇÃO)
# =========================================================

@router.post(
    "/usuarios/",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED
)
def criar_usuario(
    usuario: UsuarioCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    chave_cliente = _chave_cliente_cadastro(request)
    _verificar_limites(db, (chave_cliente,))
    _registrar_tentativa(db, (chave_cliente,))

    usuario_existente = (
        db.query(Usuario)
        .filter(
            (Usuario.email == usuario.email) |
            (Usuario.cpf_indice == indice_cpf(usuario.cpf))
        )
        .first()
    )

    if usuario_existente:
        raise HTTPException(
            status_code=400,
            detail="E-mail ou CPF já cadastrado."
        )

    codigo_confirmacao = _gerar_codigo_otp()
    agora = _agora_utc_sem_fuso()

    novo_usuario = Usuario(
        nome_completo=usuario.nome_completo,
        cpf=criptografar_cpf(usuario.cpf),
        cpf_indice=indice_cpf(usuario.cpf),
        email=usuario.email,
        telefone=(
            criptografar_telefone(usuario.telefone)
            if usuario.telefone
            else None
        ),
        senha_hash=gerar_hash_senha(usuario.senha),
        email_verificado=False,
        codigo_verificacao_hash=_hash_codigo_otp(codigo_confirmacao),
        codigo_expira_em=agora + EXPIRACAO_CODIGO_OTP,
    )

    db.add(novo_usuario)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="E-mail ou CPF já cadastrado.",
        ) from None
    db.refresh(novo_usuario)

    enviar_email_confirmacao_cadastro(
        destinatario=novo_usuario.email,
        nome=novo_usuario.nome_completo,
        codigo_confirmacao=codigo_confirmacao,
    )

    return novo_usuario


# =========================================================
# CONFIRMAR E-MAIL DE CADASTRO
# =========================================================

@router.post("/usuarios/confirmar-email")
def confirmar_email(
    dados: ConfirmarEmailRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    chaves_cliente = (
        _chave_cliente_redefinicao(request),
        _chave_conta_redefinicao(dados.email),
    )
    _verificar_limites(db, chaves_cliente)

    usuario = (
        db.query(Usuario)
        .filter(Usuario.email == dados.email)
        .first()
    )

    agora = _agora_utc_sem_fuso()
    codigo_hash = _hash_codigo_otp(dados.codigo_otp)
    codigo_valido = (
        usuario is not None
        and bool(usuario.codigo_verificacao_hash)
        and usuario.codigo_expira_em is not None
        and usuario.codigo_expira_em >= agora
        and hmac.compare_digest(usuario.codigo_verificacao_hash, codigo_hash)
    )

    if not codigo_valido:
        bloqueado = _registrar_tentativa(db, chaves_cliente)
        if bloqueado:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Muitas tentativas inválidas. Tente novamente mais tarde.",
                headers={"Retry-After": str(int(JANELA_TENTATIVAS.total_seconds()))},
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código de verificação inválido ou expirado.",
        )

    usuario.email_verificado = True
    usuario.codigo_verificacao_hash = None
    usuario.codigo_expira_em = None
    db.commit()

    _limpar_tentativas(db, chaves_cliente)

    return {
        "mensagem": "E-mail confirmado com sucesso."
    }


# =========================================================
# LOGIN
# =========================================================

@router.post("/login")
def login(
    request: Request,
    dados: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    chaves_cliente = (
        _chave_cliente_login(request),
        _chave_conta_login(dados.username),
    )
    _verificar_limites(db, chaves_cliente)

    usuario = (
        db.query(Usuario)
        .filter(
            Usuario.email == dados.username.strip().lower()
        )
        .first()
    )

    if not usuario:
        verificar_senha(
            dados.password,
            _HASH_SENHA_INEXISTENTE,
        )
        bloqueado = _registrar_tentativa(db, chaves_cliente)
        if bloqueado:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Muitas tentativas de login. Tente novamente mais tarde.",
                headers={"Retry-After": str(int(JANELA_TENTATIVAS.total_seconds()))},
            )
        raise HTTPException(
            status_code=401,
            detail="E-mail ou senha inválidos."
        )

    senha_correta = verificar_senha(
        dados.password,
        usuario.senha_hash
    )

    if not senha_correta:
        bloqueado = _registrar_tentativa(db, chaves_cliente)
        if bloqueado:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Muitas tentativas de login. Tente novamente mais tarde.",
                headers={"Retry-After": str(int(JANELA_TENTATIVAS.total_seconds()))},
            )
        raise HTTPException(
            status_code=401,
            detail="E-mail ou senha inválidos."
        )

    _limpar_tentativas(db, chaves_cliente)
    token = criar_token(usuario.id)

    return {
        "access_token": token,
        "token_type": "bearer"
    }


# =========================================================
# SOLICITAR CÓDIGO OTP DE RECUPERAÇÃO DE SENHA
# =========================================================

@router.post("/usuarios/esqueci-senha")
def esqueci_senha(
    dados: EsqueciSenhaRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    chaves_cliente = (
        _chave_cliente_redefinicao(request),
        _chave_conta_redefinicao(dados.email),
    )
    _verificar_limites(db, chaves_cliente)
    _registrar_tentativa(db, (chaves_cliente[0],))

    usuario = (
        db.query(Usuario)
        .filter(Usuario.email == dados.email)
        .first()
    )

    if usuario:
        codigo_otp = _gerar_codigo_otp()
        usuario.codigo_verificacao_hash = _hash_codigo_otp(codigo_otp)
        usuario.codigo_expira_em = _agora_utc_sem_fuso() + EXPIRACAO_CODIGO_OTP
        db.commit()

        enviar_email_codigo_recuperacao(
            destinatario=usuario.email,
            nome=usuario.nome_completo,
            codigo_otp=codigo_otp,
        )

    return {
        "mensagem": (
            "Se o e-mail informado estiver cadastrado, um código de verificação "
            "temporário (válido por 15 minutos) foi enviado."
        )
    }


# =========================================================
# REDEFINIR SENHA (POR CÓDIGO OTP OU CPF)
# =========================================================

@router.post("/usuarios/redefinir-senha")
def redefinir_senha(
    dados: RedefinirSenhaRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    chaves_cliente = (
        _chave_cliente_redefinicao(request),
        _chave_conta_redefinicao(dados.email),
    )
    _verificar_limites(db, chaves_cliente)

    usuario = (
        db.query(Usuario)
        .filter(Usuario.email == dados.email)
        .first()
    )

    agora = _agora_utc_sem_fuso()
    credencial_valida = False

    if dados.codigo_otp:
        codigo_hash_informado = _hash_codigo_otp(dados.codigo_otp)
        credencial_valida = (
            usuario is not None
            and bool(usuario.codigo_verificacao_hash)
            and usuario.codigo_expira_em is not None
            and usuario.codigo_expira_em >= agora
            and hmac.compare_digest(
                usuario.codigo_verificacao_hash,
                codigo_hash_informado,
            )
        )
    elif dados.cpf:
        cpf_hash_informado = indice_cpf(dados.cpf)
        credencial_valida = (
            usuario is not None
            and bool(usuario.cpf_indice)
            and hmac.compare_digest(usuario.cpf_indice, cpf_hash_informado)
        )

    if not usuario or not credencial_valida:
        verificar_senha(dados.nova_senha, _HASH_SENHA_INEXISTENTE)
        bloqueado = _registrar_tentativa(db, chaves_cliente)
        if bloqueado:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Muitas tentativas de redefinição. Tente novamente mais tarde.",
                headers={"Retry-After": str(int(JANELA_TENTATIVAS.total_seconds()))},
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não foi possível redefinir a senha. Verifique os dados ou o código informado.",
        )

    usuario.senha_hash = gerar_hash_senha(dados.nova_senha)
    usuario.codigo_verificacao_hash = None
    usuario.codigo_expira_em = None
    if dados.codigo_otp:
        usuario.email_verificado = True
    db.commit()

    _limpar_tentativas(
        db,
        (
            *chaves_cliente,
            _chave_conta_login(dados.email),
        ),
    )

    return {
        "mensagem": "Senha redefinida com sucesso."
    }


# =========================================================
# USUÁRIO LOGADO: CONSULTAR, ATUALIZAR E EXCLUIR CONTA
# =========================================================

@router.get(
    "/usuarios/me",
    response_model=UsuarioResponse
)
def usuario_logado(
    usuario: Usuario = Depends(obter_usuario_logado)
):
    return usuario


@router.put(
    "/usuarios/me",
    response_model=UsuarioResponse
)
def atualizar_usuario_logado(
    dados: UsuarioUpdateMe,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obter_usuario_logado),
):
    campos_enviados = dados.model_fields_set

    if "nova_senha" in campos_enviados and dados.nova_senha:
        if not dados.senha_atual or not verificar_senha(
            dados.senha_atual,
            usuario.senha_hash,
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A senha atual informada está incorreta.",
            )
        usuario.senha_hash = gerar_hash_senha(dados.nova_senha)
    elif "senha_atual" in campos_enviados and dados.senha_atual:
        if not verificar_senha(dados.senha_atual, usuario.senha_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A senha atual informada está incorreta.",
            )

    if "nome_completo" in campos_enviados and dados.nome_completo is not None:
        usuario.nome_completo = dados.nome_completo

    if "email" in campos_enviados and dados.email is not None:
        if dados.email != usuario.email:
            email_em_uso = (
                db.query(Usuario)
                .filter(
                    Usuario.email == dados.email,
                    Usuario.id != usuario.id,
                )
                .first()
            )
            if email_em_uso:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="O e-mail informado já está em uso por outra conta.",
                )
            usuario.email = dados.email

    if "telefone" in campos_enviados:
        usuario.telefone = (
            criptografar_telefone(dados.telefone)
            if dados.telefone
            else None
        )

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O e-mail informado já está em uso por outra conta.",
        ) from None

    db.refresh(usuario)
    return usuario


@router.delete("/usuarios/me")
def excluir_minha_conta(
    dados: ExcluirContaRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obter_usuario_logado),
):
    if not verificar_senha(dados.senha_atual, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A senha atual informada está incorreta.",
        )

    db.delete(usuario)
    db.commit()

    return {
        "mensagem": "Sua conta e todos os dados associados foram excluídos permanentemente."
    }


# =========================================================
# LISTAR USUÁRIOS
# =========================================================

@router.get(
    "/usuarios/",
    response_model=list[UsuarioResponse]
)
def listar_usuarios(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obter_usuario_logado)
):
    return (
        db.query(Usuario)
        .filter(Usuario.id == usuario.id)
        .offset(offset)
        .limit(limit)
        .all()
    )


# =========================================================
# BUSCAR USUÁRIO
# =========================================================

@router.get(
    "/usuarios/{usuario_id}",
    response_model=UsuarioResponse
)
def buscar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obter_usuario_logado)
):
    if usuario_id != usuario.id:
        raise HTTPException(
            status_code=404,
            detail="Usuário não encontrado."
        )

    usuario_encontrado = (
        db.query(Usuario)
        .filter(Usuario.id == usuario_id)
        .first()
    )

    if not usuario_encontrado:
        raise HTTPException(
            status_code=404,
            detail="Usuário não encontrado."
        )

    return usuario_encontrado


# =========================================================
# EXCLUIR USUÁRIO POR ID
# =========================================================

@router.delete(
    "/usuarios/{usuario_id}"
)
def excluir_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obter_usuario_logado)
):
    if usuario_id != usuario.id:
        raise HTTPException(
            status_code=404,
            detail="Usuário não encontrado."
        )

    usuario_encontrado = (
        db.query(Usuario)
        .filter(Usuario.id == usuario_id)
        .first()
    )

    if not usuario_encontrado:
        raise HTTPException(
            status_code=404,
            detail="Usuário não encontrado."
        )

    db.delete(usuario_encontrado)
    db.commit()

    return {
        "mensagem": "Usuário excluído com sucesso."
    }
