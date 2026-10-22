from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


def _cpf_valido() -> str:
    base = f"{uuid4().int % 1_000_000_000:09d}"
    primeiro_digito = (
        sum(
            int(digito) * peso
            for digito, peso in zip(base, range(10, 1, -1))
        )
        * 10
    ) % 11
    if primeiro_digito == 10:
        primeiro_digito = 0

    dez_digitos = base + str(primeiro_digito)
    segundo_digito = (
        sum(
            int(digito) * peso
            for digito, peso in zip(dez_digitos, range(11, 1, -1))
        )
        * 10
    ) % 11
    if segundo_digito == 10:
        segundo_digito = 0

    return f"{dez_digitos}{segundo_digito}"


def _usuario_autenticado(
    client: TestClient,
) -> tuple[dict, dict[str, str]]:
    identificador = uuid4().hex
    email = f"teste-{identificador}@example.com"
    senha = "TesteSeguro2026!"
    cadastro = client.post(
        "/usuarios/",
        json={
            "nome_completo": "Usuário de Integração",
            "cpf": _cpf_valido(),
            "email": email,
            "senha": senha,
        },
    )
    assert cadastro.status_code == 201, cadastro.text

    login = client.post(
        "/login",
        data={"username": email, "password": senha},
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    return cadastro.json(), {"Authorization": f"Bearer {token}"}


def _criar_conta(client: TestClient, token: dict[str, str]) -> dict:
    resposta = client.post(
        "/contas-bancarias/",
        headers=token,
        json={
            "nome_banco": "Banco de relatórios",
            "tipo_conta": "corrente",
            "valor_conta_atual": "1000.00",
            "ativa": True,
        },
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def _criar_meta(
    client: TestClient,
    token: dict[str, str],
    *,
    valor_meta: str = "5000.00",
    valor_atual: str = "2500.00",
    data_inicio: date | None = None,
    data_limite: date | None = None,
    status: str = "em_andamento",
) -> dict:
    inicio = data_inicio or date.today()
    resposta = client.post(
        "/metas-financeiras/",
        headers=token,
        json={
            "nome": "Reserva de emergência",
            "valor_meta": valor_meta,
            "valor_atual": valor_atual,
            "data_inicio": inicio.isoformat(),
            "data_limite": (
                data_limite.isoformat() if data_limite else None
            ),
            "status": status,
            "descricao": "Meta para teste",
        },
    )
    return resposta.json() if resposta.status_code == 201 else resposta


def test_meta_crud_calcula_progresso_restante_e_status(
    client: TestClient,
) -> None:
    _, token = _usuario_autenticado(client)
    meta = _criar_meta(client, token)

    assert meta["valor_meta"] == "5000.00"
    assert meta["progresso_percentual"] == "50.00"
    assert meta["valor_restante"] == "2500.00"
    assert meta["status"] == "em_andamento"

    consulta = client.get(
        f"/metas-financeiras/{meta['id']}",
        headers=token,
    )
    assert consulta.status_code == 200
    assert consulta.json()["progresso_percentual"] == "50.00"

    lista = client.get(
        "/metas-financeiras/?status=em_andamento",
        headers=token,
    )
    assert lista.status_code == 200
    assert [item["id"] for item in lista.json()] == [meta["id"]]

    atualizacao = client.put(
        f"/metas-financeiras/{meta['id']}",
        headers=token,
        json={
            "nome": "Reserva concluída",
            "valor_meta": "5000.00",
            "valor_atual": "5000.00",
            "data_inicio": date.today().isoformat(),
            "data_limite": None,
            "status": "em_andamento",
            "descricao": "Valor atingido",
        },
    )
    assert atualizacao.status_code == 200, atualizacao.text
    assert atualizacao.json()["status"] == "concluida"
    assert atualizacao.json()["progresso_percentual"] == "100.00"
    assert atualizacao.json()["valor_restante"] == "0.00"

    lista_concluidas = client.get(
        "/metas-financeiras/?status=concluida",
        headers=token,
    )
    assert lista_concluidas.status_code == 200
    assert [item["id"] for item in lista_concluidas.json()] == [meta["id"]]

    exclusao = client.delete(
        f"/metas-financeiras/{meta['id']}",
        headers=token,
    )
    assert exclusao.status_code == 200
    assert (
        client.get(
            f"/metas-financeiras/{meta['id']}",
            headers=token,
        ).status_code
        == 404
    )


def test_meta_acima_do_objetivo_mostra_progresso_real_e_restante_zero(
    client: TestClient,
) -> None:
    _, token = _usuario_autenticado(client)
    meta = _criar_meta(
        client,
        token,
        valor_meta="2000.00",
        valor_atual="2500.00",
    )

    assert meta["status"] == "concluida"
    assert meta["progresso_percentual"] == "125.00"
    assert meta["valor_restante"] == "0.00"


def test_meta_cancelada_permanece_cancelada_e_progresso_e_calculado(
    client: TestClient,
) -> None:
    _, token = _usuario_autenticado(client)
    meta = _criar_meta(
        client,
        token,
        valor_meta="5000.00",
        valor_atual="2500.00",
        status="cancelada",
    )

    assert meta["status"] == "cancelada"
    assert meta["progresso_percentual"] == "50.00"
    assert meta["valor_restante"] == "2500.00"


def test_meta_isolada_por_usuario_em_busca_listagem_edicao_e_exclusao(
    client: TestClient,
) -> None:
    _, token_a = _usuario_autenticado(client)
    _, token_b = _usuario_autenticado(client)
    meta = _criar_meta(client, token_a)
    url = f"/metas-financeiras/{meta['id']}"

    assert client.get(url, headers=token_b).status_code == 404
    assert client.put(
        url,
        headers=token_b,
        json={
            "nome": "Tentativa de alteração",
            "valor_meta": "5000.00",
            "valor_atual": "2500.00",
            "data_inicio": date.today().isoformat(),
        },
    ).status_code == 404
    assert client.delete(url, headers=token_b).status_code == 404

    lista_b = client.get("/metas-financeiras/", headers=token_b)
    assert lista_b.status_code == 200
    assert meta["id"] not in {item["id"] for item in lista_b.json()}


def test_meta_rejeita_data_limite_anterior_ao_inicio(
    client: TestClient,
) -> None:
    _, token = _usuario_autenticado(client)
    inicio = date.today()
    resposta = client.post(
        "/metas-financeiras/",
        headers=token,
        json={
            "nome": "Meta com datas inválidas",
            "valor_meta": "100.00",
            "valor_atual": "0.00",
            "data_inicio": inicio.isoformat(),
            "data_limite": (inicio - timedelta(days=1)).isoformat(),
        },
    )

    assert resposta.status_code == 422


def test_meta_com_valor_minimo_tem_progresso_preciso_e_pode_ser_concluida(
    client: TestClient,
) -> None:
    _, token = _usuario_autenticado(client)
    meta = _criar_meta(
        client,
        token,
        valor_meta="0.01",
        valor_atual="0.00",
    )
    assert meta["progresso_percentual"] == "0.00"
    assert meta["valor_restante"] == "0.01"
    assert meta["status"] == "em_andamento"

    atualizada = client.put(
        f"/metas-financeiras/{meta['id']}",
        headers=token,
        json={
            "nome": "Meta mínima",
            "valor_meta": "0.01",
            "valor_atual": "0.01",
            "data_inicio": date.today().isoformat(),
            "status": "em_andamento",
        },
    )
    assert atualizada.status_code == 200, atualizada.text
    assert atualizada.json()["progresso_percentual"] == "100.00"
    assert atualizada.json()["valor_restante"] == "0.00"
    assert atualizada.json()["status"] == "concluida"


def test_relatorio_sem_movimentacoes_preserva_saldo_zero(
    client: TestClient,
) -> None:
    _, token = _usuario_autenticado(client)
    conta = client.post(
        "/contas-bancarias/",
        headers=token,
        json={
            "nome_banco": "Conta sem movimentos",
            "tipo_conta": "poupanca",
            "valor_conta_atual": "0.00",
            "ativa": True,
        },
    ).json()
    hoje = date.today().isoformat()

    relatorio = client.post(
        "/calculos-financeiros/",
        headers=token,
        json={
            "conta_bancaria_id": conta["id"],
            "tipo_calculo": "diario",
            "data_inicio": hoje,
            "data_fim": hoje,
        },
    )

    assert relatorio.status_code == 201, relatorio.text
    corpo = relatorio.json()
    assert corpo["valor_original"] == "0.00"
    assert corpo["total_entradas"] == "0.00"
    assert corpo["total_saidas"] == "0.00"
    assert corpo["valor_final"] == "0.00"


@pytest.mark.parametrize(
    ("tipo", "categoria", "saldo_esperado"),
    [
        ("entrada", "salario", "25.75"),
        ("saida", "contas", "-25.75"),
    ],
)
def test_conta_corrente_com_somente_entrada_ou_saida(
    client: TestClient,
    tipo: str,
    categoria: str,
    saldo_esperado: str,
) -> None:
    _, token = _usuario_autenticado(client)
    conta = client.post(
        "/contas-bancarias/",
        headers=token,
        json={
            "nome_banco": "Conta de caso extremo",
            "tipo_conta": "corrente",
            "valor_conta_atual": "0.00",
            "ativa": True,
        },
    ).json()
    hoje = date.today().isoformat()

    movimento = client.post(
        "/fluxo-dinheiro/",
        headers=token,
        json={
            "conta_bancaria_id": conta["id"],
            "descricao": "Movimento único",
            "valor": "25.75",
            "tipo": tipo,
            "categoria": categoria,
            "data_movimentacao": hoje,
        },
    )
    assert movimento.status_code == 201, movimento.text

    saldo = client.get(
        f"/contas-bancarias/{conta['id']}",
        headers=token,
    )
    assert saldo.status_code == 200
    assert saldo.json()["valor_conta_atual"] == saldo_esperado

    relatorio = client.post(
        "/calculos-financeiros/",
        headers=token,
        json={
            "conta_bancaria_id": conta["id"],
            "tipo_calculo": "diario",
            "data_inicio": hoje,
            "data_fim": hoje,
        },
    )
    assert relatorio.status_code == 201, relatorio.text
    assert relatorio.json()["valor_final"] == saldo_esperado


def test_saida_maior_que_saldo_e_permitida_em_conta_corrente(
    client: TestClient,
) -> None:
    _, token = _usuario_autenticado(client)
    conta = client.post(
        "/contas-bancarias/",
        headers=token,
        json={
            "nome_banco": "Conta corrente com limite",
            "tipo_conta": "corrente",
            "valor_conta_atual": "10.00",
            "ativa": True,
        },
    ).json()
    hoje = date.today().isoformat()

    movimento = client.post(
        "/fluxo-dinheiro/",
        headers=token,
        json={
            "conta_bancaria_id": conta["id"],
            "descricao": "Saída superior ao saldo",
            "valor": "12.35",
            "tipo": "saida",
            "categoria": "contas",
            "data_movimentacao": hoje,
        },
    )
    assert movimento.status_code == 201, movimento.text

    saldo = client.get(
        f"/contas-bancarias/{conta['id']}",
        headers=token,
    )
    assert saldo.status_code == 200
    assert saldo.json()["valor_conta_atual"] == "-2.35"

    relatorio = client.post(
        "/calculos-financeiros/",
        headers=token,
        json={
            "conta_bancaria_id": conta["id"],
            "tipo_calculo": "diario",
            "data_inicio": hoje,
            "data_fim": hoje,
        },
    )
    assert relatorio.status_code == 201, relatorio.text
    assert relatorio.json()["total_saidas"] == "12.35"
    assert relatorio.json()["valor_final"] == "-2.35"


def test_saldo_zero_rejeita_saida_em_conta_sem_limite(
    client: TestClient,
) -> None:
    _, token = _usuario_autenticado(client)
    conta = client.post(
        "/contas-bancarias/",
        headers=token,
        json={
            "nome_banco": "Poupança sem saldo",
            "tipo_conta": "poupanca",
            "valor_conta_atual": "0.00",
            "ativa": True,
        },
    ).json()
    movimento = client.post(
        "/fluxo-dinheiro/",
        headers=token,
        json={
            "conta_bancaria_id": conta["id"],
            "descricao": "Saída sem cobertura",
            "valor": "0.01",
            "tipo": "saida",
            "categoria": "contas",
            "data_movimentacao": date.today().isoformat(),
        },
    )

    assert movimento.status_code == 400
    saldo = client.get(
        f"/contas-bancarias/{conta['id']}",
        headers=token,
    )
    assert saldo.status_code == 200
    assert saldo.json()["valor_conta_atual"] == "0.00"


def test_movimentacao_rejeita_valor_zero_e_preserva_saldo(
    client: TestClient,
) -> None:
    _, token = _usuario_autenticado(client)
    conta = _criar_conta(client, token)
    resposta = client.post(
        "/fluxo-dinheiro/",
        headers=token,
        json={
            "conta_bancaria_id": conta["id"],
            "descricao": "Valor zero",
            "valor": "0.00",
            "tipo": "entrada",
            "categoria": "salario",
            "data_movimentacao": date.today().isoformat(),
        },
    )

    assert resposta.status_code == 422
    saldo = client.get(
        f"/contas-bancarias/{conta['id']}",
        headers=token,
    )
    assert saldo.status_code == 200
    assert saldo.json()["valor_conta_atual"] == "1000.00"


def test_decimais_centavos_sao_consistentes_entre_conta_e_relatorio(
    client: TestClient,
) -> None:
    _, token = _usuario_autenticado(client)
    conta = _criar_conta(client, token)
    hoje = date.today().isoformat()

    for valor, tipo, categoria in (
        ("0.10", "entrada", "salario"),
        ("0.03", "saida", "contas"),
    ):
        movimento = client.post(
            "/fluxo-dinheiro/",
            headers=token,
            json={
                "conta_bancaria_id": conta["id"],
                "descricao": "Teste de centavos",
                "valor": valor,
                "tipo": tipo,
                "categoria": categoria,
                "data_movimentacao": hoje,
            },
        )
        assert movimento.status_code == 201, movimento.text

    conta_atualizada = client.get(
        f"/contas-bancarias/{conta['id']}",
        headers=token,
    )
    assert conta_atualizada.status_code == 200
    saldo = conta_atualizada.json()["valor_conta_atual"]
    assert saldo == "1000.07"

    relatorio = client.post(
        "/calculos-financeiros/",
        headers=token,
        json={
            "conta_bancaria_id": conta["id"],
            "tipo_calculo": "diario",
            "data_inicio": hoje,
            "data_fim": hoje,
        },
    )
    assert relatorio.status_code == 201, relatorio.text
    assert relatorio.json()["total_entradas"] == "0.10"
    assert relatorio.json()["total_saidas"] == "0.03"
    assert relatorio.json()["valor_final"] == saldo


def test_movimentacao_com_data_futura_afeta_saldo_e_relatorio_futuro_e_rejeitado(
    client: TestClient,
) -> None:
    _, token = _usuario_autenticado(client)
    conta = _criar_conta(client, token)
    amanha = date.today() + timedelta(days=1)

    movimento = client.post(
        "/fluxo-dinheiro/",
        headers=token,
        json={
            "conta_bancaria_id": conta["id"],
            "descricao": "Lançamento futuro",
            "valor": "10.00",
            "tipo": "entrada",
            "categoria": "salario",
            "data_movimentacao": amanha.isoformat(),
        },
    )
    assert movimento.status_code == 201, movimento.text

    saldo = client.get(
        f"/contas-bancarias/{conta['id']}",
        headers=token,
    )
    assert saldo.status_code == 200
    assert saldo.json()["valor_conta_atual"] == "1010.00"

    relatorio_futuro = client.post(
        "/calculos-financeiros/",
        headers=token,
        json={
            "conta_bancaria_id": conta["id"],
            "tipo_calculo": "diario",
            "data_inicio": amanha.isoformat(),
            "data_fim": amanha.isoformat(),
        },
    )
    assert relatorio_futuro.status_code == 400


def test_relatorio_diario_soma_entradas_saidas_e_saldos_com_limites_inclusivos(
    client: TestClient,
) -> None:
    _, token = _usuario_autenticado(client)
    conta = _criar_conta(client, token)
    hoje = date.today()
    ontem = hoje - timedelta(days=1)

    for descricao, valor, tipo, categoria, data in (
        ("Saída anterior ao período", "100.00", "saida", "contas", ontem),
        ("Entrada do período", "500.00", "entrada", "salario", hoje),
        ("Saída do período", "200.00", "saida", "contas", hoje),
    ):
        resposta = client.post(
            "/fluxo-dinheiro/",
            headers=token,
            json={
                "conta_bancaria_id": conta["id"],
                "descricao": descricao,
                "valor": valor,
                "tipo": tipo,
                "categoria": categoria,
                "data_movimentacao": data.isoformat(),
            },
        )
        assert resposta.status_code == 201, resposta.text

    relatorio = client.post(
        "/calculos-financeiros/",
        headers=token,
        json={
            "conta_bancaria_id": conta["id"],
            "tipo_calculo": "diario",
            "data_inicio": hoje.isoformat(),
            "data_fim": hoje.isoformat(),
        },
    )
    assert relatorio.status_code == 201, relatorio.text
    corpo = relatorio.json()
    assert corpo["valor_original"] == "900.00"
    assert corpo["total_entradas"] == "500.00"
    assert corpo["total_saidas"] == "200.00"
    assert corpo["valor_final"] == "1200.00"
    saldo_conta = client.get(
        f"/contas-bancarias/{conta['id']}",
        headers=token,
    )
    assert saldo_conta.status_code == 200
    assert corpo["valor_final"] == saldo_conta.json()["valor_conta_atual"]

    consulta = client.get(
        f"/calculos-financeiros/{corpo['id']}",
        headers=token,
    )
    assert consulta.status_code == 200
    assert consulta.json()["valor_final"] == "1200.00"

    lista = client.get(
        f"/calculos-financeiros/?conta_bancaria_id={conta['id']}"
        f"&data_inicio={hoje.isoformat()}&data_fim={hoje.isoformat()}",
        headers=token,
    )
    assert lista.status_code == 200
    assert [item["id"] for item in lista.json()] == [corpo["id"]]

    exclusao = client.delete(
        f"/calculos-financeiros/{corpo['id']}",
        headers=token,
    )
    assert exclusao.status_code == 200
    assert (
        client.get(
            f"/calculos-financeiros/{corpo['id']}",
            headers=token,
        ).status_code
        == 404
    )


@pytest.mark.parametrize(
    ("tipo_calculo", "data_inicio", "data_fim"),
    [
        ("diario", lambda hoje: hoje, lambda hoje: hoje),
        (
            "semanal",
            lambda hoje: hoje - timedelta(days=6),
            lambda hoje: hoje,
        ),
        (
            "mensal",
            lambda hoje: hoje.replace(day=1),
            lambda hoje: (
                hoje.replace(day=28) + timedelta(days=4)
            ).replace(day=1)
            - timedelta(days=1),
        ),
        (
            "anual",
            lambda hoje: hoje.replace(month=1, day=1),
            lambda hoje: hoje.replace(month=12, day=31),
        ),
    ],
)
def test_relatorio_aceita_periodos_diario_semanal_mensal_e_anual(
    client: TestClient,
    tipo_calculo: str,
    data_inicio,
    data_fim,
) -> None:
    _, token = _usuario_autenticado(client)
    conta = _criar_conta(client, token)
    hoje = date.today()

    resposta = client.post(
        "/calculos-financeiros/",
        headers=token,
        json={
            "conta_bancaria_id": conta["id"],
            "tipo_calculo": tipo_calculo,
            "data_inicio": data_inicio(hoje).isoformat(),
            "data_fim": data_fim(hoje).isoformat(),
        },
    )

    assert resposta.status_code == 201, resposta.text
    assert resposta.json()["tipo_calculo"] == tipo_calculo
    assert Decimal(resposta.json()["valor_final"]) == Decimal("1000.00")


def test_relatorio_rejeita_periodo_invalido_e_conta_de_outro_usuario(
    client: TestClient,
) -> None:
    _, token_a = _usuario_autenticado(client)
    _, token_b = _usuario_autenticado(client)
    conta_a = _criar_conta(client, token_a)
    hoje = date.today()

    periodo_invertido = client.post(
        "/calculos-financeiros/",
        headers=token_a,
        json={
            "conta_bancaria_id": conta_a["id"],
            "tipo_calculo": "diario",
            "data_inicio": hoje.isoformat(),
            "data_fim": (hoje - timedelta(days=1)).isoformat(),
        },
    )
    assert periodo_invertido.status_code == 422

    data_futura = hoje + timedelta(days=1)
    periodo_futuro = client.post(
        "/calculos-financeiros/",
        headers=token_a,
        json={
            "conta_bancaria_id": conta_a["id"],
            "tipo_calculo": "diario",
            "data_inicio": data_futura.isoformat(),
            "data_fim": data_futura.isoformat(),
        },
    )
    assert periodo_futuro.status_code == 400

    conta_alheia = client.post(
        "/calculos-financeiros/",
        headers=token_b,
        json={
            "conta_bancaria_id": conta_a["id"],
            "tipo_calculo": "diario",
            "data_inicio": hoje.isoformat(),
            "data_fim": hoje.isoformat(),
        },
    )
    assert conta_alheia.status_code == 404


def test_usuario_b_nao_pode_manipular_conta_movimentacao_relatorio_ou_meta_de_a(
    client: TestClient,
) -> None:
    _, token_a = _usuario_autenticado(client)
    _, token_b = _usuario_autenticado(client)
    conta_a = _criar_conta(client, token_a)
    hoje = date.today()
    movimento_a = client.post(
        "/fluxo-dinheiro/",
        headers=token_a,
        json={
            "conta_bancaria_id": conta_a["id"],
            "descricao": "Entrada protegida",
            "valor": "25.00",
            "tipo": "entrada",
            "categoria": "salario",
            "data_movimentacao": hoje.isoformat(),
        },
    )
    assert movimento_a.status_code == 201, movimento_a.text
    movimento = movimento_a.json()

    relatorio_a = client.post(
        "/calculos-financeiros/",
        headers=token_a,
        json={
            "conta_bancaria_id": conta_a["id"],
            "tipo_calculo": "diario",
            "data_inicio": hoje.isoformat(),
            "data_fim": hoje.isoformat(),
        },
    )
    assert relatorio_a.status_code == 201, relatorio_a.text
    relatorio = relatorio_a.json()

    meta = _criar_meta(client, token_a)
    ids_e_rotas = (
        (f"/contas-bancarias/{conta_a['id']}", "conta"),
        (f"/fluxo-dinheiro/{movimento['id']}", "movimentação"),
        (f"/calculos-financeiros/{relatorio['id']}", "relatório"),
        (f"/metas-financeiras/{meta['id']}", "meta"),
    )
    for url, recurso in ids_e_rotas:
        assert client.get(url, headers=token_b).status_code == 404, recurso
        assert client.delete(url, headers=token_b).status_code == 404, recurso

    alteracao_conta = client.put(
        f"/contas-bancarias/{conta_a['id']}",
        headers=token_b,
        json={
            "nome_banco": "Tentativa de alteração",
            "tipo_conta": "corrente",
            "ativa": False,
        },
    )
    assert alteracao_conta.status_code == 404

    alteracao_movimento = client.put(
        f"/fluxo-dinheiro/{movimento['id']}",
        headers=token_b,
        json={
            "conta_bancaria_id": conta_a["id"],
            "descricao": "Tentativa de alteração",
            "valor": "1.00",
            "tipo": "entrada",
            "categoria": "salario",
            "data_movimentacao": hoje.isoformat(),
        },
    )
    assert alteracao_movimento.status_code == 404

    alteracao_meta = client.put(
        f"/metas-financeiras/{meta['id']}",
        headers=token_b,
        json={
            "nome": "Tentativa de alteração",
            "valor_meta": "5000.00",
            "valor_atual": "0.00",
            "data_inicio": hoje.isoformat(),
        },
    )
    assert alteracao_meta.status_code == 404

    for url in (
        "/contas-bancarias/",
        "/fluxo-dinheiro/",
        "/calculos-financeiros/",
        "/metas-financeiras/",
    ):
        resposta = client.get(url, headers=token_b)
        assert resposta.status_code == 200
        assert resposta.json() == []

    conta_a_depois = client.get(
        f"/contas-bancarias/{conta_a['id']}",
        headers=token_a,
    )
    movimento_a_depois = client.get(
        f"/fluxo-dinheiro/{movimento['id']}",
        headers=token_a,
    )
    relatorio_a_depois = client.get(
        f"/calculos-financeiros/{relatorio['id']}",
        headers=token_a,
    )
    meta_a_depois = client.get(
        f"/metas-financeiras/{meta['id']}",
        headers=token_a,
    )
    assert conta_a_depois.status_code == 200
    assert conta_a_depois.json()["valor_conta_atual"] == "1025.00"
    assert movimento_a_depois.status_code == 200
    assert movimento_a_depois.json()["descricao"] == "Entrada protegida"
    assert relatorio_a_depois.status_code == 200
    assert meta_a_depois.status_code == 200



def test_resumo_periodo_customizado_e_exportacao_csv(
    client: TestClient,
) -> None:
    _, token_a = _usuario_autenticado(client)
    _, token_b = _usuario_autenticado(client)
    conta_1 = _criar_conta(client, token_a)
    conta_2 = client.post(
        "/contas-bancarias/",
        headers=token_a,
        json={
            "nome_banco": "Conta Poupança Relatório",
            "tipo_conta": "poupanca",
            "valor_conta_atual": "500.00",
            "ativa": True,
        },
    ).json()

    hoje = date.today()
    inicio_custom = hoje - timedelta(days=3)

    for conta_id, descricao, valor, tipo, categoria, data_mov in (
        (conta_1["id"], "Salário parcial", "300.00", "entrada", "salario", inicio_custom),
        (conta_1["id"], "Mercado semana", "120.00", "saida", "alimentacao", hoje),
        (conta_2["id"], "Rendimento poupança", "50.00", "entrada", "investimento", hoje),
    ):
        resp = client.post(
            "/fluxo-dinheiro/",
            headers=token_a,
            json={
                "conta_bancaria_id": conta_id,
                "descricao": descricao,
                "valor": valor,
                "tipo": tipo,
                "categoria": categoria,
                "data_movimentacao": data_mov.isoformat(),
            },
        )
        assert resp.status_code == 201, resp.text

    # 1. Resumo consolidado de todas as contas em intervalo customizado (4 dias)
    resumo_geral = client.get(
        f"/calculos-financeiros/resumo?data_inicio={inicio_custom.isoformat()}"
        f"&data_fim={hoje.isoformat()}",
        headers=token_a,
    )
    assert resumo_geral.status_code == 200, resumo_geral.text
    dados_gerais = resumo_geral.json()
    assert dados_gerais["conta_bancaria_id"] is None
    assert dados_gerais["saldo_inicial"] == "1500.00"
    assert dados_gerais["total_entradas"] == "350.00"
    assert dados_gerais["total_saidas"] == "120.00"
    assert dados_gerais["saldo_final"] == "1730.00"

    # 2. Resumo filtrado por uma conta específica
    resumo_conta_1 = client.get(
        f"/calculos-financeiros/resumo?conta_bancaria_id={conta_1['id']}"
        f"&data_inicio={inicio_custom.isoformat()}&data_fim={hoje.isoformat()}",
        headers=token_a,
    )
    assert resumo_conta_1.status_code == 200, resumo_conta_1.text
    dados_c1 = resumo_conta_1.json()
    assert dados_c1["conta_bancaria_id"] == conta_1["id"]
    assert dados_c1["saldo_inicial"] == "1000.00"
    assert dados_c1["total_entradas"] == "300.00"
    assert dados_c1["total_saidas"] == "120.00"
    assert dados_c1["saldo_final"] == "1180.00"

    # 3. Isolamento entre usuários e validações de período no resumo
    assert (
        client.get(
            f"/calculos-financeiros/resumo?conta_bancaria_id={conta_1['id']}"
            f"&data_inicio={inicio_custom.isoformat()}&data_fim={hoje.isoformat()}",
            headers=token_b,
        ).status_code
        == 404
    )
    assert (
        client.get(
            f"/calculos-financeiros/resumo?data_inicio={hoje.isoformat()}"
            f"&data_fim={inicio_custom.isoformat()}",
            headers=token_a,
        ).status_code
        == 422
    )

    # 4. Exportação CSV
    csv_resp = client.get(
        f"/fluxo-dinheiro/exportar-csv?data_inicio={inicio_custom.isoformat()}"
        f"&data_fim={hoje.isoformat()}",
        headers=token_a,
    )
    assert csv_resp.status_code == 200
    assert "text/csv" in csv_resp.headers["content-type"]
    conteudo_csv = csv_resp.text
    assert "id;data_movimentacao;conta_bancaria_id;tipo;categoria;descricao;valor;observacao" in conteudo_csv
    assert "Salário parcial" in conteudo_csv
    assert "Mercado semana" in conteudo_csv

    # Usuário B não vê os dados de A no CSV
    csv_b = client.get("/fluxo-dinheiro/exportar-csv", headers=token_b)
    assert csv_b.status_code == 200
    assert "Salário parcial" not in csv_b.text
