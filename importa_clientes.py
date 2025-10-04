import sqlite3

DB_NAME = 'clientes.db'
CSV_NAME = 'clientes.csv'

# Cria tabela de clientes
conn = sqlite3.connect(DB_NAME)
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT UNIQUE NOT NULL,
    nome TEXT NOT NULL
)
''')
conn.commit()

try:
    with open(CSV_NAME, encoding='utf-8') as f:
        count = 0
        for linha in f:
            linha = linha.strip()
            if not linha:
                continue
            if ',' in linha:
                codigo, nome = linha.split(',', 1)
                codigo = codigo.strip()
                nome = nome.strip()
                c.execute('INSERT OR IGNORE INTO clientes (codigo, nome) VALUES (?, ?)', (codigo, nome))
                count += 1
    conn.commit()
    print(f'Importação concluída! {count} clientes importados.')
except Exception as e:
    print(f'Erro ao importar: {e}')
finally:
    conn.close()
