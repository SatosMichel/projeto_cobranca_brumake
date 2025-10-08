import sqlite3, os
import datetime
import sys

BASE = os.path.dirname(__file__)
DB_PARTES = os.path.join(BASE, 'partes.db')
DB_ACORDOS = os.path.join(BASE, 'acordos.db')

codigo = '888'

# Ensure devedor exists
conn = sqlite3.connect(DB_PARTES)
c = conn.cursor()
try:
    c.execute('SELECT id, codigo_devedor, nome FROM devedores WHERE codigo_devedor = ?', (codigo,))
    row = c.fetchone()
    if row:
        print('Devedor existente:', row)
    else:
        nome = 'DEVEDOR TESTE 888'
        cnpj = '00000000000188'
        endereco = 'ENDERECO TESTE, Salvador'
        c.execute('INSERT INTO devedores (codigo_devedor, nome, cnpj, endereco) VALUES (?, ?, ?, ?)', (codigo, nome, cnpj, endereco))
        conn.commit()
        print('Devedor inserido com codigo', codigo)
except Exception as e:
    print('Erro ao verificar/inserir devedor:', e)
finally:
    conn.close()

# Insert acordo into acordos.db
conn = sqlite3.connect(DB_ACORDOS)
c = conn.cursor()
try:
    nome_acordo = 'ACORDO TESTE 888'
    valor_nominal = 1000.0
    valor_juros = 0.0
    valor_entrada = 0.0
    taxa_juros_mensal = 1.5
    taxa_juros_diaria = 0.05
    valor_total = 1000.0
    parcelas = 3
    valor_parcela = round(valor_total/parcelas,2)
    data_acordo = datetime.date.today().isoformat()
    codigo_devedor = codigo
    codigo_credor = None
    c.execute('INSERT INTO acordos (nome, valor_nominal, valor_juros, valor_entrada, taxa_juros_mensal, taxa_juros_diaria, valor_total, parcelas, valor_parcela, data_acordo, codigo_devedor, codigo_credor) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', (nome_acordo, valor_nominal, valor_juros, valor_entrada, taxa_juros_mensal, taxa_juros_diaria, valor_total, parcelas, valor_parcela, data_acordo, codigo_devedor, codigo_credor))
    conn.commit()
    last_id = c.lastrowid
    print('Acordo inserido id:', last_id)
except Exception as e:
    print('Erro ao inserir acordo:', e)
    conn.rollback()
    conn.close()
    sys.exit(1)
finally:
    conn.close()

# Generate PDF using existing script
try:
    import generate_pdf_for_review
    out = generate_pdf_for_review.generate()
    print('PDF gerado por script:', out)
except Exception as e:
    print('Erro ao gerar PDF:', e)
    raise
