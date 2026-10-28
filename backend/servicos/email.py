"""Serviço utilitário para envio de e-mails transacionais via API HTTP ou SMTP seguro.

Suporta dois transportes complementares configuráveis por variáveis de ambiente:
1. API HTTP de E-mail (recomendado em nuvem como Render, onde portas SMTP podem ser bloqueadas):
   - EMAIL_API_KEY: chave da API HTTP (Resend `re_...` ou Brevo `xkeysib-...`)
   - EMAIL_API_PROVIDER: `resend` (padrão) ou `brevo`
   - EMAIL_FROM: remetente verificado (ex.: `Fluxo de Caixa <nao-responda@seudominio.com>`)
2. SMTP Seguro (Gmail com Senha de App na porta 587 STARTTLS ou 465 SSL):
   - SMTP_SERVER: host do servidor SMTP (ex.: `smtp.gmail.com`)
   - SMTP_PORT: `587` (STARTTLS) ou `465` (SSL/TLS direto)
   - SMTP_USER: usuário de autenticação SMTP (ex.: `seuemail@gmail.com`)
   - SMTP_PASSWORD: senha SMTP ou Senha de App de 16 caracteres do Gmail
   - SMTP_FROM: remetente exibido no e-mail (padrão: `SMTP_USER`)

Possui logs diagnósticos claros e tratamento defensivo de exceções para que
ausência de credenciais ou bloqueios de rede acionem o modo de contingência
sem interromper o fluxo de autenticação do usuário.
"""

from __future__ import annotations

from email.message import EmailMessage
from email.utils import parseaddr
import logging
import os
import smtplib

import httpx

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"
BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


def _normalizar_senha_smtp(servidor: str, senha_bruta: str) -> str:
    """Remove espaços agrupadores de Senhas de App de 16 caracteres do Gmail."""
    senha = (senha_bruta or "").strip()
    if "gmail.com" in (servidor or "").lower() and " " in senha:
        compactada = senha.replace(" ", "")
        if len(compactada) == 16 and compactada.isalnum():
            return compactada
    return senha


def _obter_config_smtp() -> dict[str, str | int]:
    servidor = os.getenv("SMTP_SERVER", "").strip()
    porta_str = os.getenv("SMTP_PORT", "587").strip()
    usuario = os.getenv("SMTP_USER", "").strip()
    senha = _normalizar_senha_smtp(servidor, os.getenv("SMTP_PASSWORD", ""))
    remetente = (
        os.getenv("SMTP_FROM", "").strip()
        or os.getenv("EMAIL_FROM", "").strip()
        or usuario
        or "no-reply@fluxocaixa.app"
    )

    try:
        porta = int(porta_str)
    except ValueError:
        porta = 587

    return {
        "server": servidor,
        "port": porta,
        "user": usuario,
        "password": senha,
        "from": remetente,
    }


def _obter_config_http_email() -> dict[str, str]:
    api_key = os.getenv("EMAIL_API_KEY", "").strip()
    provedor = os.getenv("EMAIL_API_PROVIDER", "").strip().lower()
    if not provedor and api_key:
        if api_key.startswith("xkeysib-"):
            provedor = "brevo"
        else:
            provedor = "resend"

    remetente = (
        os.getenv("EMAIL_FROM", "").strip()
        or os.getenv("SMTP_FROM", "").strip()
        or os.getenv("SMTP_USER", "").strip()
        or "Fluxo de Caixa <onboarding@resend.dev>"
    )
    return {
        "api_key": api_key,
        "provider": provedor or "resend",
        "from": remetente,
    }


def _enviar_email_via_api_http(
    destinatario: str,
    assunto: str,
    corpo_html: str,
    corpo_texto: str | None = None,
) -> bool:
    """Envia e-mail utilizando API HTTPS (Resend ou Brevo) na porta 443."""
    cfg = _obter_config_http_email()
    api_key = cfg["api_key"]
    if not api_key:
        return False

    provedor = cfg["provider"]
    remetente = cfg["from"]

    try:
        if provedor == "brevo":
            nome_rem, email_rem = parseaddr(remetente)
            email_rem_limpo = email_rem or remetente
            payload_brevo = {
                "sender": {
                    "name": nome_rem or "Fluxo de Caixa",
                    "email": email_rem_limpo,
                },
                "to": [{"email": destinatario}],
                "subject": assunto,
                "htmlContent": corpo_html,
                "textContent": corpo_texto or assunto,
            }
            resposta = httpx.post(
                BREVO_API_URL,
                headers={
                    "api-key": api_key,
                    "accept": "application/json",
                    "content-type": "application/json",
                },
                json=payload_brevo,
                timeout=10.0,
            )
        else:
            payload_resend = {
                "from": remetente,
                "to": [destinatario],
                "subject": assunto,
                "html": corpo_html,
                "text": corpo_texto or assunto,
            }
            resposta = httpx.post(
                RESEND_API_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload_resend,
                timeout=10.0,
            )

        if 200 <= resposta.status_code < 300:
            logger.info(
                "E-mail entregue com sucesso via API HTTP (%s) para %s.",
                provedor,
                destinatario,
            )
            return True

        logger.warning(
            "API HTTP de e-mail (%s) retornou status %s ao enviar para %s: %s",
            provedor,
            resposta.status_code,
            destinatario,
            resposta.text[:240],
        )
        return False
    except Exception as erro:
        logger.warning(
            "Falha de rede ao enviar e-mail via API HTTP (%s) para %s: %s",
            provedor,
            destinatario,
            erro,
        )
        return False


