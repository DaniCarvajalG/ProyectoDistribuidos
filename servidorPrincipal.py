import zmq
import time
import random
import threading
import json
import argparse

# Lista para almacenar las solicitudes resueltas
solicitudes_resueltas = []

# Función para cargar los datos desde un archivo JSON.
def cargar_datos_archivo(json_file):
    try:
        # Intentar abrir y cargar los datos desde el archivo JSON
        with open(json_file, 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        # Si el archivo no existe, retornar un diccionario con valores por defecto
        data = {"taxis": [], "servicios": [], "estadisticas": {"servicios_satisfactorios": 0, "servicios_negados": 0}}
    return data

# Función para guardar los datos en un archivo JSON.
def guardar_datos_archivo(json_file, data):
    # Abrir el archivo en modo escritura y volcar los datos en formato JSON
    with open(json_file, 'w') as file:
        json.dump(data, file, indent=4)

# Función que sincroniza el estado de los taxis, solicitudes y estadísticas.
def sincronizar_estado(replica_socket, taxis, solicitudes, taxis_activos, solicitudes_resueltas):
    while True:
        # Crear un diccionario con el estado actual de los taxis y solicitudes
        estado = {
            'taxis': taxis,
            'solicitudes': solicitudes,
            'solicitudes_resueltas': solicitudes_resueltas,
            'taxis_activos': taxis_activos
        }
        # Enviar el estado como objeto Python serializado a través del socket
        replica_socket.send_pyobj(estado)  
        # Esperar 3 segundos antes de sincronizar nuevamente
        time.sleep(3)  

# Función que verifica si un usuario sigue esperando o si ha agotado su tiempo de espera.
def user_is_still_waiting(solicitud, solicitudes_timeout):
    # Extraer el ID del usuario de la solicitud
    user_id = solicitud.split()[1]
    current_time = time.time()  # Obtener el tiempo actual

    # Verificar si el tiempo actual supera el tiempo de espera establecido para el usuario
    if user_id in solicitudes_timeout and current_time > solicitudes_timeout[user_id]:
        return False  # El usuario ya no está esperando (tiempo agotado)
    return True  # El usuario sigue esperando

# Función para registrar un servicio completado o denegado en los datos.
def registrar_servicio(data, taxi_id, usuario_posicion, taxi_posicion, servicio_satisfactorio=True):
    # Registrar la asignación del servicio en la lista de servicios
    data["servicios"].append({
        "hora_asignacion": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),  # Hora actual en formato UTC
        "taxi_id": taxi_id,  # ID del taxi asignado
        "usuario_posicion": usuario_posicion,  # Posición del usuario solicitante
        "taxi_posicion": taxi_posicion  # Posición del taxi en el momento de la asignación
    })
    # Actualizar las estadísticas según si el servicio fue satisfactorio o no
    if servicio_satisfactorio:
        data["estadisticas"]["servicios_satisfactorios"] += 1  # Incrementar contador de servicios satisfactorios
    else:
        data["estadisticas"]["servicios_negados"] += 1  # Incrementar contador de servicios negados
