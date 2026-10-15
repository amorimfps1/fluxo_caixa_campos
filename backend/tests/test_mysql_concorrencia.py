import os
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, event, func
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from dados_sensiveis import criptografar_cpf, indice_cpf
from models import ContaBancaria, FluxoDinheiro, Usuario
from rotasdeapi import fluxo_dinheiro as fluxo_dinheiro_rotas
from rotasdeapi.fluxo_dinheiro import criar_movimentacao
from esquema import FluxoDinheiroCreate


pytestmark = pytest.mark.mysql

ROOT = Path(__file__).resolve().parents[2]
MYSQL_LOCK_WAIT_SECONDS = 10
TRANSFERENCIAS_POR_THREAD = 20


def _url_mysql_de_testes() -> str:
    valor = os.getenv("TEST_MYSQL_URL")
    if not valor:
        pytest.skip("Defina TEST_MYSQL_URL para executar os testes MySQL.")

    url = make_url(valor)
    if not url.drivername.startswith("mysql"):
        pytest.fail("TEST_MYSQL_URL deve usar um driver MySQL.")
    if not url.database or not url.database.casefold().endswith(
        ("_test", "_tests")
    ):
        pytest.fail(
            "TEST_MYSQL_URL deve apontar para um schema dedicado "
            "terminado em _test ou _tests."
        )
    return valor


@pytest.fixture(scope="session")
def mysql_session_factory():
    test_url = _url_mysql_de_testes()
    ambiente = os.environ.copy()
    ambiente["DATABASE_URL"] = test_url
    ambiente["JWT_SECRET_KEY"] = "mysql-test-only-jwt-signing-key-do-not-use"
    ambiente["CPF_ENCRYPTION_KEY"] = (
        "MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA="
    )
    resultado = subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "-c",
            str(ROOT / "banco de dados" / "alembic.ini"),
            "upgrade",
            "head",
        ],
        cwd=ROOT,
        env=ambiente,
        capture_output=True,
        text=True,
        check=False,
    )
    if resultado.returncode:
        raise RuntimeError(
            "Alembic upgrade head falhou para TEST_MYSQL_URL. "
            "Confira localmente a configuração do schema de testes."
        )

    engine = create_engine(
        test_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=10,
    )
    factory = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )

    @event.listens_for(engine, "connect")
    def configure_lock_timeout(connection, _record):
        del _record
        cursor = connection.cursor()
        try:
            cursor.execute(
                f"SET SESSION innodb_lock_wait_timeout = "
                f"{MYSQL_LOCK_WAIT_SECONDS}"
            )
        finally:
            cursor.close()

    yield factory
    engine.dispose()


@pytest.fixture
def mysql_case(mysql_session_factory):
    marker = uuid4().hex
    base = f"{uuid4().int % 1_000_000_000:09d}"
    first = (
        sum(
            int(digit) * weight
            for digit, weight in zip(base, range(10, 1, -1))
        )
        * 10
    ) % 11
    first = 0 if first == 10 else first
    first_ten = base + str(first)
    second = (
        sum(
            int(digit) * weight
            for digit, weight in zip(first_ten, range(11, 1, -1))
        )
        * 10
    ) % 11
    second = 0 if second == 10 else second
    cpf = first_ten + str(second)

    with mysql_session_factory() as session:
        usuario = Usuario(
            nome_completo=f"MySQL concorrência {marker[:12]}",
            cpf=criptografar_cpf(cpf),
            cpf_indice=indice_cpf(cpf),
            email=f"mysql-test-{marker}@example.invalid",
            senha_hash="not-used-by-concurrency-test",
        )
        session.add(usuario)
        session.flush()
        contas = [
            ContaBancaria(
                usuario_id=usuario.id,
                nome_banco=f"Teste {marker[:8]} {index}",
                tipo_conta="corrente",
                valor_conta_atual=Decimal("0.00"),
                ativa=True,
            )
            for index in range(2)
        ]
        session.add_all(contas)
        session.commit()
        usuario_id = usuario.id
        conta_ids = tuple(conta.id for conta in contas)

    yield {
        "factory": mysql_session_factory,
        "usuario_id": usuario_id,
        "conta_ids": conta_ids,
    }

    with mysql_session_factory() as session:
        session.query(FluxoDinheiro).filter(
            FluxoDinheiro.conta_bancaria_id.in_(conta_ids)
        ).delete(synchronize_session=False)
        session.query(ContaBancaria).filter(
            ContaBancaria.id.in_(conta_ids)
        ).delete(synchronize_session=False)
        session.query(Usuario).filter(Usuario.id == usuario_id).delete()
        session.commit()


