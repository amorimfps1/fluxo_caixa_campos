from datetime import date, timedelta
from decimal import Decimal

from models import ContaBancaria, FluxoDinheiro
from test_metas_relatorios import _usuario_autenticado


def test_orcamentos_alertas_isolamento_e_recalculo(client, db):
    usuario, token = _usuario_autenticado(client)
    _, outro = _usuario_autenticado(client)
    hoje = date.today()
    mes = hoje.replace(day=1).isoformat()
    conta = ContaBancaria(
        usuario_id=usuario['id'],
        nome_banco='Teste',
        tipo_conta='corrente',
        valor_conta_atual=100,
        ativa=True
    )
    db.add(conta)
    db.flush()
    movimento = FluxoDinheiro(
        conta_bancaria_id=conta.id,
        descricao='Despesa',
        valor=Decimal('12.50'),
        tipo='saida',
        categoria='alimentacao',
        data_movimentacao=hoje
    )
    futuro = FluxoDinheiro(
        conta_bancaria_id=conta.id,
        descricao='Futuro',
        valor=Decimal('4.00'),
        tipo='saida',
        categoria='alimentacao',
        data_movimentacao=hoje + timedelta(days=1)
    )
    db.add_all([movimento, futuro])
    db.commit()

    payload = {'categoria': 'alimentacao', 'mes': mes, 'limite': '0.00'}
    criado = client.post('/orcamentos', headers=token, json=payload)
    assert criado.status_code == 201, criado.text
    item_id = criado.json()['id']

    # Não permite duplicado para mesma categoria e mês
    assert client.post('/orcamentos', headers=token, json=payload).status_code == 409

    # Consulta orçamentos
    itens = client.get('/orcamentos', headers=token, params={'mes': mes}).json()
    assert len(itens) == 1
    item = itens[0]
    assert Decimal(str(item['gasto'])) == Decimal('12.50')
    assert Decimal(str(item['restante'])) == Decimal('-12.50')
    assert item['percentual_gasto'] == 0.0 or item['percentual_gasto'] >= 100.0

    # Isolamento de inquilinos
    assert client.get('/orcamentos', headers=outro, params={'mes': mes}).json() == []
    assert client.delete(f'/orcamentos/{item_id}', headers=outro).status_code == 404

    # Alertas
    alertas = client.get('/alertas', headers=token).json()
    assert len(alertas) == 3
    chave = next(a['chave'] for a in alertas if a['chave'].startswith('orcamento:'))
    assert client.put('/alertas/lido', headers=outro, params={'chave': chave}).status_code == 404
    assert client.put('/alertas/lido', headers=token, params={'chave': chave}).status_code == 200
    assert next(a for a in client.get('/alertas', headers=token).json() if a['chave'] == chave)['lido']

    # Preferências de alertas
    assert client.put('/alertas/preferencias', headers=token, json={'orcamento': False, 'vencimento': False}).status_code == 200
    assert client.get('/alertas', headers=token).json() == []

    # Recálculo após alteração
    movimento.valor = Decimal('3.00')
    db.commit()
    item = client.get('/orcamentos', headers=token, params={'mes': mes}).json()[0]
    assert Decimal(str(item['gasto'])) == Decimal('3.00')


def test_orcamentos_validacoes_e_edicao(client, db):
    usuario, token = _usuario_autenticado(client)
    hoje = date.today()
    mes_valido = hoje.replace(day=1).isoformat()
    mes_invalido = hoje.replace(day=15).isoformat()

    # Validação do primeiro dia do mês
    resp_invalido = client.post(
        '/orcamentos',
        headers=token,
        json={'categoria': 'alimentacao', 'mes': mes_invalido, 'limite': '500.00'}
    )
    assert resp_invalido.status_code == 422

    # Validação de categoria inexistente
    resp_cat = client.post(
        '/orcamentos',
        headers=token,
        json={'categoria': 'categoria_inexistente_xyz', 'mes': mes_valido, 'limite': '500.00'}
    )
    assert resp_cat.status_code == 422

    # Criação válida
    criado = client.post(
        '/orcamentos',
        headers=token,
        json={'categoria': 'alimentacao', 'mes': mes_valido, 'limite': '500.00'}
    )
    assert criado.status_code == 201
    orcamento_id = criado.json()['id']

    # Edição do orçamento
    editado = client.put(
        f'/orcamentos/{orcamento_id}',
        headers=token,
        json={'categoria': 'alimentacao', 'mes': mes_valido, 'limite': '850.00'}
    )
    assert editado.status_code == 200

    itens = client.get('/orcamentos', headers=token, params={'mes': mes_valido}).json()
    assert Decimal(str(itens[0]['limite'])) == Decimal('850.00')

    # Exclusão com sucesso
    assert client.delete(f'/orcamentos/{orcamento_id}', headers=token).status_code == 200
    assert client.get('/orcamentos', headers=token, params={'mes': mes_valido}).json() == []
