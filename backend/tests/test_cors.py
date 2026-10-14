import pytest


@pytest.mark.parametrize(
    "origem",
    [
        "http://app.fluxocaixa",
        "http://app.fluxocaixa:5173",
        "http://127.0.0.1:5173",
    ],
)
def test_cors_permite_preflight_das_origens_locais(client, origem):
    resposta = client.options(
        "/contas-bancarias/",
        headers={
            "Origin": origem,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )

    assert resposta.status_code == 200
    assert resposta.headers["access-control-allow-origin"] == origem
    assert "access-control-allow-credentials" not in resposta.headers
    assert "POST" in resposta.headers["access-control-allow-methods"]
    assert "*" not in resposta.headers["access-control-allow-methods"]
    assert "authorization" in resposta.headers[
        "access-control-allow-headers"
    ].lower()
    assert "content-type" in resposta.headers[
        "access-control-allow-headers"
    ].lower()


@pytest.mark.parametrize(
    "origem",
    [
        "http://localhost:5173",
        "http://origem-nao-autorizada",
    ],
)
def test_cors_rejeita_origem_nao_autorizada(client, origem):
    resposta = client.options(
        "/contas-bancarias/",
        headers={
            "Origin": origem,
            "Access-Control-Request-Method": "POST",
        },
    )

    assert resposta.status_code == 400
    assert "access-control-allow-origin" not in resposta.headers
