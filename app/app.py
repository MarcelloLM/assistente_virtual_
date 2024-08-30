import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import os
from collections import Counter
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

db_path = os.getenv('DB_PATH')
secret_key = os.getenv('SECRET_KEY')

# Função para inicializar o banco de dados
def init_db():
    # Garante que o diretório existe
    db_dir = os.path.dirname(db_path)
    if not os.path.exists(db_dir) and db_dir != '':
        os.makedirs(db_dir)
    
    # Conecta ao banco de dados
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Cria a tabela se não existir, agora com campo para horário
    c.execute('''CREATE TABLE IF NOT EXISTS tasks
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT NOT NULL,
                  description TEXT,
                  due_date TEXT,
                  due_time TEXT,
                  frequency TEXT,
                  completed_date TEXT,
                  time_spent INTEGER)''')
    
    # Salva e fecha a conexão
    conn.commit()
    conn.close()
    
if __name__ == "__main__":
    init_db()

# Função para adicionar tarefa
def add_task(title, description, due_date, due_time, frequency):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('INSERT INTO tasks (title, description, due_date, due_time, frequency) VALUES (?, ?, ?, ?, ?)',
              (title, description, due_date, due_time, frequency))
    conn.commit()
    conn.close()

# Função para remover tarefa
def remove_task(task_id):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Remove a tarefa pelo ID
    c.execute('DELETE FROM tasks WHERE id = ?', (task_id,))

    conn.commit()
    conn.close()

# Função para listar tarefas
def get_tasks():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('SELECT * FROM tasks')
    tasks = c.fetchall()
    conn.close()
    return tasks

# Função para verificar lembretes de tarefas próximas
def check_reminders():
    tasks = get_tasks()
    now = datetime.now()
    upcoming_tasks = []
    
    for task in tasks:
        # Verifica se a tupla tem pelo menos 5 elementos
        if len(task) < 6:
            continue
        
        due_datetime_str = f"{task[3]} {task[4]}"
        try:
            due_datetime = datetime.strptime(due_datetime_str, '%Y-%m-%d %H:%M')
        except ValueError:
            continue
        
        # Verifica se a tarefa é recorrente
        if task[5] == "Diária":
            if now.time() == datetime.strptime(task[4], '%H:%M').time() and now.date() >= datetime.strptime(task[3], '%Y-%m-%d').date():
                upcoming_tasks.append(task)
        elif task[5] == "Semanal":
            if now.time() == datetime.strptime(task[4], '%H:%M').time() and now.weekday() == datetime.strptime(task[3], '%Y-%m-%d').weekday():
                upcoming_tasks.append(task)
        elif task[5] == "Mensal":
            if now.time() == datetime.strptime(task[4], '%H:%M').time() and now.day == datetime.strptime(task[3], '%Y-%m-%d').day:
                upcoming_tasks.append(task)
        elif now <= due_datetime <= (now + timedelta(hours=1)):
            upcoming_tasks.append(task)
    
    return upcoming_tasks

def mark_task_completed(task_id):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Atualiza a data de conclusão da tarefa
    completed_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute('UPDATE tasks SET completed_date = ? WHERE id = ?', (completed_date, task_id))
    
    conn.commit()
    conn.close()

def get_pending_tasks():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Seleciona tarefas que ainda não foram concluídas
    c.execute('SELECT id, title, description, due_date FROM tasks WHERE completed_date IS NULL')
    tasks = c.fetchall()
    
    conn.close()
    return tasks

def get_completed_tasks():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Seleciona tarefas que foram concluídas
    c.execute('SELECT id, title, description, due_date, completed_date FROM tasks WHERE completed_date IS NOT NULL')
    tasks = c.fetchall()
    
    conn.close()
    return tasks

# Função para coletar dados de histórico
def get_task_history():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    try:
        c.execute('SELECT title FROM tasks WHERE completed_date IS NOT NULL')
        tasks = c.fetchall()
    except sqlite3.OperationalError as e:
        print(f"Erro ao acessar o banco de dados: {e}")
        tasks = []
    conn.close()
    return [task[0] for task in tasks]

# Função para gerar sugestões
def generate_suggestions():
    task_history = get_task_history()
    if not task_history:
        return ["Verificar e-mails", "Revisar tarefas pendentes"]
    
    # Conta a frequência das tarefas
    task_counts = Counter(task_history)
    most_common_tasks = task_counts.most_common(5)
    
    suggestions = []
    for task, count in most_common_tasks:
        suggestions.append(f"Considerando sua frequência em '{task}', você pode adicionar tarefas semelhantes.")
    
    # Adiciona sugestões padrão se não houver tarefas suficientes
    if len(suggestions) < 3:
        suggestions.append("Verificar e-mails")
        suggestions.append("Revisar tarefas pendentes")
    
    return suggestions



# Função para gerar relatório
def get_report(start_date, end_date):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Obtém o número de tarefas completadas e o tempo médio gasto por tarefa
    c.execute('''
        SELECT COUNT(*), AVG(time_spent)
        FROM tasks
        WHERE completed_date BETWEEN ? AND ?
    ''', (start_date, end_date))
    
    report = c.fetchone()
    conn.close()
    return report

# Função para gerar relatórios semanalmente 
def generate_weekly_report():
    now = datetime.now()
    start_date = (now - timedelta(days=now.weekday())).strftime('%Y-%m-%d')
    end_date = (now + timedelta(days=6 - now.weekday())).strftime('%Y-%m-%d')
    return get_report(start_date, end_date)

