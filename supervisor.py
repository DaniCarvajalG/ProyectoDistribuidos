import subprocess
import time


def obtener_pid_broker():
    """
    Verifica si broker2.py está siendo ejecutado y obtiene su PID.
    """
    try:
        # Ejecutar el comando wmic para buscar procesos Python con sus líneas de comando
        resultado = subprocess.run(
            'wmic process where "name=\'python.exe\'" get ProcessId,CommandLine',
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True,
        )

        if resultado.stdout:
            # Decodificar la salida y dividirla por líneas
            salida = resultado.stdout.decode().strip().split('\n')
            
            for linea in salida:
                if "broker2.py" in linea:
                    # La línea contiene el comando completo y el PID
                    partes = linea.rsplit(maxsplit=1)  # Dividir desde el final
                    if len(partes) == 2:
                        pid = partes[1].strip()
                        print(f"El Broker ya está corriendo con PID: {pid}")
                        return int(pid)

        return None
    except Exception as e:
        print(f"Error al verificar si el Broker está corriendo: {e}")
        return None


def iniciar_broker():
    """
    Inicia el script broker2.py como un nuevo proceso.
    """
    try:
        print("Iniciando el Broker...")
        broker_proceso = subprocess.Popen(['python', 'broker2.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return broker_proceso
    except Exception as e:
        print(f"Error al iniciar el Broker: {e}")
        return None


def verificar_proceso_pid(pid):
    """
    Verifica si un proceso con un PID específico sigue ejecutándose.
    """
    try:
        print(f"Verificando si el Broker está funcionando con PID: {pid}")
        resultado = subprocess.run(
            f'tasklist /FI "PID eq {pid}"',
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True,
        )

        if resultado.stdout:
            # Decodificar la salida usando latin-1 para evitar errores por caracteres especiales
            salida = resultado.stdout.decode('latin-1').strip()

            # Busca el PID en la salida
            if f"{pid}" in salida:
                print(f"El Broker con PID {pid} está funcionando correctamente.")
                return True
            else:
                print(f"El Broker con PID {pid} no está funcionando.")
        return False
    except Exception as e:
        print(f"Error al verificar el proceso con PID {pid}: {e}")
        return False


def supervisor_broker():
    """
    Supervisa el script broker2.py, asegurándose de que esté siempre en ejecución.
    """
    broker_pid = obtener_pid_broker()
    broker_proceso = None

    if broker_pid:
        print(f"Supervisando el Broker existente con PID {broker_pid}")
    else:
        broker_proceso = iniciar_broker()
        broker_pid = obtener_pid_broker()

    while True:
        if broker_proceso:
            # Verificar si el proceso iniciado por supervisor sigue activo
            if broker_proceso.poll() is not None:  # Si poll() no es None, el proceso terminó
                print("El Broker ha fallado. Reiniciando...")
                broker_proceso = iniciar_broker()
            else:
                if not verificar_proceso_pid(broker_pid):
                    print("El Broker existente ha fallado. Reiniciando...")
                    broker_proceso = iniciar_broker()
                    # Aquí después de iniciar el broker, verificamos su PID
                    broker_pid = obtener_pid_broker()
                    if broker_pid:
                        print(f"Broker iniciado con PID {broker_pid}")
                    else:
                        print("Error al obtener el PID del Broker después de iniciarlo.")
                
        else:
            # Verificar el proceso existente por PID
            if not verificar_proceso_pid(broker_pid):
                print("El Broker existente ha fallado. Reiniciando...")
                broker_proceso = iniciar_broker()
                # Aquí después de iniciar el broker, verificamos su PID
                broker_pid = obtener_pid_broker()
                if broker_pid:
                    print(f"Broker iniciado con PID {broker_pid}")
                else:
                    print("Error al obtener el PID del Broker después de iniciarlo.")

        time.sleep(3)  # Supervisar cada 3 segundos


if __name__ == "__main__":
    supervisor_broker()
