import csv
import io
from datetime import date
from decimal import Decimal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from autenticacao import obter_usuario_logado
from database import get_db
from models import (
    ContaBancaria,
    FluxoDinheiro,
    Usuario,
)
from esquema import (
    FluxoDinheiroCreate,
    FluxoDinheiroResponse,
    FluxoDinheiroUpdate,
    InvestimentoCreate,
)


router = APIRouter(
    prefix="/fluxo-dinheiro",
    tags=["Fluxo de Dinheiro"],
)


def _obter_contas_bloqueadas(
    db: Session,
    conta_ids: set[int],
    usuario_id: int,
) -> dict[int, ContaBancaria]:
    contas = (
        db.query(ContaBancaria)
        .filter(
            ContaBancaria.id.in_(conta_ids),
            ContaBancaria.usuario_id == usuario_id,
        )
        .order_by(ContaBancaria.id)
        .with_for_update()
        .all()
    )
    resultado = {conta.id: conta for conta in contas}
    if len(resultado) != len(conta_ids):
        raise HTTPException(
            status_code=404,
            detail="Uma ou mais contas bancárias não foram encontradas.",
        )
    if any(not conta.ativa for conta in resultado.values()):
        raise HTTPException(
            status_code=400,
            detail="Não é possível movimentar uma conta desativada.",
        )
    return resultado


def _validar_e_aplicar_saldos(
    contas: dict[int, ContaBancaria],
    variacoes: dict[int, Decimal],
) -> None:
    for conta_id, variacao in variacoes.items():
        conta = contas[conta_id]
        saldo_projetado = Decimal(str(conta.valor_conta_atual)) + variacao
        if conta.tipo_conta != "corrente" and saldo_projetado < Decimal("0.00"):
            raise HTTPException(
                status_code=400,
                detail=(
                    "A operação deixaria uma conta sem limite "
                    "com saldo negativo."
                ),
            )
    for conta_id, variacao in variacoes.items():
        contas[conta_id].valor_conta_atual = (
            Decimal(str(contas[conta_id].valor_conta_atual)) + variacao
        )


def _variacao(tipo: str, valor: Decimal) -> Decimal:
    if tipo == "ajuste":
        return valor
    return valor if tipo == "entrada" else -valor


@router.post(
    "/",
    response_model=FluxoDinheiroResponse,
    status_code=status.HTTP_201_CREATED,
)
def criar_movimentacao(
    dados: FluxoDinheiroCreate,
    db: Session = Depends(get_db),
    usuario_logado: Usuario = Depends(obter_usuario_logado),
):
    conta_ids = {dados.conta_bancaria_id}
    if dados.tipo == "transferencia":
        if dados.conta_destino_id is None:
            raise HTTPException(
                status_code=422,
                detail="conta_destino_id é obrigatória para transferências.",
            )
        conta_ids.add(dados.conta_destino_id)
    contas = _obter_contas_bloqueadas(db, conta_ids, usuario_logado.id)
    valor = Decimal(dados.valor)

    if dados.tipo == "transferencia":
        id_transferencia = str(uuid4())
        origem_id = dados.conta_bancaria_id
        destino_id = dados.conta_destino_id
        _validar_e_aplicar_saldos(
            contas,
            {origem_id: -valor, destino_id: valor},
        )
        origem = FluxoDinheiro(
            conta_bancaria_id=origem_id,
            conta_destino_id=destino_id,
            descricao=dados.descricao,
            valor=valor,
            tipo="transferencia",
            categoria="transferencia",
            data_movimentacao=dados.data_movimentacao,
            observacao=dados.observacao,
            transferencia_id=id_transferencia,
            transferencia_direcao="origem",
            natureza_conta=dados.natureza_conta,
            tipo_investimento=dados.tipo_investimento,
        )
        destino = FluxoDinheiro(
            conta_bancaria_id=destino_id,
            conta_destino_id=origem_id,
            descricao=dados.descricao,
            valor=valor,
            tipo="transferencia",
            categoria="transferencia",
            data_movimentacao=dados.data_movimentacao,
            observacao=dados.observacao,
            transferencia_id=id_transferencia,
            transferencia_direcao="destino",
            natureza_conta=dados.natureza_conta,
            tipo_investimento=dados.tipo_investimento,
        )
        db.add_all([origem, destino])
        db.commit()
        db.refresh(origem)
        return origem

    tipo_persistido = (
        "saida" if dados.tipo == "transferencia_externa" else dados.tipo
    )
    conta = contas[dados.conta_bancaria_id]
    variacao = _variacao(tipo_persistido, valor)
    _validar_e_aplicar_saldos(contas, {conta.id: variacao})
    movimentacao = FluxoDinheiro(
        conta_bancaria_id=conta.id,
        descricao=dados.descricao,
        valor=valor,
        tipo=tipo_persistido,
        categoria=dados.categoria,
        data_movimentacao=dados.data_movimentacao,
        observacao=dados.observacao,
        natureza_conta=dados.natureza_conta,
        tipo_investimento=dados.tipo_investimento,
    )
    db.add(movimentacao)
    db.commit()
    db.refresh(movimentacao)
    return movimentacao


