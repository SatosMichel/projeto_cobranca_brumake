import sqlite3
DB='partes_demo.db'
conn=sqlite3.connect(DB)
c=conn.cursor()
# Criar tabela temporária com deduplicação por codigo (ignorando codigo nulo/empty)
c.execute('CREATE TABLE IF NOT EXISTS credores_dedup AS SELECT MIN(ROWID) as keep_id, codigo, nome, cnpj, endereco FROM credores WHERE codigo IS NOT NULL AND codigo != "" GROUP BY codigo')
rows=c.execute('SELECT codigo, nome FROM credores_dedup').fetchall()
print('Registros deduplicados (count):', len(rows))
# Limpar tabela original e inserir deduplicados
c.execute('DELETE FROM credores')
for codigo,nome in rows:
    r=c.execute('SELECT cnpj, endereco FROM credores_dedup WHERE codigo=?', (codigo,)).fetchone()
    cnpj=r[0] if r else ''
    endereco=r[1] if r else ''
    c.execute('INSERT INTO credores (codigo,nome,cnpj,endereco) VALUES (?,?,?,?)', (codigo,nome,cnpj,endereco))
conn.commit()
# Remover tabela temporaria
c.execute('DROP TABLE IF EXISTS credores_dedup')
conn.commit()
# Mostrar resultado final
print(c.execute('SELECT codigo,nome FROM credores').fetchall())
conn.close()
