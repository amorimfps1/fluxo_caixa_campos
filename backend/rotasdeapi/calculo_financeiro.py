from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models import (
    CalculoFinanceiro,
    ContaBancaria,
    Usuario
)
from esquema import (
    CalculoFinanceiroCreate,
    CalculoFinanceiroResponse,
    ResumoPeriodoResponse,
)
from financeiro import (
    calcular_resumo_anual,
    calcular_resumo_mensal,
    calcular_resumo_periodo,
    salvar_calculo_financeiro,
)
from autenticacao import obter_usuario_logado


router = APIRouter(
    prefix="/calculos-financeiros",
    tags=["Cálculos Financeiros"]
)


# =========================================================
# CRIAR CÁLCULO
# =========================================================

@router.post(
    "/",
    response_model=CalculoFinanceiroResponse,
    status_code=status.HTTP_201_CREATED
)
def criar_calculo(
    dados: CalculoFinanceiroCreate,
    db: Session = Depends(get_db),
    usuario_logado: Usuario = Depends(obter_usuario_logado)
):

    conta = (
        db.query(ContaBancaria)
        .filter(
            ContaBancaria.id == dados.conta_bancaria_id,
            ContaBancaria.usuario_id == usuario_logado.id
        )
        .first()
    )

    if not conta:
        raise HTTPException(
            status_code=404,
            detail="Conta bancária não encontrada."
        )

    if not conta.ativa:
        raise HTTPException(
            status_code=400,
            detail="A conta bancária está desativada."
        )

    try:

        if dados.tipo_calculo == "mensal":
            resumo = calcular_resumo_mensal(
                db,
                dados.conta_bancaria_id,
                dados.data_inicio.month,
                dados.data_inicio.year,
            )
        elif dados.tipo_calculo == "anual":
            resumo = calcular_resumo_anual(
                db,
                dados.conta_bancaria_id,
                dados.data_inicio.year,
            )
        else:
            resumo = calcular_resumo_periodo(
                db,
                dados.conta_bancaria_id,
                dados.data_inicio,
                dados.data_fim,
            )

    except ValueError as erro:

        raise HTTPException(
            status_code=400,
            detail=str(erro)
        )

    calculo = salvar_calculo_financeiro(
        db=db,
        conta_bancaria_id=dados.conta_bancaria_id,
        tipo_calculo=dados.tipo_calculo,
        data_inicio=dados.data_inicio,
        data_fim=dados.data_fim,
        valor_original=resumo["saldo_inicial"],
        total_entradas=resumo["total_entradas"],
        total_saidas=resumo["total_saidas"],
        total_investimentos=resumo["total_investimentos"],
        total_transferencias_recebidas=resumo[
            "total_transferencias_recebidas"
        ],
        total_transferencias_enviadas=resumo[
            "total_transferencias_enviadas"
        ],
        total_ajustes=resumo["total_ajustes"],
        valor_final=resumo["saldo_final"],
    )

    return calculo


# =========================================================
# RESUMO FINANCEIRO POR PERÍODO CUSTOMIZADO
# =========================================================

