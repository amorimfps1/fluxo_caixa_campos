from uuid import uuid4

from fastapi.testclient import TestClient

from api import app


def _cpf_valido() -> str:
    base = f"{uuid4().int % 1_000_000_000:09d}"
    primeiro_digito = (
        sum(
            int(digito) * peso
            for digito, peso in zip(base, range(10, 1, -1))
        )
        * 10
    ) % 11
    if primeiro_digito == 10:
        primeiro_digito = 0

    dez_digitos = base + str(primeiro_digito)
    segundo_digito = (
        sum(
            int(digito) * peso
            for digito, peso in zip(dez_digitos, range(11, 1, -1))
        )
        * 10
    ) % 11
    if segundo_digito == 10:
        segundo_digito = 0

    return f"{dez_digitos}{segundo_digito}"


def _dados_cadastro() -> dict[str, str]:
    marcador = uuid4().hex
    return {
        "nome_completo": "Pessoa de Teste",
        "cpf": _cpf_valido(),
        "email": f"limite-{marcador}@example.com",
        "senha": "SenhaSegura2026!",
    }


def test_login_aplica_limite_por_ip_independente_da_conta(
    client: TestClient,
) -> None:
    for tentativa in range(4):
        resposta = client.post(
            "/login",
            data={
                "username": f"nao-existe-{tentativa}@example.com",
                "password": "SenhaIncorreta2026!",
            },
        )
        assert resposta.status_code == 401
        assert resposta.json()["detail"] == "E-mail ou senha inválidos."

    resposta = client.post(
        "/login",
        data={
            "username": "outra-conta@example.com",
            "password": "SenhaIncorreta2026!",
        },
    )
    assert resposta.status_code == 429


def test_login_aplica_limite_por_conta_entre_ips(
    client: TestClient,
) -> None:
    usuario = _dados_cadastro()
    cadastro = client.post("/usuarios/", json=usuario)
    assert cadastro.status_code == 201, cadastro.text

    for tentativa in range(4):
        with TestClient(
            app,
            client=(f"198.51.100.{tentativa + 1}", 50000),
        ) as cliente_ip:
            resposta = cliente_ip.post(
                "/login",
                data={
                    "username": usuario["email"],
                    "password": "SenhaIncorreta2026!",
                },
            )
        assert resposta.status_code == 401

    with TestClient(
        app,
        client=("198.51.100.5", 50000),
    ) as cliente_ip:
        resposta = cliente_ip.post(
            "/login",
            data={
                "username": usuario["email"],
                "password": "SenhaIncorreta2026!",
            },
        )
    assert resposta.status_code == 429


def test_cadastro_aplica_limite_por_ip(client: TestClient) -> None:
    for _ in range(5):
        resposta = client.post("/usuarios/", json=_dados_cadastro())
        assert resposta.status_code == 201, resposta.text

    resposta = client.post("/usuarios/", json=_dados_cadastro())
    assert resposta.status_code == 429