@router.post(
    "/investimentos",
    response_model=FluxoDinheiroResponse,
    status_code=status.HTTP_201_CREATED,
)
def criar_investimento(
    dados: InvestimentoCreate,
    db: Session = Depends(get_db),
    usuario_logado: Usuario = Depends(obter_usuario_logado),
):
    payload_movimentacao = FluxoDinheiroCreate(
        conta_bancaria_id=dados.conta_bancaria_id,
        descricao=f"Investimento - {dados.tipo_investimento}",
        valor=dados.valor,
        tipo="saida",
        categoria="investimento",
        data_movimentacao=dados.data_movimentacao,
        observacao=dados.observacao,
        natureza_conta="variavel",
        tipo_investimento=dados.tipo_investimento,
    )
    return criar_movimentacao(
        dados=payload_movimentacao,
        db=db,
        usuario_logado=usuario_logado,
    )


def _construir_consulta_movimentacoes(
    db: Session,
    usuario_id: int,
    conta_bancaria_id: int | None = None,
    categoria: str | None = None,
    data_inicio: date | None = None,
    data_fim: date | None = None,
):
    if data_inicio and data_fim and data_fim < data_inicio:
        raise HTTPException(
            status_code=422,
            detail="data_fim não pode ser anterior a data_inicio.",
        )
    consulta = (
        db.query(FluxoDinheiro)
        .join(
            ContaBancaria,
            FluxoDinheiro.conta_bancaria_id == ContaBancaria.id,
        )
        .filter(ContaBancaria.usuario_id == usuario_id)
    )
    if conta_bancaria_id is not None:
        consulta = consulta.filter(
            FluxoDinheiro.conta_bancaria_id == conta_bancaria_id
        )
    if categoria:
        categoria_normalizada = categoria.strip().casefold()
        if categoria_normalizada == "investimentos":
            categoria_normalizada = "investimento"
        consulta = consulta.filter(
            FluxoDinheiro.categoria == categoria_normalizada
        )
    if data_inicio:
        consulta = consulta.filter(
            FluxoDinheiro.data_movimentacao >= data_inicio
        )
    if data_fim:
        consulta = consulta.filter(
            FluxoDinheiro.data_movimentacao <= data_fim
        )
    return consulta.order_by(
        FluxoDinheiro.data_movimentacao.desc(),
        FluxoDinheiro.id.desc(),
    )


@router.get(
    "/",
    response_model=list[FluxoDinheiroResponse],
)
def listar_movimentacoes(
    conta_bancaria_id: int | None = None,
    categoria: str | None = None,
    data_inicio: date | None = None,
    data_fim: date | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    usuario_logado: Usuario = Depends(obter_usuario_logado),
):
    consulta = _construir_consulta_movimentacoes(
        db=db,
        usuario_id=usuario_logado.id,
        conta_bancaria_id=conta_bancaria_id,
        categoria=categoria,
        data_inicio=data_inicio,
        data_fim=data_fim,
    )
    return consulta.offset(offset).limit(limit).all()


@router.get("/exportar-csv")
def exportar_movimentacoes_csv(
    conta_bancaria_id: int | None = None,
    categoria: str | None = None,
    data_inicio: date | None = None,
    data_fim: date | None = None,
    db: Session = Depends(get_db),
    usuario_logado: Usuario = Depends(obter_usuario_logado),
):
    consulta = _construir_consulta_movimentacoes(
        db=db,
        usuario_id=usuario_logado.id,
        conta_bancaria_id=conta_bancaria_id,
        categoria=categoria,
        data_inicio=data_inicio,
        data_fim=data_fim,
    )
    movimentacoes = consulta.all()

    buffer = io.StringIO()
    buffer.write("\ufeff")
    escritor = csv.writer(buffer, delimiter=";")
    escritor.writerow(
        [
            "id",
            "data_movimentacao",
            "conta_bancaria_id",
            "tipo",
            "categoria",
            "descricao",
            "valor",
            "observacao",
        ]
    )
    for mov in movimentacoes:
        escritor.writerow(
            [
                mov.id,
                mov.data_movimentacao.isoformat(),
                mov.conta_bancaria_id,
                mov.tipo,
                mov.categoria,
                mov.descricao,
                f"{Decimal(str(mov.valor)):.2f}",
                mov.observacao or "",
            ]
        )

    return Response(
        content=buffer.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": (
                'attachment; filename="movimentacoes_fluxo_caixa.csv"'
            )
        },
    )


