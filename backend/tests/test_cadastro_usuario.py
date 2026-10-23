from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from dados_sensiveis import descriptografar_telefone
from models import Usuario


def _dados_cadastro() -> dict[str, str]:
    return {
        "nome_completo": "Pessoa de Teste",
        "cpf": "52998224725",
        "email": f"cadastro-{uuid4().hex}@gmail.com",
        "senha": "SenhaSegura2026!",
    }


def test_cadastro_guarda_telefone_cifrado_e_retorna_valor_original(
    client: TestClient,
    db: Session,
) -> None:
    telefone = "+55 (11) 98765-4321"
    resposta = client.post(
        "/usuarios/",
        json={**_dados_cadastro(), "telefone": telefone},
    )

    assert resposta.status_code == 201, resposta.text
    assert resposta.json()["telefone"] == telefone

    usuario = db.query(Usuario).filter_by(id=resposta.json()["id"]).one()
    assert usuario.telefone is not None
    assert usuario.telefone != telefone
    assert descriptografar_telefone(usuario.telefone) == telefone


def test_cadastro_aceita_telefone_omitido(
    client: TestClient,
    db: Session,
) -> None:
    resposta = client.post("/usuarios/", json=_dados_cadastro())

    assert resposta.status_code == 201, resposta.text
    assert resposta.json()["telefone"] is None

    usuario = db.query(Usuario).filter_by(id=resposta.json()["id"]).one()
    assert usuario.telefone is None


def test_cadastro_aceita_telefone_vazio_como_opcional(
    client: TestClient,
) -> None:
    resposta = client.post(
        "/usuarios/",
        json={**_dados_cadastro(), "telefone": "   "},
    )

    assert resposta.status_code == 201, resposta.text
    assert resposta.json()["telefone"] is None


def test_cadastro_rejeita_telefone_invalido(
    client: TestClient,
    db: Session,
) -> None:
    resposta = client.post(
        "/usuarios/",
        json={**_dados_cadastro(), "telefone": "11-ABC"},
    )

    assert resposta.status_code == 422
    assert resposta.status_code == 422
    assert db.query(Usuario).count() == 0


def test_redefinir_senha_com_cpf_e_email_corretos(
    client: TestClient,
) -> None:
    dados = _dados_cadastro()
    r_criacao = client.post("/usuarios/", json=dados)
    assert r_criacao.status_code == 201

    nova_senha = "NovaSenhaForte2027@"
    r_reset = client.post(
        "/usuarios/redefinir-senha",
        json={
            "email": dados["email"],
            "cpf": "529.982.247-25",
            "nova_senha": nova_senha,
        },
    )
    assert r_reset.status_code == 200
    assert r_reset.json()["mensagem"] == "Senha redefinida com sucesso."

    r_login_antiga = client.post(
        "/login",
        data={"username": dados["email"], "password": dados["senha"]},
    )
    assert r_login_antiga.status_code == 401

    r_login_nova = client.post(
        "/login",
        data={"username": dados["email"], "password": nova_senha},
    )
    assert r_login_nova.status_code == 200
    assert "access_token" in r_login_nova.json()


def test_redefinir_senha_rejeita_cpf_incorreto_e_aplica_rate_limit(
    client: TestClient,
) -> None:
    dados = _dados_cadastro()
    r_criacao = client.post("/usuarios/", json=dados)
    assert r_criacao.status_code == 201

    cpf_outro_valido = "11144477735"
    for tentativa in range(5):
        r = client.post(
            "/usuarios/redefinir-senha",
            json={
                "email": dados["email"],
                "cpf": cpf_outro_valido,
                "nova_senha": "NovaSenhaForte2027@",
            },
        )
        if tentativa < 4:
            assert r.status_code == 400
        else:
            assert r.status_code == 429

    r_bloqueado = client.post(
        "/usuarios/redefinir-senha",
        json={
            "email": dados["email"],
            "cpf": dados["cpf"],
            "nova_senha": "NovaSenhaForte2027@",
        },
    )
    assert r_bloqueado.status_code == 429