def _executar_movimentacao(
    factory,
    usuario_id: int,
    dados: FluxoDinheiroCreate,
    barreira: threading.Barrier | None = None,
) -> str:
    if barreira is not None:
        barreira.wait(timeout=MYSQL_LOCK_WAIT_SECONDS)
    with factory() as session:
        usuario = session.get(Usuario, usuario_id)
        if usuario is None:
            raise AssertionError("Usuário de teste não encontrado.")
        try:
            movimento = criar_movimentacao(dados, session, usuario)
            return f"ok:{movimento.id}"
        except HTTPException as erro:
            session.rollback()
            if erro.status_code == 400:
                return "rejected"
            raise


def _transferencia(
    origem_id: int,
    destino_id: int,
    valor: Decimal = Decimal("0.01"),
) -> FluxoDinheiroCreate:
    return FluxoDinheiroCreate(
        conta_bancaria_id=origem_id,
        conta_destino_id=destino_id,
        descricao="Transferência concorrente de teste",
        valor=valor,
        tipo="transferencia",
        categoria="transferencia",
        data_movimentacao=date.today(),
    )


def _saldos_conta(factory, conta_ids: tuple[int, int]) -> tuple[Decimal, ...]:
    with factory() as session:
        contas = (
            session.query(ContaBancaria)
            .filter(ContaBancaria.id.in_(conta_ids))
            .order_by(ContaBancaria.id)
            .all()
        )
        return tuple(Decimal(str(conta.valor_conta_atual)) for conta in contas)


def test_saques_concorrentes_nao_ultrapassam_saldo(
    mysql_case,
) -> None:
    factory = mysql_case["factory"]
    usuario_id = mysql_case["usuario_id"]
    conta_id = mysql_case["conta_ids"][0]
    with factory() as session:
        conta = session.get(ContaBancaria, conta_id)
        assert conta is not None
        conta.valor_conta_atual = Decimal("100.00")
        session.commit()

    inicio = threading.Barrier(2)
    retirada = FluxoDinheiroCreate(
        conta_bancaria_id=conta_id,
        descricao="Saque concorrente",
        valor=Decimal("80.00"),
        tipo="saida",
        categoria="contas",
        data_movimentacao=date.today(),
    )
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(
                _executar_movimentacao,
                factory,
                usuario_id,
                retirada,
                inicio,
            )
            for _ in range(2)
        ]
        resultados = [
            future.result(timeout=MYSQL_LOCK_WAIT_SECONDS + 5)
            for future in as_completed(
                futures,
                timeout=MYSQL_LOCK_WAIT_SECONDS + 10,
            )
        ]

    assert sum(resultado.startswith("ok:") for resultado in resultados) == 1
    assert resultados.count("rejected") == 1
    with factory() as session:
        conta = session.get(ContaBancaria, conta_id)
        assert conta is not None
        saldo = conta.valor_conta_atual
        total_saques = (
            session.query(func.count(FluxoDinheiro.id))
            .filter(
                FluxoDinheiro.conta_bancaria_id == conta_id,
                FluxoDinheiro.tipo == "saida",
            )
            .scalar()
        )
    assert Decimal(str(saldo)) == Decimal("20.00")
    assert total_saques == 1


