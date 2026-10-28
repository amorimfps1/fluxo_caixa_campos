import os
from datetime import datetime, timedelta, timezone

import jwt
from configuracao import carregar_configuracao
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from database import get_db
from models import Usuario


# =========================================================
# CONFIGURAÇÕES DO JWT
# =========================================================

ALGORITHM = "HS256"

carregar_configuracao()


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/login",
    auto_error=False,
)


def _chave_secreta_jwt() -> str:
    chave = os.getenv("JWT_SECRET_KEY")
    if not chave or len(chave) < 32:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "A autenticação não está configurada. "
                "Defina JWT_SECRET_KEY com pelo menos 32 caracteres."
            ),
        )
    return chave


def _validade_token_minutos() -> int:
    valor = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    try:
        minutos = int(valor)
    except ValueError as erro:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ACCESS_TOKEN_EXPIRE_MINUTES deve ser um inteiro positivo.",
        ) from erro
    if minutos <= 0:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ACCESS_TOKEN_EXPIRE_MINUTES deve ser um inteiro positivo.",
        )
    return minutos


# =========================================================
# CRIAR TOKEN
# =========================================================

def criar_token(usuario_id: int):

    expiracao = datetime.now(timezone.utc) + timedelta(
        minutes=_validade_token_minutos()
    )

    dados = {
        "sub": str(usuario_id),
        "exp": expiracao
    }

    token = jwt.encode(
        dados,
        _chave_secreta_jwt(),
        algorithm=ALGORITHM
    )

    return token


# =========================================================
# OBTER USUÁRIO LOGADO
# =========================================================

def obter_usuario_logado(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não autenticado. Faça login para continuar.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    credenciais_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado.",
        headers={
            "WWW-Authenticate": "Bearer"
        }
    )

    try:

        payload = jwt.decode(
            token,
            _chave_secreta_jwt(),
            algorithms=[ALGORITHM]
        )

        usuario_id = payload.get("sub")

        if usuario_id is None:
            raise credenciais_invalidas

        usuario_id = int(usuario_id)

    except (jwt.InvalidTokenError, ValueError):

        raise credenciais_invalidas

    usuario = (
        db.query(Usuario)
        .filter(Usuario.id == usuario_id)
        .first()
    )

    if not usuario:
        raise credenciais_invalidas

    return usuario
