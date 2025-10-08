import sqlite3, os
DB = r'C:\Users\supervisor\OneDrive - BRUMAKE COMERCIAL E SERVICOS LTDA\Documentos\Projeto_AcordoCobranÇA\partes.db.copy'
conn = sqlite3.connect(DB)
c = conn.cursor()
try:
    c.execute("SELECT codigo_devedor, nome, cnpj, endereco FROM devedores LIMIT 50")
    rows = c.fetchall()
    if not rows:
        print('Nenhum registro encontrado na tabela devedores.')
    else:
        print(f"Mostrando {len(rows)} registros (máx 50):\n")
        for r in rows:
            codigo, nome, cnpj, endereco = r
            print(f'codigo_devedor: {codigo} | nome: {nome} | cnpj: {cnpj} | endereco: {endereco}')
except Exception as e:
    print('Erro ao consultar devedores:', e)
finally:
    conn.close()
