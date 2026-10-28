from pathlib import Path
import time
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from dados_sensiveis import descriptografar_cpf
from models import Usuario
from servicos import google_oauth


def _payload_base_cadastro() -> dict[str, object]:
    return {
        "nome_completo": "Usuária Segurança LGPD",
        "cpf": "529.982.247-25",
        "email": f"seguranca-{uuid4().hex}@exemplo.com",
        "senha": "SenhaForte@2026",
        "aceite_termos": True,
        "aceite_privacidade": True,
    }


@pytest.mark.parametrize(
    "cpf_invalido",
    [
        "123",
        "123456789012",
        "abc.def.ghi-jk",
        "000.000.000-00",
        "111.111.111-11",
        "22222222222",
        "333.333.333-33",
        "44444444444",
        "555.555.555-55",
        "66666666666",
        "777.777.777-77",
        "88888888888",
        "999.999.999-99",
        "529.982.247-15",  # 1º dígito verificador incorreto
        "529.982.247-20",  # 2º dígito verificador incorreto
    ],
)
def test_bloqueio_cpfs_invalidos_no_cadastro(
    client: TestClient,
    db: Session,
    cpf_invalido: str,
) -> None:
    dados = {**_payload_base_cadastro(), "cpf": cpf_invalido}
    resposta = client.post("/usuarios/", json=dados)

    assert resposta.status_code == 422, resposta.text
    corpo = resposta.text
    assert "Value error" not in corpo
    assert "CPF" in corpo
    assert db.query(Usuario).count() == 0


def test_aceita_cpfs_validos_com_e_sem_mascara(
    client: TestClient,
    db: Session,
) -> None:
    r1 = client.post(
        "/usuarios/",
        json={**_payload_base_cadastro(), "cpf": "529.982.247-25"},
    )
    assert r1.status_code == 201, r1.text
    assert "cpf" not in r1.json()  # Minimização de dados LGPD: CPF nunca vaza no payload HTTP
    u1 = db.query(Usuario).filter_by(id=r1.json()["id"]).one()
    assert u1.cpf != "52998224725"
    assert descriptografar_cpf(u1.cpf) == "52998224725"

    r2 = client.post(
        "/usuarios/",
        json={**_payload_base_cadastro(), "cpf": "11144477735"},
    )
    assert r2.status_code == 201, r2.text
    assert "cpf" not in r2.json()
    u2 = db.query(Usuario).filter_by(id=r2.json()["id"]).one()
    assert descriptografar_cpf(u2.cpf) == "11144477735"
    assert db.query(Usuario).count() == 2


@pytest.mark.parametrize(
    ("senha_fraca", "trecho_esperado_pt"),
    [
        ("Ab1!cur", "8 caracteres"),
        ("senhaforte@2026", "maiúscula"),
        ("SENHAFORTE@2026", "minúscula"),
        ("SenhaSemNumero@", "número"),
        ("SenhaSemSimbolo2026", "caractere especial"),
        ("Senha123 ", "caractere especial"),
    ],
)
def test_criterios_senha_forte_e_mensagens_pt_br(
    client: TestClient,
    db: Session,
    senha_fraca: str,
    trecho_esperado_pt: str,
) -> None:
    dados = {**_payload_base_cadastro(), "senha": senha_fraca}
    resposta = client.post("/usuarios/", json=dados)

    assert resposta.status_code == 422, resposta.text
    texto = resposta.text
    assert "Value error" not in texto
    assert trecho_esperado_pt in texto
    assert db.query(Usuario).count() == 0


def test_erros_validacao_e_autenticacao_100_por_cento_pt_br(
    client: TestClient,
) -> None:
    r_nao_autenticado = client.get("/usuarios/me")
    assert r_nao_autenticado.status_code == 401
    assert "Not authenticated" not in r_nao_autenticado.text
    assert "Não autenticado" in r_nao_autenticado.json()["detail"]

    r_campos_ausentes = client.post("/usuarios/", json={})
    assert r_campos_ausentes.status_code == 422
    assert "Field required" not in r_campos_ausentes.text
    assert "Campo obrigatório" in r_campos_ausentes.text

    r_campo_extra = client.post(
        "/usuarios/",
        json={**_payload_base_cadastro(), "campo_inexistente": "x"},
    )
    assert r_campo_extra.status_code == 422
    assert "Extra inputs are not permitted" not in r_campo_extra.text
    assert "Campo adicional não permitido" in r_campo_extra.text


