import zmq
import time
import random
import threading

# Diccionario que mantiene el estado de los usuarios (si están activos o no)
usuarios_activos = {}

# Dirección del servidor central
# ip_central = '10.0.0.0'  # Dirección IP de servidor central
ip_central = 'localhost'  # Dirección local para pruebas


# Función para manejar la solicitud de taxi de un usuario
def solicitar_taxi(req_socket, id_usuario, x, y):
    """
    Envía una solicitud de taxi al servidor y espera la respuesta. Si se recibe respuesta dentro del
    tiempo esperado, marca al usuario como atendido, de lo contrario lo marca como inactivo.
    
    Parámetros:
        req_socket: Socket de solicitud (REQ).
        id_usuario: ID del usuario solicitante.
        x, y: Coordenadas de la ubicación del usuario.

    Retorna:
        True si se recibe respuesta a tiempo, False si se agotó el tiempo de espera.
    """
    # Enviar la solicitud de taxi al servidor
    req_socket.send_string(f"Usuario {id_usuario} en posición ({x},{y}) solicita un taxi")
    print(f"Usuario {id_usuario} ha solicitado un taxi.")
    
    # Medir el tiempo de respuesta del servidor
    inicio_respuesta = time.time()

    try:
        # Configurar el tiempo de espera para la respuesta (15 segundos)
        req_socket.setsockopt(zmq.RCVTIMEO, 15000)
        respuesta = req_socket.recv_string()
        fin_respuesta = time.time()

        # Calcular el tiempo que tomó recibir la respuesta
        tiempo_respuesta = fin_respuesta - inicio_respuesta
        print(f"Usuario {id_usuario} recibió respuesta: {respuesta} en {tiempo_respuesta:.2f} segundos")

        # Marcar al usuario como atendido (inactivo)
        usuarios_activos[id_usuario] = False

    except zmq.error.Again:
        # Si el servidor no responde a tiempo, el usuario buscará otro proveedor
        print(f"Usuario {id_usuario} no recibió respuesta, se va a otro proveedor")
        usuarios_activos[id_usuario] = False  # Marcar al usuario como inactivo por timeout
        return False  # Indicar que no se recibió respuesta

    return True  # Indicar que se recibió respuesta correctamente


# Función que simula el comportamiento de un usuario en la red
def usuario(id_usuario, x, y, tiempo_espera):
    """
    Simula un usuario solicitando un taxi. El usuario intentará conectarse a dos servidores 
    para solicitar el taxi y esperará una respuesta.
    
    Parámetros:
        id_usuario: ID único del usuario.
        x, y: Coordenadas donde se encuentra el usuario.
        tiempo_espera: Tiempo que el usuario espera antes de hacer la solicitud.
    """
    context = zmq.Context()

    # Servidores a los que los usuarios se pueden conectar
    servidores = [
        (f"tcp://{ip_central}:5551", "Servidor Central"),
        (f"tcp://{ip_central}:5552", "Servidor Réplica")
    ]
    
    # Simular tiempo hasta que el usuario decida solicitar un taxi
    print(f"Usuario {id_usuario} en posición ({x},{y}) esperando {tiempo_espera} segundos para solicitar un taxi.")
    time.sleep(tiempo_espera)

    # Marcar al usuario como activo
    usuarios_activos[id_usuario] = True

    # Intentar conectarse a los servidores disponibles
    for direccion_servidor, nombre_servidor in servidores:
        req_socket = context.socket(zmq.REQ)
        req_socket.connect(direccion_servidor)  # Conectar al servidor correspondiente

        print(f"Usuario {id_usuario} intentando conectarse a {nombre_servidor} ({direccion_servidor})...")
        
        # Intentar solicitar el taxi al servidor
        if solicitar_taxi(req_socket, id_usuario, x, y):
            req_socket.close()
            return  # Si se recibió respuesta, cerrar y salir

        else:
            print(f"Fallo en {nombre_servidor}, intentando con otro servidor...")
            req_socket.close()

    # Si no se pudo conectar a ningún servidor, informar al usuario
    print(f"Usuario {id_usuario} no pudo conectarse a ningún servidor.")


# Función para generar múltiples usuarios con atributos aleatorios
def generador_usuarios(num_usuarios, grid_size):
    """
    Genera múltiples usuarios con posiciones aleatorias y tiempos de espera aleatorios.
    
    Parámetros:
        num_usuarios: Número de usuarios a generar.
        grid_size: Tamaño de la cuadrícula donde los usuarios se ubicaran aleatoriamente.
    """
    threads = []
    for i in range(num_usuarios):
        # Generar posiciones aleatorias para los usuarios en la cuadrícula
        x, y = random.randint(0, grid_size[0] - 1), random.randint(0, grid_size[1] - 1)
        tiempo_espera = random.randint(1, 5)  # Tiempo aleatorio para simular la espera antes de solicitar un taxi
        
        # Crear y empezar el hilo para cada usuario
        hilo_usuario = threading.Thread(target=usuario, args=(i, x, y, tiempo_espera))
        threads.append(hilo_usuario)
        hilo_usuario.start()

    # Esperar a que todos los hilos terminen
    for thread in threads:
        thread.join()


# Ejecución principal
if __name__ == "__main__":
    num_usuarios = 1  # Número de usuarios a simular (puedes cambiar este número)
    grid_size = (10, 10)  # Tamaño de la cuadrícula en la que se ubicarán los usuarios
    generador_usuarios(num_usuarios, grid_size)