def enviar_email(
    destinatario: str,
    assunto: str,
    corpo_html: str,
    corpo_texto: str | None = None,
) -> bool:
    """Envia um e-mail via API HTTP (Resend/Brevo) ou SMTP (STARTTLS 587 / SSL 465).

    Retorna True se o envio foi concluído com sucesso, ou False caso nenhum
    provedor esteja configurado ou ocorra falha de transporte.
    """
    cfg_http = _obter_config_http_email()
    if cfg_http["api_key"]:
        if _enviar_email_via_api_http(
            destinatario=destinatario,
            assunto=assunto,
            corpo_html=corpo_html,
            corpo_texto=corpo_texto,
        ):
            return True

    cfg = _obter_config_smtp()
    if not cfg["server"] or not cfg["user"] or not cfg["password"]:
        logger.info(
            "Provedor de e-mail não configurado (EMAIL_API_KEY e SMTP_SERVER/SMTP_USER/SMTP_PASSWORD ausentes). "
            "Envio externo ignorado para %s ('%s').",
            destinatario,
            assunto,
        )
        return False

    mensagem = EmailMessage()
    mensagem["Subject"] = assunto
    mensagem["From"] = str(cfg["from"])
    mensagem["To"] = destinatario
    mensagem.set_content(
        corpo_texto or "Visualize este e-mail em um cliente compatível com HTML."
    )
    mensagem.add_alternative(corpo_html, subtype="html")

    servidor = str(cfg["server"])
    porta = int(cfg["port"])

    try:
        if porta == 465:
            with smtplib.SMTP_SSL(servidor, porta, timeout=10) as cliente_ssl:
                cliente_ssl.ehlo()
                cliente_ssl.login(str(cfg["user"]), str(cfg["password"]))
                cliente_ssl.send_message(mensagem)
        else:
            with smtplib.SMTP(servidor, porta, timeout=10) as cliente:
                cliente.ehlo()
                if porta != 25:
                    cliente.starttls()
                    cliente.ehlo()
                cliente.login(str(cfg["user"]), str(cfg["password"]))
                cliente.send_message(mensagem)

        logger.info(
            "E-mail entregue com sucesso via SMTP (%s:%s) para %s.",
            servidor,
            porta,
            destinatario,
        )
        return True
    except Exception as erro:
        logger.warning(
            "Falha ao enviar e-mail via SMTP (%s:%s) para %s: %s",
            servidor,
            porta,
            destinatario,
            erro,
        )
        return False


def enviar_email_confirmacao_cadastro(
    destinatario: str,
    nome: str,
    codigo_confirmacao: str,
) -> bool:
    """Dispara o e-mail de boas-vindas e confirmação de cadastro com código OTP."""
    assunto = "Bem-vindo ao Fluxo de Caixa — Código de verificação (6 dígitos)"
    corpo_texto = (
        f"Olá, {nome}!\n\n"
        f"Sua conta no Sistema de Fluxo de Caixa foi criada com sucesso.\n"
        f"Seu código de confirmação (válido por 15 minutos) é: {codigo_confirmacao}\n\n"
        f"Se você não reconhece este cadastro, ignore esta mensagem."
    )
    corpo_html = f"""
    <div style="font-family: Inter, Arial, sans-serif; max-width: 520px; margin: 0 auto; padding: 24px; border: 1px solid #e8edf4; border-radius: 12px; color: #172033;">
        <h2 style="color: #16a34a; margin-top: 0;">Bem-vindo(a) ao Fluxo de Caixa, {nome}!</h2>
        <p>Sua conta foi criada com sucesso. Para confirmar sua identidade, digite o código de 6 dígitos abaixo:</p>
        <div style="background: #dcfce7; color: #15803d; font-size: 26px; font-weight: 800; letter-spacing: 5px; text-align: center; padding: 14px; border-radius: 8px; margin: 20px 0;">
            {codigo_confirmacao}
        </div>
        <p style="font-size: 13px; color: #475569;">Este código expira em <strong>15 minutos</strong> e é de uso único.</p>
        <p style="font-size: 12px; color: #64748b;">Caso não tenha solicitado este cadastro, basta ignorar este e-mail.</p>
    </div>
    """
    return enviar_email(
        destinatario=destinatario,
        assunto=assunto,
        corpo_html=corpo_html,
        corpo_texto=corpo_texto,
    )


