import sqlite3

DB_NAME = 'partes.db'
CSV_NAME = 'devedor.csv'

conn = sqlite3.connect(DB_NAME)
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS devedores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_devedor TEXT NOT NULL,
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
                codigo_devedor, nome, cnpj, endereco = linha.split(';', 3)
                codigo_devedor = codigo_devedor.strip()
                nome = nome.strip()
                cnpj = cnpj.strip()
                endereco = endereco.strip()
                c.execute('INSERT INTO devedores (codigo_devedor, nome, cnpj, endereco) VALUES (?, ?, ?, ?)', (codigo_devedor, nome, cnpj, endereco))
                count += 1
    conn.commit()
    print(f'Importação de devedores concluída! {count} registros.')
except Exception as e:
    print(f'Erro ao importar devedores: {e}')
finally:
    conn.close()

