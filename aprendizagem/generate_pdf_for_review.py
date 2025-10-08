import sqlite3
import os
from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa
from utils_format import formatar_cnpj
from utils_extenso import valor_por_extenso, numero_por_extenso, percentual_por_extenso

DB_ACORDOS = 'acordos.db'
DB_PARTES = 'partes.db'
TEMPLATE = 'termo_template.html'

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


def _normalize_parte(row):
    # reutiliza a lógica de normalização do credor para devedores/credores
    return _normalize_credor(row)


def generate():
    # get last acordo
    conn = sqlite3.connect(DB_ACORDOS)
    c = conn.cursor()
    c.execute('SELECT id, nome, valor_nominal, valor_juros, valor_entrada, taxa_juros_mensal, taxa_juros_diaria, valor_total, parcelas, valor_parcela, data_acordo, codigo_devedor, codigo_credor FROM acordos ORDER BY id DESC LIMIT 1')
    row = c.fetchone()
    conn.close()
    if not row:
        print('Nenhum acordo encontrado em', DB_ACORDOS)
        return None
    acordo_id = row[0]
    # get partes
    codigo_devedor = row[11] if len(row) > 11 else None
    codigo_credor = row[12] if len(row) > 12 else None
    conn = sqlite3.connect(DB_PARTES)
    c = conn.cursor()
    devedor = None
    credor = None
    if codigo_devedor:
        try:
            c.execute('SELECT nome, cnpj, endereco FROM devedores WHERE codigo_devedor = ?', (str(codigo_devedor),))
            devedor = c.fetchone()
        except Exception:
            devedor = None
    def _fetch_credor_by_code(cursor, code):
        try:
            cursor.execute("PRAGMA table_info(credores)")
            cols = [r[1] for r in cursor.fetchall()]
            if 'codigo' in cols:
                cursor.execute('SELECT nome, cnpj, endereco FROM credores WHERE codigo = ? LIMIT 1', (str(code),))
                return cursor.fetchone()
            if 'codigo_credor' in cols:
                cursor.execute('SELECT nome, cnpj, endereco FROM credores WHERE codigo_credor = ? LIMIT 1', (str(code),))
                return cursor.fetchone()
            try:
                cursor.execute('SELECT nome, cnpj, endereco FROM credores WHERE rowid = ? LIMIT 1', (str(code),))
                return cursor.fetchone()
            except Exception:
                pass
            cursor.execute('SELECT nome, cnpj, endereco FROM credores WHERE nome LIKE ? LIMIT 1', (f'%{code}%',))
            return cursor.fetchone()
        except Exception:
            return None

    if codigo_credor:
        credor = _fetch_credor_by_code(c, codigo_credor)

    if not credor:
        try:
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='credores'")
            if c.fetchone():
                c.execute('SELECT nome, cnpj, endereco FROM credores LIMIT 1')
                credor = c.fetchone()
        except Exception:
            credor = None
    conn.close()

    nome_credor_raw, cnpj_credor_raw, endereco_credor_raw = _normalize_credor(credor)
    try:
        cnpj_credor_fmt = formatar_cnpj(cnpj_credor_raw) if cnpj_credor_raw else ''
    except Exception:
        cnpj_credor_fmt = cnpj_credor_raw or ''

    # Normalizar devedor (caso import mal formatada tenha deslocado campos)
    if devedor:
        nome_devedor_raw, cnpj_devedor_raw, endereco_devedor_raw = _normalize_parte(devedor)
        nome_devedor = nome_devedor_raw or (devedor[0] if devedor else row[1])
        try:
            cnpj_devedor = formatar_cnpj(cnpj_devedor_raw) if cnpj_devedor_raw else ''
        except Exception:
            cnpj_devedor = cnpj_devedor_raw or ''
        endereco_devedor = endereco_devedor_raw or (devedor[2] if len(devedor) > 2 else '')
    else:
        nome_devedor = row[1]
        cnpj_devedor = ''
        endereco_devedor = ''

    # parcelas
    conn = sqlite3.connect(DB_ACORDOS)
    c = conn.cursor()
    c.execute('SELECT numero, valor, data FROM parcelas WHERE acordo_id = ? ORDER BY numero', (acordo_id,))
    parcelas_db = c.fetchall()
    conn.close()
    parcelas_list = []
    parcelas_total_numeric = 0.0
    for p in parcelas_db:
        numero, valor, data_venc = p
        try:
            parcelas_total_numeric += float(valor)
        except Exception:
            pass
        parcelas_list.append({
            'numero': numero,
            'valor': f'{valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'),
            'valor_por_extenso': valor_por_extenso(valor),
            'data_vencimento': data_venc
        })

    # Se não houver parcelas na tabela, gerar a lista com base nos campos do acordo
    if not parcelas_list:
        try:
            from datetime import datetime, timedelta
            parcelas_qtd = int(row[8]) if row[8] else 0
            taxa_mensal = float(row[5]) if row[5] else 0.0
            valor_base = float(row[3]) - float(row[4]) if row[3] is not None and row[4] is not None else float(row[7]) if row[7] is not None else 0.0
            parcela_fixa = valor_base / parcelas_qtd if parcelas_qtd > 0 else 0.0
            data_inicio = None
            if row[10]:
                try:
                    data_inicio = datetime.strptime(row[10], '%Y-%m-%d')
                except Exception:
                    data_inicio = None
            for i in range(1, parcelas_qtd + 1):
                juros_parcela = parcela_fixa * (taxa_mensal / 100) * i
                valor_parcela = round(parcela_fixa + juros_parcela, 2)
                if data_inicio:
                    venc = (data_inicio + timedelta(days=30 * i)).strftime('%d/%m/%Y')
                else:
                    venc = ''
                try:
                    parcelas_total_numeric += float(valor_parcela)
                except Exception:
                    pass
                parcelas_list.append({
                    'numero': i,
                    'valor': f'{valor_parcela:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'),
                    'valor_por_extenso': valor_por_extenso(valor_parcela),
                    'data_vencimento': venc
                })
        except Exception:
            pass

    dados_termo = {
        'nome_credor': nome_credor_raw or (credor[0] if credor else ''),
        'cnpj_credor': cnpj_credor_fmt or (formatar_cnpj(credor[1]) if credor and len(credor)>1 else ''),
        'endereco_credor': endereco_credor_raw or (credor[2] if credor and len(credor)>2 else ''),
        'nome_devedor': nome_devedor,
        'cnpj_devedor': cnpj_devedor,
        'endereco_devedor': endereco_devedor,
        'valor_total_divida': f'{row[3]:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'),
    'valor_total_por_extenso': valor_por_extenso(row[3]),
        'origem_divida': 'Acordo comercial',
        'data_origem_divida': row[10],
        'parcelas_quantidade': row[8],
        'parcelas': parcelas_list,
    'parcelas_total': f'{parcelas_total_numeric:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'),
    'parcelas_total_por_extenso': valor_por_extenso(parcelas_total_numeric),
    'forma_pagamento': 'Pix',
    'percentual_multa': '2%',
    'percentual_multa_por_extenso': percentual_por_extenso(2),
    'percentual_juros': f'{row[5]:.2f}% ao mês' if row[5] else '',
    'percentual_juros_por_extenso': percentual_por_extenso(row[5]) if row[5] else '',
        'dias_antecipacao': '30',
        'dia': row[10].split('-')[2] if row[10] and '-' in row[10] else '',
        'mes': row[10].split('-')[1] if row[10] and '-' in row[10] else '',
        'ano': row[10].split('-')[0] if row[10] and '-' in row[10] else '',
    }

    env = Environment(loader=FileSystemLoader(os.path.dirname(TEMPLATE) or '.'))
    template = env.get_template(TEMPLATE)
    html_renderizado = template.render(dados_termo)

    output_filename = f'Instrumento_Acordo_{acordo_id}_review.pdf'
    with open(output_filename, 'w+b') as result_file:
        pisa_status = pisa.CreatePDF(html_renderizado, dest=result_file)
    if pisa_status.err:
        print('Erro ao gerar PDF')
        return None
    print('PDF gerado:', output_filename)
    return output_filename

if __name__ == '__main__':
    generate()