@pytest.mark.parametrize(
    ("aceite_termos", "aceite_privacidade", "trecho_esperado"),
    [
        (False, True, "Termos de Serviço"),
        (True, False, "Política de Privacidade"),
    ],
)
def test_bloqueio_cadastro_sem_aceite_termos_e_lgpd(
    client: TestClient,
    db: Session,
    aceite_termos: bool,
    aceite_privacidade: bool,
    trecho_esperado: str,
) -> None:
    dados = {
        **_payload_base_cadastro(),
        "aceite_termos": aceite_termos,
        "aceite_privacidade": aceite_privacidade,
    }
    resposta = client.post("/usuarios/", json=dados)

    assert resposta.status_code == 422, resposta.text
    assert "Value error" not in resposta.text
    assert trecho_esperado in resposta.text
    assert db.query(Usuario).count() == 0


def test_verificacao_email_anti_bot_fluxo_completo_e_reenvio(
    client: TestClient,
    db: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import rotasdeapi.usuario as rota_usuario

    codigos_enviados: list[tuple[str, str, str]] = []

    def fake_envio_confirmacao(
        destinatario: str,
        nome: str,
        codigo_confirmacao: str,
    ) -> bool:
        codigos_enviados.append((destinatario, nome, codigo_confirmacao))
        return True

    monkeypatch.setattr(
        rota_usuario,
        "enviar_email_confirmacao_cadastro",
        fake_envio_confirmacao,
    )

    dados = _payload_base_cadastro()
    r_cadastro = client.post("/usuarios/", json=dados)
    assert r_cadastro.status_code == 201, r_cadastro.text
    assert r_cadastro.json()["email_verificado"] is False
    assert len(codigos_enviados) == 1

    email_enviado, _, otp_inicial = codigos_enviados[0]
    assert email_enviado == dados["email"]
    assert len(otp_inicial) == 6 and otp_inicial.isdigit()

    # Código incorreto deve ser rejeitado
    r_invalido = client.post(
        "/usuarios/verificar-email",
        json={"email": dados["email"], "codigo": "000000" if otp_inicial != "000000" else "999999"},
    )
    assert r_invalido.status_code == 400
    assert "inválido" in r_invalido.json()["detail"].lower()

    # Reenvio gera novo código válido de 6 dígitos
    r_reenvio = client.post(
        "/usuarios/reenviar-verificacao",
        json={"email": dados["email"]},
    )
    assert r_reenvio.status_code == 200, r_reenvio.text
    assert len(codigos_enviados) == 2
    otp_reenviado = codigos_enviados[1][2]
    assert len(otp_reenviado) == 6 and otp_reenviado.isdigit()

    # Verificação com o código válido ativa a conta e entrega JWT de sessão
    r_ok = client.post(
        "/usuarios/verificar-email",
        json={"email": dados["email"], "codigo_otp": otp_reenviado},
    )
    assert r_ok.status_code == 200, r_ok.text
    corpo_ok = r_ok.json()
    assert corpo_ok["email_verificado"] is True
    assert "access_token" in corpo_ok

    # Token retornado autentica imediatamente no /usuarios/me
    r_me = client.get(
        "/usuarios/me",
        headers={"Authorization": f"Bearer {corpo_ok['access_token']}"},
    )
    assert r_me.status_code == 200
    assert r_me.json()["email_verificado"] is True

    # Reuso do mesmo OTP não é permitido (uso único: rejeita com 400 sem emitir novo token)
    r_replay = client.post(
        "/usuarios/verificar-email",
        json={"email": dados["email"], "codigo": otp_reenviado},
    )
    assert r_replay.status_code == 400
    assert "access_token" not in r_replay.json()

    usuario_db = db.query(Usuario).filter_by(email=dados["email"]).one()
    assert usuario_db.email_verificado is True
    assert usuario_db.codigo_verificacao_hash is None


def test_servico_google_oauth_unit_com_mock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Em produção sem GOOGLE_CLIENT_ID configurado -> RuntimeError em PT-BR (mapeado para 503 na rota)
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "")
    monkeypatch.setenv("APP_ENV", "production")
    with pytest.raises(RuntimeError) as exc_sem_cfg:
        google_oauth.verificar_token_google("qualquer-token-valido-12345")
    assert "Google" in str(exc_sem_cfg.value)
    monkeypatch.setenv("APP_ENV", "development")

    client_id = "1234567890-teste.apps.googleusercontent.com"
    monkeypatch.setenv("GOOGLE_CLIENT_ID", client_id)

    class FakeResponse:
        def __init__(self, status_code: int, payload: dict[str, object]):
            self.status_code = status_code
            self._payload = payload

        def json(self) -> dict[str, object]:
            return self._payload

    agora_futuro = str(int(time.time()) + 3600)

    # 1. Token Google válido
    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: FakeResponse(
            200,
            {
                "iss": "https://accounts.google.com",
                "aud": client_id,
                "sub": "google-sub-987654321",
                "email": "Usuaria.Google@Exemplo.com",
                "email_verified": "true",
                "name": "Usuária Google OAuth",
                "exp": agora_futuro,
            },
        ),
    )
    dados = google_oauth.verificar_token_google("credential.jwt.simulado.valido")
    assert dados["sub"] == "google-sub-987654321"
    assert dados["email"] == "usuaria.google@exemplo.com"
    assert dados["nome"] == "Usuária Google OAuth"
    assert dados["email_verificado"] is True

    # 2. Audience divergente -> ValueError (mapeado para 401 na rota)
    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: FakeResponse(
            200,
            {
                "iss": "accounts.google.com",
                "aud": "outro-client-id.apps.googleusercontent.com",
                "sub": "google-sub-987654321",
                "email": "usuaria@exemplo.com",
                "email_verified": "true",
                "exp": agora_futuro,
            },
        ),
    )
    with pytest.raises(ValueError) as exc_aud:
        google_oauth.verificar_token_google("credential.jwt.aud.invalido")
    assert "aplicação" in str(exc_aud.value)

    # 3. E-mail não verificado no Google -> ValueError (mapeado para 401 na rota)
    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: FakeResponse(
            200,
            {
                "iss": "https://accounts.google.com",
                "aud": client_id,
                "sub": "google-sub-987654321",
                "email": "usuaria@exemplo.com",
                "email_verified": "false",
                "exp": agora_futuro,
            },
        ),
    )
    with pytest.raises(ValueError) as exc_email:
        google_oauth.verificar_token_google("credential.jwt.email.nao.verificado")
    assert "verificado" in str(exc_email.value)

    # 4. Falha de rede com provedor Google -> RuntimeError (mapeado para 503 na rota)
    def falhar_rede(*args, **kwargs):
        raise httpx.ConnectError("Falha simulada de conexão")

    monkeypatch.setattr(httpx, "get", falhar_rede)
    with pytest.raises(RuntimeError) as exc_rede:
        google_oauth.verificar_token_google("credential.jwt.erro.rede")
    assert "Google" in str(exc_rede.value)


