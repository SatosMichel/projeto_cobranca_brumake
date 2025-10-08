import sqlite3
from database import salvar_acordo

# Criar um acordo de teste
nome = 'TESTE PARCELAS'
valor_nominal = 1000.0
valor_juros = 1000.0
valor_entrada = 0.0
taxa_juros_mensal = 1.0
taxa_juros_diaria = round(taxa_juros_mensal/30, 5)
valor_total = valor_nominal - valor_entrada
parcelas = 3
valor_parcela = 0.0
from datetime import datetime

data_acordo = datetime.now().strftime('%Y-%m-%d')

acordo_id = salvar_acordo(nome, valor_nominal, valor_juros, valor_entrada, taxa_juros_mensal, taxa_juros_diaria, valor_total, parcelas, valor_parcela, data_acordo, codigo_devedor='9999', codigo_credor='1', forma_pagamento='Pix', agencia='', conta='')
print('acordo_id created:', acordo_id)

# Inserir parcelas
conn = sqlite3.connect('acordos.db')
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS parcelas (id INTEGER PRIMARY KEY AUTOINCREMENT, acordo_id INTEGER, numero INTEGER, data TEXT, valor REAL)')
for i in range(1, parcelas+1):
    c.execute('INSERT INTO parcelas (acordo_id, numero, data, valor) VALUES (?, ?, ?, ?)', (acordo_id, i, data_acordo, 100.0*i))
conn.commit()

# Ler parcelas inseridas
c.execute('SELECT id, acordo_id, numero, valor FROM parcelas WHERE acordo_id = ? ORDER BY numero', (acordo_id,))
rows = c.fetchall()
print('parcelas inserted:', len(rows))
for r in rows:
    print(r)

conn.close()