def test_servico_email_com_mock_e_tratamento_excecao(monkeypatch) -> None:
    import smtplib
    from servicos.email import enviar_email

    # Sem variáveis SMTP configuradas -> retorna False sem lançar erro
    monkeypatch.delenv("SMTP_SERVER", raising=False)
    monkeypatch.delenv("SMTP_USER", raising=False)
    monkeypatch.delenv("SMTP_PASSWORD", raising=False)
    assert enviar_email("teste@exemplo.com", "Assunto", "<p>Oi</p>") is False

    # Com variáveis SMTP e mock de servidor funcional -> retorna True
    monkeypatch.setenv("SMTP_SERVER", "smtp.exemplo.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USER", "sistema@exemplo.com")
    monkeypatch.setenv("SMTP_PASSWORD", "segredo-smtp")
    monkeypatch.setenv("SMTP_FROM", "Fluxo <sistema@exemplo.com>")

    enviados = []

    class FakeSMTP:
        def __init__(self, host, port, timeout=10):
            self.host = host
            self.port = port

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def ehlo(self):
            pass

        def starttls(self):
            pass

        def login(self, user, password):
            assert user == "sistema@exemplo.com"
            assert password == "segredo-smtp"

        def send_message(self, msg):
            enviados.append(msg)

    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)
    assert enviar_email("destino@exemplo.com", "Teste OTP", "<b>123456</b>") is True
    assert len(enviados) == 1
    assert enviados[0]["To"] == "destino@exemplo.com"

    # Simulando falha de rede no SMTP -> retorna False sem quebrar a requisição
    class BrokenSMTP:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("Falha de conexão SMTP")

    monkeypatch.setattr(smtplib, "SMTP", BrokenSMTP)
    assert enviar_email("destino@exemplo.com", "Teste Falha", "<b>000000</b>") is False


def test_confirmacao_email_no_cadastro_com_mock_otp(
    client: TestClient,
    db: Session,
    monkeypatch,
) -> None:
    import rotasdeapi.usuario as rota_usuario

    codigos_enviados: list[tuple[str, str]] = []

    def fake_enviar_confirmacao(destinatario: str, nome: str, codigo_confirmacao: str) -> bool:
        codigos_enviados.append((destinatario, codigo_confirmacao))
        return True

    monkeypatch.setattr(
        rota_usuario,
        "enviar_email_confirmacao_cadastro",
        fake_enviar_confirmacao,
    )

    dados = _dados_cadastro()
    r_cadastro = client.post("/usuarios/", json=dados)
    assert r_cadastro.status_code == 201, r_cadastro.text
    assert r_cadastro.json()["email_verificado"] is False
    assert len(codigos_enviados) == 1
    email_enviado, codigo_gerado = codigos_enviados[0]
    assert email_enviado == dados["email"]
    assert len(codigo_gerado) == 6 and codigo_gerado.isdigit()

    r_confirmar = client.post(
        "/usuarios/confirmar-email",
        json={
            "email": dados["email"],
            "codigo_otp": codigo_gerado,
        },
    )
    assert r_confirmar.status_code == 200, r_confirmar.text

    usuario_db = db.query(Usuario).filter_by(email=dados["email"]).one()
    assert usuario_db.email_verificado is True
    assert usuario_db.codigo_verificacao_hash is None
    assert usuario_db.codigo_expira_em is None


