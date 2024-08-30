import sqlite3

# Caminho para o banco de dados
db_path = r'H:\Atendentes CAF pastas\Marcello\ANÁLISELIVEOFF\Assistente_virtual\data\tasks.db'

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
