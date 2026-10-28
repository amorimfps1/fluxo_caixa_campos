"""Serviço unificado de notificação OTP multi-canal (E-mail / SMS / WhatsApp).

Recursos implementados:
1. Normalização estrita de telefones brasileiros para o padrão internacional E.164 (`+55DD9XXXXXXXX`)
   com validação de DDD (11 a 99) e 10 ou 11 dígitos nacionais.
2. Mascaramento seguro de destinos para exibição na UI (`ar***@gmail.com` e `(11) 9****-4321`).
3. Disparo de SMS / WhatsApp compatível com Twilio (`TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`,
   `TWILIO_FROM_NUMBER`, `TWILIO_WHATSAPP_FROM`) e Webhook HTTP genérico (`SMS_PROVIDER_URL`, `SMS_API_KEY`).
4. Modo de Contingência Inteligente (Anti-Travamento): quando o servidor (ex.: Render Free Tier)
   não possui credenciais SMTP/HTTP-Email/SMS ativas ou sofre bloqueio externo de porta, registra
   o código nos logs diagnósticos e retorna `modo_contingencia=True` com `codigo_demonstracao`
   para que o usuário conclua a verificação sem ficar bloqueado.
"""

from __future__ import annotations

from collections.abc import Callable
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)


def extrair_telefone_nacional_br(telefone: str) -> str | None:
    """Extrai os 10 ou 11 dígitos nacionais (DDD + número) se for telefone brasileiro."""
    bruto = (telefone or "").strip()
    if not bruto:
        return None

    digitos = "".join(c for c in bruto if c.isdigit() and c.isascii())
    if bruto.startswith("+"):
        if not bruto.startswith("+55"):
            return None
        nacional = digitos[2:]
    elif len(digitos) in (12, 13) and digitos.startswith("55"):
        nacional = digitos[2:]
    else:
        nacional = digitos

    return nacional


def normalizar_telefone_e164(telefone: str) -> str:
    """Valida e converte um telefone brasileiro (ou internacional com `+`) para E.164."""
    bruto = (telefone or "").strip()
    if not bruto:
        raise ValueError("Informe um telefone válido com DDD.")

    caracteres_permitidos = set("+0123456789 ().-\t")
    if any(c not in caracteres_permitidos for c in bruto):
        raise ValueError("O telefone contém caracteres inválidos.")

    if bruto.count("+") > 1 or ("+" in bruto and not bruto.startswith("+")):
        raise ValueError("O código do país deve aparecer no início do telefone.")

    digitos = "".join(c for c in bruto if c.isdigit() and c.isascii())
    if not 10 <= len(digitos) <= 15:
        raise ValueError("O telefone deve conter entre 10 e 15 dígitos.")

    # Telefone internacional não-brasileiro iniciado explicitamente com '+'
    if bruto.startswith("+") and not bruto.startswith("+55"):
        return f"+{digitos}"

    nacional = extrair_telefone_nacional_br(bruto)
    if nacional is None or len(nacional) not in (10, 11):
        raise ValueError(
            "Informe um telefone brasileiro válido com DDD e 10 ou 11 dígitos (ex.: (11) 98765-4321)."
        )

    ddd = int(nacional[:2])
    if not 11 <= ddd <= 99:
        raise ValueError("Informe um DDD brasileiro válido entre 11 e 99.")

    if len(nacional) == 11 and nacional[2] != "9":
        raise ValueError(
            "Telefones celulares com 11 dígitos devem iniciar com 9 após o DDD."
        )

    return f"+55{nacional}"


def mascarar_email(email: str) -> str:
    """Mascara um endereço de e-mail preservando prefixo inicial e domínio (`ar***@gmail.com`)."""
    limpo = (email or "").strip().lower()
    if "@" not in limpo:
        return limpo
    local, dominio = limpo.split("@", 1)
    if len(local) <= 2:
        prefixo = local[:1] or "*"
    else:
        prefixo = local[:2]
    return f"{prefixo}***@{dominio}"