def test_recuperacao_senha_por_codigo_otp_uso_unico_e_expiracao(
    client: TestClient,
    db: Session,
    monkeypatch,
) -> None:
    from datetime import datetime, timedelta, timezone
    import rotasdeapi.usuario as rota_usuario

    otps_capturados: list[str] = []

    def fake_enviar_otp(destinatario: str, nome: str, codigo_otp: str) -> bool:
        otps_capturados.append(codigo_otp)
        return True

    monkeypatch.setattr(
        rota_usuario,
        "enviar_email_codigo_recuperacao",
        fake_enviar_otp,
    )

    dados = _dados_cadastro()
    assert client.post("/usuarios/", json=dados).status_code == 201

    r_esqueci = client.post(
        "/usuarios/esqueci-senha",
        json={"email": dados["email"]},
    )
    assert r_esqueci.status_code == 200
    assert len(otps_capturados) == 1
    codigo_otp = otps_capturados[0]

    nova_senha = "SenhaRecuperadaOTP2027#"
    r_redefinir = client.post(
        "/usuarios/redefinir-senha",
        json={
            "email": dados["email"],
            "codigo_otp": codigo_otp,
            "nova_senha": nova_senha,
        },
    )
    assert r_redefinir.status_code == 200, r_redefinir.text

    # O código OTP deve ser descartado imediatamente após o uso (uso único)
    r_reuso = client.post(
        "/usuarios/redefinir-senha",
        json={
            "email": dados["email"],
            "codigo_otp": codigo_otp,
            "nova_senha": "OutraSenhaValida2028$",
        },
    )
    assert r_reuso.status_code == 400

    # Testar expiração de 15 minutos
    client.post("/usuarios/esqueci-senha", json={"email": dados["email"]})
    novo_otp = otps_capturados[-1]
    usuario_db = db.query(Usuario).filter_by(email=dados["email"]).one()
    usuario_db.codigo_expira_em = (
        datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=1)
    )
    db.commit()

    r_expirado = client.post(
        "/usuarios/redefinir-senha",
        json={
            "email": dados["email"],
            "codigo_otp": novo_otp,
            "nova_senha": "OutraSenhaValida2028$",
        },
    )
    assert r_expirado.status_code == 400


def test_atualizar_dados_cadastrais_e_zona_de_perigo_usuarios_me(
    client: TestClient,
    db: Session,
) -> None:
    dados = _dados_cadastro()
    assert client.post("/usuarios/", json=dados).status_code == 201

    r_login = client.post(
        "/login",
        data={"username": dados["email"], "password": dados["senha"]},
    )
    assert r_login.status_code == 200
    token = r_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    novo_email = f"atualizado-{uuid4().hex}@gmail.com"
    nova_senha = "SenhaAtualizada2027!"
    r_update = client.put(
        "/usuarios/me",
        headers=headers,
        json={
            "nome_completo": "Nome Atualizado Config",
            "email": novo_email,
            "telefone": "+55 (21) 99887-6655",
            "senha_atual": dados["senha"],
            "nova_senha": nova_senha,
        },
    )
    assert r_update.status_code == 200, r_update.text
    corpo = r_update.json()
    assert corpo["nome_completo"] == "Nome Atualizado Config"
    assert corpo["email"] == novo_email
    assert corpo["telefone"] == "+55 (21) 99887-6655"

    # Tentar excluir conta com senha incorreta deve falhar
    r_del_invalido = client.request(
        "DELETE",
        "/usuarios/me",
        headers=headers,
        json={"senha_atual": "SenhaErrada123!"},
    )
    assert r_del_invalido.status_code == 400

    # Excluir conta com a senha atual correta (Zona de Perigo)
    r_del_ok = client.request(
        "DELETE",
        "/usuarios/me",
        headers=headers,
        json={"senha_atual": nova_senha},
    )
    assert r_del_ok.status_code == 200, r_del_ok.text
    assert db.query(Usuario).filter_by(email=novo_email).first() is None


def test_saudacao_dinamica_dashboard_frontend() -> None:
    from pathlib import Path

    raiz_frontend = Path(__file__).resolve().parents[2] / "frontend"
    html_index = (raiz_frontend / "index.html").read_text(encoding="utf-8")
    js_dashboard = (raiz_frontend / "js" / "dashboard.js").read_text(encoding="utf-8")

    assert 'id="user-greeting"' in html_index
    assert "VISÃO GERAL" not in html_index
    assert "Olá, Sr(a). ${nome}" in js_dashboard
    assert 'getElementById("user-greeting")' in js_dashboard
