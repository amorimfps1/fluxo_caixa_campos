from uuid import uuid4

from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session

from dados_sensiveis import (
    criptografar_cpf,
    descriptografar_cpf,
    indice_cpf,
)
from models import Usuario


def test_cpf_e_armazenado_cifrado_e_omitido_da_resposta(
    client: TestClient,
    db: Session,
) -> None:
    cpf = "52998224725"
    resposta = client.post(
        "/usuarios/",
        json={
            "nome_completo": "Pessoa com CPF protegido",
            "cpf": cpf,
            "email": f"cpf-{uuid4().hex}@example.com",
            "senha": "SenhaSegura2026!",
        },
    )

    assert resposta.status_code == 201, resposta.text
    assert "cpf" not in resposta.json()
    usuario = db.query(Usuario).filter_by(id=resposta.json()["id"]).one()
    assert usuario.cpf != cpf
    assert cpf not in usuario.cpf
    assert descriptografar_cpf(usuario.cpf) == cpf
    assert usuario.cpf_indice == indice_cpf(cpf)
    assert cpf not in usuario.cpf_indice


def test_cadastro_detecta_cpf_duplicado_sem_persistir_cpf_em_claro(
    client: TestClient,
    db: Session,
) -> None:
    cpf = "52998224725"
    primeiro = {
        "nome_completo": "Primeira pessoa",
        "cpf": cpf,
        "email": f"primeira-{uuid4().hex}@example.com",
        "senha": "SenhaSegura2026!",
    }
    resposta_criacao = client.post("/usuarios/", json=primeiro)
    assert resposta_criacao.status_code == 201, resposta_criacao.text

    duplicado = {
        **primeiro,
        "email": f"duplicado-{uuid4().hex}@example.com",
    }
    resposta_duplicado = client.post("/usuarios/", json=duplicado)
    assert resposta_duplicado.status_code == 400
    assert resposta_duplicado.json()["detail"] == (
        "E-mail ou CPF já cadastrado."
    )

    usuario = db.query(Usuario).filter_by(
        id=resposta_criacao.json()["id"]
    ).one()
    assert usuario.cpf != cpf
    assert descriptografar_cpf(usuario.cpf) == cpf
    assert (
        db.query(Usuario)
        .filter(Usuario.cpf_indice == indice_cpf(cpf))
        .count()
        == 1
    )


def test_cadastro_rejeita_cpf_com_digitos_unicode(
    client: TestClient,
    db: Session,
) -> None:
    resposta = client.post(
        "/usuarios/",
        json={
            "nome_completo": "Pessoa com CPF Unicode",
            "cpf": "١٢٣٤٥٦٧٨٩09",
            "email": f"cpf-unicode-{uuid4().hex}@example.com",
            "senha": "SenhaSegura2026!",
        },
    )

    assert resposta.status_code == 422
    assert db.query(Usuario).count() == 0


def test_funcoes_de_cpf_rejeitam_digitos_unicode() -> None:
    cpf = "١٢٣٤٥٦٧٨٩09"

    with pytest.raises(ValueError):
        criptografar_cpf(cpf)
    with pytest.raises(ValueError):
        indice_cpf(cpf)