def enviar_email_confirmacao_nova_conta_bancaria(
    destinatario: str,
    nome_usuario: str,
    nome_banco: str,
    tipo_conta: str,
    saldo_inicial: str,
) -> bool:
    """Dispara e-mail de confirmação sempre que uma nova conta bancária é criada."""
    assunto = f"Fluxo de Caixa — Nova conta cadastrada ({nome_banco})"
    corpo_texto = (
        f"Olá, {nome_usuario}!\n\n"
        f"Confirmamos o cadastro de uma nova conta bancária no seu Fluxo de Caixa:\n"
        f"- Instituição/Nome: {nome_banco}\n"
        f"- Tipo de conta: {tipo_conta}\n"
        f"- Saldo inicial: R$ {saldo_inicial}\n\n"
        f"Caso você não reconheça esta operação, acesse suas configurações imediatamente."
    )
    corpo_html = f"""
    <div style="font-family: Inter, Arial, sans-serif; max-width: 520px; margin: 0 auto; padding: 24px; border: 1px solid #e8edf4; border-radius: 12px; color: #172033;">
        <h2 style="color: #16a34a; margin-top: 0;">Nova Conta Cadastrada</h2>
        <p>Olá, <strong>{nome_usuario}</strong>! Uma nova conta bancária foi adicionada com sucesso ao seu painel do Fluxo de Caixa:</p>
        <div style="background: #f8fafc; padding: 16px; border-radius: 10px; border: 1px solid #e2e8f0; margin: 18px 0;">
            <p style="margin: 4px 0;"><strong>Conta / Instituição:</strong> {nome_banco}</p>
            <p style="margin: 4px 0;"><strong>Tipo:</strong> {tipo_conta}</p>
            <p style="margin: 4px 0;"><strong>Saldo inicial:</strong> R$ {saldo_inicial}</p>
        </div>
        <p style="font-size: 12px; color: #64748b;">Esta é uma mensagem automática de confirmação de segurança do Fluxo de Caixa.</p>
    </div>
    """
    return enviar_email(
        destinatario=destinatario,
        assunto=assunto,
        corpo_html=corpo_html,
        corpo_texto=corpo_texto,
    )


def enviar_email_codigo_recuperacao(
    destinatario: str,
    nome: str,
    codigo_otp: str,
) -> bool:
    """Dispara o e-mail com o código OTP temporário (15 minutos) para redefinição de senha."""
    assunto = "Fluxo de Caixa — Código de recuperação de senha"
    corpo_texto = (
        f"Olá, {nome}!\n\n"
        f"Recebemos uma solicitação para redefinir a senha da sua conta.\n"
        f"Seu código de verificação temporário (válido por 15 minutos) é: {codigo_otp}\n\n"
        f"Se você não solicitou esta alteração, ignore este e-mail."
    )
    corpo_html = f"""
    <div style="font-family: Inter, Arial, sans-serif; max-width: 520px; margin: 0 auto; padding: 24px; border: 1px solid #e8edf4; border-radius: 12px; color: #172033;">
        <h2 style="color: #16a34a; margin-top: 0;">Recuperação de Senha</h2>
        <p>Olá, <strong>{nome}</strong>. Utilize o código de verificação temporário abaixo para redefinir sua senha:</p>
        <div style="background: #f1f5f9; color: #172033; font-size: 26px; font-weight: 800; letter-spacing: 5px; text-align: center; padding: 16px; border-radius: 8px; margin: 20px 0; border: 1px solid #cbd5e1;">
            {codigo_otp}
        </div>
        <p style="font-size: 13px; color: #64748b;">Este código expira em <strong>15 minutos</strong> e é descartado automaticamente após o uso.</p>
    </div>
    """
    return enviar_email(
        destinatario=destinatario,
        assunto=assunto,
        corpo_html=corpo_html,
        corpo_texto=corpo_texto,
    )
