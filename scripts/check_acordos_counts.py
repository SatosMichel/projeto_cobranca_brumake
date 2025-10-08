import sqlite3
conn = sqlite3.connect('acordos.db')
c = conn.cursor()
c.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='acordos'")
print('acordos table exists:', c.fetchone()[0])
try:
    c.execute("SELECT count(*) FROM acordos")
    print('acordos rows:', c.fetchone()[0])
except Exception as e:
    print('acordos rows error:', e)
try:
    c.execute("SELECT seq FROM sqlite_sequence WHERE name='acordos'")
    r = c.fetchone()
    print('sqlite_sequence acordos seq:', r[0] if r else 'None')
except Exception as e:
    print('sqlite_sequence error:', e)

c.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='parcelas'")
print('parcelas table exists:', c.fetchone()[0])
try:
    c.execute("SELECT count(*) FROM parcelas")
    print('parcelas rows:', c.fetchone()[0])
except Exception as e:
    print('parcelas count error:', e)

conn.close()
