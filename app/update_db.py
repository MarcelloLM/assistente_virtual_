import os
from dotenv import load_dotenv
import sqlite3

load_dotenv()

# Caminho para o banco de dados
db_path = os.getenv('DB_PATH')

# Conecta ao banco de dados
conn = sqlite3.connect(db_path)
c = conn.cursor()

# Adiciona a coluna due_time
try:
    c.execute('ALTER TABLE tasks ADD COLUMN due_time TEXT')
except sqlite3.OperationalError:
    print("Coluna 'due_time' já existe.")

# Adiciona a coluna frequency
try:
    c.execute('ALTER TABLE tasks ADD COLUMN frequency TEXT')
except sqlite3.OperationalError:
    print("Coluna 'frequency' já existe.")

# Adiciona a coluna completed_date
try:
    c.execute('ALTER TABLE tasks ADD COLUMN completed_date TEXT')
except sqlite3.OperationalError:
    print("Coluna 'completed_date' já existe. ")

# Adiciona a coluna time_spent
try:
    c.execute('ALTER TABLE tasks ADD COLUMN time_spent INTEGER')  # Tempo gasto em minutos
except sqlite3.OperationalError:
    print("Coluna 'time_spent' já existe. ")


# Verifica a estrutura da tabela para confirmar a adição da coluna
c.execute('PRAGMA table_info(tasks)')
print("Estrutura da tabela atualizada:")
for row in c.fetchall():
    print(row)

# Fecha a conexão
conn.commit()
conn.close()
