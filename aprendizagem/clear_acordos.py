#!/usr/bin/env python3
import sqlite3
import shutil
import os
import datetime
import sys

BASE = os.path.dirname(__file__)
DB = os.path.join(BASE, 'acordos.db')

if not os.path.exists(DB):
    print('Arquivo não encontrado:', DB)
    sys.exit(1)

timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
backup = DB + '.bak.' + timestamp
shutil.copy2(DB, backup)
print('Backup criado em:', backup)

conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute('PRAGMA foreign_keys = ON;')

# listar tabelas
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
all_tables = [r[0] for r in cur.fetchall()]
print('Tabelas no DB:', all_tables)

if 'acordos' not in all_tables:
    print('Tabela `acordos` não encontrada. Abortando.')
    conn.close()
    sys.exit(1)

# contar antes
counts = {}
for t in ['parcelas','acordos']:
    if t in all_tables:
        cur.execute(f'SELECT COUNT(*) FROM {t}')
        counts[t] = cur.fetchone()[0]
    else:
        counts[t] = 0

print('Contagens antes da limpeza:', counts)

# apagar parcelas primeiro (se existir)
if 'parcelas' in all_tables:
    cur.execute('DELETE FROM parcelas')
    conn.commit()
    print('Parcelas apagadas.')

# apagar acordos
cur.execute('DELETE FROM acordos')
conn.commit()
print('Acordos apagados.')

# resetar sqlite_sequence se existir
cur.execute("SELECT name FROM sqlite_master WHERE name='sqlite_sequence'")
if cur.fetchone():
    cur.execute("DELETE FROM sqlite_sequence WHERE name IN ('acordos','parcelas')")
    conn.commit()
    print('sqlite_sequence atualizada (zerada para acordos e parcelas).')
else:
    print('sqlite_sequence não existe neste DB.')

# vacum para resetar rowid
try:
    cur.execute('VACUUM')
    print('VACUUM executado.')
except Exception as e:
    print('VACUUM falhou:', e)

# contar depois
counts_after = {}
for t in ['parcelas','acordos']:
    if t in all_tables:
        cur.execute(f'SELECT COUNT(*) FROM {t}')
        counts_after[t] = cur.fetchone()[0]
    else:
        counts_after[t] = 0

print('Contagens depois da limpeza:', counts_after)

conn.close()
print('Operação concluída.')