def test_endpoint_login_social_google_cria_vincula_e_protege_contra_abuso(
    client: TestClient,
    db: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import rotasdeapi.usuario as rota_usuario

    monkeypatch.setenv(
        "GOOGLE_CLIENT_ID",
        "client-id-publico.apps.googleusercontent.com",
    )

    r_cfg = client.get("/usuarios/auth/google/config")
    assert r_cfg.status_code == 200
    assert r_cfg.json()["habilitado"] is True
    assert r_cfg.json()["client_id"] == "client-id-publico.apps.googleusercontent.com"

    email_novo_oauth = f"google-novo-{uuid4().hex}@exemplo.com"
    monkeypatch.setattr(
        rota_usuario,
        "verificar_token_google",
        lambda credential: {
            "sub": "google-uid-unico-001",
            "email": email_novo_oauth,
            "nome": "Arthur Via Google",
            "email_verificado": True,
        },
    )

    # 1. Primeiro login com Google cria conta automaticamente com identificador cifrado
    r_oauth_1 = client.post(
        "/usuarios/auth/google",
        json={"credential": "token-google-valido-00001"},
    )
    assert r_oauth_1.status_code == 200, r_oauth_1.text
    corpo_1 = r_oauth_1.json()
    assert "access_token" in corpo_1
    assert corpo_1["usuario"]["email"] == email_novo_oauth
    assert corpo_1["usuario"]["email_verificado"] is True
    assert "cpf" not in corpo_1["usuario"]

    usuario_criado = db.query(Usuario).filter_by(email=email_novo_oauth).one()
    assert "google-uid-unico-001" not in usuario_criado.cpf
    assert len(usuario_criado.cpf_indice) == 64

    # Token JWT funciona normalmente nas rotas autenticadas
    r_me = client.get(
        "/usuarios/me",
        headers={"Authorization": f"Bearer {corpo_1['access_token']}"},
    )
    assert r_me.status_code == 200
    assert r_me.json()["nome_completo"] == "Arthur Via Google"

    # 2. Conta tradicional existente ainda não verificada é vinculada sem duplicar registro
    dados_existente = _payload_base_cadastro()
    r_cad = client.post("/usuarios/", json=dados_existente)
    assert r_cad.status_code == 201
    assert r_cad.json()["email_verificado"] is False

    monkeypatch.setattr(
        rota_usuario,
        "verificar_token_google",
        lambda credential: {
            "sub": "google-uid-unico-002",
            "email": dados_existente["email"],
            "nome": str(dados_existente["nome_completo"]),
            "email_verificado": True,
        },
    )
    r_oauth_vinculo = client.post(
        "/usuarios/auth/google",
        json={"credential": "token-google-valido-00002"},
    )
    assert r_oauth_vinculo.status_code == 200, r_oauth_vinculo.text
    assert r_oauth_vinculo.json()["usuario"]["id"] == r_cad.json()["id"]
    assert r_oauth_vinculo.json()["usuario"]["email_verificado"] is True
    assert db.query(Usuario).filter_by(email=dados_existente["email"]).count() == 1

    # 3. Falhas repetidas de token inválido acionam rate limiting (429 na 5ª falha)
    def rejeitar_token(_credential: str):
        raise ValueError("Token do Google inválido.")

    monkeypatch.setattr(rota_usuario, "verificar_token_google", rejeitar_token)
    for tentativa in range(5):
        r_falha = client.post(
            "/usuarios/auth/google",
            json={"credential": f"token-invalido-{tentativa}-123456"},
        )
        if tentativa < 4:
            assert r_falha.status_code == 401
        else:
            assert r_falha.status_code == 429


def test_estrutura_frontend_landing_lgpd_oauth_e_temas() -> None:
    raiz_frontend = Path(__file__).resolve().parents[2] / "frontend"

    logo_svg = (raiz_frontend / "assets" / "logo.svg").read_text(encoding="utf-8")
    inicio_html = (raiz_frontend / "inicio.html").read_text(encoding="utf-8")
    termos_html = (raiz_frontend / "termos.html").read_text(encoding="utf-8")
    privacidade_html = (raiz_frontend / "privacidade.html").read_text(encoding="utf-8")
    login_html = (raiz_frontend / "login.html").read_text(encoding="utf-8")
    cadastro_html = (raiz_frontend / "cadastro.html").read_text(encoding="utf-8")
    index_html = (raiz_frontend / "index.html").read_text(encoding="utf-8")
    legal_js = (raiz_frontend / "js" / "legal.js").read_text(encoding="utf-8")
    style_css = (raiz_frontend / "css" / "style.css").read_text(encoding="utf-8")

    # Logotipo oficial SVG
    assert "<svg" in logo_svg and "#047857" in logo_svg
    for pagina in (inicio_html, termos_html, privacidade_html, login_html, cadastro_html, index_html):
        assert "brand-logo" in pagina

    # Landing Page e CTAs estratégicos
    assert "cadastro.html" in inicio_html
    assert "login.html" in inicio_html
    assert "LGPD" in inicio_html

    # Conformidade Legal (Termos de Serviço + Política de Privacidade LGPD)
    assert "Lei nº 13.709/2018" in legal_js
    assert "Fernet" in legal_js and "Argon2id" in legal_js
    assert 'id="accept-terms"' in cadastro_html
    assert 'id="accept-privacy"' in cadastro_html
    assert 'data-open-legal="termos"' in cadastro_html
    assert 'data-open-legal="privacidade"' in cadastro_html

    # Login Social Google, Checklist de Senha, Validação de CPF e Modal Anti-Bot
    assert 'id="google-oauth-btn"' in login_html
    assert 'id="google-oauth-btn"' in cadastro_html
    assert 'id="verify-email-dialog"' in cadastro_html
    assert "validarCpfMatematico" in legal_js
    assert "vincularChecklistSenha" in legal_js

    # Tipografia Inter e correções de Tema Claro e Escuro no CSS
    assert "Inter" in style_css
    assert '[data-theme="dark"]' in style_css
    assert ".password-checklist" in style_css
    assert ".legal-dialog" in style_css


def test_design_system_wcag_hierarquia_botoes_validacoes_e_sidebar() -> None:
    raiz_frontend = Path(__file__).resolve().parents[2] / "frontend"

    logo_svg = (raiz_frontend / "assets" / "logo.svg").read_text(encoding="utf-8")
    login_html = (raiz_frontend / "login.html").read_text(encoding="utf-8")
    cadastro_html = (raiz_frontend / "cadastro.html").read_text(encoding="utf-8")
    index_html = (raiz_frontend / "index.html").read_text(encoding="utf-8")
    style_css = (raiz_frontend / "css" / "style.css").read_text(encoding="utf-8")
    api_js = (raiz_frontend / "js" / "api.js").read_text(encoding="utf-8")
    legal_js = (raiz_frontend / "js" / "legal.js").read_text(encoding="utf-8")
    cadastro_js = (raiz_frontend / "js" / "cadastro.js").read_text(encoding="utf-8")
    dashboard_js = (raiz_frontend / "js" / "dashboard.js").read_text(encoding="utf-8")

    # 1. Logotipo vetorial local com verde esmeralda #10B981
    assert "#10B981" in logo_svg or "#10b981" in logo_svg

    # 2. Tokens semânticos WCAG AA (Tema Claro e Tema Escuro) e Autofill Fix
    css_lower = style_css.lower()
    assert "#f8fafc" in css_lower
    assert "#0b0f19" in css_lower
    assert "#10b981" in css_lower
    assert "#dc2626" in css_lower
    assert "--btn-primary-text" in style_css
    assert "input:-webkit-autofill" in style_css
    assert "-webkit-text-fill-color" in style_css
    assert "small.field-error" in style_css
    assert ".btn-logout" in style_css

    # 3. Hierarquia estrita de botões em index.html
    assert 'class="button-danger btn-logout"' in index_html
    assert 'class="button-primary btn-exportar-csv"' in index_html
    assert 'id="clear-movements-filter"' in index_html
    assert 'id="new-account"' in index_html

    # 4. Reorganização da Sidebar: sem Gmail solto e perfil unificado com #configuracoes
    assert "mail.google.com" not in index_html
    assert 'href="#configuracoes"' in index_html
    assert 'id="user-profile-badge"' in index_html
    assert ".sidebar .nav-link" in dashboard_js
    assert ".btn-abrir-nova-movimentacao:not(#new-movement)" in dashboard_js

    # 5. Validações reativas no Cadastro e Login (CPF Módulo 11, E-mail e 5 regras de senha)
    assert 'id="cpf-error"' in cadastro_html
    assert 'id="email-error"' in cadastro_html
    assert 'id="password-confirm-error"' in cadastro_html
    assert 'id="login-email-error"' in login_html
    assert "Mínimo de 8 caracteres" in cadastro_html
    assert "Pelo menos uma letra maiúscula (A-Z)" in cadastro_html
    assert "Pelo menos uma letra minúscula (a-z)" in cadastro_html
    assert "Pelo menos um número (0-9)" in cadastro_html
    assert "Pelo menos um caractere especial" in cadastro_html
    assert "validarEmailFormato" in legal_js
    assert "vincularValidacaoEmailTempoReal" in legal_js
    assert "CPF inválido. Verifique os números digitados." in legal_js
    assert "As senhas digitadas não coincidem." in legal_js
    assert "traduzirMensagemErroApi" in api_js
    assert "cpfNormalizado" in cadastro_js

