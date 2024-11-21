import zmq
import time
import random
import json

# Dirección del broker
ip_broker = 'localhost'

def mover_taxi(id_taxi, grid_size, velocidad, max_servicios):
    """
    Función para simular el movimiento de un taxi en un entorno de cuadrícula.
    El taxi se conecta a los brokers y atiende solicitudes de servicio hasta alcanzar el máximo permitido.
    """
    context = zmq.Context()

    # Crear sockets PUB para enviar la posición a los Brokers
    pub_socket = context.socket(zmq.PUB)
    pub_socket2 = context.socket(zmq.PUB)

    try:
        # Conectar a ambos brokers
        pub_socket.connect(f"tcp://{ip_broker}:5555")
        pub_socket2.connect(f"tcp://{ip_broker}:5755")

        # Crear un socket REP para recibir solicitudes de servicio
        rep_socket = context.socket(zmq.REP)
        rep_socket.bind(f"tcp://*:556{id_taxi}")

        print(f"Taxi {id_taxi} iniciado y conectado a los brokers")

        # Posición inicial aleatoria del taxi
        x, y = random.randint(0, grid_size[0] - 1), random.randint(0, grid_size[1] - 1)
        servicios_realizados = 0

        # Realizar servicios hasta alcanzar el máximo
        while servicios_realizados < max_servicios:
            # Enviar la posición actual del taxi en formato JSON
            taxi_posicion = {"x": x, "y": y}
            mensaje = json.dumps(taxi_posicion)

            # Enviar la posición a ambos brokers
            pub_socket.send_string(f"ubicacion_taxi {id_taxi} {mensaje}")
            pub_socket2.send_string(f"ubicacion_taxi {id_taxi} {mensaje}")

            print(f"Taxi {id_taxi} enviando posición: ({x}, {y})")

            # Configurar el poller para recibir solicitudes de servicio
            poller = zmq.Poller()
            poller.register(rep_socket, zmq.POLLIN)

            # Esperar hasta 1 segundo por solicitudes de servicio
            socks = dict(poller.poll(1000))

            if rep_socket in socks:
                # Recibir y procesar el servicio solicitado
                servicio = rep_socket.recv_string()
                print(f"Taxi {id_taxi} recibió servicio: {servicio}")
                rep_socket.send_string(f"Taxi {id_taxi} aceptando servicio")
                servicios_realizados += 1

            # Simular movimiento del taxi en la cuadrícula
            x, y = mover_taxi_en_grilla(x, y, grid_size, velocidad)
            time.sleep(1)  # Actualización de la posición cada segundo

    except Exception as e:
        print(f"Error en taxi {id_taxi}: {e}")
    finally:
        # Cerrar conexiones de los sockets y finalizar el contexto
        print(f"Taxi {id_taxi} cerrando conexiones")
        pub_socket.close()
        pub_socket2.close()
        rep_socket.close()
        context.term()

def mover_taxi_en_grilla(x, y, grid_size, velocidad):
    """
    Función para mover el taxi en la cuadrícula.
    El taxi se mueve aleatoriamente en una de las cuatro direcciones (norte, sur, este, oeste).
    """
    direccion = random.choice(['norte', 'sur', 'este', 'oeste'])

    # Mover el taxi según la dirección seleccionada
    if direccion == 'norte' and y < grid_size[1] - velocidad:
        y += velocidad
    elif direccion == 'sur' and y >= velocidad:
        y -= velocidad
    elif direccion == 'este' and x < grid_size[0] - velocidad:
        x += velocidad
    elif direccion == 'oeste' and x >= velocidad:
        x -= velocidad

    return x, y

if __name__ == "__main__":
    # Solicitar al usuario el ID del taxi
    try:
        id_taxi = int(input("Ingrese el ID del taxi: "))
    except ValueError:
        print("Por favor, ingrese un número válido para el ID del taxi.")
        exit()

    # Configuración inicial del taxi
    grid_size = (10, 10)  # Tamaño de la cuadrícula
    velocidad = 1  # Velocidad de movimiento del taxi
    max_servicios = 10  # Número máximo de servicios a realizar

    print(f"Iniciando taxi {id_taxi}")
    mover_taxi(id_taxi, grid_size, velocidad, max_servicios)