def servidor(is_primary=True):
    context = zmq.Context()

    # Configurar el puerto para las solicitudes de usuarios, dependiendo de si el servidor es primario o réplica
    user_rep_port = 5551 if is_primary else 5 

    # Conectar al Broker 1 para recibir información sobre la ubicación de los taxis
    sub_socket = context.socket(zmq.SUB)
    sub_socket.connect("tcp://localhost:5556")  # Conexión con Broker 1
    sub_socket.setsockopt_string(zmq.SUBSCRIBE, "ubicacion_taxi")  # Suscripción al tópico de ubicación de taxis

    # Conectar al Broker 2 para recibir el estado de los taxis
    sub_socket2 = context.socket(zmq.SUB)
    sub_socket2.connect("tcp://localhost:5756")  # Conexión con Broker 2
    sub_socket2.setsockopt_string(zmq.SUBSCRIBE, "estado_taxi")  # Suscripción al tópico de estado de taxis

    # Crear un socket REP para recibir solicitudes de los usuarios
    user_rep_socket = context.socket(zmq.REP)
    user_rep_socket.bind(f"tcp://*:{user_rep_port}")

    # Crear un socket REQ para enviar solicitudes de servicio a los taxis
    taxi_req_socket = context.socket(zmq.REQ)

    # Crear un socket REP para el health-check (verificación de estado)
    ping_rep_socket = context.socket(zmq.REP)
    ping_rep_socket.bind(f"tcp://*:5558")

    # Inicialización de estructuras de datos para taxis, solicitudes, y tiempos de espera
    taxis = {}
    solicitudes = []
    taxis_activos = {}
    solicitudes_timeout = {}
    taxi_ip = 'localhost'

    json_file = 'dataBase.json'
    data = cargar_datos_archivo(json_file)  # Cargar la base de datos de taxis y servicios

    print("Servidor iniciado como", "Primario" if is_primary else "Réplica")

    # Configuración de poller para manejar múltiples sockets sin bloqueo
    poller = zmq.Poller()
    poller.register(sub_socket, zmq.POLLIN)  # Registrar socket SUB para Broker 1 (ubicaciones de taxis)
    poller.register(sub_socket2, zmq.POLLIN)  # Registrar socket SUB para Broker 2 (estado de taxis)
    poller.register(user_rep_socket, zmq.POLLIN)  # Registrar socket REP para solicitudes de usuarios
    poller.register(ping_rep_socket, zmq.POLLIN)  # Registrar socket REP para health-check

    ultimo_tiempo_limpieza = time.time()
    while True:
        try:
            # Limpiar taxis inactivos cada 5 segundos
            tiempo_actual = time.time()
            if tiempo_actual - ultimo_tiempo_limpieza > 5:
                limpiar_taxis_inactivos(taxis, taxis_activos)  # Eliminar taxis que ya no están activos
                ultimo_tiempo_limpieza = tiempo_actual
            
            # Polling para revisar mensajes de los brokers y solicitudes de los usuarios
            sockets_activados = dict(poller.poll(1000))  # Timeout de 1 segundo para polling

            # Manejar mensajes de los taxis desde el Broker 1
            if sub_socket in sockets_activados:
                manejar_mensaje(sub_socket, taxis, taxis_activos, data, json_file)

            # Manejar mensajes de los taxis desde el Broker 2
            if sub_socket2 in sockets_activados:
                manejar_mensaje(sub_socket2, taxis, taxis_activos, data, json_file)

            # Manejo de solicitudes de los usuarios (REQ/REP)
            if user_rep_socket in sockets_activados:
                solicitud = user_rep_socket.recv_string()
                print(f"Solicitud recibida: {solicitud}")
                print(f"Taxis disponibles: {list(taxis.keys())}")  # Mostrar los taxis disponibles para depuración
                solicitudes.append(solicitud)

                # Extraer el ID del usuario y establecer un timeout para la solicitud
                user_id = solicitud.split()[1]
                solicitudes_timeout[user_id] = time.time() + 15  # Timeout de 15 segundos para cada solicitud

                # Verificar si hay taxis disponibles
                if taxis:
                    # Verificar si el usuario sigue esperando (sin haber agotado el tiempo de espera)
                    if user_is_still_waiting(solicitud, solicitudes_timeout):
                        posicion_usuario = extraer_posicion_usuario(solicitud)
                        if posicion_usuario:
                            taxi_seleccionado = seleccionar_taxi(taxis, posicion_usuario)  # Seleccionar el taxi más cercano
                            if taxi_seleccionado is not None:
                                try:
                                    print(f"Asignando servicio al taxi {taxi_seleccionado} (más cercano)")
                                    taxi_req_socket.connect(f"tcp://{taxi_ip}:556{taxi_seleccionado}")
                                    taxi_req_socket.setsockopt(zmq.RCVTIMEO, 5000)  # Timeout de 5 segundos para la respuesta del taxi
                                    taxi_req_socket.send_string("Servicio asignado")  # Enviar la solicitud de servicio al taxi
                                    respuesta = taxi_req_socket.recv_string()  # Recibir respuesta del taxi
                                    taxi_req_socket.disconnect(f"tcp://{taxi_ip}:556{taxi_seleccionado}")  # Desconectar después de la respuesta

                                    # Calcular distancia entre el taxi y el usuario y enviar la respuesta al usuario
                                    distancia = calcular_distancia(taxis[taxi_seleccionado], posicion_usuario)
                                    user_rep_socket.send_string(f"Taxi {taxi_seleccionado} asignado (distancia: {distancia} unidades)")
                                    registrar_servicio(
                                        data,
                                        taxi_seleccionado,
                                        posicion_usuario,
                                        taxis[taxi_seleccionado],
                                        True  # Servicio satisfactorio
                                    )
                                    
                                    solicitudes.remove(solicitud)  # Eliminar la solicitud de la lista
                                    print(f"Servicio asignado exitosamente al taxi {taxi_seleccionado}")
                                except zmq.ZMQError as e:
                                    print(f"Error al comunicarse con el taxi {taxi_seleccionado}: {e}")
                                    user_rep_socket.send_string("Error al asignar taxi, intentando con otro...")  # Respuesta de error al usuario
                            

                            else:
                                print("Error al seleccionar taxi")
                                user_rep_socket.send_string("No hay taxis disponibles en este momento")  # Respuesta en caso de no encontrar taxi
                        else:
                            print("Error al extraer posición del usuario")
                            user_rep_socket.send_string("Error en el formato de la solicitud")  # Respuesta en caso de error en formato de solicitud
                    else:
                        print("Tiempo de espera agotado para la solicitud")
                        user_rep_socket.send_string("Tiempo de espera agotado")  # Respuesta por timeout
                else:
                    print("No hay taxis disponibles en este momento")
                    user_rep_socket.send_string("No hay taxis disponibles, intente más tarde")  # Respuesta si no hay taxis disponibles

            # Verificación de health-check (ping)
            if ping_rep_socket in sockets_activados:
                ping_message = ping_rep_socket.recv_string()
                if ping_message == "ping":
                    print("Recibido ping, respondiendo con pong")
                    ping_rep_socket.send_string("pong")  # Responder con pong cuando se recibe un ping

        except zmq.ZMQError as e:
            print(f"Error en la conexión con los brokers o sockets: {e}")
            time.sleep(1)  # Pausar antes de intentar reconectar
            # Intentar reconectar a los brokers en caso de error de conexión
            try:
                sub_socket.connect("tcp://localhost:5556")
                sub_socket2.connect("tcp://localhost:5756")
            except zmq.ZMQError:
                print("Error al reconectar a los brokers")

        time.sleep(1)  # Pausa para evitar sobrecargar el servidor