def test_transferencias_cruzadas_em_loop_nao_deadlockeiam(
    mysql_case,
) -> None:
    factory = mysql_case["factory"]
    usuario_id = mysql_case["usuario_id"]
    conta_a, conta_b = mysql_case["conta_ids"]
    with factory() as session:
        session.query(ContaBancaria).filter(
            ContaBancaria.id.in_((conta_a, conta_b))
        ).update(
            {ContaBancaria.valor_conta_atual: Decimal("1000.00")},
            synchronize_session=False,
        )
        session.commit()

    total_inicial = sum(_saldos_conta(factory, (conta_a, conta_b)))
    inicio = threading.Barrier(2)

    def executar_loop(origem: int, destino: int) -> int:
        inicio.wait(timeout=MYSQL_LOCK_WAIT_SECONDS)
        for _ in range(TRANSFERENCIAS_POR_THREAD):
            resultado = _executar_movimentacao(
                factory,
                usuario_id,
                _transferencia(origem, destino),
            )
            assert resultado.startswith("ok:")
        return TRANSFERENCIAS_POR_THREAD

    with ThreadPoolExecutor(max_workers=2) as executor:
        futuros = [
            executor.submit(executar_loop, conta_a, conta_b),
            executor.submit(executar_loop, conta_b, conta_a),
        ]
        assert sum(
            futuro.result(timeout=MYSQL_LOCK_WAIT_SECONDS * 3)
            for futuro in as_completed(
                futuros,
                timeout=MYSQL_LOCK_WAIT_SECONDS * 4,
            )
        ) == TRANSFERENCIAS_POR_THREAD * 2

    assert sum(_saldos_conta(factory, (conta_a, conta_b))) == total_inicial
    with factory() as session:
        assert (
            session.query(func.count(FluxoDinheiro.id))
            .filter(
                FluxoDinheiro.conta_bancaria_id.in_((conta_a, conta_b)),
                FluxoDinheiro.tipo == "transferencia",
            )
            .scalar()
            == TRANSFERENCIAS_POR_THREAD * 4
        )


def test_saldo_total_permanece_invariante_em_transferencias_concorrentes(
    mysql_case,
) -> None:
    factory = mysql_case["factory"]
    usuario_id = mysql_case["usuario_id"]
    conta_a, conta_b = mysql_case["conta_ids"]
    with factory() as session:
        for conta_id, saldo in (
            (conta_a, Decimal("2500.00")),
            (conta_b, Decimal("1750.25")),
        ):
            conta = session.get(ContaBancaria, conta_id)
            assert conta is not None
            conta.valor_conta_atual = saldo
        session.commit()

    saldo_inicial = sum(_saldos_conta(factory, (conta_a, conta_b)))
    inicio = threading.Barrier(4)
    tarefas = [
        (conta_a, conta_b, 17),
        (conta_b, conta_a, 23),
        (conta_a, conta_b, 31),
        (conta_b, conta_a, 29),
    ]

    def executar_tarefa(origem: int, destino: int, quantidade: int) -> int:
        inicio.wait(timeout=MYSQL_LOCK_WAIT_SECONDS)
        for _ in range(quantidade):
            resultado = _executar_movimentacao(
                factory,
                usuario_id,
                _transferencia(origem, destino),
            )
            assert resultado.startswith("ok:")
        return quantidade

    with ThreadPoolExecutor(max_workers=len(tarefas)) as executor:
        futuros = [
            executor.submit(executar_tarefa, *tarefa)
            for tarefa in tarefas
        ]
        assert sum(
            futuro.result(timeout=MYSQL_LOCK_WAIT_SECONDS * 5)
            for futuro in as_completed(
                futuros,
                timeout=MYSQL_LOCK_WAIT_SECONDS * 6,
            )
        ) == sum(tarefa[2] for tarefa in tarefas)

    assert sum(_saldos_conta(factory, (conta_a, conta_b))) == saldo_inicial