def _obter_movimentacao_do_usuario(
    db: Session,
    movimentacao_id: int,
    usuario_id: int,
) -> FluxoDinheiro:
    movimentacao = (
        db.query(FluxoDinheiro)
        .join(
            ContaBancaria,
            FluxoDinheiro.conta_bancaria_id == ContaBancaria.id,
        )
        .filter(
            FluxoDinheiro.id == movimentacao_id,
            ContaBancaria.usuario_id == usuario_id,
        )
        .with_for_update()
        .first()
    )
    if not movimentacao:
        raise HTTPException(
            status_code=404,
            detail="Movimentação não encontrada.",
        )
    return movimentacao


@router.get(
    "/{movimentacao_id}",
    response_model=FluxoDinheiroResponse,
)
def buscar_movimentacao(
    movimentacao_id: int,
    db: Session = Depends(get_db),
    usuario_logado: Usuario = Depends(obter_usuario_logado),
):
    return _obter_movimentacao_do_usuario(
        db,
        movimentacao_id,
        usuario_logado.id,
    )


@router.put(
    "/{movimentacao_id}",
    response_model=FluxoDinheiroResponse,
)
def atualizar_movimentacao(
    movimentacao_id: int,
    dados: FluxoDinheiroUpdate,
    db: Session = Depends(get_db),
    usuario_logado: Usuario = Depends(obter_usuario_logado),
):
    movimentacao = _obter_movimentacao_do_usuario(
        db,
        movimentacao_id,
        usuario_logado.id,
    )
    if movimentacao.tipo == "transferencia":
        raise HTTPException(
            status_code=409,
            detail=(
                "Transferências não podem ser editadas. "
                "Exclua a transferência e registre-a novamente."
            ),
        )

    conta_ids = {movimentacao.conta_bancaria_id, dados.conta_bancaria_id}
    contas = _obter_contas_bloqueadas(db, conta_ids, usuario_logado.id)
    variacoes: dict[int, Decimal] = {}
    variacoes[movimentacao.conta_bancaria_id] = -_variacao(
        movimentacao.tipo,
        Decimal(str(movimentacao.valor)),
    )
    variacoes[dados.conta_bancaria_id] = (
        variacoes.get(dados.conta_bancaria_id, Decimal("0.00"))
        + _variacao(dados.tipo, Decimal(dados.valor))
    )
    _validar_e_aplicar_saldos(contas, variacoes)

    movimentacao.conta_bancaria_id = dados.conta_bancaria_id
    movimentacao.descricao = dados.descricao
    movimentacao.valor = dados.valor
    movimentacao.tipo = dados.tipo
    movimentacao.categoria = dados.categoria
    movimentacao.data_movimentacao = dados.data_movimentacao
    movimentacao.observacao = dados.observacao
    if dados.natureza_conta is not None:
        movimentacao.natureza_conta = dados.natureza_conta
    if dados.tipo_investimento is not None:
        movimentacao.tipo_investimento = dados.tipo_investimento
    db.commit()
    db.refresh(movimentacao)
    return movimentacao


@router.delete("/{movimentacao_id}")
def excluir_movimentacao(
    movimentacao_id: int,
    db: Session = Depends(get_db),
    usuario_logado: Usuario = Depends(obter_usuario_logado),
):
    movimentacao = _obter_movimentacao_do_usuario(
        db,
        movimentacao_id,
        usuario_logado.id,
    )
    if movimentacao.tipo == "transferencia":
        if not movimentacao.transferencia_id:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Esta transferência antiga não está vinculada a "
                    "uma contraparte e não pode ser revertida automaticamente."
                ),
            )
        par = (
            db.query(FluxoDinheiro)
            .filter(
                FluxoDinheiro.transferencia_id == movimentacao.transferencia_id
            )
            .order_by(FluxoDinheiro.id)
            .with_for_update()
            .all()
        )
        if len(par) != 2 or {item.transferencia_direcao for item in par} != {
            "origem",
            "destino",
        }:
            raise HTTPException(
                status_code=409,
                detail="O registro da transferência está inconsistente.",
            )

        conta_ids = {item.conta_bancaria_id for item in par}
        contas = _obter_contas_bloqueadas(db, conta_ids, usuario_logado.id)
        variacoes: dict[int, Decimal] = {}
        for item in par:
            sinal = (
                Decimal("1.00")
                if item.transferencia_direcao == "origem"
                else Decimal("-1.00")
            )
            variacoes[item.conta_bancaria_id] = (
                variacoes.get(item.conta_bancaria_id, Decimal("0.00"))
                + sinal * Decimal(str(item.valor))
            )
        _validar_e_aplicar_saldos(contas, variacoes)
        for item in par:
            db.delete(item)
    else:
        contas = _obter_contas_bloqueadas(
            db,
            {movimentacao.conta_bancaria_id},
            usuario_logado.id,
        )
        _validar_e_aplicar_saldos(
            contas,
            {
                movimentacao.conta_bancaria_id: -_variacao(
                    movimentacao.tipo,
                    Decimal(str(movimentacao.valor)),
                )
            },
        )
        db.delete(movimentacao)

    db.commit()
    return {"mensagem": "Movimentação excluída com sucesso."}