# Función para manejar los mensajes de los taxis
def manejar_mensaje(socket, taxis, taxis_activos, data, json_file):
    """
    Recibe y procesa los mensajes de los taxis que contienen su ID y posición.
    Actualiza la posición del taxi en el diccionario de taxis y registra su última actividad.
    """
    mensaje = socket.recv_string()  # Recibe el mensaje del taxi
    print(f"Mensaje recibido del taxi: {mensaje}")
    
    partes = mensaje.split(maxsplit=2)
    if len(partes) == 3:
        _, id_taxi, posicion = partes  # Se ignora el primer parámetro (tópico)
        id_taxi = int(id_taxi)
        
        try:
            taxi_posicion = json.loads(posicion)  # Convierte la posición recibida en un diccionario JSON
            taxis[id_taxi] = taxi_posicion  # Actualiza la posición del taxi
            taxis_activos[id_taxi] = time.time()  # Actualiza el tiempo de última actividad del taxi
            print(f"Taxi {id_taxi} actualizado en nueva posición: {taxi_posicion}")
            guardar_datos_archivo(json_file, data)  # Guarda la información actualizada en el archivo JSON
        except json.JSONDecodeError as e:
            print(f"Error al decodificar el JSON del taxi {id_taxi}: {e}")
    else:
        print("Mensaje recibido malformado, se esperaban tres partes")

