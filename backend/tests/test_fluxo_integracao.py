from datetime import date
from decimal import Decimal
from uuid import uuid4

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


def _cadastrar_usuario(
    client: TestClient,
    marcador: str,
    identificador: str,
) -> dict:
    resposta = client.post(
        "/usuarios/",
        json={
            "nome_completo": f"Usuário de teste {identificador}",
            "cpf": _cpf_valido(),
            "email": f"teste-{marcador}-{identificador}@example.com",
            "senha": "TesteSeguro2026!",
        },
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def _obter_token(
    client: TestClient,
    email: str,
    senha: str,
) -> dict[str, str]:
    resposta = client.post(
        "/login",
        data={"username": email, "password": senha},
    )
    assert resposta.status_code == 200, resposta.text
    corpo = resposta.json()
    assert corpo["access_token"]
    assert corpo["token_type"] == "bearer"
    return {"Authorization": f"Bearer {corpo['access_token']}"}


def test_cadastro_login_jwt_fluxo_financeiro_e_isolamento_entre_usuarios(
    client: TestClient,
) -> None:
    marcador = uuid4().hex
    senha = "TesteSeguro2026!"
    email_a = f"teste-{marcador}-a@example.com"
    email_b = f"teste-{marcador}-b@example.com"
    dados_criados: dict[str, list[dict]] = {
        "usuarios": [],
        "contas": [],
        "movimentacoes": [],
    }
    tokens: list[dict[str, str]] = []

    try:
        assert client.get("/usuarios/me").status_code == 401
        assert (
            client.get(
                "/usuarios/me",
                headers={"Authorization": "Bearer token-invalido"},
            ).status_code
            == 401
        )

        usuario_a = _cadastrar_usuario(client, marcador, "a")
        dados_criados["usuarios"].append(usuario_a)
        usuario_b = _cadastrar_usuario(client, marcador, "b")
        dados_criados["usuarios"].append(usuario_b)

        login_invalido = client.post(
            "/login",
            data={"username": email_a, "password": "SenhaErrada2026!"},
        )
        assert login_invalido.status_code == 401

        token_a = _obter_token(client, email_a, senha)
        tokens.append(token_a)
        token_b = _obter_token(client, email_b, senha)
        tokens.append(token_b)

        usuario_logado_a = client.get("/usuarios/me", headers=token_a)
        usuario_logado_b = client.get("/usuarios/me", headers=token_b)
        assert usuario_logado_a.status_code == 200
        assert usuario_logado_b.status_code == 200
        assert usuario_logado_a.json()["id"] == usuario_a["id"]
        assert usuario_logado_b.json()["id"] == usuario_b["id"]
        assert "cpf" not in usuario_logado_a.json()
        assert "cpf" not in usuario_logado_b.json()

        acesso_usuario_alheio = client.get(
            f"/usuarios/{usuario_a['id']}",
            headers=token_b,
        )
        assert acesso_usuario_alheio.status_code == 404
        exclusao_usuario_alheio = client.delete(
            f"/usuarios/{usuario_a['id']}",
            headers=token_b,
        )
        assert exclusao_usuario_alheio.status_code == 404

        resposta_conta_a = client.post(
            "/contas-bancarias/",
            headers=token_a,
            json={
                "nome_banco": f"Banco de teste {marcador[:8]} A",
                "tipo_conta": "corrente",
                "valor_conta_atual": "1000.00",
                "ativa": True,
            },
        )
        assert resposta_conta_a.status_code == 201, resposta_conta_a.text
        conta_a = resposta_conta_a.json()
        dados_criados["contas"].append(conta_a)

        resposta_conta_b = client.post(
            "/contas-bancarias/",
            headers=token_b,
            json={
                "nome_banco": f"Banco de teste {marcador[:8]} B",
                "tipo_conta": "corrente",
                "valor_conta_atual": "200.00",
                "ativa": True,
            },
        )
        assert resposta_conta_b.status_code == 201, resposta_conta_b.text
        conta_b = resposta_conta_b.json()
        dados_criados["contas"].append(conta_b)
        assert conta_a["usuario_id"] == usuario_a["id"]
        assert conta_b["usuario_id"] == usuario_b["id"]

        hoje = date.today().isoformat()
        for token, conta, descricao, valor, tipo, categoria in (
            (
                token_a,
                conta_a,
                "Entrada de teste",
                "500.00",
                "entrada",
                "salario",
            ),
            (
                token_a,
                conta_a,
                "Saída de teste",
                "200.00",
                "saida",
                "contas",
            ),
            (
                token_b,
                conta_b,
                "Entrada do usuário B",
                "50.00",
                "entrada",
                "salario",
            ),
        ):
            resposta_movimentacao = client.post(
                "/fluxo-dinheiro/",
                headers=token,
                json={
                    "conta_bancaria_id": conta["id"],
                    "descricao": descricao,
                    "valor": valor,
                    "tipo": tipo,
                    "categoria": categoria,
                    "data_movimentacao": hoje,
                },
            )
            assert resposta_movimentacao.status_code == 201, (
                resposta_movimentacao.text
            )
            dados_criados["movimentacoes"].append(
                resposta_movimentacao.json()
            )

        saldo_a = client.get(
            f"/contas-bancarias/{conta_a['id']}",
            headers=token_a,
        )
        saldo_b = client.get(
            f"/contas-bancarias/{conta_b['id']}",
            headers=token_b,
        )
        assert saldo_a.status_code == 200
        assert saldo_b.status_code == 200
        assert Decimal(saldo_a.json()["valor_conta_atual"]) == Decimal(
            "1300.00"
        )
        assert Decimal(saldo_b.json()["valor_conta_atual"]) == Decimal(
            "250.00"
        )

        movimento_a = dados_criados["movimentacoes"][0]
        assert (
            client.get(
                f"/contas-bancarias/{conta_a['id']}",
                headers=token_b,
            ).status_code
            == 404
        )
        assert (
            client.put(
                f"/contas-bancarias/{conta_a['id']}",
                headers=token_b,
                json={
                    "nome_banco": "Conta alterada indevidamente",
                    "tipo_conta": "corrente",
                    "ativa": False,
                },
            ).status_code
            == 404
        )
        assert (
            client.delete(
                f"/contas-bancarias/{conta_a['id']}",
                headers=token_b,
            ).status_code
            == 404
        )
        assert (
            client.get(
                f"/fluxo-dinheiro/{movimento_a['id']}",
                headers=token_b,
            ).status_code
            == 404
        )
        dados_movimentacao_alheia = {
            "conta_bancaria_id": conta_b["id"],
            "descricao": "Tentativa de edição cruzada",
            "valor": "1.00",
            "tipo": "entrada",
            "categoria": "salario",
            "data_movimentacao": hoje,
        }
        assert (
            client.put(
                f"/fluxo-dinheiro/{movimento_a['id']}",
                headers=token_b,
                json=dados_movimentacao_alheia,
            ).status_code
            == 404
        )
        assert (
            client.delete(
                f"/fluxo-dinheiro/{movimento_a['id']}",
                headers=token_b,
            ).status_code
            == 404
        )
        escrita_cruzada = client.post(
            "/fluxo-dinheiro/",
            headers=token_b,
            json={
                "conta_bancaria_id": conta_a["id"],
                "descricao": "Tentativa de acesso cruzado",
                "valor": "1.00",
                "tipo": "entrada",
                "categoria": "salario",
                "data_movimentacao": hoje,
            },
        )
        assert escrita_cruzada.status_code == 404

        contas_usuario_b = client.get(
            "/contas-bancarias/",
            headers=token_b,
        )
        movimentacoes_usuario_b = client.get(
            "/fluxo-dinheiro/",
            headers=token_b,
        )
        assert contas_usuario_b.status_code == 200
        assert movimentacoes_usuario_b.status_code == 200
        assert conta_a["id"] not in {
            conta["id"] for conta in contas_usuario_b.json()
        }
        assert movimento_a["id"] not in {
            movimentacao["id"]
            for movimentacao in movimentacoes_usuario_b.json()
        }
    finally:
        if len(tokens) == len(dados_criados["usuarios"]):
            for movimentacao in reversed(dados_criados["movimentacoes"]):
                token = (
                    tokens[0]
                    if movimentacao["conta_bancaria_id"]
                    == dados_criados["contas"][0]["id"]
                    else tokens[1]
                )
                resposta = client.delete(
                    f"/fluxo-dinheiro/{movimentacao['id']}",
                    headers=token,
                )
                assert resposta.status_code == 200, resposta.text

            for indice, conta in reversed(
                list(enumerate(dados_criados["contas"]))
            ):
                resposta = client.delete(
                    f"/contas-bancarias/{conta['id']}",
                    headers=tokens[indice],
                )
                assert resposta.status_code == 200, resposta.text

            for indice, usuario in reversed(
                list(enumerate(dados_criados["usuarios"]))
            ):
                resposta = client.delete(
                    f"/usuarios/{usuario['id']}",
                    headers=tokens[indice],
                )
                assert resposta.status_code == 200, resposta.text
