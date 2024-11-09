import psutil
import time
from socket import gethostname
import platform
import mysql.connector

try:
    # Conexão com o banco
    mydb = mysql.connector.connect(
        user='', 
        password='', 
        host='',
        database='',
        port='',
        autocommit=True  # Garante que as alterações sejam confirmadas automaticamente
    )

    cursor = mydb.cursor()

    nomeMaquina = gethostname()
    sistemaOperacional = platform.system()

    intervalo = 2

    # Uso de disco
    if sistemaOperacional == "Windows":
        disco = psutil.disk_usage('C:\\')
    else:
        disco = psutil.disk_usage('/')

    # Frequência total do processador e memória total
    freq_cpu_info = psutil.cpu_freq()
    freqTotalProcessador = round(freq_cpu_info.max, 2) if freq_cpu_info else 0  # Verifica se cpu_freq() não é None
    memoriaTotal = round(psutil.virtual_memory().total / pow(10, 9), 0)
    discoTotal = round(disco.total / pow(10, 9), 0)

    cursor.execute(f"SELECT * FROM CaixaEletronico WHERE nomeEquipamento = '{nomeMaquina}'")
    for i in cursor.fetchall():
        print(i)

    if cursor.rowcount < 1: 
        cursor.execute(f"INSERT INTO CaixaEletronico VALUES (default, '{nomeMaquina}', '{sistemaOperacional}', {memoriaTotal}, {discoTotal}, {freqTotalProcessador}, 1)")

    cursor.execute(f"SELECT idCaixa FROM CaixaEletronico WHERE nomeEquipamento LIKE '{nomeMaquina}'")
    idEquipamento_tupla = cursor.fetchone()
    idEquipamento = idEquipamento_tupla[0]

    repeticao_CPU_RAM = 0
    repeticao_CPU = 0
    repeticao_RAM = 0

    while True:
        try:
            porcent_cpu = psutil.cpu_percent()
            memoria = psutil.virtual_memory()
            freq_cpu = psutil.cpu_freq()
            rede = psutil.net_io_counters()
            tempo_atividade = psutil.boot_time()

            redeMB = ((rede.bytes_recv - rede.bytes_sent) * pow(10, -6)) / 60
            tempo_atual = time.time()
            uptime_s = tempo_atual - tempo_atividade

            redeMB_upload = ((rede.bytes_recv - rede.bytes_sent) * pow(10, -6))/ 60
            redeMB_download = (rede.bytes_recv * pow(10, -6)) / 60

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
            """.format(intervalo, freq_cpu.max if freq_cpu else 0, porcent_cpu, freq_cpu.current if freq_cpu else 0, 
                       memoria.total/pow(10, 9), memoria.used, memoria.percent, disco.total/pow(10, 9), disco.percent, disco.used, repeticao_RAM))

            # Tempo de captura de dados
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

            cursor.execute(f"SELECT idRegistro FROM Registro ORDER BY idRegistro DESC LIMIT 1")
            idRegistro_tupla = cursor.fetchone()
            idRegistro = idRegistro_tupla[0]

            # Verificação de alertas
            if round(porcent_cpu, 2) > 80 and round(memoria.percent, 2) > 80:
                cursor.execute(f"INSERT INTO Alerta VALUES (DEFAULT, 'Memória e CPU', 'Ambos acima de 80%', {idRegistro}, {idEquipamento})")
                repeticao_CPU_RAM += 1
                if repeticao_CPU_RAM >= 5:
                    repeticao_CPU_RAM = 0

            elif round(memoria.percent, 2) > 80:
                cursor.execute(f"INSERT INTO Alerta VALUES (DEFAULT, 'Memória', 'Memória RAM acima de 80%', {idRegistro}, {idEquipamento})")
                repeticao_RAM += 1
                if repeticao_RAM >= 5:
                    repeticao_RAM = 0

            elif round(porcent_cpu, 2) > 80:
                cursor.execute(f"INSERT INTO Alerta VALUES (DEFAULT, 'CPU', 'CPU acima de 80%', {idRegistro}, {idEquipamento})")
                repeticao_CPU += 1
                if repeticao_CPU >= 5:
                    repeticao_CPU = 0

        except Exception as e:
            print("Erro durante o monitoramento:", e)
            break

    cursor.close()
    mydb.close()

except mysql.connector.Error as err:
    print("Erro de conexão com o banco de dados:", err)
except Exception as e:
    print("Erro geral:", e)
