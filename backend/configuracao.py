import os
from pathlib import Path

from dotenv import load_dotenv


def carregar_configuracao() -> None:
    local_app_data = os.getenv("LOCALAPPDATA")
    if local_app_data:
        arquivo_segredos = (
            Path(local_app_data) / "fluxo_caixa" / "secrets.env"
        )
        if arquivo_segredos.is_file():
            load_dotenv(arquivo_segredos, override=False)

    arquivo_env_raiz = Path(__file__).resolve().parent.parent / ".env"
    if arquivo_env_raiz.is_file():
        load_dotenv(arquivo_env_raiz, override=False)

    load_dotenv(override=False)


def obter_configuracao() -> dict[str, str]:
    """Retorna um dicionário com as configurações essenciais carregadas."""
    carregar_configuracao()
    return {
        "APP_ENV": os.getenv("APP_ENV", "development"),
        "DATABASE_URL": os.getenv("DATABASE_URL", ""),
        "ACCESS_TOKEN_EXPIRE_MINUTES": os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"),
        "CORS_ORIGINS": os.getenv("CORS_ORIGINS", ""),
    }

