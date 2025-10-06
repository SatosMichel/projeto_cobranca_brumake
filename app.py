from flask import Flask, render_template, request, redirect, session, url_for, send_file
from functools import wraps
from datetime import datetime
import sqlite3
import os
from xhtml2pdf import pisa
from jinja2 import Environment, FileSystemLoader
from utils_format import formatar_cnpj
from database import salvar_acordo
from utils_extenso import valor_por_extenso, numero_por_extenso, percentual_por_extenso
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
        conn = sqlite3.connect('partes.db')
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
        # Garantir que exista um acordo salvo antes de inserir parcelas
        codigo_devedor = session.get('codigo')
        codigo_credor = session.get('codigo_credor')
        nome = session.get('nome')
        valor_nominal = session.get('valor_nominal', 0.0)
        valor_juros = session.get('valor_juros', 0.0)
        valor_entrada = session.get('valor_entrada', 0.0)
        parcelas_session = parcelas
        data_acordo = datetime.now().strftime('%Y-%m-%d')

        # Chama salvar_acordo que retorna o id do acordo criado/atualizado
        try:
            # obter forma de pagamento salva na sessão ou usar Pix por padrão
            forma_pagamento = session.get('forma_pagamento', 'Pix')
            agencia = session.get('agencia', '')
            conta = session.get('conta', '')
            acordo_id = salvar_acordo(
                nome,
                valor_nominal,
                valor_juros,
                valor_entrada,
                float(taxa_juros_mensal),
                float(taxa_juros_diaria),
                valor_nominal - valor_entrada,
                parcelas_session,
                0.0,
                data_acordo,
                codigo_devedor=codigo_devedor,
                codigo_credor=codigo_credor,
                forma_pagamento=forma_pagamento,
                agencia=agencia,
                conta=conta,
                acordo_id=session.get('acordo_id')
            )
        except TypeError:
            # Em caso de versão anterior que não retorna id, tentar recuperar da sessão
            acordo_id = session.get('acordo_id')

        # Salvar acordo_id na sessão
        if acordo_id:
            session['acordo_id'] = acordo_id

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

        # Calcular valor de cada parcela
        valor_base = session.get('valor_juros', 0) - session.get('valor_entrada', 0)
        parcela_fixa = valor_base / parcelas if parcelas > 0 else 0
        for idx, data in enumerate(datas_parcelas, start=1):
            juros_parcela = parcela_fixa * (taxa_juros_mensal / 100) * idx
            valor_parcela = parcela_fixa + juros_parcela
            valor_parcela = round(valor_parcela, 2)
            cursor.execute('INSERT INTO parcelas (acordo_id, numero, data, valor) VALUES (?, ?, ?, ?)',
                           (acordo_id, idx, data, valor_parcela))
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
        # recuperar códigos do usuário da sessão
        codigo_devedor = session.get('codigo')
        codigo_credor = session.get('codigo_credor')
        # ler campos de forma de pagamento enviados pelo formulário (se houver)
        forma_pagamento = request.form.get('forma_pagamento', 'Pix')
        agencia = request.form.get('agencia', '')
        conta = request.form.get('conta', '')

        # persistir acordo, incluindo forma de pagamento como parte dos metadados (armazenamos em nome por compatibilidade ou estender a tabela)
        # ler campos de forma de pagamento enviados pelo formulário (se houver)
        forma_pagamento = request.form.get('forma_pagamento', session.get('forma_pagamento', 'Pix'))
        agencia = request.form.get('agencia', session.get('agencia', ''))
        conta = request.form.get('conta', session.get('conta', ''))
        # salvar na sessão para uso posterior
        session['forma_pagamento'] = forma_pagamento
        session['agencia'] = agencia
        session['conta'] = conta

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
            data_acordo,
            codigo_devedor=codigo_devedor,
            codigo_credor=codigo_credor,
            forma_pagamento=forma_pagamento,
            agencia=agencia,
            conta=conta
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
    c.execute('SELECT id, nome, valor_nominal, valor_juros, valor_entrada, taxa_juros_mensal, taxa_juros_diaria, valor_total, parcelas, valor_parcela, data_acordo, codigo_devedor, codigo_credor FROM acordos WHERE id = ?', (acordo_id,))
    row = c.fetchone()
    conn.close()
    if row:
        raw_name = row[1] or ''
        nome_limpo = raw_name.strip().rstrip(';').strip()
        acordo = {
            'id': row[0],
            'nome': nome_limpo,
            'valor_nominal': row[2],
            'valor_juros': row[3],
            'valor_entrada': row[4],
            'taxa_juros_mensal': row[5],
            'taxa_juros_diaria': row[6],
            'valor_base': row[7],
            'parcelas': row[8],
            'valor_parcela': row[9],
            'data_acordo': row[10],
            'codigo_devedor': row[11] if len(row) > 11 else None,
            'codigo_credor': row[12] if len(row) > 12 else None,
        }
        # Se codigo_devedor não estiver salvo, tentar inferir pelo nome
        if not acordo.get('codigo_devedor'):
            try:
                conn2 = sqlite3.connect('partes.db')
                c2 = conn2.cursor()
                # tentar match exato primeiro
                c2.execute('SELECT codigo_devedor FROM devedores WHERE nome = ? LIMIT 1', (nome_limpo,))
                r = c2.fetchone()
                if not r:
                    # tentar match parcial
                    c2.execute('SELECT codigo_devedor FROM devedores WHERE nome LIKE ? LIMIT 1', (f"%{nome_limpo}%",))
                    r = c2.fetchone()
                if r:
                    acordo['codigo_devedor'] = r[0]
                conn2.close()
            except Exception:
                pass
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