@router.get(
    "/resumo",
    response_model=ResumoPeriodoResponse,
)
def obter_resumo_periodo(
    data_inicio: date,
    data_fim: date,
    conta_bancaria_id: int | None = None,
    db: Session = Depends(get_db),
    usuario_logado: Usuario = Depends(obter_usuario_logado),
):
    if data_fim < data_inicio:
        raise HTTPException(
            status_code=422,
            detail="data_fim não pode ser anterior a data_inicio.",
        )

    if conta_bancaria_id is not None:
        conta = (
            db.query(ContaBancaria)
            .filter(
                ContaBancaria.id == conta_bancaria_id,
                ContaBancaria.usuario_id == usuario_logado.id,
            )
            .first()
        )
        if not conta:
            raise HTTPException(
                status_code=404,
                detail="Conta bancária não encontrada.",
            )
        try:
            return calcular_resumo_periodo(
                db,
                conta.id,
                data_inicio,
                data_fim,
            )
        except ValueError as erro:
            raise HTTPException(status_code=400, detail=str(erro))

    contas = (
        db.query(ContaBancaria)
        .filter(ContaBancaria.usuario_id == usuario_logado.id)
        .all()
    )

    if data_inicio > date.today():
        raise HTTPException(
            status_code=400,
            detail="A data inicial não pode estar no futuro.",
        )

    acumulado = {
        "conta_bancaria_id": None,
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "saldo_inicial": Decimal("0.00"),
        "total_entradas": Decimal("0.00"),
        "total_saidas": Decimal("0.00"),
        "total_investimentos": Decimal("0.00"),
        "total_transferencias_recebidas": Decimal("0.00"),
        "total_transferencias_enviadas": Decimal("0.00"),
        "total_ajustes": Decimal("0.00"),
        "saldo_final": Decimal("0.00"),
    }

    for conta in contas:
        resumo_conta = calcular_resumo_periodo(
            db,
            conta.id,
            data_inicio,
            data_fim,
        )
        for chave in (
            "saldo_inicial",
            "total_entradas",
            "total_saidas",
            "total_investimentos",
            "total_transferencias_recebidas",
            "total_transferencias_enviadas",
            "total_ajustes",
            "saldo_final",
        ):
            acumulado[chave] += resumo_conta[chave]

    return acumulado


# =========================================================
# LISTAR CÁLCULOS DO USUÁRIO
# =========================================================

@router.get(
    "/",
    response_model=list[CalculoFinanceiroResponse]
)
def listar_calculos(
    conta_bancaria_id: int | None = None,
    data_inicio: date | None = None,
    data_fim: date | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    usuario_logado: Usuario = Depends(obter_usuario_logado)
):

    if data_inicio and data_fim and data_fim < data_inicio:
        raise HTTPException(
            status_code=422,
            detail="data_fim não pode ser anterior a data_inicio.",
        )
    consulta = (
        db.query(CalculoFinanceiro)
        .join(
            ContaBancaria,
            CalculoFinanceiro.conta_bancaria_id ==
            ContaBancaria.id
        )
        .filter(
            ContaBancaria.usuario_id == usuario_logado.id
        )
    )
    if conta_bancaria_id is not None:
        consulta = consulta.filter(
            CalculoFinanceiro.conta_bancaria_id == conta_bancaria_id
        )
    if data_inicio:
        consulta = consulta.filter(
            CalculoFinanceiro.data_inicio >= data_inicio
        )
    if data_fim:
        consulta = consulta.filter(CalculoFinanceiro.data_fim <= data_fim)
    return (
        consulta.order_by(CalculoFinanceiro.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


# =========================================================
# BUSCAR CÁLCULO
# =========================================================

@router.get(
    "/{calculo_id}",
    response_model=CalculoFinanceiroResponse
)
def buscar_calculo(
    calculo_id: int,
    db: Session = Depends(get_db),
    usuario_logado: Usuario = Depends(obter_usuario_logado)
):

    calculo = (
        db.query(CalculoFinanceiro)
        .join(
            ContaBancaria,
            CalculoFinanceiro.conta_bancaria_id ==
            ContaBancaria.id
        )
        .filter(
            CalculoFinanceiro.id == calculo_id,
            ContaBancaria.usuario_id == usuario_logado.id
        )
        .first()
    )

    if not calculo:
        raise HTTPException(
            status_code=404,
            detail="Cálculo financeiro não encontrado."
        )

    return calculo


# =========================================================
# EXCLUIR CÁLCULO
# =========================================================

@router.delete(
    "/{calculo_id}"
)
def excluir_calculo(
    calculo_id: int,
    db: Session = Depends(get_db),
    usuario_logado: Usuario = Depends(obter_usuario_logado)
):

    calculo = (
        db.query(CalculoFinanceiro)
        .join(
            ContaBancaria,
            CalculoFinanceiro.conta_bancaria_id ==
            ContaBancaria.id
        )
        .filter(
            CalculoFinanceiro.id == calculo_id,
            ContaBancaria.usuario_id == usuario_logado.id
        )
        .first()
    )

    if not calculo:
        raise HTTPException(
            status_code=404,
            detail="Cálculo financeiro não encontrado."
        )

    db.delete(calculo)
    db.commit()

    return {
        "mensagem": "Cálculo financeiro excluído com sucesso."
    }
