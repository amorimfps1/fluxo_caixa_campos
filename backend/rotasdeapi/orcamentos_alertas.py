from datetime import date, timedelta
from decimal import Decimal
import calendar

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from autenticacao import obter_usuario_logado
from database import get_db
from models import AlertaLido, CategoriaMovimentacao, ContaBancaria, FluxoDinheiro, Orcamento, PreferenciaAlerta, Usuario

router = APIRouter(tags=["Orçamentos e alertas"])

class DadosOrcamento(BaseModel):
    categoria: str = Field(min_length=1, max_length=100)
    mes: date
    limite: Decimal = Field(ge=0, max_digits=12, decimal_places=2, allow_inf_nan=False)

    @field_validator("mes")
    @classmethod
    def primeiro_dia(cls, valor):
        if valor.day != 1:
            raise ValueError("Informe o primeiro dia do mês.")
        return valor

class Preferencias(BaseModel):
    orcamento: bool
    vencimento: bool

def listar(db, usuario_id, mes):
    ultimo = date(mes.year, mes.month, calendar.monthrange(mes.year, mes.month)[1])
    gastos = dict(db.query(FluxoDinheiro.categoria, func.sum(FluxoDinheiro.valor))
        .join(ContaBancaria, ContaBancaria.id == FluxoDinheiro.conta_bancaria_id)
        .filter(ContaBancaria.usuario_id == usuario_id, FluxoDinheiro.tipo.in_(["saida", "investimento"]),
                FluxoDinheiro.transferencia_id.is_(None), FluxoDinheiro.data_movimentacao >= mes,
                FluxoDinheiro.data_movimentacao <= min(ultimo, date.today()))
        .group_by(FluxoDinheiro.categoria).all())
    return [{"id": o.id, "categoria": o.categoria, "mes": o.mes, "limite": o.limite,
             "gasto": gastos.get(o.categoria, Decimal("0.00")),
             "restante": o.limite - gastos.get(o.categoria, Decimal("0.00"))}
            for o in db.query(Orcamento).filter_by(usuario_id=usuario_id, mes=mes).order_by(Orcamento.categoria).all()]

@router.get("/orcamentos")
def obter_orcamentos(mes: date = Query(...), db: Session = Depends(get_db), usuario: Usuario = Depends(obter_usuario_logado)):
    if mes.day != 1:
        raise HTTPException(422, "Informe o primeiro dia do mês.")
    return listar(db, usuario.id, mes)

@router.post("/orcamentos", status_code=201)
def criar_orcamento(dados: DadosOrcamento, db: Session = Depends(get_db), usuario: Usuario = Depends(obter_usuario_logado)):
    if not db.get(CategoriaMovimentacao, dados.categoria):
        raise HTTPException(422, "Categoria inválida.")
    item = Orcamento(usuario_id=usuario.id, **dados.model_dump())
    db.add(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Já existe orçamento para esta categoria e mês.")
    return {"id": item.id}

@router.put("/orcamentos/{item_id}")
def editar_orcamento(item_id: int, dados: DadosOrcamento, db: Session = Depends(get_db), usuario: Usuario = Depends(obter_usuario_logado)):
    item = db.query(Orcamento).filter_by(id=item_id, usuario_id=usuario.id).first()
    if not item:
        raise HTTPException(404, "Orçamento não encontrado.")
    if not db.get(CategoriaMovimentacao, dados.categoria):
        raise HTTPException(422, "Categoria inválida.")
    for chave, valor in dados.model_dump().items():
        setattr(item, chave, valor)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Já existe orçamento para esta categoria e mês.")
    return {"id": item.id}

@router.delete("/orcamentos/{item_id}")
def excluir_orcamento(item_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(obter_usuario_logado)):
    item = db.query(Orcamento).filter_by(id=item_id, usuario_id=usuario.id).first()
    if not item:
        raise HTTPException(404, "Orçamento não encontrado.")
    db.delete(item)
    db.commit()
    return {"ok": True}

@router.get("/alertas/preferencias")
def obter_preferencias(db: Session = Depends(get_db), usuario: Usuario = Depends(obter_usuario_logado)):
    p = db.get(PreferenciaAlerta, usuario.id)
    return {"orcamento": p.orcamento if p else True, "vencimento": p.vencimento if p else True}

@router.put("/alertas/preferencias")
def salvar_preferencias(dados: Preferencias, db: Session = Depends(get_db), usuario: Usuario = Depends(obter_usuario_logado)):
    p = db.get(PreferenciaAlerta, usuario.id)
    if not p:
        p = PreferenciaAlerta(usuario_id=usuario.id)
        db.add(p)
    p.orcamento, p.vencimento = dados.orcamento, dados.vencimento
    db.commit()
    return dados

@router.get("/alertas")
def obter_alertas(db: Session = Depends(get_db), usuario: Usuario = Depends(obter_usuario_logado)):
    hoje = date.today()
    prefs = obter_preferencias(db, usuario)
    lidos = {a.chave for a in db.query(AlertaLido).filter_by(usuario_id=usuario.id).all()}
    alertas = []
    if prefs["orcamento"]:
        for o in listar(db, usuario.id, hoje.replace(day=1)):
            if o["gasto"] > o["limite"]:
                chave = f"orcamento:{o['id']}"
                alertas.append({"chave": chave, "mensagem": f"Orçamento de {o['categoria']} excedido: gasto R$ {o['gasto']} de R$ {o['limite']}.", "lido": chave in lidos})
    if prefs["vencimento"]:
        movimentos = (db.query(FluxoDinheiro).join(ContaBancaria, ContaBancaria.id == FluxoDinheiro.conta_bancaria_id)
            .filter(ContaBancaria.usuario_id == usuario.id, FluxoDinheiro.tipo.in_(["saida", "investimento"]),
                    FluxoDinheiro.transferencia_id.is_(None), FluxoDinheiro.data_movimentacao >= hoje,
                    FluxoDinheiro.data_movimentacao <= hoje + timedelta(days=7)).order_by(FluxoDinheiro.data_movimentacao, FluxoDinheiro.id).all())
        for m in movimentos:
            chave = f"movimento:{m.id}:{m.data_movimentacao.isoformat()}"
            alertas.append({"chave": chave, "mensagem": f"Saída cadastrada para {m.data_movimentacao.strftime('%d/%m/%Y')}: {m.descricao} (R$ {m.valor}).", "lido": chave in lidos})
    return alertas

@router.put("/alertas/lido")
def marcar_lido(chave: str = Query(..., max_length=100), db: Session = Depends(get_db), usuario: Usuario = Depends(obter_usuario_logado)):
    if chave not in {a["chave"] for a in obter_alertas(db, usuario)}:
        raise HTTPException(404, "Alerta não encontrado.")
    if not db.get(AlertaLido, (usuario.id, chave)):
        db.add(AlertaLido(usuario_id=usuario.id, chave=chave))
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
    return {"ok": True}
