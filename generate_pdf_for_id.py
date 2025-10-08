import sqlite3, os, sys
from jinja2 import Environment, FileSystemLoader
from utils_format import formatar_cnpj
from utils_extenso import valor_por_extenso, percentual_por_extenso
from xhtml2pdf import pisa

DB_ACORDOS = 'acordos.db'
DB_PARTES = 'partes.db'
TEMPLATE = 'termo_template.html'

if len(sys.argv) > 1:
    acordo_id = int(sys.argv[1])
else:
    # pega último
    conn = sqlite3.connect(DB_ACORDOS)
    c = conn.cursor()
    c.execute('SELECT id FROM acordos ORDER BY id DESC LIMIT 1')
    r = c.fetchone()
    conn.close()
    if not r:
        print('Nenhum acordo no DB')
        sys.exit(1)
    acordo_id = r[0]

print('Gerando PDF para acordo id', acordo_id)

# ler acordo
conn = sqlite3.connect(DB_ACORDOS)
c = conn.cursor()
c.execute('SELECT id, nome, valor_nominal, valor_juros, valor_entrada, taxa_juros_mensal, taxa_juros_diaria, valor_total, parcelas, valor_parcela, data_acordo, codigo_devedor, codigo_credor FROM acordos WHERE id = ?', (acordo_id,))
row = c.fetchone()
conn.close()
if not row:
    print('Acordo não encontrado')
    sys.exit(1)

codigo_devedor = row[11] if len(row) > 11 else None
codigo_credor = row[12] if len(row) > 12 else None

conn = sqlite3.connect(DB_PARTES)
c = conn.cursor()
# fetch devedor
devedor = None
if codigo_devedor:
    try:
        c.execute('SELECT nome, cnpj, endereco FROM devedores WHERE codigo_devedor = ?', (str(codigo_devedor),))
        devedor = c.fetchone()
    except Exception as e:
        print('Erro fetch devedor:', e)
# fetch credor com pragma
credor = None
try:
    c.execute("PRAGMA table_info(credores)")
    cols = [r[1] for r in c.fetchall()]
    if codigo_credor:
        if 'codigo' in cols:
            c.execute('SELECT nome, cnpj, endereco FROM credores WHERE codigo = ? LIMIT 1', (str(codigo_credor),))
            credor = c.fetchone()
        elif 'codigo_credor' in cols:
            c.execute('SELECT nome, cnpj, endereco FROM credores WHERE codigo_credor = ? LIMIT 1', (str(codigo_credor),))
            credor = c.fetchone()
        else:
            try:
                c.execute('SELECT nome, cnpj, endereco FROM credores WHERE rowid = ? LIMIT 1', (str(codigo_credor),))
                credor = c.fetchone()
            except Exception:
                pass
    if not credor:
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='credores'")
        if c.fetchone():
            c.execute('SELECT nome, cnpj, endereco FROM credores LIMIT 1')
            credor = c.fetchone()
except Exception as e:
    print('Erro fetch credor:', e)
conn.close()

print('\nValores lidos:')
print('Acordo row nome:', row[1])
print('codigo_devedor:', codigo_devedor)
print('devedor tuple:', devedor)
print('codigo_credor:', codigo_credor)
print('credor tuple:', credor)

# normalizar e preparar dados como no gerador
def _normalize_credor(row):
    if not row:
        return ('', '', '')
    nome_field = row[0] if len(row) > 0 else ''
    cnpj_field = row[1] if len(row) > 1 else ''
    endereco_field = row[2] if len(row) > 2 else ''
    nome = str(nome_field or '').strip().strip('"').rstrip(';')
    cnpj = str(cnpj_field or '').strip().strip('"')
    endereco = str(endereco_field or '').strip().strip('"')
    if nome.isdigit() and cnpj and not endereco:
        if ';' in endereco_field:
            parts = endereco_field.split(';')
            real_cnpj = parts[0]
            real_end = ';'.join(parts[1:]).strip()
            real_name = cnpj
            return (real_name.strip().rstrip(';'), real_cnpj.strip(), real_end.strip())
    if ';' in cnpj and not endereco:
        parts = cnpj.split(';')
        real_cnpj = parts[0]
        real_end = ';'.join(parts[1:]).strip()
        return (nome, real_cnpj.strip(), real_end)
    if ';' in endereco:
        parts = endereco.split(';')
        if parts[0].strip().replace('.', '').replace('/', '').replace('-', '').isdigit():
            real_cnpj = parts[0]
            real_end = ';'.join(parts[1:]).strip()
            return (nome, real_cnpj.strip(), real_end)
    return (nome, cnpj, endereco)

# normalize devedor
if devedor:
    nome_devedor_raw, cnpj_devedor_raw, endereco_devedor_raw = _normalize_credor(devedor)
else:
    nome_devedor_raw, cnpj_devedor_raw, endereco_devedor_raw = ('', '', '')

print('\nNormalizados:')
print('nome_devedor_raw:', nome_devedor_raw)
print('cnpj_devedor_raw:', cnpj_devedor_raw)
print('endereco_devedor_raw:', endereco_devedor_raw)

# montar context e gerar PDF
dados = {
    'nome_credor': (credor[0] if credor else ''),
    'cnpj_credor': (formatar_cnpj(credor[1]) if credor and len(credor)>1 else ''),
    'endereco_credor': (credor[2] if credor and len(credor)>2 else ''),
    'nome_devedor': nome_devedor_raw or row[1],
    'cnpj_devedor': (formatar_cnpj(cnpj_devedor_raw) if cnpj_devedor_raw else ''),
    'endereco_devedor': endereco_devedor_raw or '',
    'valor_total_divida': f'{row[2]:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'),
    'valor_total_por_extenso': valor_por_extenso(row[2]) if row[2] else '',
    'parcelas': [],
    'parcelas_total': '0,00',
}

env = Environment(loader=FileSystemLoader('.'))
template = env.get_template(TEMPLATE)
html = template.render(dados)

out = f'Instrumento_Acordo_{acordo_id}_debug.pdf'
with open(out, 'w+b') as f:
    pisa_status = pisa.CreatePDF(html, dest=f)
if pisa_status.err:
    print('Erro ao gerar PDF')
else:
    print('\nPDF gerado:', out)
