import sqlite3, os, datetime, sys
BASE = os.path.dirname(__file__)
DB_ACORDOS = os.path.join(BASE, 'acordos.db')
DB_PARTES = os.path.join(BASE, 'partes.db')

# Insert acordo using existing devedor 1 and default credor
codigo_devedor = '1'
codigo_credor = None

conn = sqlite3.connect(DB_ACORDOS)
c = conn.cursor()
try:
    nome_acordo = 'ACORDO TESTE PADRAO'
    valor_nominal = 1500.0
    valor_juros = 0.0
    valor_entrada = 0.0
    taxa_juros_mensal = 1.2
    taxa_juros_diaria = 0.04
    valor_total = 1500.0
    parcelas = 4
    valor_parcela = round(valor_total/parcelas,2)
    data_acordo = datetime.date.today().isoformat()
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

# Generate PDF (this will pick the last acordo)
try:
    import generate_pdf_for_review
    out = generate_pdf_for_review.generate()
    print('PDF gerado:', out)
except Exception as e:
    print('Erro ao gerar PDF:', e)
    raise
