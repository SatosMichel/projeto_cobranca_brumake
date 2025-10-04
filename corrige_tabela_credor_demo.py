import sqlite3

DB_PATH = 'partes_demo.db'

def corrige_tabela():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Adiciona o campo codigo se não existir
    c.execute("PRAGMA table_info(credores)")
    colunas = [col[1] for col in c.fetchall()]
    if 'codigo' not in colunas:
        c.execute("ALTER TABLE credores ADD COLUMN codigo TEXT")
        print('Campo codigo adicionado!')
    else:
        print('Campo codigo já existe.')
    conn.commit()
    conn.close()

if __name__ == '__main__':
    corrige_tabela()
