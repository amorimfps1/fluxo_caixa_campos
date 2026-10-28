from pathlib import Path
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from dados_sensiveis import descriptografar_cpf, descriptografar_telefone
from models import Usuario
from servicos import email as servico_email
from servicos import google_oauth
from servicos import notificacao_otp


def _gerar_cpf_valido(semente: int) -> str:
    """Gera um CPF matematicamente válido (Módulo 11) a partir de uma semente de 9 dígitos."""
    base = f"{(100000000 + (semente % 899999999)):09d}"
    if len(set(base)) == 1:
        base = "529982247"
    soma1 = sum(int(base[i]) * (10 - i) for i in range(9))
    d1 = (soma1 * 10) % 11
    d1 = 0 if d1 == 10 else d1
    base10 = base + str(d1)
    soma2 = sum(int(base10[i]) * (11 - i) for i in range(10))
    d2 = (soma2 * 10) % 11
    d2 = 0 if d2 == 10 else d2
    return f"{base}{d1}{d2}"


def test_normalizacao_telefone_e164_e_mascaramento_destinos() -> None:
    assert notificacao_otp.normalizar_telefone_e164("(11) 98765-4321") == "+5511987654321"
    assert notificacao_otp.normalizar_telefone_e164("2134567890") == "+552134567890"
    assert notificacao_otp.normalizar_telefone_e164("+55 (31) 99888-7766") == "+5531998887766"

    assert notificacao_otp.mascarar_email("arthur@gmail.com") == "ar***@gmail.com"
    assert notificacao_otp.mascarar_telefone("(11) 98765-4321") == "(11) 9****-4321"

    with pytest.raises(ValueError, match="DDD brasileiro válido"):
        notificacao_otp.normalizar_telefone_e164("(00) 98765-4321")

    with pytest.raises(ValueError, match="iniciar com 9"):
        notificacao_otp.normalizar_telefone_e164("(11) 88765-4321")


@pytest.mark.parametrize(
    ("email_incorreto", "sugestao_esperada"),
    [
        ("usuario@gamil.com", "@gmail.com"),
        ("usuario@gnail.com", "@gmail.com"),
        ("usuario@hotmial.com", "@hotmail.com"),
        ("usuario@outlok.com", "@outlook.com"),
        ("usuario@yaho.com", "@yahoo.com"),
    ],
)
def test_bloqueio_dominios_email_com_erro_de_digitacao(
    client: TestClient,
    db: Session,
    email_incorreto: str,
    sugestao_esperada: str,
) -> None:
    resposta = client.post(
        "/usuarios/",
        json={
            "nome_completo": "Teste Domínio E-mail",
            "cpf": _gerar_cpf_valido(101),
            "email": email_incorreto,
            "senha": "SenhaForte@2026",
            "aceite_termos": True,
            "aceite_privacidade": True,
        },
    )
    assert resposta.status_code == 422, resposta.text
    assert sugestao_esperada in resposta.text
    assert db.query(Usuario).count() == 0


@pytest.mark.parametrize(
    "telefone_invalido",
    [
        None,
        "",
        "(00) 98765-4321",
        "(09) 98765-4321",
        "1198765",
        "(11) 88765-4321",
    ],
)
def test_cadastro_por_telefone_exige_numero_valido_com_ddd(
    client: TestClient,
    db: Session,
    telefone_invalido: str | None,
) -> None:
    resposta = client.post(
        "/usuarios/",
        json={
            "nome_completo": "Teste Telefone Obrigatório",
            "cpf": _gerar_cpf_valido(202),
            "email": f"tel-invalido-{uuid4().hex}@gmail.com",
            "telefone": telefone_invalido,
            "senha": "SenhaForte@2026",
            "canal_verificacao": "telefone",
            "aceite_termos": True,
            "aceite_privacidade": True,
        },
    )
    assert resposta.status_code == 422, resposta.text
    assert db.query(Usuario).count() == 0


