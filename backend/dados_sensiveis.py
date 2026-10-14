import base64
import hashlib
import hmac
import os
from functools import lru_cache

from configuracao import carregar_configuracao
from cryptography.fernet import Fernet, InvalidToken


def _chave_cpf() -> bytes:
    carregar_configuracao()
    chave = os.getenv("CPF_ENCRYPTION_KEY")
    if not chave:
        raise RuntimeError(
            "CPF_ENCRYPTION_KEY não está configurada no ambiente."
        )
    try:
        chave_bytes = chave.encode("ascii")
        base64.urlsafe_b64decode(chave_bytes)
        _fernet(chave_bytes)
    except (UnicodeEncodeError, ValueError) as erro:
        raise RuntimeError(
            "CPF_ENCRYPTION_KEY deve ser uma chave Fernet válida."
        ) from erro
    return chave_bytes


def validar_chave_cpf() -> None:
    _chave_cpf()


@lru_cache(maxsize=1)
def _fernet(chave: bytes) -> Fernet:
    return Fernet(chave)


def criptografar_cpf(cpf: str) -> str:
    if len(cpf) != 11 or not cpf.isdigit():
        raise ValueError("CPF deve conter exatamente 11 dígitos.")
    return _fernet(_chave_cpf()).encrypt(cpf.encode("ascii")).decode("ascii")


def descriptografar_cpf(cpf_cifrado: str) -> str:
    try:
        return _fernet(_chave_cpf()).decrypt(
            cpf_cifrado.encode("ascii")
        ).decode("ascii")
    except (InvalidToken, UnicodeEncodeError, UnicodeDecodeError) as erro:
        raise ValueError("Não foi possível descriptografar o CPF.") from erro


def indice_cpf(cpf: str) -> str:
    if len(cpf) != 11 or not cpf.isdigit():
        raise ValueError("CPF deve conter exatamente 11 dígitos.")
    chave_mestra = base64.urlsafe_b64decode(_chave_cpf())
    chave_indice = hmac.digest(
        chave_mestra,
        b"fluxo_caixa:cpf:index:v1",
        hashlib.sha256,
    )
    return hmac.new(
        chave_indice,
        cpf.encode("ascii"),
        hashlib.sha256,
    ).hexdigest()


def criptografar_telefone(telefone: str) -> str:
    if not telefone:
        raise ValueError("Telefone não pode ficar vazio.")
    return _fernet(_chave_cpf()).encrypt(
        telefone.encode("utf-8")
    ).decode("ascii")


def descriptografar_telefone(telefone_cifrado: str) -> str:
    try:
        return _fernet(_chave_cpf()).decrypt(
            telefone_cifrado.encode("ascii")
        ).decode("utf-8")
    except (InvalidToken, UnicodeEncodeError, UnicodeDecodeError) as erro:
        raise ValueError(
            "Não foi possível descriptografar o telefone."
        ) from erro
