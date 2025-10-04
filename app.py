from flask import Flask, render_template, request, redirect, session, url_for, send_file
from functools import wraps
from datetime import datetime
import sqlite3
import os
from xhtml2pdf import pisa
from jinja2 import Environment, FileSystemLoader
from utils_format import formatar_cnpj
from database import salvar_acordo
from usuarios import solicitar_acesso, listar_usuarios, aprovar_usuario, bloquear_usuario, alternar_ativo

app = Flask(__name__)
# Use variável de ambiente para a secret key em vez de hardcode
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'supersecretkey')  # Pode configurar FLASK_SECRET_KEY no ambiente

# Função de proteção das rotas
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('usuario_autenticado'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# Rota para listar todos os credores (usada pelo select no frontend)
@app.route('/listar_credor')
@login_required
def listar_credor():
    conn = sqlite3.connect('partes_demo.db')
    c = conn.cursor()
    c.execute('SELECT codigo, nome FROM credores ORDER BY nome')
    resultados = [{'codigo': row[0], 'nome': row[1]} for row in c.fetchall()]
    conn.close()
    return {'credor': resultados}


# Rota para autocomplete de credor (mantida para compatibilidade)
@app.route('/buscar_credor')
@login_required
def buscar_credor():
    termo = request.args.get('q', '').strip()
    conn = sqlite3.connect('partes_demo.db')
    c = conn.cursor()
    c.execute('SELECT codigo, nome FROM credores WHERE nome LIKE ? OR codigo LIKE ? LIMIT 10', (f'%{termo}%', f'%{termo}%'))
    resultados = [{'codigo': row[0], 'nome': row[1]} for row in c.fetchall()]
    conn.close()
    return {'credor': resultados}

@app.route('/login', methods=['GET', 'POST'])
def login():
    erro = None
    if request.method == 'POST':
        usuario = request.form['usuario']
        senha = request.form['senha']
        if usuario.lower() == 'sup' and senha == 'Miguel2@':
            session['usuario_autenticado'] = usuario
            return redirect(url_for('inicio'))
        # Verifica no banco se usuário está ativo
        import sqlite3
        conn = sqlite3.connect('usuarios.db')
        c = conn.cursor()
        c.execute('SELECT senha, status, ativo FROM usuarios WHERE usuario = ?', (usuario.lower(),))
        row = c.fetchone()
        conn.close()
        if row:
            senha_db, status, ativo = row
            if ativo != 'sim':
                erro = 'Contate o desenvolvedor do programa.'
            elif status == 'aprovado' and senha_db == senha:
                session['usuario_autenticado'] = usuario
                return redirect(url_for('cliente'))
            else:
                erro = 'Usuário ou senha inválidos.'
        else:
            erro = 'Usuário ou senha inválidos.'
    return render_template('login.html', erro=erro)

@app.route('/logout')
def logout():
    session.pop('usuario_autenticado', None)
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
@login_required
def root():
    if not session.get('usuario_autenticado'):
        return redirect(url_for('login'))
    return redirect(url_for('cliente'))

# Etapa 1: Seleção do cliente
@app.route('/cliente', methods=['GET', 'POST'])
@login_required
def cliente():
    if request.method == 'POST':
        import sqlite3
        codigo_cliente = request.form['codigo']
        nome_cliente = request.form['nome']
        codigo_credor = request.form.get('busca_credor')
        # Validar cliente
        conn = sqlite3.connect('partes_demo.db')
        c = conn.cursor()
        c.execute('SELECT nome FROM devedores WHERE codigo_devedor = ?', (codigo_cliente,))
        cliente_row = c.fetchone()
        # Validar credor
        c.execute('SELECT nome FROM credores WHERE id = ?', (codigo_credor,))
        credor_row = c.fetchone()
        conn.close()
        if not cliente_row or not credor_row:
            return render_template('cliente.html', erro='Selecione um cliente e credor válidos!')
        session['codigo'] = codigo_cliente
        session['nome'] = nome_cliente
        session['codigo_credor'] = codigo_credor
        return redirect(url_for('valor_nominal'))
    return render_template('cliente.html')

# Etapa 2: Valor nominal da dívida
@app.route('/valor_nominal', methods=['GET', 'POST'])
@login_required
def valor_nominal():
    if request.method == 'POST':
        valor_str = request.form['valor_nominal']
        # Remove máscara e converte para float
        valor_str = valor_str.replace('R$', '').replace('.', '').replace(',', '.').strip()
        valor_float = float(valor_str)
        session['valor_nominal'] = valor_float
        return redirect(url_for('valor_juros'))
    return render_template('valor_nominal.html')

# Etapa 3: Valor da dívida com juros
@app.route('/valor_juros', methods=['GET', 'POST'])
@login_required
def valor_juros():
    if request.method == 'POST':
        valor_juros = request.form['valor_juros']
        # Remove máscara e converte para float
        valor_juros = valor_juros.replace('R$', '').replace('.', '').replace(',', '.').strip()
        try:
            valor_juros_float = float(valor_juros)
        except ValueError:
            return render_template('valor_juros.html', erro='Valor inválido!')
        session['valor_juros'] = valor_juros_float
        return redirect(url_for('entrada'))
    return render_template('valor_juros.html')

# Etapa 4: Entrada
@app.route('/entrada', methods=['GET', 'POST'])
@login_required
def entrada():
    if request.method == 'POST':
        entrada = request.form['entrada']
        session['entrada'] = entrada
        valor_entrada = request.form.get('valor_entrada', '').strip()
        if entrada == 'sim' and valor_entrada:
            valor_entrada = valor_entrada.replace('R$', '').replace('.', '').replace(',', '.').strip()
            try:
                valor_entrada_float = float(valor_entrada)
            except ValueError:
                return render_template('entrada.html', erro='Valor da entrada inválido!')
            session['valor_entrada'] = valor_entrada_float
        else:
            session['valor_entrada'] = 0.0
        return redirect(url_for('parcelas_juros'))
    return render_template('entrada.html')

# Etapa 5: Parcelas e taxa de juros
@app.route('/parcelas_juros', methods=['GET', 'POST'])
@login_required
def parcelas_juros():
    if request.method == 'POST':
        import sqlite3
        parcelas = int(request.form['parcelas'])
        taxa_juros_mensal = float(request.form['taxa_juros'])
        taxa_juros_diaria = round(taxa_juros_mensal / 30, 5)
        datas_parcelas = []
        for i in range(1, parcelas + 1):
            datas_parcelas.append(request.form.get(f'data_parcela_{i}', ''))
        session['parcelas'] = parcelas
        session['taxa_juros_mensal'] = taxa_juros_mensal
        session['taxa_juros_diaria'] = taxa_juros_diaria
        session['datas_parcelas'] = datas_parcelas

        # Salvar parcelas no banco acordos.db
        conn = sqlite3.connect('acordos.db')
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS parcelas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            acordo_id INTEGER,
            numero INTEGER,
            data TEXT,
            valor REAL
        )''')
        acordo_id = session.get('acordo_id')  # Certifique-se de salvar o acordo_id na sessão antes
        # Exemplo: session['acordo_id'] = id do acordo criado
        # Calcular valor de cada parcela
        valor_base = session.get('valor_juros', 0) - session.get('valor_entrada', 0)
        parcela_fixa = valor_base / parcelas if parcelas > 0 else 0
        for i, data in enumerate(datas_parcelas, start=1):
            juros_parcela = parcela_fixa * (taxa_juros_mensal / 100) * i
            valor_parcela = parcela_fixa + juros_parcela
            valor_parcela = round(valor_parcela, 2)
            cursor.execute('INSERT INTO parcelas (acordo_id, numero, data, valor) VALUES (?, ?, ?, ?)',
                           (acordo_id, i, data, valor_parcela))
        conn.commit()
        conn.close()

        return redirect(url_for('resumo'))
    return render_template('parcelas_juros.html')

# Etapa 6: Resumo e cálculo final
@app.route('/resumo', methods=['GET', 'POST'])
@login_required
def resumo():
    # Recupera dados da sessão
    codigo = session.get('codigo')
    nome = session.get('nome')
    valor_nominal = session.get('valor_nominal')
    valor_juros = session.get('valor_juros')
    entrada = session.get('entrada')
    valor_entrada = session.get('valor_entrada', 0.0)
    parcelas = session.get('parcelas')
    taxa_juros_mensal = session.get('taxa_juros_mensal', 0.0)
    taxa_juros_diaria = session.get('taxa_juros_diaria', 0.0)
    datas_parcelas = session.get('datas_parcelas', [])

    # Cálculo do valor base para acordo
    valor_base = valor_juros - valor_entrada if entrada == 'sim' else valor_juros
    valor_pos_entrada = valor_base

    # Cálculo das parcelas considerando juros mensal
    lista_parcelas = []
    valor_total_parcelas = 0
    parcela_fixa = valor_base / parcelas if parcelas > 0 else 0
    for i in range(1, parcelas + 1):
        juros_parcela = parcela_fixa * (taxa_juros_mensal / 100) * i
        valor_parcela = parcela_fixa + juros_parcela
        valor_parcela = round(valor_parcela, 2)
        lista_parcelas.append(valor_parcela)
        valor_total_parcelas += valor_parcela
    valor_total_parcelas = round(valor_total_parcelas, 2)

    if request.method == 'POST':
        # Salva no banco de dados todos os dados relevantes
        data_acordo = datetime.now().strftime('%Y-%m-%d')
        salvar_acordo(
            nome,
            valor_nominal,
            valor_juros,
            valor_entrada,
            float(taxa_juros_mensal),
            float(taxa_juros_diaria),
            valor_base,
            parcelas,
            lista_parcelas[-1],
            data_acordo
        )
        return redirect(url_for('cliente'))

    return render_template('resumo.html',
        codigo=codigo,
        nome=nome,
        valor_nominal=valor_nominal,
        valor_juros=valor_juros,
        entrada=entrada,
        valor_entrada=valor_entrada,
        valor_base=valor_base,
        valor_pos_entrada=valor_pos_entrada,
        parcelas=lista_parcelas,
        taxa_juros_diaria="%.5f" % taxa_juros_diaria,
        taxa_juros_mensal="%.2f" % taxa_juros_mensal,
        valor_total_parcelas=valor_total_parcelas,
        datas_parcelas=datas_parcelas
    )

@app.route('/acordos')
@login_required
def acordos():
    conn = sqlite3.connect('acordos.db')
    c = conn.cursor()
    c.execute('SELECT * FROM acordos')
    acordos = c.fetchall()
    conn.close()
    return render_template('acordos.html', acordos=acordos)

@app.route('/acordo/<int:acordo_id>')
@login_required
def acordo_detalhe(acordo_id):
    import sqlite3
    conn = sqlite3.connect('acordos.db')
    c = conn.cursor()
    c.execute('SELECT id, nome, valor_nominal, valor_juros, valor_entrada, taxa_juros_mensal, taxa_juros_diaria, valor_total, parcelas, valor_parcela, data_acordo FROM acordos WHERE id = ?', (acordo_id,))
    row = c.fetchone()
    conn.close()
    if row:
        acordo = {
            'id': row[0],
            'nome': row[1],
            'valor_nominal': row[2],
            'valor_juros': row[3],
            'valor_entrada': row[4],
            'taxa_juros_mensal': row[5],
            'taxa_juros_diaria': row[6],
            'valor_base': row[7],
            'parcelas': row[8],
            'valor_parcela': row[9],
            'data_acordo': row[10]
        }
        parcela_fixa = acordo['valor_base'] / acordo['parcelas'] if acordo['parcelas'] > 0 else 0
        lista_parcelas = []
        for i in range(1, acordo['parcelas'] + 1):
            juros_parcela = parcela_fixa * (acordo['taxa_juros_mensal'] / 100) * i
            valor_parcela = parcela_fixa + juros_parcela
            valor_parcela = round(valor_parcela, 2)
            lista_parcelas.append(valor_parcela)
        acordo['lista_parcelas'] = lista_parcelas
        acordo['valor_total_parcelas'] = sum(lista_parcelas)
        # Recupera datas das parcelas da sessão (para novos acordos)
        acordo['datas_parcelas'] = session.get('datas_parcelas', [''] * acordo['parcelas'])
        return render_template('acordo_detalhe.html', acordo=acordo)
    else:
        return 'Acordo não encontrado', 404

@app.route('/solicitar_acesso', methods=['GET', 'POST'])
def solicitar_acesso_route():
    erro = None
    sucesso = None
    if request.method == 'POST':
        nome = request.form['nome']
        usuario = request.form['usuario']
        senha = request.form['senha']
        confirmar_senha = request.form['confirmar_senha']
        if senha != confirmar_senha:
            erro = 'As senhas não conferem.'
        else:
            solicitar_acesso(nome, usuario, senha)
            sucesso = 'Solicitação enviada! Aguarde aprovação do administrador.'
    return render_template('solicitar_acesso.html', erro=erro, sucesso=sucesso)

@app.route('/aprovacao_usuarios', methods=['GET'])
@login_required
def aprovacao_usuarios():
    if session.get('usuario_autenticado', '').lower() == 'sup':
        usuarios = listar_usuarios()
        return render_template('aprovacao_usuarios.html', usuarios=usuarios)
    else:
        return redirect(url_for('cliente'))

@app.route('/aprovar_usuario/<int:usuario_id>', methods=['POST'])
@login_required
def aprovar_usuario_route(usuario_id):
    if session.get('usuario_autenticado', '').lower() == 'sup':
        aprovar_usuario(usuario_id)
    return redirect(url_for('aprovacao_usuarios'))

@app.route('/bloquear_usuario/<int:usuario_id>', methods=['POST'])
@login_required
def bloquear_usuario_route(usuario_id):
    if session.get('usuario_autenticado', '').lower() == 'sup':
        bloquear_usuario(usuario_id)
    return redirect(url_for('aprovacao_usuarios'))

@app.route('/alternar_ativo/<int:usuario_id>', methods=['POST'])
@login_required
def alternar_ativo_route(usuario_id):
    if session.get('usuario_autenticado', '').lower() == 'sup':
        novo_status = request.form['novo_status']
        alternar_ativo(usuario_id, novo_status)
    return redirect(url_for('aprovacao_usuarios'))

@app.route('/buscar_cliente')
@login_required
def buscar_cliente():
    termo = request.args.get('q', '').strip()
    conn = sqlite3.connect('clientes.db')
    c = conn.cursor()
    c.execute('SELECT codigo, nome FROM clientes WHERE nome LIKE ? OR codigo LIKE ? LIMIT 10', (f'%{termo}%', f'%{termo}%'))
    resultados = [{'codigo': row[0], 'nome': row[1]} for row in c.fetchall()]
    conn.close()
    return {'clientes': resultados}

# Redireciona usuário master para tela de aprovação ao logar
@app.route('/inicio')
@login_required
def inicio():
    if session.get('usuario_autenticado', '').lower() == 'sup':
        return redirect(url_for('aprovacao_usuarios'))
    else:
        return redirect(url_for('cliente'))

@app.route('/excluir_acordo/<int:acordo_id>', methods=['POST'])
@login_required
def excluir_acordo(acordo_id):
    senha_sup = request.form.get('senha_sup', '')
    # Senha do sup definida no login: 'Miguel2@'
    if senha_sup != 'Miguel2@':
        return '<script>alert("Senha do SUP incorreta!");window.history.back();</script>'
    conn = sqlite3.connect('acordos.db')
    c = conn.cursor()
    c.execute('DELETE FROM acordos WHERE id = ?', (acordo_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('acordos'))

@app.route('/gerar_instrumento/<int:acordo_id>', methods=['POST'])
@login_required
def gerar_instrumento(acordo_id):
    # Buscar dados do acordo
    conn = sqlite3.connect('acordos.db')
    c = conn.cursor()
    c.execute('SELECT id, nome, valor_nominal, valor_juros, valor_entrada, taxa_juros_mensal, taxa_juros_diaria, valor_total, parcelas, valor_parcela, data_acordo FROM acordos WHERE id = ?', (acordo_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return 'Acordo não encontrado', 404
    # Buscar dados do devedor pelo código
    conn = sqlite3.connect('partes.db')
    c = conn.cursor()
    c.execute('SELECT nome, cnpj, endereco FROM devedores WHERE codigo_devedor = ?', (str(row[0]),))
    devedor = c.fetchone()
    # Buscar dados do credor (primeiro credor cadastrado)
    c.execute('SELECT nome, cnpj, endereco FROM credores LIMIT 1')
    credor = c.fetchone()
    conn.close()
    # Montar dados para o template
    # Buscar parcelas do banco
    conn = sqlite3.connect('acordos.db')
    c = conn.cursor()
    c.execute('SELECT numero, valor, data FROM parcelas WHERE acordo_id = ? ORDER BY numero', (acordo_id,))
    parcelas_db = c.fetchall()
    conn.close()
    parcelas_list = []
    for p in parcelas_db:
        numero, valor, data_vencimento = p
        parcelas_list.append({
            'numero': numero,
            'valor': f'{valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'),
            'valor_por_extenso': '', # implementar se desejar
            'data_vencimento': data_vencimento
        })
    dados_termo = {
        'nome_credor': credor[0] if credor else '',
        'cnpj_credor': formatar_cnpj(credor[1]) if credor else '',
        'endereco_credor': credor[2] if credor else '',
        'nome_devedor': devedor[0] if devedor else row[1],
        'cnpj_devedor': formatar_cnpj(devedor[1]) if devedor else '',
        'endereco_devedor': devedor[2] if devedor else '',
        'valor_total_divida': f'{row[3]:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'),
        'valor_total_por_extenso': '', # implementar função para extenso se desejar
        'origem_divida': 'Acordo comercial',
        'data_origem_divida': row[10],
        'parcelas_quantidade': row[8],
        'parcelas': parcelas_list,
        'forma_pagamento': 'Depósito bancário',
        'percentual_multa': '2%',
        'percentual_juros': f'{row[5]:.2f}% ao mês',
        'dias_antecipacao': '30',
        'dia': row[10].split('-')[2],
        'mes': row[10].split('-')[1],
        'ano': row[10].split('-')[0],
    }
    # Gerar PDF
    env = Environment(loader=FileSystemLoader(os.path.dirname('termo_template.html')))
    template = env.get_template('termo_template.html')
    html_renderizado = template.render(dados_termo)
    output_filename = f'Instrumento_Acordo_{acordo_id}.pdf'
    with open(output_filename, "w+b") as result_file:
        pisa_status = pisa.CreatePDF(html_renderizado, dest=result_file)
    if pisa_status.err:
        return 'Erro ao gerar PDF', 500
    return send_file(output_filename, as_attachment=True)
