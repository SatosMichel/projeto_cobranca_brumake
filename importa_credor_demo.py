import sqlite3
import csv

# Caminho do banco de credores demo
DB_PATH = 'partes_demo.db'
CSV_PATH = 'credor_demo.csv'

def criar_banco():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS credores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        cnpj TEXT,
        endereco TEXT
    )''')
    conn.commit()
    conn.close()

def importar_credor_csv():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    with open(CSV_PATH, encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=';')
        for row in reader:
            if len(row) < 3:
                continue
            nome = row[1].strip()
            cnpj = row[2].strip()
            endereco = row[3].strip() if len(row) > 3 else ''
            c.execute('INSERT INTO credores (nome, cnpj, endereco) VALUES (?, ?, ?)', (nome, cnpj, endereco))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    criar_banco()
    importar_credor_csv()
    print('Banco partes_demo.db criado e credores importados com sucesso!')
