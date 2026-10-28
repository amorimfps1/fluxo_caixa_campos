"""Serviço de verificação de credenciais Google OAuth 2.0 (ID Token e Access Token)."""

from __future__ import annotations

import os
import time
from typing import Any

import httpx

from dados_sensiveis import descriptografar_cpf

GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
EMISSORES_GOOGLE_VALIDOS = frozenset({
    "accounts.google.com",
    "https://accounts.google.com",
})


def obter_google_client_id() -> str:
    """Retorna o GOOGLE_CLIENT_ID configurado no ambiente (ou string vazia)."""
    return os.getenv("GOOGLE_CLIENT_ID", "").strip()


def modo_google_assistido_habilitado() -> bool:
    """Indica se o fluxo assistido de contingência Google está disponível quando GOOGLE_CLIENT_ID está vazio."""
    if os.getenv("DISABLE_GOOGLE_ASSISTED", "").strip().lower() in ("1", "true", "yes"):
        return False
    if os.getenv("ALLOW_GOOGLE_ASSISTED", "").strip().lower() in ("1", "true", "yes"):
        return True
    return not bool(obter_google_client_id())


def usuario_possui_cadastro_incompleto_oauth(usuario: Any) -> bool:
    """Retorna True se o usuário ainda possui identificador temporário OAuth em vez de CPF real."""
    cpf_cifrado = getattr(usuario, "cpf", None)
    if not cpf_cifrado or not isinstance(cpf_cifrado, str):
        return False
    try:
        valor = descriptografar_cpf(cpf_cifrado)
        return valor.startswith("oauth:")
    except ValueError:
        return False


def _derivar_nome_padrao(email: str, nome_informado: str) -> str:
    nome = (nome_informado or "").strip()
    if len(nome) >= 3:
        return nome[:150]
    parte_local = email.split("@", 1)[0].replace(".", " ").replace("_", " ").strip()
    candid = parte_local.title() if len(parte_local) >= 3 else f"Usuário {parte_local or 'Google'}"
    return candid[:150]


def verificar_token_google(credential: str) -> dict[str, Any]:
    """Valida um ID Token do Google OAuth 2.0 e retorna os dados verificados do titular.

    Verifica:
    - Assinatura e integridade junto ao endpoint oficial do Google (`tokeninfo`).
    - Emissor (`iss`) pertencente ao Google (`accounts.google.com`).
    - Audiência (`aud`) correspondente ao `GOOGLE_CLIENT_ID` da aplicação.
    - Expiração (`exp`) vigente.
    - E-mail verificado (`email_verified == true`) e identificador único (`sub`).
    """
    token = (credential or "").strip()
    if not token or len(token) < 10:
        raise ValueError("Credencial do Google ausente ou malformada.")

    client_id = obter_google_client_id()
    if not client_id:
        raise RuntimeError(
            "O login social com Google não está configurado neste ambiente."
        )

    try:
        resposta = httpx.get(
            GOOGLE_TOKENINFO_URL,
            params={"id_token": token},
            timeout=10.0,
        )
    except httpx.HTTPError as erro:
        raise RuntimeError(
            "Não foi possível validar a credencial com os servidores do Google. "
            "Tente novamente em instantes."
        ) from erro

    if resposta.status_code != 200:
        raise ValueError("Credencial do Google inválida ou expirada.")

    try:
        payload = resposta.json()
    except ValueError as erro:
        raise ValueError("Resposta inválida ao verificar a credencial do Google.") from erro

    emissor = str(payload.get("iss") or "").strip()
    if emissor not in EMISSORES_GOOGLE_VALIDOS:
        raise ValueError("Emissor do token do Google inválido.")

    audiencia = str(payload.get("aud") or "").strip()
    if audiencia != client_id:
        raise ValueError("O token do Google não pertence a esta aplicação.")

    exp_bruto = payload.get("exp")
    if exp_bruto is not None:
        try:
            if int(exp_bruto) <= int(time.time()):
                raise ValueError("O token de autenticação do Google expirou.")
        except (TypeError, ValueError) as erro:
            if "expirou" in str(erro):
                raise
            raise ValueError("Data de expiração do token do Google inválida.") from erro

    email_verificado_bruto = payload.get("email_verified")
    email_verificado = email_verificado_bruto in (True, "true", "True", "1", 1)
    if not email_verificado:
        raise ValueError("A conta do Google informada não possui e-mail verificado.")

    sub = str(payload.get("sub") or "").strip()
    email = str(payload.get("email") or "").strip().lower()
    if not sub or not email or "@" not in email:
        raise ValueError(
            "O token do Google não contém os dados obrigatórios de identificação."
        )

    nome = _derivar_nome_padrao(email, str(payload.get("name") or ""))

    return {
        "sub": sub,
        "email": email,
        "nome": nome,
        "email_verificado": True,
    }


def verificar_access_token_google(access_token: str) -> dict[str, Any]:
    """Valida um Access Token OAuth 2.0 do Google Identity Services (fluxo popup TokenClient)."""
    token = (access_token or "").strip()
    if not token or len(token) < 10:
        raise ValueError("Token de acesso do Google ausente ou malformado.")

    client_id = obter_google_client_id()
    if not client_id:
        raise RuntimeError(
            "O login social com Google não está configurado neste ambiente."
        )

    try:
        resp_info = httpx.get(
            GOOGLE_TOKENINFO_URL,
            params={"access_token": token},
            timeout=10.0,
        )
    except httpx.HTTPError as erro:
        raise RuntimeError(
            "Não foi possível validar o token de acesso com os servidores do Google."
        ) from erro

    if resp_info.status_code != 200:
        raise ValueError("Token de acesso do Google inválido ou expirado.")

    try:
        info = resp_info.json()
    except ValueError as erro:
        raise ValueError("Resposta inválida ao verificar o token do Google.") from erro

    aud = str(info.get("aud") or info.get("azp") or "").strip()
    if aud != client_id:
        raise ValueError("O token de acesso do Google não pertence a esta aplicação.")

    try:
        resp_perfil = httpx.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0,
        )
    except httpx.HTTPError as erro:
        raise RuntimeError(
            "Não foi possível obter os dados de perfil da conta Google."
        ) from erro

    if resp_perfil.status_code != 200:
        raise ValueError("Não foi possível consultar o perfil autenticado do Google.")

    perfil = resp_perfil.json()
    email_verificado = perfil.get("email_verified") in (True, "true", "True", "1", 1)
    if not email_verificado:
        raise ValueError("A conta do Google informada não possui e-mail verificado.")

    sub = str(perfil.get("sub") or info.get("sub") or "").strip()
    email = str(perfil.get("email") or info.get("email") or "").strip().lower()
    if not sub or not email or "@" not in email:
        raise ValueError(
            "O perfil do Google não contém os dados obrigatórios de identificação."
        )

    nome = _derivar_nome_padrao(email, str(perfil.get("name") or ""))
    return {
        "sub": sub,
        "email": email,
        "nome": nome,
        "email_verificado": True,
    }
