import psutil
import time
from socket import gethostname
import platform
import mysql.connector

#Conexão com o banco
mydb = mysql.connector.connect(
    user='capturaDados', 
    password='SPTech#2024', 
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
memortiaTotal = round(psutil.virtual_memory().total/pow(10, 9),0)
discoTotal = round(disco.total/pow(10, 9), 0)

cursor.execute(f"SELECT * FROM CaixaEletronico WHERE nomeEquipamento = '{nomeMaquina}'")

for i in cursor.fetchall():
    print(i)

if cursor.rowcount < 1: 
    cursor.execute(f"INSERT INTO CaixaEletronico VALUES (default, '{nomeMaquina}', '{sistemaOperacional}', {memortiaTotal}, {discoTotal}, {freqTotalProcessador}, 1)") 
    mydb.commit()

cursor.execute(f"SELECT idCaixa FROM CaixaEletronico WHERE nomeEquipamento LIKE '{nomeMaquina}'")
idEquipamento_tupla = cursor.fetchone()
idEquipamento = idEquipamento_tupla[0]

while True:
    porcent_cpu = psutil.cpu_percent()
    memoria = psutil.virtual_memory()
    freq_cpu = psutil.cpu_freq()
    rede = psutil.net_io_counters()
    tempo_atividade = psutil.boot_time()
    rede = psutil.net_io_counters()

    redeMB = ((rede.bytes_recv - rede.bytes_sent) * pow(10, -6))/ 60

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
          
    Pressione Ctrl+C para encerrar a captura
    """.format(intervalo, freq_cpu.max, porcent_cpu, freq_cpu.current,  memoria.total/pow(10, 9), memoria.used, memoria.percent, disco.total/pow(10, 9), disco.percent, disco.used))

    #Tempo de captura de dados
    time.sleep(intervalo)

    cursor.execute(f"INSERT INTO Registro VALUES (DEFAULT, ,{round(disco.percent, 2)}, {round(memoria.percent, 2)}, {round(porcent_cpu, 2)}, {round(memoria.used /pow(10,9), 2)}, {round(disco.used /pow(10,9), 2)}, {round(freq_cpu.current)}, {round(redeMB, 2)}, {uptime_s}, {idEquipamento})")
    mydb.commit()

cursor.close()
mydb.close()
