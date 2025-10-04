import sqlite3

DB_PATH = 'partes_demo.db'
CSV_PATH = 'credor.csv'

def importar_credor_csv():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS credores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        cnpj TEXT,
        endereco TEXT
    )''')
    conn.commit()
    with open(CSV_PATH, encoding='utf-8') as f:
        for linha in f:
            linha = linha.strip()
            if not linha:
                continue
            if ';' in linha:
                partes = linha.split(';')
                if len(partes) >= 3:
                    nome = partes[0].strip()
                    cnpj = partes[1].strip()
                    endereco = partes[2].strip()
                    c.execute('INSERT INTO credores (nome, cnpj, endereco) VALUES (?, ?, ?)', (nome, cnpj, endereco))
    conn.commit()
    conn.close()
    print('Importação de credores concluída!')

if __name__ == '__main__':
    importar_credor_csv()
