import sqlite3
import os

DB_PATH = 'partes_demo.db'
CSV_PATH = 'credor.csv'

def importar_credor_csv():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    count = 0
    with open(CSV_PATH, encoding='utf-8') as f:
        for linha in f:
            linha = linha.strip()
            if not linha:
                continue
            if ';' in linha:
                partes = linha.split(';')
                if len(partes) >= 4:
                    codigo = partes[0].strip()
                    nome = partes[1].strip()
                    cnpj = partes[2].strip()
                    endereco = partes[3].strip()
                elif len(partes) == 3:
                    codigo = partes[0].strip()
                    nome = partes[1].strip()
                    cnpj = partes[2].strip()
                    endereco = ''
                else:
                    continue
                c.execute('INSERT INTO credores (codigo, nome, cnpj, endereco) VALUES (?, ?, ?, ?)', (codigo, nome, cnpj, endereco))
                count += 1
    conn.commit()
    conn.close()
    print(f'Importação de credores concluída! {count} registros.')

if __name__ == '__main__':
    importar_credor_csv()
