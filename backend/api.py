from contextlib import asynccontextmanager
import os
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from configuracao import carregar_configuracao
from dados_sensiveis import validar_chave_cpf
from database import garantir_esquema_banco
from rotasdeapi import (
    usuario,
    conta_bancaria,
    fluxo_dinheiro,
    calculo_financeiro,
    meta_financeira,
    orcamentos_alertas
)

carregar_configuracao()
validar_chave_cpf()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    garantir_esquema_banco()
    yield


app = FastAPI(
    title="Sistema de Fluxo de Caixa",
    description="API REST para controle e planejamento financeiro pessoal",
    version="1.0.0",
    lifespan=lifespan,
)


_TRADUCOES_HTTP_PADRAO = {
    "Not authenticated": "Não autenticado. Faça login para continuar.",
    "Not Found": "Recurso não encontrado.",
    "Method Not Allowed": "Método HTTP não permitido para este endereço.",
    "Internal Server Error": "Erro interno do servidor.",
    "Bad Request": "Requisição inválida.",
    "Forbidden": "Acesso negado.",
    "Unauthorized": "Não autorizado.",
}


def _traduzir_mensagem_validacao(erro: dict[str, Any]) -> str:
    """Converte mensagens padrão em inglês do Pydantic v2/FastAPI para PT-BR."""
    tipo = str(erro.get("type") or "")
    msg = str(erro.get("msg") or "")
    ctx = erro.get("ctx") or {}

    for prefixo in ("Value error, ", "Assertion failed, "):
        if msg.startswith(prefixo):
            msg = msg[len(prefixo):]

    msg_lower = msg.lower()
    if "email" in msg_lower and (
        "value is not a valid email" in msg_lower
        or "an email address" in msg_lower
        or "domain name" in msg_lower
        or "part after the @" in msg_lower
        or "there must be something" in msg_lower
    ):
        return "Informe um endereço de e-mail válido."

    if tipo == "missing":
        return "Campo obrigatório."
    if tipo == "extra_forbidden":
        return "Campo adicional não permitido."
    if tipo == "string_type":
        return "O valor informado deve ser um texto."
    if tipo == "string_too_short":
        minimo = ctx.get("min_length")
        if minimo == 8 and "senha" in ".".join(str(p) for p in erro.get("loc", ())):
            return "A senha deve possuir no mínimo 8 caracteres."
        if minimo is not None:
            return f"O campo deve conter no mínimo {minimo} caractere(s)."
        return "O texto informado é muito curto."
    if tipo == "string_too_long":
        maximo = ctx.get("max_length")
        if maximo is not None:
            return f"O campo deve conter no máximo {maximo} caracteres."
        return "O texto informado excede o tamanho máximo."
    if tipo in ("int_parsing", "int_type"):
        return "Informe um número inteiro válido."
    if tipo in ("float_parsing", "float_type", "decimal_parsing", "decimal_type"):
        return "Informe um valor numérico válido."
    if tipo == "decimal_max_places":
        casas = ctx.get("decimal_places", 2)
        return f"O valor deve ter no máximo {casas} casas decimais."
    if tipo in ("decimal_max_digits", "decimal_whole_digits"):
        return "O valor numérico excede a quantidade máxima de dígitos permitida."
    if tipo == "greater_than":
        limite = ctx.get("gt", 0)
        return f"O valor deve ser maior que {limite}."
    if tipo == "greater_than_equal":
        limite = ctx.get("ge", 0)
        return f"O valor deve ser maior ou igual a {limite}."
    if tipo == "less_than":
        limite = ctx.get("lt", "")
        return f"O valor deve ser menor que {limite}."
    if tipo == "less_than_equal":
        limite = ctx.get("le", "")
        return f"O valor deve ser menor ou igual a {limite}."
    if tipo in ("bool_parsing", "bool_type"):
        return "Informe um valor booleano válido (verdadeiro ou falso)."
    if tipo in ("date_parsing", "date_from_datetime_parsing", "date_type", "date_from_datetime_inexact"):
        return "Informe uma data válida no formato AAAA-MM-DD."
    if tipo in ("datetime_parsing", "datetime_from_date_parsing", "datetime_type"):
        return "Informe uma data e hora válidas."
    if tipo == "literal_error":
        esperado = ctx.get("expected", "")
        return f"Opção inválida. Valores aceitos: {esperado}." if esperado else "Opção inválida."
    if tipo == "json_invalid":
        return "O corpo da requisição não contém um JSON válido."
    if tipo in ("dict_type", "model_attributes_type", "model_type"):
        return "Formato de dados inválido. Envie um objeto JSON válido."

    return msg


@app.exception_handler(RequestValidationError)
async def tratar_erro_validacao_ptbr(
    _request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    detalhes = []
    for erro in exc.errors():
        item: dict[str, Any] = {
            "type": erro.get("type", "validation_error"),
            "loc": erro.get("loc", ()),
            "msg": _traduzir_mensagem_validacao(erro),
        }
        if "input" in erro:
            item["input"] = erro["input"]
        detalhes.append(item)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": detalhes}),
    )


@app.exception_handler(StarletteHTTPException)
async def tratar_excecao_http_ptbr(
    _request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    detalhe = exc.detail
    if isinstance(detalhe, str) and detalhe in _TRADUCOES_HTTP_PADRAO:
        detalhe = _TRADUCOES_HTTP_PADRAO[detalhe]
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": detalhe},
        headers=exc.headers,
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
                "CORS_ORIGINS deve ser definida em produção (APP_ENV=production)."
            )
        origens = [origem.strip() for origem in origens_env.split(",") if origem.strip()]
        if "*" in origens:
            raise RuntimeError(
                "CORS_ORIGINS não permite curinga '*' em produção. "
                "Liste explicitamente os domínios confiáveis."
            )
        return origens

    # Desenvolvimento: permissivo com as origens locais padrão.
    padrao = [
        "http://app.fluxocaixa",
        "http://app.fluxocaixa:5173",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5500",
        "https://fluxo-caixa-coral-dois.vercel.app",
        "https://fluxo-caixa-coral-two.vercel.app",
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
app.include_router(orcamentos_alertas.router)


@app.get("/")
def inicio():
    return {
        "mensagem": "API do Fluxo de Caixa funcionando!",
        "status": "online"
    }


@app.get("/health")
def status_saude():
    return {
        "status": "operacional",
        "ambiente": os.getenv("APP_ENV", "development"),
        "versao": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)
