import sqlite3
import os
DB = os.path.join(os.path.dirname(__file__), 'acordos.db')
conn = sqlite3.connect(DB)
c = conn.cursor()
try:
    c.execute("SELECT name, seq FROM sqlite_sequence")
    rows = c.fetchall()
    if rows:
        print('sqlite_sequence rows:')
        for r in rows:
            print(r)
    else:
        print('sqlite_sequence: (vazio ou não existe)')
except Exception as e:
    print('ERR', e)
conn.close()
