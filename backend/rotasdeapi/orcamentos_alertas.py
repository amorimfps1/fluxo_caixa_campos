"""Módulo de rotas para Orçamentos Mensais e Alertas Financeiros.

Permite que os usuários definam limites orçamentários por categoria e mês,
acompanhem gastos acumulados em tempo real e recebam alertas proativos de
limites excedidos ou vencimentos próximos nos próximos 7 dias.
"""

from datetime import date, timedelta
from decimal import Decimal
import calendar

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from autenticacao import obter_usuario_logado
from database import get_db
from esquema import (
    AlertaResponse,
    DadosOrcamento,
    OrcamentoResponse,
    PreferenciasAlerta,
    PreferenciasAlertaResponse,
)
from models import (
    AlertaLido,
    CategoriaMovimentacao,
    ContaBancaria,
    FluxoDinheiro,
    Orcamento,
    PreferenciaAlerta,
    Usuario,
)

router = APIRouter(tags=["Orçamentos e alertas"])


def calcular_gastos_e_orcamentos(
    db: Session,
    usuario_id: int,
    mes: date
) -> list[dict]:
    """Calcula os gastos reais e orçamentos configurados para o mês informado."""
    ultimo_dia = date(mes.year, mes.month, calendar.monthrange(mes.year, mes.month)[1])
    hoje = date.today()
    limite_data = min(ultimo_dia, hoje)

    gastos_query = (
        db.query(FluxoDinheiro.categoria, func.sum(FluxoDinheiro.valor))
        .join(ContaBancaria, ContaBancaria.id == FluxoDinheiro.conta_bancaria_id)
        .filter(
            ContaBancaria.usuario_id == usuario_id,
            FluxoDinheiro.tipo.in_(["saida", "investimento"]),
            FluxoDinheiro.transferencia_id.is_(None),
            FluxoDinheiro.data_movimentacao >= mes,
            FluxoDinheiro.data_movimentacao <= limite_data,
        )
        .group_by(FluxoDinheiro.categoria)
        .all()
    )
    gastos = dict(gastos_query)

    orcamentos = (
        db.query(Orcamento)
        .filter_by(usuario_id=usuario_id, mes=mes)
        .order_by(Orcamento.categoria)
        .all()
    )

    resultado = []
    for o in orcamentos:
        gasto_categoria = gastos.get(o.categoria, Decimal("0.00"))
        restante = o.limite - gasto_categoria
        percentual = (
            round(float((gasto_categoria / o.limite) * 100), 1)
            if o.limite > 0
            else 0.0
        )
        resultado.append({
            "id": o.id,
            "categoria": o.categoria,
            "mes": o.mes,
            "limite": o.limite,
            "gasto": gasto_categoria,
            "restante": restante,
            "percentual_gasto": percentual,
        })
    return resultado


@router.get(
    "/orcamentos",
    response_model=list[OrcamentoResponse],
    summary="Listar orçamentos do mês"
)
def obter_orcamentos(
    mes: date = Query(..., description="Primeiro dia do mês (YYYY-MM-01)"),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obter_usuario_logado),
):
    """Retorna os orçamentos mensais com gastos consolidados e saldo restante."""
    if mes.day != 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Informe o primeiro dia do mês."
        )
    return calcular_gastos_e_orcamentos(db, usuario.id, mes)


@router.post(
    "/orcamentos",
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar orçamento para uma categoria"
)
def criar_orcamento(
    dados: DadosOrcamento,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obter_usuario_logado),
):
    """Cria um orçamento para a categoria e mês especificados."""
    if not db.get(CategoriaMovimentacao, dados.categoria):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Categoria inválida."
        )

    item = Orcamento(
        usuario_id=usuario.id,
        categoria=dados.categoria,
        mes=dados.mes,
        limite=dados.limite,
    )
    db.add(item)
    try:
        db.commit()
        db.refresh(item)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe orçamento para esta categoria e mês."
        )
    return {"id": item.id}


@router.put(
    "/orcamentos/{item_id}",
    summary="Editar orçamento existente"
)
def editar_orcamento(
    item_id: int,
    dados: DadosOrcamento,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obter_usuario_logado),
):
    """Atualiza a categoria, mês ou limite de um orçamento existente."""
    item = db.query(Orcamento).filter_by(id=item_id, usuario_id=usuario.id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Orçamento não encontrado."
        )
    if not db.get(CategoriaMovimentacao, dados.categoria):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Categoria inválida."
        )

    for chave, valor in dados.model_dump().items():
        setattr(item, chave, valor)

    try:
        db.commit()
        db.refresh(item)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe orçamento para esta categoria e mês."
        )
    return {"id": item.id}


