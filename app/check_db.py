import os
from dotenv import load_dotenv
import sqlite3

load_dotenv()

# Caminho para o banco de dados
db_path = os.getenv('DB_PATH')

# Conecta ao banco de dados
conn = sqlite3.connect(db_path)
c = conn.cursor()

# Verifica a estrutura da tabela
c.execute('PRAGMA table_info(tasks)')
print("Estrutura da tabela:")
for row in c.fetchall():
    print(row)

# Verifica os dados existentes
print("\nDados existentes na tabela:")
c.execute('SELECT * FROM tasks')
for row in c.fetchall():
    print(row)

# Fecha a conexão
conn.close()