def test_cadastro_contingencia_email_e_telefone_e_troca_de_canal(
    client: TestClient,
    db: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Garante modo de contingência limpo (sem provedores externos configurados)
    for var in (
        "EMAIL_API_KEY",
        "SMTP_USER",
        "SMTP_PASSWORD",
        "TWILIO_ACCOUNT_SID",
        "TWILIO_AUTH_TOKEN",
        "SMS_PROVIDER_URL",
    ):
        monkeypatch.delenv(var, raising=False)

    # 1. Cadastro escolhendo canal E-mail sem telefone inicial
    email_usr = f"multicanal-{uuid4().hex}@gmail.com"
    r_cad = client.post(
        "/usuarios/",
        json={
            "nome_completo": "Arthur Multicanal",
            "cpf": _gerar_cpf_valido(303),
            "email": email_usr,
            "senha": "SenhaForte@2026",
            "canal_verificacao": "email",
            "aceite_termos": True,
            "aceite_privacidade": True,
        },
    )
    assert r_cad.status_code == 201, r_cad.text
    corpo_cad = r_cad.json()
    assert corpo_cad["email_verificado"] is False
    assert corpo_cad["canal_verificacao"] == "email"
    assert corpo_cad["modo_contingencia"] is True
    codigo_inicial = corpo_cad["codigo_demonstracao"]
    assert isinstance(codigo_inicial, str) and len(codigo_inicial) == 6 and codigo_inicial.isdigit()
    assert "@gmail.com" in corpo_cad["destino_mascarado"]

    # 2. Usuário não recebeu no Gmail e troca para Telefone informando celular inline
    r_troca = client.post(
        "/usuarios/enviar-codigo",
        json={
            "email": email_usr,
            "canal_verificacao": "telefone",
            "telefone": "(11) 98765-4321",
        },
    )
    assert r_troca.status_code == 200, r_troca.text
    corpo_troca = r_troca.json()
    assert corpo_troca["canal_utilizado"] == "telefone"
    assert corpo_troca["destino_mascarado"] == "(11) 9****-4321"
    assert corpo_troca["modo_contingencia"] is True
    novo_codigo_tel = corpo_troca["codigo_demonstracao"]
    assert isinstance(novo_codigo_tel, str) and len(novo_codigo_tel) == 6

    # Caso coincida aleatoriamente (1 em 1.000.000), apenas valida o fluxo; caso diferente, antigo falha
    if novo_codigo_tel != codigo_inicial:
        r_antigo = client.post(
            "/usuarios/verificar-codigo",
            json={"email": email_usr, "codigo_otp": codigo_inicial},
        )
        assert r_antigo.status_code == 400

    # 3. Confirma o código recebido no Telefone e já recebe o JWT autenticado
    r_confirma = client.post(
        "/usuarios/verificar-codigo",
        json={"email": email_usr, "codigo_otp": novo_codigo_tel},
    )
    assert r_confirma.status_code == 200, r_confirma.text
    dados_token = r_confirma.json()
    assert dados_token["email_verificado"] is True
    assert dados_token["access_token"]

    # Verifica que o telefone informado na troca de canal ficou salvo e criptografado
    usuario_db = db.query(Usuario).filter_by(id=corpo_cad["id"]).one()
    assert usuario_db.email_verificado is True
    assert descriptografar_telefone(usuario_db.telefone) == "(11) 98765-4321"


def test_envio_email_via_api_http_resend_e_brevo_e_smtp_ssl_465(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    chamadas_http: list[tuple[str, dict, dict]] = []

    def fake_httpx_post(url: str, headers: dict = None, json: dict = None, timeout: float = 10.0):
        chamadas_http.append((url, headers or {}, json or {}))
        req = httpx.Request("POST", url)
        return httpx.Response(200, json={"id": "msg_ok"}, request=req)

    monkeypatch.setattr(servico_email.httpx, "post", fake_httpx_post)

    # 1. Resend (detectado automaticamente pelo prefixo re_)
    monkeypatch.setenv("EMAIL_API_KEY", "re_chave_teste_123")
    monkeypatch.delenv("EMAIL_API_PROVIDER", raising=False)
    assert servico_email.enviar_email_confirmacao_cadastro(
        "cliente@gmail.com", "Cliente Resend", "123456"
    ) is True
    assert "api.resend.com" in chamadas_http[-1][0]
    assert chamadas_http[-1][1]["Authorization"] == "Bearer re_chave_teste_123"

    # 2. Brevo (detectado pelo prefixo xkeysib-)
    monkeypatch.setenv("EMAIL_API_KEY", "xkeysib-chave-brevo-456")
    assert servico_email.enviar_email_codigo_recuperacao(
        "cliente@gmail.com", "Cliente Brevo", "654321"
    ) is True
    assert "api.brevo.com" in chamadas_http[-1][0]
    assert chamadas_http[-1][1]["api-key"] == "xkeysib-chave-brevo-456"

    # 3. SMTP_SSL porta 465 com normalização de Senha de App de 16 caracteres com espaços
    monkeypatch.delenv("EMAIL_API_KEY", raising=False)
    monkeypatch.setenv("SMTP_SERVER", "smtp.gmail.com")
    monkeypatch.setenv("SMTP_PORT", "465")
    monkeypatch.setenv("SMTP_USER", "sistema@gmail.com")
    monkeypatch.setenv("SMTP_PASSWORD", "abcd efgh ijkl mnop")

    logins_smtp: list[tuple[str, str]] = []

    class FakeSmtpSsl:
        def __init__(self, host: str, port: int, timeout: int = 12) -> None:
            self.host = host
            self.port = port

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def ehlo(self) -> None:
            return None

        def login(self, user: str, password: str) -> None:
            logins_smtp.append((user, password))

        def send_message(self, msg) -> None:
            return None

    monkeypatch.setattr(servico_email.smtplib, "SMTP_SSL", FakeSmtpSsl)
    assert servico_email.enviar_email_confirmacao_cadastro(
        "destino@gmail.com", "Usuária Gmail", "987654"
    ) is True
    assert logins_smtp == [("sistema@gmail.com", "abcdefghijklmnop")]


def test_envio_codigo_telefone_via_twilio_sms_whatsapp_e_webhook(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    chamadas_twilio: list[tuple[str, dict]] = []

    def fake_post_twilio(
        url: str,
        data: dict = None,
        json: dict = None,
        auth: tuple = None,
        headers: dict = None,
        timeout: float = 12.0,
    ):
        chamadas_twilio.append((url, data if data is not None else (json or {})))
        req = httpx.Request("POST", url)
        return httpx.Response(201, json={"sid": "SM123"}, request=req)

    monkeypatch.setattr(notificacao_otp.httpx, "post", fake_post_twilio)
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "AC_TEST_SID")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "AUTH_TOKEN_TEST")
    monkeypatch.setenv("TWILIO_FROM_NUMBER", "+15005550006")
    monkeypatch.setenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")

    # SMS via Twilio
    res_sms = notificacao_otp.disparar_codigo_otp(
        canal="telefone",
        codigo_otp="445566",
        nome="Arthur",
        email="arthur@gmail.com",
        telefone="(11) 98765-4321",
        finalidade="cadastro",
    )
    assert res_sms["entregue"] is True
    assert res_sms["modo_contingencia"] is False
    assert chamadas_twilio[-1][1]["To"] == "+5511987654321"
    assert "445566" in chamadas_twilio[-1][1]["Body"]

    # WhatsApp via Twilio
    res_wpp = notificacao_otp.disparar_codigo_otp(
        canal="whatsapp",
        codigo_otp="778899",
        nome="Arthur",
        email="arthur@gmail.com",
        telefone="(11) 98765-4321",
        finalidade="recuperacao",
    )
    assert res_wpp["entregue"] is True
    assert chamadas_twilio[-1][1]["To"] == "whatsapp:+5511987654321"

    # Webhook HTTP genérico
    monkeypatch.delenv("TWILIO_ACCOUNT_SID", raising=False)
    monkeypatch.setenv("SMS_PROVIDER_URL", "https://sms-gateway.exemplo.com/send")
    monkeypatch.setenv("SMS_API_KEY", "key_sms_123")

    res_webhook = notificacao_otp.disparar_codigo_otp(
        canal="sms",
        codigo_otp="112233",
        nome="Arthur",
        email="arthur@gmail.com",
        telefone="(21) 99876-5432",
    )
    assert res_webhook["entregue"] is True
    assert chamadas_twilio[-1][0] == "https://sms-gateway.exemplo.com/send"
    assert chamadas_twilio[-1][1]["to"] == "+5521998765432"


def test_recuperacao_senha_multicanal_por_telefone_e_bloqueio_sem_telefone(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for var in ("TWILIO_ACCOUNT_SID", "SMS_PROVIDER_URL", "EMAIL_API_KEY", "SMTP_USER"):
        monkeypatch.delenv(var, raising=False)

    # 1. Conta COM telefone cadastrado consegue recuperar senha por SMS/WhatsApp
    email_com_tel = f"rec-tel-{uuid4().hex}@gmail.com"
    r_cad = client.post(
        "/usuarios/",
        json={
            "nome_completo": "Usuária Recuperação SMS",
            "cpf": _gerar_cpf_valido(404),
            "email": email_com_tel,
            "telefone": "(11) 99123-4567",
            "senha": "SenhaAntiga@2026",
            "canal_verificacao": "telefone",
            "aceite_termos": True,
            "aceite_privacidade": True,
        },
    )
    assert r_cad.status_code == 201, r_cad.text

    r_esq = client.post(
        "/usuarios/esqueci-senha",
        json={"email": email_com_tel, "canal_verificacao": "telefone"},
    )
    assert r_esq.status_code == 200, r_esq.text
    dados_esq = r_esq.json()
    assert dados_esq["canal_utilizado"] == "telefone"
    assert dados_esq["destino_mascarado"] == "(11) 9****-4567"
    assert dados_esq["modo_contingencia"] is True
    otp_rec = dados_esq["codigo_demonstracao"]

    r_red = client.post(
        "/usuarios/redefinir-senha",
        json={
            "email": email_com_tel,
            "codigo_otp": otp_rec,
            "nova_senha": "NovaSenhaForte@2027",
        },
    )
    assert r_red.status_code == 200, r_red.text

    r_login = client.post(
        "/login",
        data={"username": email_com_tel, "password": "NovaSenhaForte@2027"},
    )
    assert r_login.status_code == 200, r_login.text
    assert r_login.json()["access_token"]

    # 2. Conta SEM telefone cadastrado recebe orientação clara ao pedir SMS
    email_sem_tel = f"rec-sem-tel-{uuid4().hex}@gmail.com"
    client.post(
        "/usuarios/",
        json={
            "nome_completo": "Usuário Sem Telefone",
            "cpf": _gerar_cpf_valido(505),
            "email": email_sem_tel,
            "senha": "SenhaAntiga@2026",
            "aceite_termos": True,
            "aceite_privacidade": True,
        },
    )
    r_esq_sem_tel = client.post(
        "/usuarios/esqueci-senha",
        json={"email": email_sem_tel, "canal_verificacao": "telefone"},
    )
    assert r_esq_sem_tel.status_code == 400
    assert "telefone" in r_esq_sem_tel.json()["detail"].lower()


def test_google_oauth_access_token_aprovacao_automatica_e_completar_cadastro(
    client: TestClient,
    db: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import rotasdeapi.usuario as rota_usuario

    email_google = f"oauth-popup-{uuid4().hex}@gmail.com"
    monkeypatch.setattr(
        rota_usuario,
        "verificar_access_token_google",
        lambda token: {
            "sub": "google-popup-sub-999",
            "email": email_google,
            "nome_completo": "Usuária Google Popup",
            "email_verified": True,
        },
    )

    # 1. Login via access_token do popup OAuth2 aprova e-mail automaticamente e sinaliza cadastro rápido pendente
    r_auth = client.post(
        "/usuarios/auth/google",
        json={"access_token": "ya29.token_valido_simulado"},
    )
    assert r_auth.status_code == 200, r_auth.text
    corpo = r_auth.json()
    assert corpo["email_verificado"] is True
    assert corpo["precisa_completar_cadastro"] is True
    token_jwt = corpo["access_token"]

    # 2. Usuário conclui CPF e Telefone no mini-modal pós-Google (PUT /usuarios/me/completar-cadastro)
    cpf_real = _gerar_cpf_valido(606)
    r_comp = client.put(
        "/usuarios/me/completar-cadastro",
        headers={"Authorization": f"Bearer {token_jwt}"},
        json={"cpf": cpf_real, "telefone": "(11) 98888-7777"},
    )
    assert r_comp.status_code == 200, r_comp.text
    dados_me = r_comp.json()
    assert dados_me["precisa_completar_cadastro"] is False
    assert dados_me["telefone"] == "(11) 98888-7777"

    usuario_db = db.query(Usuario).filter_by(id=dados_me["id"]).one()
    assert usuario_db.email_verificado is True
    assert descriptografar_cpf(usuario_db.cpf) == cpf_real


def test_google_assistido_funciona_sem_client_id_e_protege_contra_takeover(
    client: TestClient,
    db: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
    monkeypatch.setenv("APP_ENV", "development")

    r_cfg = client.get("/usuarios/auth/google/config")
    assert r_cfg.status_code == 200
    assert r_cfg.json()["habilitado"] is False
    assert r_cfg.json()["modo_assistido"] is True

    # 1. Cria nova conta Google assistida com aprovação automática de e-mail
    email_novo = f"google-assistido-{uuid4().hex}@gmail.com"
    r_novo = client.post(
        "/usuarios/auth/google/assistido",
        json={
            "email": email_novo,
            "nome_completo": "Arthur Google Assistido",
        },
    )
    assert r_novo.status_code == 200, r_novo.text
    assert r_novo.json()["email_verificado"] is True
    assert r_novo.json()["precisa_completar_cadastro"] is True
    assert r_novo.json()["access_token"]

    # Retorno subsequente da mesma conta Google entra direto
    r_retorno = client.post(
        "/usuarios/auth/google/assistido",
        json={"email": email_novo, "nome_completo": "Arthur Google Assistido"},
    )
    assert r_retorno.status_code == 200

    # 2. Conta tradicional existente com CPF real NÃO pode ser tomada sem confirmar o CPF do titular
    cpf_titular = _gerar_cpf_valido(707)
    email_tradicional = f"titular-protegido-{uuid4().hex}@gmail.com"
    client.post(
        "/usuarios/",
        json={
            "nome_completo": "Titular Tradicional",
            "cpf": cpf_titular,
            "email": email_tradicional,
            "senha": "SenhaForte@2026",
            "aceite_termos": True,
            "aceite_privacidade": True,
        },
    )

    # Sem CPF -> 409 exigindo CPF
    r_sem_cpf = client.post(
        "/usuarios/auth/google/assistido",
        json={"email": email_tradicional, "nome_completo": "Tentativa Sem CPF"},
    )
    assert r_sem_cpf.status_code == 409

    # Com CPF errado -> 401 bloqueado
    r_cpf_errado = client.post(
        "/usuarios/auth/google/assistido",
        json={
            "email": email_tradicional,
            "nome_completo": "Tentativa CPF Errado",
            "cpf": _gerar_cpf_valido(808),
        },
    )
    assert r_cpf_errado.status_code == 401

    # Com CPF correto do titular -> 200 autenticado e e-mail marcado como verificado
    r_cpf_correto = client.post(
        "/usuarios/auth/google/assistido",
        json={
            "email": email_tradicional,
            "nome_completo": "Titular Tradicional",
            "cpf": cpf_titular,
        },
    )
    assert r_cpf_correto.status_code == 200
    assert r_cpf_correto.json()["email_verificado"] is True


def test_verificar_access_token_google_consulta_tokeninfo_e_userinfo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "meu-client-id.apps.googleusercontent.com")

    def fake_get(url: str, params: dict = None, headers: dict = None, timeout: float = 10.0):
        req = httpx.Request("GET", url)
        if "tokeninfo" in url:
            return httpx.Response(
                200,
                json={"aud": "meu-client-id.apps.googleusercontent.com"},
                request=req,
            )
        return httpx.Response(
            200,
            json={
                "sub": "sub-userinfo-123",
                "email": "userinfo@gmail.com",
                "email_verified": True,
                "name": "Usuária Userinfo",
            },
            request=req,
        )

    monkeypatch.setattr(google_oauth.httpx, "get", fake_get)
    dados = google_oauth.verificar_access_token_google("ya29.access_token_real")
    assert dados["sub"] == "sub-userinfo-123"
    assert dados["email"] == "userinfo@gmail.com"
    assert dados["nome"] == "Usuária Userinfo"


def test_integridade_frontend_multicanal_contingencia_e_google_oauth() -> None:
    raiz = Path(__file__).resolve().parents[2] / "frontend"
    cadastro_html = (raiz / "cadastro.html").read_text(encoding="utf-8")
    login_html = (raiz / "login.html").read_text(encoding="utf-8")
    legal_js = (raiz / "js" / "legal.js").read_text(encoding="utf-8")
    cadastro_js = (raiz / "js" / "cadastro.js").read_text(encoding="utf-8")
    login_js = (raiz / "js" / "login.js").read_text(encoding="utf-8")
    style_css = (raiz / "css" / "style.css").read_text(encoding="utf-8")

    for seletor in (
        'id="channel-email"',
        'id="channel-phone"',
        'id="phone-error"',
        'id="verify-contingency-banner"',
        'id="switch-verification-channel-btn"',
    ):
        assert seletor in cadastro_html

    for seletor in (
        'id="login-verify-dialog"',
        'id="reset-channel-email"',
        'id="reset-channel-phone"',
        'id="reset-contingency-banner"',
        'id="reset-switch-channel-btn"',
    ):
        assert seletor in login_html

    for simbolo in (
        "formatarMascaraTelefone",
        "validarTelefoneBrasileiro",
        "detectarErroDominioEmail",
        "abrirModalGoogleAssistido",
        "abrirModalCompletarCadastroGoogle",
        "initTokenClient",
    ):
        assert simbolo in legal_js

    assert "/usuarios/enviar-codigo" in cadastro_js
    assert "/usuarios/enviar-codigo" in login_js
    assert ".channel-selector-grid" in style_css
    assert ".otp-contingency-banner" in style_css
    assert ".email-typo-fix-btn" in style_css
