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
    codigo_devedor TEXT,
    codigo_credor TEXT,
    forma_pagamento TEXT,
    agencia TEXT,
    conta TEXT,
    data_acordo TEXT NOT NULL
)
''')
conn.commit()
conn.close()

# Função para salvar acordo
def salvar_acordo(nome, valor_nominal, valor_juros, valor_entrada, taxa_juros_mensal, taxa_juros_diaria, valor_total, parcelas, valor_parcela, data_acordo, codigo_devedor=None, codigo_credor=None, forma_pagamento=None, agencia=None, conta=None, acordo_id=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Garantir que colunas existam (migração leve para bancos antigos)
    c.execute("PRAGMA table_info(acordos)")
    cols = [r[1] for r in c.fetchall()]
    if 'codigo_devedor' not in cols:
        try:
            c.execute('ALTER TABLE acordos ADD COLUMN codigo_devedor TEXT')
        except Exception:
            pass
    if 'codigo_credor' not in cols:
        try:
            c.execute('ALTER TABLE acordos ADD COLUMN codigo_credor TEXT')
        except Exception:
            pass
    if 'forma_pagamento' not in cols:
        try:
            c.execute('ALTER TABLE acordos ADD COLUMN forma_pagamento TEXT')
        except Exception:
            pass
    if 'agencia' not in cols:
        try:
            c.execute('ALTER TABLE acordos ADD COLUMN agencia TEXT')
        except Exception:
            pass
    if 'conta' not in cols:
        try:
            c.execute('ALTER TABLE acordos ADD COLUMN conta TEXT')
        except Exception:
            pass
    if acordo_id:
        # update existing
        c.execute('''UPDATE acordos SET nome=?, valor_nominal=?, valor_juros=?, valor_entrada=?, taxa_juros_mensal=?, taxa_juros_diaria=?, valor_total=?, parcelas=?, valor_parcela=?, codigo_devedor=?, codigo_credor=?, forma_pagamento=?, agencia=?, conta=?, data_acordo=? WHERE id=?''',
                  (nome, valor_nominal, valor_juros, valor_entrada, taxa_juros_mensal, taxa_juros_diaria, valor_total, parcelas, valor_parcela, codigo_devedor, codigo_credor, forma_pagamento, agencia, conta, data_acordo, acordo_id))
        conn.commit()
        conn.close()
        return acordo_id
    else:
        c.execute('''INSERT INTO acordos (nome, valor_nominal, valor_juros, valor_entrada, taxa_juros_mensal, taxa_juros_diaria, valor_total, parcelas, valor_parcela, codigo_devedor, codigo_credor, forma_pagamento, agencia, conta, data_acordo) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (nome, valor_nominal, valor_juros, valor_entrada, taxa_juros_mensal, taxa_juros_diaria, valor_total, parcelas, valor_parcela, codigo_devedor, codigo_credor, forma_pagamento, agencia, conta, data_acordo))
        inserted = c.lastrowid
        conn.commit()
        conn.close()
        return inserted
