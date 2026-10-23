"""Serviço utilitário para envio de e-mails transacionais via SMTP.

Configurável inteiramente por variáveis de ambiente:
- SMTP_SERVER: host do servidor SMTP (ex.: smtp.gmail.com)
- SMTP_PORT: porta SMTP (padrão: 587)
- SMTP_USER: usuário de autenticação SMTP
- SMTP_PASSWORD: senha ou App Password SMTP
- SMTP_FROM: remetente exibido no e-mail (padrão: SMTP_USER)

Possui tratamento defensivo de exceções para que falhas de rede ou ausência de
configuração SMTP em ambiente de desenvolvimento/demonstração nunca interrompam
as requisições principais da API.
"""

from email.message import EmailMessage
import logging
import os
import smtplib

logger = logging.getLogger(__name__)


def _obter_config_smtp() -> dict[str, str | int]:
    servidor = os.getenv("SMTP_SERVER", "").strip()
    porta_str = os.getenv("SMTP_PORT", "587").strip()
    usuario = os.getenv("SMTP_USER", "").strip()
    senha = os.getenv("SMTP_PASSWORD", "").strip()
    remetente = os.getenv("SMTP_FROM", "").strip() or usuario or "no-reply@fluxocaixa.app"

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


def enviar_email(
    destinatario: str,
    assunto: str,
    corpo_html: str,
    corpo_texto: str | None = None,
) -> bool:
    """Envia um e-mail via SMTP com STARTTLS.

    Retorna True se o envio foi concluído com sucesso, ou False caso o SMTP
    não esteja configurado ou ocorra qualquer erro de transporte.
    """
    cfg = _obter_config_smtp()
    if not cfg["server"] or not cfg["user"] or not cfg["password"]:
        logger.info(
            "SMTP não configurado (SMTP_SERVER/SMTP_USER/SMTP_PASSWORD ausentes). "
            "Simulando envio de e-mail para %s com assunto '%s'.",
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

    try:
        with smtplib.SMTP(str(cfg["server"]), int(cfg["port"]), timeout=10) as cliente:
            cliente.ehlo()
            if int(cfg["port"]) != 25:
                cliente.starttls()
                cliente.ehlo()
            cliente.login(str(cfg["user"]), str(cfg["password"]))
            cliente.send_message(mensagem)
        return True
    except Exception as erro:
        logger.warning(
            "Falha ao enviar e-mail para %s: %s",
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
    assunto = "Bem-vindo ao Fluxo de Caixa — Confirme seu e-mail"
    corpo_texto = (
        f"Olá, {nome}!\n\n"
        f"Sua conta no Sistema de Fluxo de Caixa foi criada com sucesso.\n"
        f"Seu código de confirmação de e-mail é: {codigo_confirmacao}\n\n"
        f"Se você não reconhece este cadastro, ignore esta mensagem."
    )
    corpo_html = f"""
    <div style="font-family: Inter, Arial, sans-serif; max-width: 520px; margin: 0 auto; padding: 24px; border: 1px solid #e8edf4; border-radius: 12px; color: #172033;">
        <h2 style="color: #16a34a; margin-top: 0;">Bem-vindo(a) ao Fluxo de Caixa, {nome}!</h2>
        <p>Sua conta foi criada com sucesso. Para confirmar a titularidade do seu e-mail, utilize o código abaixo:</p>
        <div style="background: #dcfce7; color: #15803d; font-size: 24px; font-weight: 800; letter-spacing: 4px; text-align: center; padding: 14px; border-radius: 8px; margin: 20px 0;">
            {codigo_confirmacao}
        </div>
        <p style="font-size: 12px; color: #64748b;">Caso não tenha solicitado este cadastro, basta ignorar este e-mail.</p>
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
