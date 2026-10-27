from datetime import date, timedelta
from decimal import Decimal

from models import ContaBancaria, FluxoDinheiro
from test_metas_relatorios import _usuario_autenticado


def test_orcamentos_alertas_isolamento_e_recalculo(client, db):
    usuario, token = _usuario_autenticado(client)
    _, outro = _usuario_autenticado(client)
    hoje = date.today()
    mes = hoje.replace(day=1).isoformat()
    conta = ContaBancaria(usuario_id=usuario['id'], nome_banco='Teste', tipo_conta='corrente', valor_conta_atual=100, ativa=True)
    db.add(conta)
    db.flush()
    movimento = FluxoDinheiro(conta_bancaria_id=conta.id, descricao='Despesa', valor=Decimal('12.50'), tipo='saida', categoria='alimentacao', data_movimentacao=hoje)
    futuro = FluxoDinheiro(conta_bancaria_id=conta.id, descricao='Futuro', valor=Decimal('4.00'), tipo='saida', categoria='alimentacao', data_movimentacao=hoje + timedelta(days=1))
    db.add_all([movimento, futuro])
    db.commit()
    payload = {'categoria': 'alimentacao', 'mes': mes, 'limite': '0.00'}
    criado = client.post('/orcamentos', headers=token, json=payload)
    assert criado.status_code == 201, criado.text
    item_id = criado.json()['id']
    assert client.post('/orcamentos', headers=token, json=payload).status_code == 409
    item = client.get('/orcamentos', headers=token, params={'mes': mes}).json()[0]
    assert Decimal(str(item['gasto'])) == Decimal('12.50')
    assert Decimal(str(item['restante'])) == Decimal('-12.50')
    assert client.get('/orcamentos', headers=outro, params={'mes': mes}).json() == []
    assert client.delete(f'/orcamentos/{item_id}', headers=outro).status_code == 404
    alertas = client.get('/alertas', headers=token).json()
    assert len(alertas) == 3
    chave = next(a['chave'] for a in alertas if a['chave'].startswith('orcamento:'))
    assert client.put('/alertas/lido', headers=outro, params={'chave': chave}).status_code == 404
    assert client.put('/alertas/lido', headers=token, params={'chave': chave}).status_code == 200
    assert next(a for a in client.get('/alertas', headers=token).json() if a['chave'] == chave)['lido']
    assert client.put('/alertas/preferencias', headers=token, json={'orcamento': False, 'vencimento': False}).status_code == 200
    assert client.get('/alertas', headers=token).json() == []
    movimento.valor = Decimal('3.00')
    db.commit()
    item = client.get('/orcamentos', headers=token, params={'mes': mes}).json()[0]
    assert Decimal(str(item['gasto'])) == Decimal('3.00')
