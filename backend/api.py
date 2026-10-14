from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from dados_sensiveis import validar_chave_cpf
from rotasdeapi import (
    usuario,
    conta_bancaria,
    fluxo_dinheiro,
    calculo_financeiro,
    meta_financeira
)

validar_chave_cpf()

app = FastAPI(
    title="Sistema de Fluxo de Caixa",
    description="API para controle de finanças domésticas",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://app.fluxocaixa",
        "http://app.fluxocaixa:5173",
        "http://127.0.0.1:5173",
    ],
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
        "mensagem": "API do Fluxo de Caixa funcionando!"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)