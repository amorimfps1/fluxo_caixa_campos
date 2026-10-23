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
