import zmq
import time

def broker():
    """
    Broker que recibe mensajes de taxis y los reenvía a un servidor.
    """
    context = zmq.Context()

    # Socket para recibir mensajes de los taxis
    frontend = context.socket(zmq.SUB)
    frontend.bind("tcp://*:5555")
    frontend.setsockopt_string(zmq.SUBSCRIBE, "")  # Suscribirse a todos los mensajes
    
    # Socket para reenviar mensajes al servidor
    backend = context.socket(zmq.PUB)
    backend.bind("tcp://*:5556")

    print("Broker iniciado - esperando mensajes...")
    
    try:
        while True:
            try:
                # Intentar recibir mensaje del taxi de forma no bloqueante
                mensaje = frontend.recv_string(zmq.NOBLOCK)
                print(f"Broker recibió: {mensaje}")

                # Reenviar al servidor
                backend.send_string(mensaje)
                print(f"Broker reenvió: {mensaje}")
            
            except zmq.Again:
                # No hay mensajes disponibles, continúa el ciclo
                pass
            
            time.sleep(0.1)  # Pequeña pausa para no saturar el CPU

    except KeyboardInterrupt:
        print("Broker terminando...")

    finally:
        # Cerrar sockets y liberar recursos
        frontend.close()
        backend.close()
        context.term()

if __name__ == "__main__":
    broker()