@router.delete(
    "/orcamentos/{item_id}",
    summary="Excluir orçamento"
)
def excluir_orcamento(
    item_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obter_usuario_logado),
):
    """Remove o orçamento especificado."""
    item = db.query(Orcamento).filter_by(id=item_id, usuario_id=usuario.id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Orçamento não encontrado."
        )
    db.delete(item)
    db.commit()
    return {"ok": True}


@router.get(
    "/alertas/preferencias",
    response_model=PreferenciasAlertaResponse,
    summary="Obter preferências de alertas"
)
def obter_preferencias(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obter_usuario_logado),
):
    """Retorna as configurações do usuário sobre quais alertas deseja receber."""
    pref = db.get(PreferenciaAlerta, usuario.id)
    return {
        "orcamento": pref.orcamento if pref else True,
        "vencimento": pref.vencimento if pref else True,
    }


@router.put(
    "/alertas/preferencias",
    response_model=PreferenciasAlertaResponse,
    summary="Atualizar preferências de alertas"
)
def salvar_preferencias(
    dados: PreferenciasAlerta,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obter_usuario_logado),
):
    """Atualiza as preferências de notificação de alertas do usuário."""
    pref = db.get(PreferenciaAlerta, usuario.id)
    if not pref:
        pref = PreferenciaAlerta(usuario_id=usuario.id)
        db.add(pref)
    pref.orcamento = dados.orcamento
    pref.vencimento = dados.vencimento
    db.commit()
    return dados


@router.get(
    "/alertas",
    response_model=list[AlertaResponse],
    summary="Listar alertas ativos e notificações"
)
def obter_alertas(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obter_usuario_logado),
):
    """Retorna os alertas de limites orçamentários excedidos e saídas próximas em 7 dias."""
    hoje = date.today()
    prefs = obter_preferencias(db, usuario)
    lidos = {
        a.chave for a in db.query(AlertaLido).filter_by(usuario_id=usuario.id).all()
    }
    alertas = []

    # 1. Alertas de orçamentos excedidos
    if prefs["orcamento"]:
        orcamentos_mes = calcular_gastos_e_orcamentos(db, usuario.id, hoje.replace(day=1))
        for o in orcamentos_mes:
            if o["gasto"] > o["limite"]:
                chave = f"orcamento:{o['id']}"
                alertas.append({
                    "chave": chave,
                    "tipo": "orcamento",
                    "titulo": "Orçamento Excedido",
                    "categoria": o["categoria"],
                    "valor": o["gasto"],
                    "mensagem": (
                        f"Orçamento de {o['categoria']} excedido: "
                        f"gasto R$ {o['gasto']} de R$ {o['limite']}."
                    ),
                    "lido": chave in lidos,
                })

    # 2. Alertas de vencimentos nos próximos 7 dias
    if prefs["vencimento"]:
        limite_futuro = hoje + timedelta(days=7)
        movimentos = (
            db.query(FluxoDinheiro)
            .join(ContaBancaria, ContaBancaria.id == FluxoDinheiro.conta_bancaria_id)
            .filter(
                ContaBancaria.usuario_id == usuario.id,
                FluxoDinheiro.tipo.in_(["saida", "investimento"]),
                FluxoDinheiro.transferencia_id.is_(None),
                FluxoDinheiro.data_movimentacao >= hoje,
                FluxoDinheiro.data_movimentacao <= limite_futuro,
            )
            .order_by(FluxoDinheiro.data_movimentacao, FluxoDinheiro.id)
            .all()
        )
        for m in movimentos:
            chave = f"movimento:{m.id}:{m.data_movimentacao.isoformat()}"
            alertas.append({
                "chave": chave,
                "tipo": "vencimento",
                "titulo": "Saída Próxima (7 dias)",
                "categoria": m.categoria,
                "data_referencia": m.data_movimentacao,
                "valor": m.valor,
                "mensagem": (
                    f"Saída cadastrada para {m.data_movimentacao.strftime('%d/%m/%Y')}: "
                    f"{m.descricao} (R$ {m.valor})."
                ),
                "lido": chave in lidos,
            })

    return alertas


@router.put(
    "/alertas/lido",
    summary="Marcar alerta como lido"
)
def marcar_lido(
    chave: str = Query(..., max_length=100, description="Chave única do alerta"),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obter_usuario_logado),
):
    """Marca um alerta específico como lido para o usuário autenticado."""
    alertas_ativos = obter_alertas(db, usuario)
    if chave not in {a["chave"] for a in alertas_ativos}:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alerta não encontrado."
        )

    if not db.get(AlertaLido, (usuario.id, chave)):
        db.add(AlertaLido(usuario_id=usuario.id, chave=chave))
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
    return {"ok": True}
