from app import app
import sqlite3
from datetime import datetime

# Preparar DB mínimo para as rotas usadas no teste (evita erros de tabela ausente)
conn = sqlite3.connect('acordos.db')
cur = conn.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS clientes (id INTEGER PRIMARY KEY AUTOINCREMENT, codigo TEXT, nome TEXT)')
# insere um cliente de teste se não existir
cur.execute("SELECT COUNT(*) FROM clientes WHERE codigo = '1'")
if cur.fetchone()[0] == 0:
    cur.execute("INSERT INTO clientes (codigo, nome) VALUES (?, ?)", ('1', 'CLIENTE TESTE'))
conn.commit()
conn.close()

with app.test_client() as client:
    # Autentica como sup
    resp = client.post('/login', data={'usuario':'sup','senha':'Miguel2@'}, follow_redirects=True)
    print('login status_code:', resp.status_code)

    # Define sessão com cliente e credor (bypass validação de DB para fluidez do teste)
    with client.session_transaction() as sess:
        sess['usuario_autenticado'] = 'sup'
        sess['codigo'] = '1'
        sess['nome'] = 'CLIENTE TESTE'
        sess['codigo_credor'] = '1'

    # Valor nominal
    resp = client.post('/valor_nominal', data={'valor_nominal': 'R$1.000,00'}, follow_redirects=True)
    print('valor_nominal ->', resp.status_code)

    # Valor juros
    resp = client.post('/valor_juros', data={'valor_juros': 'R$1.000,00'}, follow_redirects=True)
    print('valor_juros ->', resp.status_code)

    # Entrada (sem entrada)
    resp = client.post('/entrada', data={'entrada': 'nao'}, follow_redirects=True)
    print('entrada ->', resp.status_code)

    # Parcelas e juros
    datas = {
        'data_parcela_1': (datetime.now().strftime('%Y-%m-%d')),
        'data_parcela_2': (datetime.now().strftime('%Y-%m-%d')),
        'data_parcela_3': (datetime.now().strftime('%Y-%m-%d')),
    }
    form = {'parcelas': '3', 'taxa_juros': '1.0'}
    form.update(datas)
    resp = client.post('/parcelas_juros', data=form, follow_redirects=True)
    print('parcelas_juros ->', resp.status_code)

    # Resumo: enviar para salvar o acordo
    resp = client.post('/resumo', data={}, follow_redirects=True)
    print('resumo POST ->', resp.status_code)

    # Obter acordo_id da sessão
    with client.session_transaction() as sess:
        acordo_id = sess.get('acordo_id')
    print('session acordo_id:', acordo_id)

    # Consultar DB para verificar parcelas vinculadas
    conn = sqlite3.connect('acordos.db')
    c = conn.cursor()
    if acordo_id:
        c.execute('SELECT id, nome, codigo_devedor, codigo_credor, data_acordo FROM acordos WHERE id = ?', (acordo_id,))
        a = c.fetchone()
        print('acordo row:', a)

        c.execute('SELECT id, acordo_id, numero, valor, data FROM parcelas WHERE acordo_id = ? ORDER BY numero', (acordo_id,))
        rows = c.fetchall()
        print('parcelas found:', len(rows))
        for r in rows:
            print(r)
    else:
        print('nenhum acordo_id encontrado na sessão; listando últimos acordos...')
        c.execute('SELECT id, nome, codigo_devedor, codigo_credor, data_acordo FROM acordos ORDER BY id DESC LIMIT 3')
        for a in c.fetchall():
            print('acordo sample:', a)
    conn.close()

print('Teste de fluxo completo finalizado')