def mascarar_telefone(telefone: str | None) -> str:
    """Mascara um telefone exibindo DDD e os 4 dígitos finais (`(11) 9****-4321`)."""
    if not telefone or not telefone.strip():
        return "(**) *****-****"

    nacional = extrair_telefone_nacional_br(telefone)
    if nacional and len(nacional) == 11:
        return f"({nacional[:2]}) {nacional[2]}****-{nacional[-4:]}"
    if nacional and len(nacional) == 10:
        return f"({nacional[:2]}) ****-{nacional[-4:]}"

    digitos = "".join(c for c in telefone if c.isdigit())
    if len(digitos) >= 6:
        return f"+*** ****-{digitos[-4:]}"
    return "(**) *****-****"


def enviar_codigo_telefone(
    telefone: str,
    nome: str,
    codigo_otp: str,
    canal: str = "telefone",
    finalidade: str = "cadastro",
) -> bool:
    """Envia código OTP de 6 dígitos por SMS ou WhatsApp (Twilio ou Webhook HTTP)."""
    telefone_e164 = normalizar_telefone_e164(telefone)
    primeiro_nome = (nome or "Titular").strip().split(" ")[0]
    acao_texto = (
        "recuperar sua senha"
        if finalidade == "recuperacao"
        else "confirmar sua conta"
    )
    mensagem = (
        f"Fluxo de Caixa: Ola, {primeiro_nome}! "
        f"Seu codigo de verificacao para {acao_texto} e {codigo_otp} "
        f"(valido por 15 minutos)."
    )

    canal_limpo = (canal or "telefone").strip().lower()
    usar_whatsapp = canal_limpo == "whatsapp"

    # 1. Provedor Twilio (SMS ou WhatsApp)
    twilio_sid = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
    twilio_token = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
    twilio_from = (
        os.getenv("TWILIO_WHATSAPP_FROM", "").strip()
        if usar_whatsapp and os.getenv("TWILIO_WHATSAPP_FROM", "").strip()
        else os.getenv("TWILIO_FROM_NUMBER", "").strip()
    )

    if twilio_sid and twilio_token and twilio_from:
        remetente_twilio = twilio_from
        destino_twilio = telefone_e164
        if usar_whatsapp or remetente_twilio.startswith("whatsapp:"):
            if not remetente_twilio.startswith("whatsapp:"):
                remetente_twilio = f"whatsapp:{remetente_twilio}"
            if not destino_twilio.startswith("whatsapp:"):
                destino_twilio = f"whatsapp:{destino_twilio}"

        url_twilio = (
            f"https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}/Messages.json"
        )
        try:
            resposta = httpx.post(
                url_twilio,
                data={
                    "To": destino_twilio,
                    "From": remetente_twilio,
                    "Body": mensagem,
                },
                auth=(twilio_sid, twilio_token),
                timeout=10.0,
            )
            if 200 <= resposta.status_code < 300:
                logger.info(
                    "Código OTP entregue via Twilio (%s) para %s.",
                    "whatsapp" if "whatsapp:" in destino_twilio else "sms",
                    mascarar_telefone(telefone_e164),
                )
                return True
            logger.warning(
                "Twilio retornou status %s ao enviar OTP para %s: %s",
                resposta.status_code,
                mascarar_telefone(telefone_e164),
                resposta.text[:240],
            )
        except Exception as erro:
            logger.warning(
                "Falha de comunicação com Twilio para %s: %s",
                mascarar_telefone(telefone_e164),
                erro,
            )

    # 2. Provedor Webhook HTTP genérico (SMS / WhatsApp Gateway)
    webhook_url = os.getenv("SMS_PROVIDER_URL", "").strip()
    webhook_key = os.getenv("SMS_API_KEY", "").strip()
    if webhook_url:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if webhook_key:
            headers["Authorization"] = f"Bearer {webhook_key}"
        try:
            resposta = httpx.post(
                webhook_url,
                headers=headers,
                json={
                    "to": telefone_e164,
                    "phone": telefone_e164,
                    "channel": "whatsapp" if usar_whatsapp else "sms",
                    "code": codigo_otp,
                    "message": mensagem,
                    "purpose": finalidade,
                },
                timeout=10.0,
            )
            if 200 <= resposta.status_code < 300:
                logger.info(
                    "Código OTP entregue via Webhook (%s) para %s.",
                    canal_limpo,
                    mascarar_telefone(telefone_e164),
                )
                return True
            logger.warning(
                "Webhook SMS/WhatsApp retornou status %s para %s: %s",
                resposta.status_code,
                mascarar_telefone(telefone_e164),
                resposta.text[:240],
            )
        except Exception as erro:
            logger.warning(
                "Falha ao enviar OTP via Webhook SMS/WhatsApp para %s: %s",
                mascarar_telefone(telefone_e164),
                erro,
            )

    if not (twilio_sid and twilio_token and twilio_from) and not webhook_url:
        logger.info(
            "Provedor SMS/WhatsApp não configurado (TWILIO_* e SMS_PROVIDER_URL ausentes) para %s.",
            mascarar_telefone(telefone_e164),
        )
    return False