def limpiar_taxis_inactivos(taxis, taxis_activos, timeout=10):
    """
    Elimina los taxis que no han enviado actualización en los últimos 'timeout' segundos.
    Este procedimiento asegura que solo se mantengan los taxis activos en el sistema.
    """
    tiempo_actual = time.time()  # Obtiene el tiempo actual
    taxis_a_eliminar = []  # Lista para almacenar los taxis a eliminar
    
    for taxi_id, ultimo_tiempo in taxis_activos.items():
        if tiempo_actual - ultimo_tiempo > timeout:
            taxis_a_eliminar.append(taxi_id)  # Añade el taxi a la lista si ha superado el tiempo de inactividad
    
    for taxi_id in taxis_a_eliminar:
        taxis.pop(taxi_id, None)  # Elimina el taxi de la lista de taxis
        taxis_activos.pop(taxi_id, None)  # Elimina el taxi de la lista de taxis activos
        print(f"Taxi {taxi_id} eliminado por inactividad (última actualización hace {int(tiempo_actual - ultimo_tiempo)} segundos)")

def calcular_distancia(pos1, pos2):
    """
    Calcula la distancia Manhattan entre dos posiciones en el espacio bidimensional.
    La distancia Manhattan es la suma de las diferencias absolutas entre las coordenadas x y y.
    """
    distancia = abs(pos1['x'] - pos2['x']) + abs(pos1['y'] - pos2['y'])
    print(f"Calculando distancia entre {pos1} y {pos2}: {distancia} unidades")
    return distancia

def extraer_posicion_usuario(solicitud):
    """
    Extrae la posición del usuario desde el mensaje de solicitud.
    Se espera que el mensaje tenga el formato: "Usuario {id} en posición ({x},{y})".
    """
    try:
        partes = solicitud.split("posición (")[1].split(")")[0].split(",")  # Extrae las coordenadas
        posicion_usuario = {
            'x': int(partes[0]),
            'y': int(partes[1])
        }
        print(f"Posición extraída del usuario: {posicion_usuario}")
        return posicion_usuario
    except (IndexError, ValueError) as e:
        print(f"Error al extraer la posición del usuario: {e}")
        return None

def seleccionar_taxi(taxis, posicion_usuario):
    """
    Selecciona el taxi más cercano a la posición del usuario utilizando la distancia Manhattan.
    Si no hay taxis disponibles, retorna None.
    """
    if not taxis:
        print("No hay taxis disponibles para asignar.")
        return None
        
    distancias = {
        taxi_id: calcular_distancia(posicion, posicion_usuario)  # Calcula la distancia de cada taxi al usuario
        for taxi_id, posicion in taxis.items()
    }
    
    taxi_seleccionado = min(distancias.items(), key=lambda x: x[1])[0]  # Selecciona el taxi más cercano
    print(f"Taxi seleccionado: {taxi_seleccionado} (distancia más corta)")
    return taxi_seleccionado

if __name__ == "__main__":
    # Argumentos de línea de comando para saber si es réplica o primario
    parser = argparse.ArgumentParser(description="Servidor Central o Réplica")
    parser.add_argument("--replica", action="store_true", help="Iniciar como réplica")
    args = parser.parse_args()

    # Iniciar servidor como primario o réplica
    print("Iniciando servidor...")
    servidor(is_primary=not args.replica)  # Llama a la función para iniciar el servidor como primario o réplica
