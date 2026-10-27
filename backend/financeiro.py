import calendar
from datetime import date
from decimal import Decimal
from typing import TypedDict

from sqlalchemy import func
from sqlalchemy.orm import Session

from models import CalculoFinanceiro, ContaBancaria, FluxoDinheiro


ZERO = Decimal("0.00")


class ResumoFinanceiro(TypedDict):
    conta_bancaria_id: int
    data_inicio: date
    data_fim: date
    saldo_inicial: Decimal
    total_entradas: Decimal
    total_saidas: Decimal
    total_investimentos: Decimal
    total_transferencias_recebidas: Decimal
    total_transferencias_enviadas: Decimal
    total_ajustes: Decimal
    saldo_final: Decimal


def _soma_movimentacoes(db: Session, *filtros) -> Decimal:
    resultado = (
        db.query(func.coalesce(func.sum(FluxoDinheiro.valor), 0))
        .filter(*filtros)
        .scalar()
    )
    return Decimal(str(resultado or ZERO))


def _filtro_entradas():
    return FluxoDinheiro.tipo == "entrada"


def _filtro_saidas():
    return FluxoDinheiro.tipo.in_(["saida", "investimento"])


def _filtro_transferencias(direcao: str):
    return (
        (FluxoDinheiro.tipo == "transferencia")
        & (FluxoDinheiro.transferencia_direcao == direcao)
    )


def obter_saldo_conta(db: Session, conta_bancaria_id: int) -> Decimal:
    conta = (
        db.query(ContaBancaria)
        .filter(ContaBancaria.id == conta_bancaria_id)
        .first()
    )
    if conta is None:
        raise ValueError("Conta bancária não encontrada.")
    return Decimal(str(conta.valor_conta_atual))


def calcular_movimentacoes_apos_data(
    db: Session,
    conta_bancaria_id: int,
    data_inicio: date,
) -> Decimal:
    filtros = (
        FluxoDinheiro.conta_bancaria_id == conta_bancaria_id,
        FluxoDinheiro.data_movimentacao >= data_inicio,
    )
    entradas = _soma_movimentacoes(db, *filtros, _filtro_entradas())
    saidas = _soma_movimentacoes(db, *filtros, FluxoDinheiro.tipo.in_(["saida", "investimento"]))
    recebidas = _soma_movimentacoes(
        db, *filtros, _filtro_transferencias("destino")
    )
    enviadas = _soma_movimentacoes(
        db, *filtros, _filtro_transferencias("origem")
    )
    ajustes = _soma_movimentacoes(
        db, *filtros, FluxoDinheiro.tipo == "ajuste"
    )
    return entradas + recebidas - saidas - enviadas + ajustes


def calcular_saldo_inicial(
    db: Session,
    conta_bancaria_id: int,
    data_inicio: date,
) -> Decimal:
    saldo_atual = obter_saldo_conta(db, conta_bancaria_id)
    variacao_apos_data = calcular_movimentacoes_apos_data(
        db,
        conta_bancaria_id,
        data_inicio,
    )
    return saldo_atual - variacao_apos_data


def calcular_entradas(
    db: Session,
    conta_bancaria_id: int,
    data_inicio: date,
    data_fim: date,
) -> Decimal:
    return _soma_movimentacoes(
        db,
        FluxoDinheiro.conta_bancaria_id == conta_bancaria_id,
        _filtro_entradas(),
        FluxoDinheiro.data_movimentacao >= data_inicio,
        FluxoDinheiro.data_movimentacao <= data_fim,
    )


def calcular_saidas(
    db: Session,
    conta_bancaria_id: int,
    data_inicio: date,
    data_fim: date,
) -> Decimal:
    return _soma_movimentacoes(
        db,
        FluxoDinheiro.conta_bancaria_id == conta_bancaria_id,
        _filtro_saidas(),
        FluxoDinheiro.data_movimentacao >= data_inicio,
        FluxoDinheiro.data_movimentacao <= data_fim,
    )


def calcular_investimentos(
    db: Session,
    conta_bancaria_id: int,
    data_inicio: date,
    data_fim: date,
) -> Decimal:
    return _soma_movimentacoes(
        db,
        FluxoDinheiro.conta_bancaria_id == conta_bancaria_id,
        FluxoDinheiro.tipo.in_(["saida", "investimento"]),
        (FluxoDinheiro.categoria == "investimento") | (FluxoDinheiro.tipo_investimento.isnot(None)),
        FluxoDinheiro.data_movimentacao >= data_inicio,
        FluxoDinheiro.data_movimentacao <= data_fim,
    )


