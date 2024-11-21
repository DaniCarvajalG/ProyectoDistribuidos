import zmq
import time


def health_check(replica_ip="tcp://localhost", primary_socket_addr="tcp://localhost:5558"):
    """
    Realiza un ping al servidor principal para verificar si está funcionando. Si no responde después de varios intentos, activa la réplica.
    """
    context = zmq.Context()

    def create_socket():
        """
        Crea un socket REQ con el timeout apropiado.
        """
        sock = context.socket(zmq.REQ)
        sock.connect(primary_socket_addr)
        sock.setsockopt(zmq.RCVTIMEO, 5000)  # Timeout de 5 segundos
        return sock

    while True:
        retry_attempts = 3  # Número de intentos para contactar al servidor principal
        success = False

        for attempt in range(retry_attempts):
            health_socket = create_socket()  # Crear un nuevo socket para cada intento
            try:
                print("Enviando ping al servidor principal...")
                health_socket.send_string("ping")
                respuesta = health_socket.recv_string()
                print(f"Respuesta recibida: {respuesta}")

                if respuesta == "pong":
                    print("Servidor principal en funcionamiento")
                    success = True
                    break  # Sale del bucle si la respuesta es exitosa

            except zmq.error.Again:
                print(f"Intento {attempt + 1} fallido. Reintentando...")
                # Si es el último intento fallido, activa la réplica
                if attempt == retry_attempts - 1:
                    print("Servidor principal no respondió después de varios intentos, enviando señal a la réplica")
                    ping_replica_to_activate(replica_ip)

            except zmq.ZMQError as e:
                print(f"Error de ZMQ: {e}")

            finally:
                health_socket.close()

            time.sleep(1)  # Espera entre intentos

        if success:
            time.sleep(1)  # Espera antes de verificar nuevamente el servidor principal
        else:
            break  # Si no hay éxito después de los intentos, termina el ciclo


def ping_replica_to_activate(replica_ip):
    """
    Envía un ping de activación a la réplica para asegurarse de que esté disponible.
    """
    context = zmq.Context()
    activate_socket = context.socket(zmq.REQ)
    replica_ping_port = "5559"  # Puerto para el ping de activación de la réplica
    
    # Construir la dirección completa con puerto
    replica_address = f"{replica_ip}:{replica_ping_port}"
    print(f"Conectando a la réplica en {replica_address}")
    activate_socket.connect(replica_address)
    activate_socket.setsockopt(zmq.RCVTIMEO, 5000)  # Timeout de 5 segundos
    
    # Enviar el ping a la réplica
    print("Enviando ping a la réplica para activación...")
    activate_socket.send_string("ping")
    response = activate_socket.recv_string()
    print(f"Respuesta de la réplica: {response}")
    activate_socket.close()


if __name__ == "__main__":
    health_check(replica_ip="tcp://localhost")  # Dirección IP de la réplica
