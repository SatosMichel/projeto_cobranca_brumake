import sqlite3

DB_NAME = 'partes.db'
CSV_NAME = 'credor.csv'

conn = sqlite3.connect(DB_NAME)
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS credores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    cnpj TEXT NOT NULL,
    endereco TEXT NOT NULL
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
            if ';' in linha:
                nome, cnpj, endereco = linha.split(';', 2)
                nome = nome.strip()
                cnpj = cnpj.strip()
                endereco = endereco.strip()
                c.execute('INSERT INTO credores (nome, cnpj, endereco) VALUES (?, ?, ?)', (nome, cnpj, endereco))
                count += 1
    conn.commit()
    print(f'Importação de credores concluída! {count} registros.')
except Exception as e:
    print(f'Erro ao importar credores: {e}')
finally:
    conn.close()
