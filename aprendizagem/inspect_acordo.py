import sqlite3, os, sys
BASE = os.path.dirname(__file__)
DB_ACORDOS = os.path.join(BASE, 'acordos.db')
DB_PARTES = os.path.join(BASE, 'partes.db')
acordo_id = 4

print('Abrindo', DB_ACORDOS)
conn = sqlite3.connect(DB_ACORDOS)
c = conn.cursor()
c.execute('SELECT id, nome, valor_nominal, valor_juros, valor_entrada, taxa_juros_mensal, taxa_juros_diaria, valor_total, parcelas, valor_parcela, data_acordo, codigo_devedor, codigo_credor FROM acordos WHERE id = ?', (acordo_id,))
row = c.fetchone()
print('Acordo row:', row)
conn.close()

print('\nAbrindo', DB_PARTES)
conn = sqlite3.connect(DB_PARTES)
c = conn.cursor()
if row:
    codigo_devedor = row[11]
    codigo_credor = row[12]
    print('codigo_devedor:', codigo_devedor, 'codigo_credor:', codigo_credor)
    try:
        c.execute('SELECT nome, cnpj, endereco FROM devedores WHERE codigo_devedor = ?', (str(codigo_devedor),))
        devedor = c.fetchone()
    except Exception as e:
        devedor = None
        print('Erro ao consultar devedores:', e)
    try:
        c.execute('SELECT nome, cnpj, endereco FROM credores WHERE codigo = ? OR rowid = ?', (str(codigo_credor), str(codigo_credor)))
        credor = c.fetchone()
    except Exception as e:
        credor = None
        print('Erro ao consultar credores:', e)
    print('Devedor:', devedor)
    print('Credor:', credor)
else:
    print('Acordo não encontrado')
conn.close()