def contingencia_otp_habilitada() -> bool:
    """Indica se o fallback anti-travamento está ativo quando o transporte externo falha."""
    desativado = os.getenv("DISABLE_OTP_CONTINGENCY", "").strip().lower()
    return desativado not in ("1", "true", "yes")


def disparar_codigo_otp(
    *,
    canal: str,
    email: str,
    telefone: str | None,
    nome: str,
    codigo_otp: str,
    finalidade: str = "cadastro",
    envio_email_fn: Callable[[], bool] | None = None,
    envio_telefone_fn: Callable[[], bool] | None = None,
) -> dict[str, Any]:
    """Orquestra o disparo do código OTP pelo canal escolhido com fallback anti-travamento."""
    canal_bruto = (canal or "email").strip().lower()
    eh_telefone = canal_bruto in ("telefone", "sms", "whatsapp")
    canal_utilizado = "telefone" if canal_bruto == "telefone" else canal_bruto

    if eh_telefone:
        if not telefone or not telefone.strip():
            raise ValueError(
                "Informe um telefone válido com DDD para receber o código por SMS ou WhatsApp."
            )
        telefone_e164 = normalizar_telefone_e164(telefone)
        destino_mascarado = mascarar_telefone(telefone_e164)
        if envio_telefone_fn is not None:
            entregue = bool(envio_telefone_fn())
        else:
            entregue = enviar_codigo_telefone(
                telefone=telefone_e164,
                nome=nome,
                codigo_otp=codigo_otp,
                canal=canal_bruto,
                finalidade=finalidade,
            )
    else:
        canal_utilizado = "email"
        destino_mascarado = mascarar_email(email)
        if envio_email_fn is not None:
            entregue = bool(envio_email_fn())
        else:
            from servicos.email import (
                enviar_email_codigo_recuperacao,
                enviar_email_confirmacao_cadastro,
            )

            if finalidade == "recuperacao":
                entregue = enviar_email_codigo_recuperacao(
                    destinatario=email,
                    nome=nome,
                    codigo_otp=codigo_otp,
                )
            else:
                entregue = enviar_email_confirmacao_cadastro(
                    destinatario=email,
                    nome=nome,
                    codigo_confirmacao=codigo_otp,
                )

    if entregue:
        return {
            "entregue": True,
            "modo_contingencia": False,
            "canal_utilizado": canal_utilizado,
            "destino_mascarado": destino_mascarado,
            "codigo_demonstracao": None,
        }

    permitir_contingencia = contingencia_otp_habilitada()
    logger.warning(
        "[MODO CONTINGÊNCIA OTP] Transporte externo (%s) indisponível para %s (%s). "
        "Código temporário gerado para ativação sem bloqueio: %s",
        canal_utilizado,
        destino_mascarado,
        finalidade,
        codigo_otp,
    )
    return {
        "entregue": False,
        "modo_contingencia": permitir_contingencia,
        "canal_utilizado": canal_utilizado,
        "destino_mascarado": destino_mascarado,
        "codigo_demonstracao": codigo_otp if permitir_contingencia else None,
    }
