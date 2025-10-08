import sqlite3, os
BASE = os.path.dirname(__file__)
DB_ACORDOS = os.path.join(BASE, 'acordos.db')
DB_PARTES = os.path.join(BASE, 'partes.db')

conn = sqlite3.connect(DB_ACORDOS)
c = conn.cursor()
print('Últimos 5 acordos (id, nome, data_acordo, codigo_devedor, codigo_credor):')
c.execute('SELECT id, nome, data_acordo, codigo_devedor, codigo_credor FROM acordos ORDER BY id DESC LIMIT 5')
rows = c.fetchall()
for row in rows:
    print('\nACORDO:', row)
    acordo_id = row[0]
    codigo_devedor = row[3]
    codigo_credor = row[4]
    # show parcelas count
    try:
        c.execute('SELECT COUNT(*) FROM parcelas WHERE acordo_id = ?', (acordo_id,))
        pc = c.fetchone()[0]
    except Exception:
        pc = 'ERR'
    print(' parcelas_count:', pc)

conn.close()

# now check partes db for devedor/credor
conn = sqlite3.connect(DB_PARTES)
c = conn.cursor()
for row in rows:
    codigo_devedor = row[3]
    codigo_credor = row[4]
    print('\nLookup for acordo id', row[0])
    if codigo_devedor:
        try:
            c.execute('SELECT nome, cnpj, endereco FROM devedores WHERE codigo_devedor = ?', (str(codigo_devedor),))
            d = c.fetchone()
            print(' devedor record:', d)
        except Exception as e:
            print(' devedor lookup error:', e)
    else:
        print(' devedor: (no codigo_devedor)')
    if codigo_credor:
        try:
            c.execute('SELECT nome, cnpj, endereco FROM credores WHERE codigo = ? OR rowid = ?', (str(codigo_credor), str(codigo_credor)))
            cr = c.fetchone()
            print(' credor record:', cr)
        except Exception as e:
            print(' credor lookup error:', e)
    else:
        print(' credor: (no codigo_credor)')

conn.close()
