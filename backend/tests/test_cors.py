import os

import pytest

import api as api_mod


@pytest.mark.parametrize(
    "origem",
    [
        "http://app.fluxocaixa",
        "http://app.fluxocaixa:5173",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5500",
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


def test_cors_producao_sem_cors_origens_falha(monkeypatch):
    """APP_ENV=production sem CORS_ORIGINS deve impedir a inicialização da API."""
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("CORS_ORIGINS", raising=False)

    with pytest.raises(RuntimeError, match="CORS_ORIGINS deve ser definida"):
        api_mod._origens_cors()


def test_cors_producao_rejeita_curinga(monkeypatch):
    """APP_ENV=production com CORS_ORIGINS='*' deve ser rejeitado."""
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("CORS_ORIGINS", "*")

    with pytest.raises(RuntimeError, match="curinga"):
        api_mod._origens_cors()


def test_cors_desenvolvimento_usa_origens_padrao(monkeypatch):
    """APP_ENV=development sem CORS_ORIGINS usa as origens locais padrão."""
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.delenv("CORS_ORIGINS", raising=False)

    origens = api_mod._origens_cors()
    assert "http://app.fluxocaixa" in origens
    assert "http://app.fluxocaixa:5173" in origens
    assert "http://127.0.0.1:5173" in origens
    assert "http://127.0.0.1:5500" in origens


def test_cors_app_env_ausente_falha(monkeypatch):
    """APP_ENV ausente deve falhar ao iniciar a API."""
    monkeypatch.delenv("APP_ENV", raising=False)

    with pytest.raises(RuntimeError, match="APP_ENV não está definida"):
        api_mod._origens_cors()


def test_cors_app_env_vazio_falha(monkeypatch):
    """APP_ENV vazia deve falhar ao iniciar a API."""
    monkeypatch.setenv("APP_ENV", "")

    with pytest.raises(RuntimeError, match="APP_ENV não está definida"):
        api_mod._origens_cors()


def test_cors_app_env_invalido_falha(monkeypatch):
    """APP_ENV com valor inválido (ex.: 'prod') deve falhar ao iniciar a API."""
    monkeypatch.setenv("APP_ENV", "prod")

    with pytest.raises(RuntimeError, match="APP_ENV não está definida"):
        api_mod._origens_cors()


def test_cors_producao_valida_retorna_origens_definidas(monkeypatch):
    """APP_ENV=production com CORS_ORIGINS definida retorna apenas essas origens."""
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv(
        "CORS_ORIGINS", "https://app.fluxocaixa.com,https://api.fluxocaixa.com"
    )

    origens = api_mod._origens_cors()
    assert "https://app.fluxocaixa.com" in origens
    assert "https://api.fluxocaixa.com" in origens
    assert "http://app.fluxocaixa" not in origens
