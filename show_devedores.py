import sqlite3
import os
DB = os.path.join(os.path.dirname(__file__), 'partes.db')
if not os.path.exists(DB):
    print('Arquivo partes.db não encontrado em', DB)
    raise SystemExit(1)
# Tentar abrir em modo somente leitura (URI) para evitar locks se o DB estiver em uso
try:
    conn = sqlite3.connect(f'file:{DB}?mode=ro', uri=True, timeout=5)
except Exception:
    # fallback para modo normal se URI não for suportado
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