# Função para gerar relatórios mensalmente
def generate_monthly_report():
    now = datetime.now()
    start_date = now.replace(day=1).strftime('%Y-%m-%d')
    end_date = (now.replace(day=1) + timedelta(days=31)).replace(day=1).strftime('%Y-%m-%d')
    return get_report(start_date, end_date)

# Função para plotar gráficos
def plot_productivity_report(report_type):
    if report_type == "Semanal":
        report = generate_weekly_report()
    else:
        report = generate_monthly_report()
    
    tasks_count, avg_time_spent = report
    if tasks_count is None:
        tasks_count = 0
    if avg_time_spent is None:
        avg_time_spent = 0
    
    # Plotando gráficos
    fig, ax = plt.subplots(1, 2, figsize=(12, 5))
    
    # Gráfico de número de tarefas completadas
    sns.barplot(x=["Tarefas Completadas"], y=[tasks_count], ax=ax[0])
    ax[0].set_title('Número de Tarefas Completadas')
    
    # Gráfico de tempo médio gasto por tarefa
    sns.barplot(x=["Tempo Médio Gasto"], y=[avg_time_spent], ax=ax[1])
    ax[1].set_title('Tempo Médio Gasto por Tarefa (min)')
    
    st.pyplot(fig)

# Função para comparar relatórios de diferentes períodos
def compare_reports(start_date1, end_date1, start_date2, end_date2):
    report1 = get_report(start_date1, end_date1)
    report2 = get_report(start_date2, end_date2)
    
    return report1, report2

# Inicializa o banco de dados
init_db()

# Streamlit UI
st.title("Assistente Virtual para Produtividade")

# Formulário para adicionar tarefas
st.subheader("Adicionar Nova Tarefa")
task_title = st.text_input("Título da Tarefa")
task_description = st.text_area("Descrição")
task_due_date = st.date_input("Data de Vencimento", datetime.now())
task_due_time = st.time_input("Hora de Vencimento", datetime.now().time())
task_frequency = st.selectbox("Frequência", ["Única", "Diária", "Semanal", "Mensal"])

if st.button("Adicionar Tarefa"):
    add_task(task_title, task_description, task_due_date.strftime('%Y-%m-%d'), task_due_time.strftime('%H:%M'), task_frequency)
    st.success(f"Tarefa '{task_title}' adicionada com sucesso!")


# Exibe lembretes de tarefas próximas
st.subheader("Lembretes de Tarefas Próximas")
upcoming_tasks = check_reminders()

if upcoming_tasks:
    for task in upcoming_tasks:
        st.warning(f"**Lembrete:** {task[1]} - {task[3]} {task[4]}")
else:
    st.write("Nenhuma tarefa próxima no momento.")

# Exibe sugestões de novas tarefas
st.subheader("Sugestões de Novas Tarefas")
suggestions = generate_suggestions()
for suggestion in suggestions:
    st.write(f"- {suggestion}")

# Exibe as Tarefas pendentes 
st.subheader("Tarefas Pendentes")
tasks = get_pending_tasks()
for task in tasks:
    task_id, title, description, due_date = task
    st.write(f"**{title}** - {description} (Vence em: {due_date})")
    
    # Botão para marcar tarefa como concluída
    if st.button(f"Marcar como concluída", key=f"concluir-{task_id}"):
        mark_task_completed(task_id)
        st.success(f"Tarefa '{title}' marcada como concluída.")
        st.experimental_rerun()  # Recarrega a página para atualizar a lista de tarefas
    
    # Botão para remover tarefa
    if st.button("Remover", key=f"remover-{task_id}"):
        remove_task(task_id)
        st.warning(f"Tarefa '{title}' removida.")
        st.experimental_rerun()  # Recarrega a página para atualizar a lista de tarefas

st.write("Tarefas concluídas podem ser visualizadas nos relatórios de produtividade.")

# Visualizar tarefas concluídas
st.subheader("Tarefas Concluídas")
completed_tasks = get_completed_tasks()
if completed_tasks:
    for task in completed_tasks:
        task_id, title, description, due_date, completed_date = task
        st.write(f"**{title}** - {description} (Venceu em: {due_date}, Concluída em: {completed_date})")
else:
    st.write("Nenhuma tarefa concluída.")


# Selecione o tipo de relatório
report_type = st.selectbox("Selecione o Tipo de Relatório", ["Semanal", "Mensal"])

if st.button("Gerar Relatório"):
    plot_productivity_report(report_type)

st.title("Comparação de Produtividade")

# Selecione os períodos para comparação
start_date1 = st.date_input("Início do Período 1", datetime.now() - timedelta(days=30))
end_date1 = st.date_input("Fim do Período 1", datetime.now())
start_date2 = st.date_input("Início do Período 2", datetime.now() - timedelta(days=60))
end_date2 = st.date_input("Fim do Período 2", datetime.now() - timedelta(days=30))

if st.button("Comparar Períodos"):
    report1, report2 = compare_reports(start_date1.strftime('%Y-%m-%d'), end_date1.strftime('%Y-%m-%d'),
                                        start_date2.strftime('%Y-%m-%d'), end_date2.strftime('%Y-%m-%d'))
    
    st.write(f"Período 1: {start_date1} a {end_date1}")
    st.write(f"Número de Tarefas Completadas: {report1[0]}")
    st.write(f"Tempo Médio Gasto por Tarefa: {report1[1]}")

    st.write(f"Período 2: {start_date2} a {end_date2}")
    st.write(f"Número de Tarefas Completadas: {report2[0]}")
    st.write(f"Tempo Médio Gasto por Tarefa: {report2[1]}")
