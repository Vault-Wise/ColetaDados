import psutil

def verificar_processo(nome_process: str):
    print("Lista de processos em execução:")
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            print(f"PID: {proc.info['pid']}, Nome: {proc.info['name']}")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'] == nome_process:
                print(f"\nProcesso encontrado: {proc.info['name']} com PID: {proc.info['pid']}")
                return proc.info['pid']
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    print(f"Processo '{nome_process}' não encontrado.")
    return None

nome_processo = 'python'
pid = verificar_processo(nome_processo)

if pid:
    print(f"\nO PID do processo {nome_processo} é {pid}")
else:
    print(f"O processo {nome_processo} não está em execução.")
