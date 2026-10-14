from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import jwt
import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from autenticacao import criar_token  # noqa: E402
from financeiro import (  # noqa: E402
    calcular_entradas,
    calcular_investimentos,
    calcular_saidas,
    calcular_resumo_periodo,
)
from models import (  # noqa: E402
    ContaBancaria,
    FluxoDinheiro,
    Usuario,
)
from seguranca.seguranca import gerar_hash_senha  # noqa: E402
from dados_sensiveis import criptografar_cpf, indice_cpf  # noqa: E402
from rotasdeapi.fluxo_dinheiro import (  # noqa: E402
    criar_movimentacao,
    excluir_movimentacao,
)
from esquema import (  # noqa: E402
    CalculoFinanceiroCreate,
    ContaBancariaCreate,
    FluxoDinheiroCreate,
    FluxoDinheiroUpdate,
    MetaFinanceiraCreate,
    UsuarioCreate,
)
from pydantic import ValidationError  # noqa: E402


def _criar_usuario(
    db: Session,
    email: str = "teste@example.com",
    cpf: str = "52998224725",
) -> Usuario:
    usuario = Usuario(
        nome_completo="Pessoa de Teste",
        cpf=criptografar_cpf(cpf),
        cpf_indice=indice_cpf(cpf),
        email=email,
        senha_hash="hash",
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


def _criar_conta(
    db: Session,
    usuario_id: int,
    saldo: str,
    tipo: str = "corrente",
) -> ContaBancaria:
    conta = ContaBancaria(
        usuario_id=usuario_id,
        nome_banco="Banco de Teste",
        tipo_conta=tipo,
        valor_conta_atual=Decimal(saldo),
        ativa=True,
    )
    db.add(conta)
    db.commit()
    db.refresh(conta)
    return conta


def test_agregacoes_sql_somam_entradas_saidas_e_investimentos(db: Session):
    usuario = _criar_usuario(db)
    conta = _criar_conta(db, usuario.id, "65.00")
    hoje = date.today()
    db.add_all(
        [
            FluxoDinheiro(
                conta_bancaria_id=conta.id,
                descricao="Salário",
                valor=Decimal("100.00"),
                tipo="entrada",
                categoria="salario",
                data_movimentacao=hoje,
            ),
            FluxoDinheiro(
                conta_bancaria_id=conta.id,
                descricao="Mercado",
                valor=Decimal("25.00"),
                tipo="saida",
                categoria="alimentacao",
                data_movimentacao=hoje,
            ),
            FluxoDinheiro(
                conta_bancaria_id=conta.id,
                descricao="Investimento",
                valor=Decimal("10.00"),
                tipo="saida",
                categoria="investimento",
                data_movimentacao=hoje,
            ),
        ]
    )
    db.commit()

    assert calcular_entradas(db, conta.id, hoje, hoje) == Decimal("100.00")
    assert calcular_saidas(db, conta.id, hoje, hoje) == Decimal("35.00")
    assert calcular_investimentos(db, conta.id, hoje, hoje) == Decimal("10.00")
    resumo = calcular_resumo_periodo(db, conta.id, hoje, hoje)
    assert resumo["saldo_inicial"] == Decimal("0.00")
    assert resumo["saldo_final"] == Decimal("65.00")


def test_transferencia_e_exclusao_revertem_ambos_os_saldos(db: Session):
    usuario = _criar_usuario(db)
    origem = _criar_conta(db, usuario.id, "100.00")
    destino = _criar_conta(db, usuario.id, "20.00", tipo="poupanca")
    movimento = criar_movimentacao(
        FluxoDinheiroCreate(
            conta_bancaria_id=origem.id,
            conta_destino_id=destino.id,
            descricao="Transferência",
            valor=Decimal("25.00"),
            tipo="transferencia",
            categoria="transferencia",
            data_movimentacao=date.today(),
        ),
        db,
        usuario,
    )

    db.refresh(origem)
    db.refresh(destino)
    assert origem.valor_conta_atual == Decimal("75.00")
    assert destino.valor_conta_atual == Decimal("45.00")
    assert (
        db.query(FluxoDinheiro)
        .filter(FluxoDinheiro.transferencia_id == movimento.transferencia_id)
        .count()
        == 2
    )
    resumo_origem = calcular_resumo_periodo(
        db, origem.id, date.today(), date.today()
    )
    resumo_destino = calcular_resumo_periodo(
        db, destino.id, date.today(), date.today()
    )
    assert resumo_origem["total_entradas"] == Decimal("0.00")
    assert resumo_origem["total_saidas"] == Decimal("0.00")
    assert resumo_origem["total_transferencias_enviadas"] == Decimal("25.00")
    assert resumo_destino["total_transferencias_recebidas"] == Decimal("25.00")
    assert resumo_origem["saldo_final"] == Decimal("75.00")
    assert resumo_destino["saldo_final"] == Decimal("45.00")

    excluir_movimentacao(movimento.id, db, usuario)
    db.refresh(origem)
    db.refresh(destino)
    assert origem.valor_conta_atual == Decimal("100.00")
    assert destino.valor_conta_atual == Decimal("20.00")


def test_transferencia_para_a_mesma_conta_e_rejeitada():
    with pytest.raises(ValidationError):
        FluxoDinheiroCreate(
            conta_bancaria_id=1,
            conta_destino_id=1,
            descricao="Transferência inválida",
            valor=Decimal("1.00"),
            tipo="transferencia",
            categoria="transferencia",
            data_movimentacao=date.today(),
        )


def test_transferencia_sem_saldo_nao_altera_contas_nem_cria_movimentos(
    db: Session,
):
    usuario = _criar_usuario(db)
    origem = _criar_conta(db, usuario.id, "10.00", tipo="poupanca")
    destino = _criar_conta(db, usuario.id, "20.00", tipo="poupanca")

    with pytest.raises(HTTPException) as erro:
        criar_movimentacao(
            FluxoDinheiroCreate(
                conta_bancaria_id=origem.id,
                conta_destino_id=destino.id,
                descricao="Transferência sem saldo",
                valor=Decimal("15.00"),
                tipo="transferencia",
                categoria="transferencia",
                data_movimentacao=date.today(),
            ),
            db,
            usuario,
        )

    assert erro.value.status_code == 400
    db.refresh(origem)
    db.refresh(destino)
    assert origem.valor_conta_atual == Decimal("10.00")
    assert destino.valor_conta_atual == Decimal("20.00")
    assert db.query(FluxoDinheiro).count() == 0


def test_saldo_e_resumo_preservam_precisao_decimal_em_operacoes_fracionarias(
    db: Session,
):
    usuario = _criar_usuario(db)
    conta = _criar_conta(db, usuario.id, "0.00")
    hoje = date.today()

    for valor in (Decimal("0.10"), Decimal("0.20")):
        criar_movimentacao(
            FluxoDinheiroCreate(
                conta_bancaria_id=conta.id,
                descricao="Entrada fracionária",
                valor=valor,
                tipo="entrada",
                categoria="salario",
                data_movimentacao=hoje,
            ),
            db,
            usuario,
        )
    criar_movimentacao(
        FluxoDinheiroCreate(
            conta_bancaria_id=conta.id,
            descricao="Ajuste fracionário",
            valor=Decimal("-0.01"),
            tipo="ajuste",
            categoria="ajuste",
            data_movimentacao=hoje,
        ),
        db,
        usuario,
    )

    db.refresh(conta)
    resumo = calcular_resumo_periodo(db, conta.id, hoje, hoje)
    assert conta.valor_conta_atual == Decimal("0.29")
    assert resumo["total_entradas"] == Decimal("0.30")
    assert resumo["total_ajustes"] == Decimal("-0.01")
    assert resumo["saldo_final"] == Decimal("0.29")


def test_poupanca_nao_pode_ficar_negativa(db: Session):
    usuario = _criar_usuario(db)
    conta = _criar_conta(db, usuario.id, "0.00", tipo="poupanca")

    with pytest.raises(HTTPException) as erro:
        criar_movimentacao(
            FluxoDinheiroCreate(
                conta_bancaria_id=conta.id,
                descricao="Compra",
                valor=Decimal("1.00"),
                tipo="saida",
                categoria="alimentacao",
                data_movimentacao=date.today(),
            ),
            db,
            usuario,
        )

    assert erro.value.status_code == 400
    db.refresh(conta)
    assert conta.valor_conta_atual == Decimal("0.00")


def test_digitos_verificadores_do_cpf_sao_validos():
    payload = {
        "nome_completo": "Pessoa de Teste",
        "cpf": "529.982.247-25",
        "email": "teste@example.com",
        "senha": "Senha@123",
    }
    assert UsuarioCreate.model_validate(payload).cpf == "52998224725"
    payload["cpf"] = "12345678901"
    with pytest.raises(ValidationError):
        UsuarioCreate.model_validate(payload)


def test_periodo_do_calculo_deve_corresponder_ao_tipo():
    with pytest.raises(ValidationError):
        CalculoFinanceiroCreate(
            conta_bancaria_id=1,
            tipo_calculo="diario",
            data_inicio=date(2026, 1, 1),
            data_fim=date(2026, 1, 2),
        )


def test_valores_monetarios_rejeitam_mais_de_duas_casas_decimais():
    with pytest.raises(ValidationError):
        ContaBancariaCreate(
            nome_banco="Banco",
            tipo_conta="corrente",
            valor_conta_atual=Decimal("10.999"),
        )
    with pytest.raises(ValidationError):
        FluxoDinheiroCreate(
            conta_bancaria_id=1,
            descricao="Salário",
            valor=Decimal("10.999"),
            tipo="entrada",
            categoria="salario",
            data_movimentacao=date.today(),
        )
    with pytest.raises(ValidationError):
        MetaFinanceiraCreate(
            nome="Reserva",
            valor_meta=Decimal("100.001"),
            data_inicio=date.today(),
        )


def test_categoria_transferencia_e_fixa_e_reservada():
    with pytest.raises(ValidationError):
        FluxoDinheiroCreate(
            conta_bancaria_id=1,
            descricao="Entrada inválida",
            valor=Decimal("10.00"),
            tipo="entrada",
            categoria="transferencia",
            data_movimentacao=date.today(),
        )
    with pytest.raises(ValidationError):
        FluxoDinheiroUpdate(
            conta_bancaria_id=1,
            descricao="Categoria livre",
            valor=Decimal("10.00"),
            tipo="entrada",
            categoria="categoria-nova",
            data_movimentacao=date.today(),
        )


def test_email_e_categoria_sao_normalizados():
    usuario = UsuarioCreate(
        nome_completo="Pessoa de Teste",
        cpf="52998224725",
        email="TESTE@EXAMPLE.COM",
        senha="Senha@123",
    )
    assert str(usuario.email) == "teste@example.com"
    movimento = FluxoDinheiroCreate(
        conta_bancaria_id=1,
        descricao="Mercado",
        valor=Decimal("10.00"),
        tipo="saida",
        categoria="Alimentação",
        data_movimentacao=date.today(),
    )
    assert movimento.categoria == "alimentacao"


def test_ajuste_assinado_atualiza_saldo_e_nao_vira_entrada_ou_saida(
    db: Session,
):
    usuario = _criar_usuario(db)
    conta = _criar_conta(db, usuario.id, "20.00")
    movimento = criar_movimentacao(
        FluxoDinheiroCreate(
            conta_bancaria_id=conta.id,
            descricao="Correção de saldo inicial",
            valor=Decimal("-3.25"),
            tipo="ajuste",
            categoria="ajuste",
            data_movimentacao=date.today(),
        ),
        db,
        usuario,
    )
    db.refresh(conta)
    resumo = calcular_resumo_periodo(
        db, conta.id, date.today(), date.today()
    )
    assert movimento.valor == Decimal("-3.25")
    assert conta.valor_conta_atual == Decimal("16.75")
    assert resumo["total_entradas"] == Decimal("0.00")
    assert resumo["total_saidas"] == Decimal("0.00")
    assert resumo["total_ajustes"] == Decimal("-3.25")
    assert resumo["saldo_final"] == Decimal("16.75")


def test_rotas_isolam_dados_e_login_rejeita_token_expirado(
    client,
    db: Session,
    monkeypatch,
):
    segredo = "segredo-de-teste-com-mais-de-32-caracteres"
    monkeypatch.setenv("JWT_SECRET_KEY", segredo)
    usuario_a = _criar_usuario(db)
    usuario_b = _criar_usuario(
        db,
        email="outra@example.com",
        cpf="11144477735",
    )
    conta_a = _criar_conta(db, usuario_a.id, "10.00")
    conta_b = _criar_conta(db, usuario_b.id, "20.00")
    usuario_a.senha_hash = gerar_hash_senha("Senha@123")
    db.commit()

    login = client.post(
        "/login",
        data={"username": usuario_a.email, "password": "Senha@123"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resposta_usuarios = client.get("/usuarios/", headers=headers)
    assert resposta_usuarios.status_code == 200
    assert [item["id"] for item in resposta_usuarios.json()] == [usuario_a.id]
    assert "cpf" not in resposta_usuarios.json()[0]

    resposta_contas = client.get("/contas-bancarias/", headers=headers)
    assert [item["id"] for item in resposta_contas.json()] == [conta_a.id]
    assert (
        client.get(f"/contas-bancarias/{conta_b.id}", headers=headers).status_code
        == 404
    )

    expirado = jwt.encode(
        {
            "sub": str(usuario_a.id),
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        },
        segredo,
        algorithm="HS256",
    )
    resposta_expirada = client.get(
        "/usuarios/me",
        headers={"Authorization": f"Bearer {expirado}"},
    )
    assert resposta_expirada.status_code == 401


def test_login_bloqueia_quinta_falha_por_cliente(client):
    respostas = [
        client.post(
            "/login",
            data={"username": "nao-existe@example.com", "password": "Senha@123"},
        )
        for _ in range(5)
    ]
    assert [resposta.status_code for resposta in respostas[:4]] == [401] * 4
    assert respostas[4].status_code == 429
    assert "Retry-After" in respostas[4].headers
    assert client.post(
        "/login",
        data={"username": "nao-existe@example.com", "password": "Senha@123"},
    ).status_code == 429


def test_put_movimentacao_atualiza_saldo_do_usuario(
    client,
    db: Session,
    monkeypatch,
):
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "segredo-de-teste-com-mais-de-32-caracteres",
    )
    usuario = _criar_usuario(db)
    conta = _criar_conta(db, usuario.id, "90.00")
    movimento = FluxoDinheiro(
        conta_bancaria_id=conta.id,
        descricao="Compra original",
        valor=Decimal("10.00"),
        tipo="saida",
        categoria="compras",
        data_movimentacao=date.today(),
    )
    db.add(movimento)
    db.commit()
    token = criar_token(usuario.id)

    resposta = client.put(
        f"/fluxo-dinheiro/{movimento.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "conta_bancaria_id": conta.id,
            "descricao": "Compra corrigida",
            "valor": "15.00",
            "tipo": "saida",
            "categoria": "compras",
            "data_movimentacao": date.today().isoformat(),
        },
    )

    assert resposta.status_code == 200
    assert resposta.json()["valor"] == "15.00"
    db.refresh(conta)
    assert conta.valor_conta_atual == Decimal("85.00")