def test_falha_apos_inserir_transferencia_reverte_saldos_e_lancamentos(
    mysql_case,
) -> None:
    factory = mysql_case["factory"]
    usuario_id = mysql_case["usuario_id"]
    conta_a, conta_b = mysql_case["conta_ids"]
    with factory() as session:
        for conta_id, saldo in (
            (conta_a, Decimal("100.00")),
            (conta_b, Decimal("20.00")),
        ):
            conta = session.get(ContaBancaria, conta_id)
            assert conta is not None
            conta.valor_conta_atual = saldo
        session.commit()

    session = factory()
    usuario = session.get(Usuario, usuario_id)
    assert usuario is not None
    connection = session.connection()
    insercao_observada = False

    def falhar_depois_da_insercao(
        _connection,
        _cursor,
        statement,
        _parameters,
        _context,
        _executemany,
    ):
        del _connection, _cursor, _parameters, _context, _executemany
        nonlocal insercao_observada
        if (
            not insercao_observada
            and statement.lstrip()
            .upper()
            .startswith("INSERT INTO FLUXO_DINHEIRO")
        ):
            insercao_observada = True
            raise RuntimeError("Falha injetada antes do commit.")

    event.listen(connection, "after_cursor_execute", falhar_depois_da_insercao)
    try:
        with pytest.raises(RuntimeError, match="Falha injetada"):
            criar_movimentacao(
                _transferencia(conta_a, conta_b, Decimal("10.00")),
                session,
                usuario,
            )
    finally:
        event.remove(
            connection,
            "after_cursor_execute",
            falhar_depois_da_insercao,
        )
        session.rollback()
        session.close()

    assert insercao_observada
    assert _saldos_conta(factory, (conta_a, conta_b)) == (
        Decimal("100.00"),
        Decimal("20.00"),
    )
    with factory() as verify:
        assert (
            verify.query(func.count(FluxoDinheiro.id))
            .filter(
                FluxoDinheiro.conta_bancaria_id.in_((conta_a, conta_b))
            )
            .scalar()
            == 0
        )


def test_controle_negativo_sem_for_update_reproduz_saque_duplo(
    mysql_case,
    monkeypatch,
) -> None:
    factory = mysql_case["factory"]
    conta_id = mysql_case["conta_ids"][0]
    with factory() as session:
        conta = session.get(ContaBancaria, conta_id)
        assert conta is not None
        conta.valor_conta_atual = Decimal("100.00")
        session.commit()

    contas_lidas = threading.Barrier(2)

    def obter_contas_sem_bloqueio(
        session: Session,
        conta_ids: set[int],
        usuario_id: int,
    ) -> dict[int, ContaBancaria]:
        contas = (
            session.query(ContaBancaria)
            .filter(
                ContaBancaria.id.in_(conta_ids),
                ContaBancaria.usuario_id == usuario_id,
            )
            .order_by(ContaBancaria.id)
            .all()
        )
        contas_lidas.wait(timeout=MYSQL_LOCK_WAIT_SECONDS)
        return {conta.id: conta for conta in contas}

    monkeypatch.setattr(
        fluxo_dinheiro_rotas,
        "_obter_contas_bloqueadas",
        obter_contas_sem_bloqueio,
    )
    retirada = FluxoDinheiroCreate(
        conta_bancaria_id=conta_id,
        descricao="Saque do controle negativo",
        valor=Decimal("80.00"),
        tipo="saida",
        categoria="contas",
        data_movimentacao=date.today(),
    )

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(
                _executar_movimentacao,
                factory,
                mysql_case["usuario_id"],
                retirada,
            )
            for _ in range(2)
        ]
        for future in as_completed(
            futures,
            timeout=MYSQL_LOCK_WAIT_SECONDS * 2,
        ):
            assert future.result(timeout=MYSQL_LOCK_WAIT_SECONDS).startswith(
                "ok:"
            )

    with factory() as session:
        saldo = session.get(ContaBancaria, conta_id).valor_conta_atual
        total_saques = (
            session.query(func.coalesce(func.sum(FluxoDinheiro.valor), 0))
            .filter(
                FluxoDinheiro.conta_bancaria_id == conta_id,
                FluxoDinheiro.tipo == "saida",
            )
            .scalar()
        )
    assert Decimal(str(saldo)) == Decimal("20.00")
    assert Decimal(str(total_saques)) == Decimal("160.00")