def calcular_transferencias(
    db: Session,
    conta_bancaria_id: int,
    data_inicio: date,
    data_fim: date,
    direcao: str,
) -> Decimal:
    return _soma_movimentacoes(
        db,
        FluxoDinheiro.conta_bancaria_id == conta_bancaria_id,
        _filtro_transferencias(direcao),
        FluxoDinheiro.data_movimentacao >= data_inicio,
        FluxoDinheiro.data_movimentacao <= data_fim,
    )


def calcular_ajustes(
    db: Session,
    conta_bancaria_id: int,
    data_inicio: date,
    data_fim: date,
) -> Decimal:
    return _soma_movimentacoes(
        db,
        FluxoDinheiro.conta_bancaria_id == conta_bancaria_id,
        FluxoDinheiro.tipo == "ajuste",
        FluxoDinheiro.data_movimentacao >= data_inicio,
        FluxoDinheiro.data_movimentacao <= data_fim,
    )


def calcular_resumo_periodo(
    db: Session,
    conta_bancaria_id: int,
    data_inicio: date,
    data_fim: date,
) -> ResumoFinanceiro:
    if data_fim < data_inicio:
        raise ValueError("A data final não pode ser anterior à data inicial.")
    if data_inicio > date.today():
        raise ValueError("A data inicial não pode estar no futuro.")

    saldo_inicial = calcular_saldo_inicial(
        db,
        conta_bancaria_id,
        data_inicio,
    )
    total_entradas = calcular_entradas(
        db,
        conta_bancaria_id,
        data_inicio,
        data_fim,
    )
    total_saidas = calcular_saidas(
        db,
        conta_bancaria_id,
        data_inicio,
        data_fim,
    )
    total_investimentos = calcular_investimentos(
        db,
        conta_bancaria_id,
        data_inicio,
        data_fim,
    )
    total_transferencias_recebidas = calcular_transferencias(
        db, conta_bancaria_id, data_inicio, data_fim, "destino"
    )
    total_transferencias_enviadas = calcular_transferencias(
        db, conta_bancaria_id, data_inicio, data_fim, "origem"
    )
    total_ajustes = calcular_ajustes(
        db, conta_bancaria_id, data_inicio, data_fim
    )

    return {
        "conta_bancaria_id": conta_bancaria_id,
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "saldo_inicial": saldo_inicial,
        "total_entradas": total_entradas,
        "total_saidas": total_saidas,
        "total_investimentos": total_investimentos,
        "total_transferencias_recebidas": total_transferencias_recebidas,
        "total_transferencias_enviadas": total_transferencias_enviadas,
        "total_ajustes": total_ajustes,
        "saldo_final": (
            saldo_inicial
            + total_entradas
            - total_saidas
            + total_transferencias_recebidas
            - total_transferencias_enviadas
            + total_ajustes
        ),
    }


def calcular_resumo_mensal(
    db: Session,
    conta_bancaria_id: int,
    mes: int,
    ano: int,
) -> ResumoFinanceiro:
    if mes < 1 or mes > 12:
        raise ValueError("O mês deve estar entre 1 e 12.")
    data_inicio = date(ano, mes, 1)
    data_fim = date(ano, mes, calendar.monthrange(ano, mes)[1])
    return calcular_resumo_periodo(
        db,
        conta_bancaria_id,
        data_inicio,
        data_fim,
    )


def calcular_resumo_anual(
    db: Session,
    conta_bancaria_id: int,
    ano: int,
) -> ResumoFinanceiro:
    return calcular_resumo_periodo(
        db,
        conta_bancaria_id,
        date(ano, 1, 1),
        date(ano, 12, 31),
    )


def salvar_calculo_financeiro(
    db: Session,
    conta_bancaria_id: int,
    tipo_calculo: str,
    data_inicio: date,
    data_fim: date,
    valor_original: Decimal,
    total_entradas: Decimal,
    total_saidas: Decimal,
    total_investimentos: Decimal,
    total_transferencias_recebidas: Decimal,
    total_transferencias_enviadas: Decimal,
    total_ajustes: Decimal,
    valor_final: Decimal,
) -> CalculoFinanceiro:
    calculo = CalculoFinanceiro(
        conta_bancaria_id=conta_bancaria_id,
        tipo_calculo=tipo_calculo,
        data_inicio=data_inicio,
        data_fim=data_fim,
        valor_original=valor_original,
        total_entradas=total_entradas,
        total_saidas=total_saidas,
        total_investimentos=total_investimentos,
        total_transferencias_recebidas=total_transferencias_recebidas,
        total_transferencias_enviadas=total_transferencias_enviadas,
        total_ajustes=total_ajustes,
        valor_final=valor_final,
    )
    db.add(calculo)
    db.commit()
    db.refresh(calculo)
    return calculo