@app.route('/editar_acordo/<int:acordo_id>', methods=['GET', 'POST'])
@login_required
def editar_acordo(acordo_id):
    erro = None
    import sqlite3
    conn = sqlite3.connect('acordos.db')
    c = conn.cursor()
    # selecionar também os campos de pagamento se existirem
    c.execute('''SELECT id, nome, valor_nominal, valor_juros, valor_entrada, taxa_juros_mensal,
                 taxa_juros_diaria, valor_total, parcelas, valor_parcela, data_acordo,
                 codigo_devedor, codigo_credor, forma_pagamento, agencia, conta
                 FROM acordos WHERE id = ?''', (acordo_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return 'Acordo não encontrado', 404

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
        'data_acordo': row[10],
        'codigo_devedor': row[11],
        'codigo_credor': row[12],
        'forma_pagamento': row[13] if len(row) > 13 else 'Pix',
        'agencia': row[14] if len(row) > 14 else '',
        'conta': row[15] if len(row) > 15 else '',
    }

    if request.method == 'POST':
        # validar senha SUP antes de aplicar alterações
        sup_password = request.form.get('sup_password', '')
        if sup_password != 'Miguel2@':
            erro = 'Senha SUP inválida. Apenas o SUP pode editar acordos.'
            return render_template('editar_acordo.html', acordo=acordo, erro=erro)

        forma_pagamento = request.form.get('forma_pagamento', 'Pix')
        agencia = request.form.get('agencia', '')
        conta = request.form.get('conta', '')

        # buscar demais campos atuais para não sobrescrever com nulos
        import sqlite3 as _sqlite
        conn = _sqlite.connect('acordos.db')
        cur = conn.cursor()
        cur.execute('SELECT nome, valor_nominal, valor_juros, valor_entrada, taxa_juros_mensal, taxa_juros_diaria, valor_total, parcelas, valor_parcela, data_acordo, codigo_devedor, codigo_credor FROM acordos WHERE id = ?', (acordo_id,))
        existing = cur.fetchone()
        conn.close()
        if not existing:
            return 'Acordo não encontrado', 404

        nome = existing[0]
        valor_nominal = existing[1]
        valor_juros = existing[2]
        valor_entrada = existing[3]
        taxa_juros_mensal = existing[4]
        taxa_juros_diaria = existing[5]
        valor_total = existing[6]
        parcelas = existing[7]
        valor_parcela = existing[8]
        data_acordo = existing[9]
        codigo_devedor = existing[10]
        codigo_credor = existing[11]

        # salvar usando helper existente (faz alterações/insert conforme acordo_id)
        try:
            salvar_acordo(
                nome,
                valor_nominal,
                valor_juros,
                valor_entrada,
                float(taxa_juros_mensal),
                float(taxa_juros_diaria),
                valor_total,
                parcelas,
                valor_parcela,
                data_acordo,
                codigo_devedor=codigo_devedor,
                codigo_credor=codigo_credor,
                forma_pagamento=forma_pagamento,
                agencia=agencia,
                conta=conta,
                acordo_id=acordo_id
            )
        except Exception:
            # tentar um update direto caso o helper falhe
            conn2 = _sqlite.connect('acordos.db')
            c2 = conn2.cursor()
            c2.execute('UPDATE acordos SET forma_pagamento = ?, agencia = ?, conta = ? WHERE id = ?', (forma_pagamento, agencia, conta, acordo_id))
            conn2.commit()
            conn2.close()

        return redirect(url_for('acordo_detalhe', acordo_id=acordo_id))

    return render_template('editar_acordo.html', acordo=acordo, erro=erro)

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
    resultados = []
    # Tentar bancos possíveis na ordem: clientes.db, acordos.db
    db_candidates = ['clientes.db', 'acordos.db']
    for db in db_candidates:
        try:
            conn = sqlite3.connect(db)
            c = conn.cursor()
            # verificar se a tabela existe
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='clientes'")
            if not c.fetchone():
                conn.close()
                continue
            c.execute('SELECT codigo, nome FROM clientes WHERE nome LIKE ? OR codigo LIKE ? LIMIT 10', (f'%{termo}%', f'%{termo}%'))
            resultados = [{'codigo': row[0], 'nome': row[1]} for row in c.fetchall()]
            conn.close()
            break
        except Exception:
            # se um DB falhar, tentar o próximo candidato
            try:
                conn.close()
            except Exception:
                pass
            continue
    return {'clientes': resultados}

# Redireciona usuário master para tela de aprovação ao logar
@app.route('/inicio')
def inicio():
    if session.get('usuario_autenticado', '').lower() == 'sup':
        return redirect(url_for('aprovacao_usuarios'))
    else:
        return redirect(url_for('cliente'))

@app.route('/excluir_acordo/<int:acordo_id>', methods=['POST'])
@login_required
def excluir_acordo(acordo_id):
    # Excluir acordo e suas parcelas
    conn = sqlite3.connect('acordos.db')
    c = conn.cursor()
    c.execute('DELETE FROM parcelas WHERE acordo_id = ?', (acordo_id,))
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
    # Buscar dados do devedor/credor pelos códigos salvos no acordo
    codigo_devedor = row[11] if len(row) > 11 else None
    codigo_credor = row[12] if len(row) > 12 else None
    conn = sqlite3.connect('partes.db')
    c = conn.cursor()
    devedor = None
    credor = None
    if codigo_devedor:
        c.execute('SELECT nome, cnpj, endereco FROM devedores WHERE codigo_devedor = ?', (str(codigo_devedor),))
        devedor = c.fetchone()
    if codigo_credor:
        try:
            c.execute('SELECT nome, cnpj, endereco FROM credores WHERE codigo = ? OR rowid = ?', (str(codigo_credor), str(codigo_credor)))
            credor = c.fetchone()
        except Exception:
            credor = None
    # if not found, fallback to first credor
    if not credor:
        try:
            c.execute('SELECT nome, cnpj, endereco FROM credores LIMIT 1')
            credor = c.fetchone()
        except Exception:
            credor = None
    # Normalize credor fields in case import produced shifted/concatenated columns
    def _normalize_credor(row):
        if not row:
            return ('', '', '')
        nome_field = row[0] if len(row) > 0 else ''
        cnpj_field = row[1] if len(row) > 1 else ''
        endereco_field = row[2] if len(row) > 2 else ''
        nome = str(nome_field or '').strip().strip('"').rstrip(';')
        cnpj = str(cnpj_field or '').strip().strip('"')
        endereco = str(endereco_field or '').strip().strip('"')
        # Caso import mal formatada: nome contém apenas número (id) e cnpj_field contém o nome real
        if nome.isdigit() and cnpj and not endereco:
            # exemplo: (nome='1', cnpj='BRUMAKE MATERIAIS ELETRICOS', endereco='0197...;RUA ...')
            # mas quando endereco está vazio aqui, tentar recuperar da mesma coluna se tiver ;
            parts = endereco_field.split(';') if endereco_field else []
            # se cnpj_field parece ser o nome real e endereco_field contém cnpj;endereco concatenado
            if ';' in endereco_field:
                parts = endereco_field.split(';')
                real_cnpj = parts[0]
                real_end = ';'.join(parts[1:]).strip()
                real_name = cnpj
                return (real_name.strip().rstrip(';'), real_cnpj.strip(), real_end.strip())
            # fallback: assume cnpj_field is name and endereco_field holds cnpj+address
        # Caso cnpj_field contenha "cnpj;endereco" concatenado
        if ';' in cnpj and not endereco:
            parts = cnpj.split(';')
            real_cnpj = parts[0]
            real_end = ';'.join(parts[1:]).strip()
            return (nome, real_cnpj.strip(), real_end)
        # Caso endereco contenha "cnpj;endereco"
        if ';' in endereco:
            parts = endereco.split(';')
            # se o primeiro pedaço parece com cnpj (apenas dígitos)
            if parts[0].strip().replace('.', '').replace('/', '').replace('-', '').isdigit():
                real_cnpj = parts[0]
                real_end = ';'.join(parts[1:]).strip()
                return (nome, real_cnpj.strip(), real_end)
        return (nome, cnpj, endereco)

    nome_credor_raw, cnpj_credor_raw, endereco_credor_raw = _normalize_credor(credor)
    # formatar cnpj se possível
    try:
        cnpj_credor_fmt = formatar_cnpj(cnpj_credor_raw) if cnpj_credor_raw else ''
    except Exception:
        cnpj_credor_fmt = cnpj_credor_raw
    conn.close()
    # Montar dados para o template
    # Buscar parcelas do banco
    conn = sqlite3.connect('acordos.db')
    c = conn.cursor()
    c.execute('SELECT numero, valor, data FROM parcelas WHERE acordo_id = ? ORDER BY numero', (acordo_id,))
    parcelas_db = c.fetchall()
    conn.close()
    parcelas_list = []
    parcelas_total_numeric = 0.0
    for p in parcelas_db:
        numero, valor, data_vencimento = p
        try:
            parcelas_total_numeric += float(valor)
        except Exception:
            pass
        parcelas_list.append({
            'numero': numero,
            'valor': f'{valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'),
            'valor_por_extenso': valor_por_extenso(valor),
            'data_vencimento': data_vencimento
        })

    # Se não houver parcelas na tabela, gerar com base nos campos do acordo
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
        'nome_credor': nome_credor_raw if nome_credor_raw else (credor[0] if credor else ''),
        'cnpj_credor': cnpj_credor_fmt if cnpj_credor_fmt else (formatar_cnpj(credor[1]) if credor and len(credor) > 1 else ''),
        'endereco_credor': endereco_credor_raw if endereco_credor_raw else (credor[2] if credor and len(credor) > 2 else ''),
        'nome_devedor': devedor[0] if devedor else row[1],
        'cnpj_devedor': formatar_cnpj(devedor[1]) if devedor else '',
        'endereco_devedor': devedor[2] if devedor else '',
    'valor_total_divida': f'{row[3]:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'),
    'valor_total_por_extenso': valor_por_extenso(row[3]),
        'origem_divida': 'Acordo comercial',
        'data_origem_divida': row[10],
        'parcelas_quantidade': row[8],
        'parcelas': parcelas_list,
    'parcelas_total': f'{parcelas_total_numeric:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'),
    'parcelas_total_por_extenso': valor_por_extenso(parcelas_total_numeric),
    'forma_pagamento': 'Pix',
    'agencia': '',
    'conta': '',
        'percentual_multa': '2%',
    'percentual_multa_por_extenso': percentual_por_extenso(2),
    'percentual_juros': f'{row[5]:.2f}% ao mês',
    'percentual_juros_por_extenso': percentual_por_extenso(row[5]) if row[5] else '',
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
