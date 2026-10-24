from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models import ContaBancaria, FluxoDinheiro, Usuario
from esquema import (
    ContaBancariaCreate,
    ContaBancariaResponse,
    ContaBancariaUpdate
)
from autenticacao import obter_usuario_logado
from servicos.email import enviar_email_confirmacao_nova_conta_bancaria


router = APIRouter(
    prefix="/contas-bancarias",
    tags=["Contas Bancárias"]
)


# =========================================================
# CRIAR CONTA
# =========================================================

@router.post(
    "/",
    response_model=ContaBancariaResponse,
    status_code=status.HTTP_201_CREATED
)
def criar_conta(
    conta: ContaBancariaCreate,
    db: Session = Depends(get_db),
    usuario_logado: Usuario = Depends(obter_usuario_logado)
):

    nova_conta = ContaBancaria(
        usuario_id=usuario_logado.id,
        nome_banco=conta.nome_banco,
        tipo_conta=conta.tipo_conta,
        valor_conta_atual=conta.valor_conta_atual,
        ativa=conta.ativa
    )

    db.add(nova_conta)
    db.commit()
    db.refresh(nova_conta)

    enviar_email_confirmacao_nova_conta_bancaria(
        destinatario=usuario_logado.email,
        nome_usuario=usuario_logado.nome_completo,
        nome_banco=nova_conta.nome_banco,
        tipo_conta=nova_conta.tipo_conta,
        saldo_inicial=f"{Decimal(str(nova_conta.valor_conta_atual)):.2f}",
    )

    return nova_conta


# =========================================================
# LISTAR CONTAS DO USUÁRIO
# =========================================================

@router.get(
    "/",
    response_model=list[ContaBancariaResponse]
)
def listar_contas(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    usuario_logado: Usuario = Depends(obter_usuario_logado)
):

    return (
        db.query(ContaBancaria)
        .filter(
            ContaBancaria.usuario_id == usuario_logado.id
        )
        .order_by(ContaBancaria.id)
        .offset(offset)
        .limit(limit)
        .all()
    )


# =========================================================
# BUSCAR CONTA
# =========================================================

@router.get(
    "/{conta_id}",
    response_model=ContaBancariaResponse
)
def buscar_conta(
    conta_id: int,
    db: Session = Depends(get_db),
    usuario_logado: Usuario = Depends(obter_usuario_logado)
):

    conta = (
        db.query(ContaBancaria)
        .filter(
            ContaBancaria.id == conta_id,
            ContaBancaria.usuario_id == usuario_logado.id
        )
        .first()
    )

    if not conta:
        raise HTTPException(
            status_code=404,
            detail="Conta bancária não encontrada."
        )

    return conta


# =========================================================
# ATUALIZAR CONTA
# =========================================================

@router.put(
    "/{conta_id}",
    response_model=ContaBancariaResponse
)
def atualizar_conta(
    conta_id: int,
    dados: ContaBancariaUpdate,
    db: Session = Depends(get_db),
    usuario_logado: Usuario = Depends(obter_usuario_logado)
):

    conta = (
        db.query(ContaBancaria)
        .filter(
            ContaBancaria.id == conta_id,
            ContaBancaria.usuario_id == usuario_logado.id
        )
        .with_for_update()
        .first()
    )

    if not conta:
        raise HTTPException(
            status_code=404,
            detail="Conta bancária não encontrada."
        )

    if (
        dados.tipo_conta != "corrente"
        and conta.valor_conta_atual < Decimal("0.00")
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Não é possível trocar para uma conta sem limite "
                "enquanto o saldo estiver negativo."
            ),
        )

    conta.nome_banco = dados.nome_banco
    conta.tipo_conta = dados.tipo_conta
    conta.ativa = dados.ativa

    db.commit()
    db.refresh(conta)

    return conta


# =========================================================
# EXCLUIR CONTA
# =========================================================

@router.delete(
    "/{conta_id}"
)
def excluir_conta(
    conta_id: int,
    db: Session = Depends(get_db),
    usuario_logado: Usuario = Depends(obter_usuario_logado)
):

    conta = (
        db.query(ContaBancaria)
        .filter(
            ContaBancaria.id == conta_id,
            ContaBancaria.usuario_id == usuario_logado.id
        )
        .with_for_update()
        .first()
    )

    if not conta:
        raise HTTPException(
            status_code=404,
            detail="Conta bancária não encontrada."
        )

    possui_transferencia = (
        db.query(FluxoDinheiro.id)
        .filter(
            FluxoDinheiro.tipo == "transferencia",
            FluxoDinheiro.conta_bancaria_id == conta.id,
        )
        .first()
    )
    if possui_transferencia:
        raise HTTPException(
            status_code=409,
            detail=(
                "Não é possível excluir uma conta com transferências. "
                "Remova primeiro as transferências vinculadas."
            ),
        )

    db.delete(conta)
    db.commit()

    return {
        "mensagem": "Conta bancária excluída com sucesso."
    }