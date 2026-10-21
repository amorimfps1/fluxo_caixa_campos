import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from configuracao import carregar_configuracao
from dados_sensiveis import validar_chave_cpf
from rotasdeapi import (
    usuario,
    conta_bancaria,
    fluxo_dinheiro,
    calculo_financeiro,
    meta_financeira
)

carregar_configuracao()
validar_chave_cpf()

app = FastAPI(
    title="Sistema de Fluxo de Caixa",
    description="API REST para controle e planejamento financeiro pessoal",
    version="1.0.0"
)
def _validar_app_env() -> str:
    """Valida e retorna o valor de APP_ENV.

    APP_ENV é obrigatório e deve ser "development" ou "production".
    """
    app_env = os.getenv("APP_ENV", "").strip().lower()
    if app_env not in ("development", "production"):
        raise RuntimeError(
            "APP_ENV não está definida ou é inválida. "
            'Defina APP_ENV="development" ou APP_ENV="production".'
        )
    return app_env

def _origens_cors() -> list[str]:
    """Retorna as origens permitidas pelo CORS.

    Em desenvolvimento (APP_ENV diferente de "production") aceita as origens
    locais padrão. Em produção, restringe a lista definida em CORS_ORIGINS.
    """
    app_env = _validar_app_env()
    origens_env = os.getenv("CORS_ORIGINS", "").strip()

    if app_env == "production":
        if not origens_env:
            raise RuntimeError(
                "CORS_ORIGINS deve ser definida em produção (APP_ENV=production).")      
        origens = [origem.strip() for origem in origens_env.split(",") if origem.strip()]
        if "*" in origens:
            raise RuntimeError(
                "CORS_ORIGINS não permite curinga '*' em produção. "
                "Liste explicitamente as origens confiáveis."
            )
        return origens

    # Desenvolvimento: permissivo com as origens locais padrão.
    padrao = [
        "http://app.fluxocaixa",
        "http://app.fluxocaixa:5173",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5500",
        "https://fluxo-caixa-coral-dois.vercel.app",
        "https://fluxo-caixa-4nnewcrbc-camposxresenhudos.vercel.app",
    ]
    if origens_env:
        return [origem.strip() for origem in origens_env.split(",") if origem.strip()]
    return padrao


app.add_middleware(
    CORSMiddleware,
    allow_origins=_origens_cors(),
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(usuario.router)
app.include_router(conta_bancaria.router)
app.include_router(fluxo_dinheiro.router)
app.include_router(calculo_financeiro.router)
app.include_router(meta_financeira.router)


@app.get("/")
def inicio():
    return {
        "mensagem": "API do Fluxo de Caixa funcionando!",
        "status": "online"
    }


@app.get("/health")
def status_saude():
    return {
        "status": "healthy",
        "ambiente": os.getenv("APP_ENV", "development"),
        "versao": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)