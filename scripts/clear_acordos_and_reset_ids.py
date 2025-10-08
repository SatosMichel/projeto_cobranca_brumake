import shutil
import sqlite3
import time
from pathlib import Path

DB = Path('acordos.db')
BACKUP = Path(f'acordos.db.bak.{int(time.time())}')

print('Criando backup de', DB)
shutil.copy2(DB, BACKUP)
print('Backup criado em', BACKUP)

conn = sqlite3.connect(str(DB))
c = conn.cursor()

print('Deletando registros de parcelas e acordos...')
c.execute('DELETE FROM parcelas')
c.execute('DELETE FROM acordos')
conn.commit()

# Resetar sqlite_sequence se existir
try:
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sqlite_sequence'")
    if c.fetchone():
        print('Resetando sqlite_sequence...')
        c.execute("DELETE FROM sqlite_sequence WHERE name='acordos' OR name='parcelas'")
        conn.commit()
except Exception as e:
    print('Erro ao resetar sqlite_sequence:', e)

print('Executando VACUUM para recuperar espaço e reiniciar contadores...')
conn.execute('VACUUM')
conn.close()
print('Pronto. IDs devem iniciar em 1 no próximo INSERT.')
print('Backup localizado em', BACKUP)
