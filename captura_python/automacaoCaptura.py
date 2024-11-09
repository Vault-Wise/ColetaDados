import psutil
import time
from socket import gethostname
import platform
import mysql.connector
from atlassian import Jira
from requests import HTTPError

#Conexão com o Jira
jira = Jira(
    url = "https://vault-wise.atlassian.net", #URL DA EMPRESA
    username = "nicolas.lopes@sptech.school", #EMAIL
    password = "ATATT3xFfGF0ym1f3zHairjYwt84NeHddfeAv287mj6iafa3HZa__pSsF_lVpNPtA7eawVaxnC1nUboyCqcrmXZnHqjI11f0OmCiE72w48xD6xs2f8fkJaM2X4BWsj6GTBsU6EmgG30cXnaezbxXlkSn_xln_rAnn4cJ5LWSVROuhB8fKWw0eHo=743EFEAD" #TOKEN
)

#Conexão com o banco
mydb = mysql.connector.connect(
    user='root', 
    password='', 
    host='localhost',
    database='VaultWise',
    port='3306'
)

cursor = mydb.cursor()

nomeMaquina = gethostname()
sistemaOperacional = platform.system()

intervalo = 2 

if(sistemaOperacional == "Windows"):
    disco = psutil.disk_usage('C:\\')
else:
    disco = psutil.disk_usage('/')

freqTotalProcessador = round(psutil.cpu_freq().max, 2)
memoriaTotal = round(psutil.virtual_memory().total/pow(10, 9),0)
discoTotal = round(disco.total/pow(10, 9), 0)

cursor.execute(f"SELECT * FROM CaixaEletronico WHERE nomeEquipamento = '{nomeMaquina}'")

for i in cursor.fetchall():
    print(i)

if cursor.rowcount < 1:
    cursor.execute(f"INSERT INTO CaixaEletronico VALUES (default, '{nomeMaquina}', '{sistemaOperacional}', {memoriaTotal}, {freqTotalProcessador}, 1)") 
    mydb.commit()

cursor.execute(f"SELECT idCaixa FROM CaixaEletronico WHERE nomeEquipamento LIKE '{nomeMaquina}'")
idEquipamento_tupla = cursor.fetchone()
idEquipamento = idEquipamento_tupla[0]

repeticao_CPU_RAM = 0
repeticao_CPU = 0
repeticao_RAM = 0

while True:
    porcent_cpu = psutil.cpu_percent()
    memoria = psutil.virtual_memory()
    freq_cpu = psutil.cpu_freq()
    rede = psutil.net_io_counters()
    tempo_atividade = psutil.boot_time()
    rede = psutil.net_io_counters()

    redeMB_upload = ((rede.bytes_recv - rede.bytes_sent) * pow(10, -6))/ 60
    redeMB_download = (rede.bytes_recv * pow(10, -6)) / 60

    tempo_atual = time.time()

    uptime_s = tempo_atual - tempo_atividade


    print(""" 
    DADOS ARMAZENADOS
          
    (Intervalo de {:d} s)
          
    CPU (Freqência total = {:.2f} MHz):      
    Porcentagem de uso da CPU: {:.2f}%
    Freq CPU: {:f}
    
    Memória (Total = {:.2f} GB):
    Porcentagem de uso memória RAM: {:.1f}
    Memoria Usada: {:f} GB
          
    Disco Rígido (Total = {:.2f} GB): 
    Porcentagem de uso do disco: {:.1f}%
    Disco usado: {:f} 
    
    {:d}
    Pressione Ctrl+C para encerrar a captura
    """.format(intervalo, freq_cpu.max, porcent_cpu, freq_cpu.current,  memoria.total/pow(10, 9), memoria.used, memoria.percent, disco.total/pow(10, 9), disco.percent, disco.used, repeticao_RAM))

    #Tempo de captura de dados
    time.sleep(intervalo)
    cursor.execute(f"""
    INSERT INTO Registro 
    (percentMemoria, percentProcessador, memoriaUsada, freqProcessador, 
    velocidadeUpload, velocidadeDownload, tempoAtividade, fkCaixa)
    VALUES 
    ({round(memoria.percent, 2)}, {round(porcent_cpu, 2)}, 
    {round(memoria.used / pow(10, 9), 2)}, {round(freq_cpu.current, 2)}, 
    {round(redeMB_upload, 2)}, {round(redeMB_download, 2)}, {uptime_s}, {idEquipamento})
    """)
    mydb.commit()

    cursor.execute(f"SELECT idRegistro FROM Registro ORDER BY idRegistro DESC LIMIT 1")
    idRegistro_tupla = cursor.fetchone()
    idRegistro = idRegistro_tupla[0]

    if(round(porcent_cpu, 2) > 80 and round(memoria.percent, 2) > 80):
        cursor.execute(f"INSERT INTO Alerta VALUES (DEFAULT, 'Memória e CPU', 'Ambos acima de 80%', {idRegistro}, {idEquipamento})")
        mydb.commit()
        repeticao_CPU_RAM+=1

        if(repeticao_CPU_RAM >= 5):
                    
                    jira.issue_create(
                fields={
                    'project': {
                        'key': 'VAULT' #SIGLA DO PROJETO
                    },
                    'summary': 'Alerta de CPU e RAM',
                    'description': 'CPU e RAM acima da média, necessario olhar com atenção esse Caixa em específico caso precise de manutenção em breve',
                    'issuetype': {
                        "name": "Task"
                    },
                }
            )
                    repeticao_CPU_RAM=0

    elif (round(memoria.percent, 2) > 80):
        cursor.execute(f"INSERT INTO Alerta VALUES (DEFAULT, 'Memória', 'Memória RAM acima de 80%', {idRegistro}, {idEquipamento})")
        mydb.commit()
        repeticao_RAM+=1

        if(repeticao_RAM >= 5):
                    try:
                        jira.issue_create(
                    fields={
                        'project': {
                            'key': 'VAULT' #SIGLA DO PROJETO
                        },
                        'summary': 'Alerta de RAM',
                        'description': 'Memória RAM acima da média, analisar comportamento estranho e verificar se é frequente',
                        'issuetype': {
                            "name": "Task"
                        },
                    }
                )
                    except HTTPError as e:
                        print(e.response.text)

                    repeticao_RAM=0

    elif(round(porcent_cpu, 2) > 80):
        cursor.execute(f"INSERT INTO Alerta VALUES (DEFAULT, 'CPU', 'CPU acima de 80%', {idRegistro}, {idEquipamento})")
        mydb.commit()
        repeticao_CPU+=1

        if(repeticao_CPU >= 5):
                    
                    jira.issue_create(
                fields={
                    'project': {
                        'key': 'VAULT' #SIGLA DO PROJETO
                    },
                    'summary': 'Alerta de CPU',
                    'description': 'Processador acima da média, possível ataque no Caixa ou erro de Hardware.',
                    'issuetype': {
                        "name": "Task"
                    },
                }
            )
                    repeticao_CPU=0
        

    cursor.close()
    mydb.close()
