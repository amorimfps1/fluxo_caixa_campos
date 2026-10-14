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
    assert db.query(Usuario).count() == 0
