import sqlite3
import datetime

DB_NAME = 'usuarios.db'

def corrigir_tabela():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        comando_sql_correcao = "ALTER TABLE usuarios ADD COLUMN ativo TEXT NOT NULL DEFAULT 'sim';"
        print(f"Tentando adicionar a coluna 'ativo' à tabela 'usuarios'...")
        cursor.execute(comando_sql_correcao)
        conn.commit()
        print("Coluna 'ativo' adicionada com sucesso!")
    except sqlite3.OperationalError as e:
        if 'duplicate column name' in str(e):
            print("Coluna 'ativo' já existe. Correção não é necessária.")
        else:
            print(f"Erro inesperado: {e}")
    except Exception as e:
        print(f"Um erro ocorreu: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

    # Garantir que a coluna can_cadastrar_devedor exista (se não, tentar criá-la)
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        comando = "ALTER TABLE usuarios ADD COLUMN can_cadastrar_devedor TEXT NOT NULL DEFAULT 'nao';"
        cursor.execute(comando)
        conn.commit()
    except sqlite3.OperationalError as e:
        # coluna já existe ou outro erro de operação; silencioso
        pass
    except Exception:
        pass
    finally:
        try:
            conn.close()
        except Exception:
            pass

corrigir_tabela()

def criar_tabela_usuarios():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        usuario TEXT NOT NULL,
        senha TEXT NOT NULL,
        status TEXT NOT NULL,
        ativo TEXT NOT NULL DEFAULT 'sim',
        can_cadastrar_devedor TEXT NOT NULL DEFAULT 'nao'
    )
    ''')
    conn.commit()
    # Garante que o usuário master esteja aprovado e ativo
    c.execute('SELECT * FROM usuarios WHERE usuario = ?', ('sup',))
    if not c.fetchone():
        c.execute('INSERT INTO usuarios (nome, usuario, senha, status, ativo) VALUES (?, ?, ?, ?, ?)',
                  ('Administrador', 'sup', 'Miguel2@', 'aprovado', 'sim'))
        conn.commit()
    else:
        c.execute('UPDATE usuarios SET status = ?, ativo = ? WHERE usuario = ?', ('aprovado', 'sim', 'sup'))
        conn.commit()
    conn.close()

criar_tabela_usuarios()

def solicitar_acesso(nome, usuario, senha):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('INSERT INTO usuarios (nome, usuario, senha, status, ativo) VALUES (?, ?, ?, ?, ?)',
              (nome, usuario.lower(), senha, 'pendente', 'sim'))
    conn.commit()
    conn.close()

def registrar_acesso(usuario):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    agora = datetime.datetime.now().isoformat()
    try:
        c.execute('ALTER TABLE usuarios ADD COLUMN ultimo_acesso TEXT')
        conn.commit()
    except sqlite3.OperationalError:
        pass
    c.execute('UPDATE usuarios SET ultimo_acesso = ? WHERE usuario = ?', (agora, usuario.lower()))
    conn.commit()
    conn.close()

def listar_usuarios():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # tentar retornar também o campo can_cadastrar_devedor quando presente
    try:
        c.execute('SELECT id, nome, usuario, status, ativo, can_cadastrar_devedor FROM usuarios')
        usuarios = c.fetchall()
    except sqlite3.OperationalError:
        # fallback: retornar sem a coluna, adicionando valor default 'nao'
        c.execute('SELECT id, nome, usuario, status, ativo FROM usuarios')
        usuarios = [tuple(list(row) + ['nao']) for row in c.fetchall()]
    conn.close()
    return usuarios

def aprovar_usuario(usuario_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('UPDATE usuarios SET status = ? WHERE id = ?', ('aprovado', usuario_id))
    conn.commit()
    conn.close()

def bloquear_usuario(usuario_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('UPDATE usuarios SET status = ? WHERE id = ?', ('bloqueado', usuario_id))
    conn.commit()
    conn.close()

def alternar_ativo(usuario_id, novo_status):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('UPDATE usuarios SET ativo = ? WHERE id = ?', (novo_status, usuario_id))
    conn.commit()
    conn.close()


def alternar_permissao_cadastro(usuario_id, novo_status):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('UPDATE usuarios SET can_cadastrar_devedor = ? WHERE id = ?', (novo_status, usuario_id))
    conn.commit()
    conn.close()

def pode_cadastrar_devedor(usuario):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT can_cadastrar_devedor FROM usuarios WHERE usuario = ? LIMIT 1', (usuario,))
    r = c.fetchone()
    conn.close()
    return (r and r[0] == 'sim')

def consultar_acessos():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT nome, usuario, ultimo_acesso FROM usuarios WHERE ultimo_acesso IS NOT NULL')
    acessos = c.fetchall()
    conn.close()
    resultado = []
    for nome, usuario, ultimo_acesso in acessos:
        try:
            dt_ultimo = datetime.datetime.fromisoformat(ultimo_acesso)
            tempo = datetime.datetime.now() - dt_ultimo
            tempo_str = str(tempo).split('.')[0]
        except Exception:
            tempo_str = 'N/A'
        resultado.append((nome, usuario, ultimo_acesso, tempo_str))
    return resultado
