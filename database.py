# database.py
import sqlite3

DB_NAME = 'acordos.db'

# Criação da tabela de acordos
conn = sqlite3.connect(DB_NAME)
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS acordos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    valor_nominal REAL NOT NULL,
    valor_juros REAL NOT NULL,
    valor_entrada REAL NOT NULL,
    taxa_juros_mensal REAL NOT NULL,
    taxa_juros_diaria REAL NOT NULL,
    valor_total REAL NOT NULL,
    parcelas INTEGER NOT NULL,
    valor_parcela REAL NOT NULL,
    data_acordo TEXT NOT NULL
)
''')
conn.commit()
conn.close()

# Função para salvar acordo
def salvar_acordo(nome, valor_nominal, valor_juros, valor_entrada, taxa_juros_mensal, taxa_juros_diaria, valor_total, parcelas, valor_parcela, data_acordo):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''INSERT INTO acordos (nome, valor_nominal, valor_juros, valor_entrada, taxa_juros_mensal, taxa_juros_diaria, valor_total, parcelas, valor_parcela, data_acordo) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (nome, valor_nominal, valor_juros, valor_entrada, taxa_juros_mensal, taxa_juros_diaria, valor_total, parcelas, valor_parcela, data_acordo))
    conn.commit()
    conn.close()
