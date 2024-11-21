import zmq
import time

def broker():
    context = zmq.Context()
    
    # Socket para recibir mensajes de los taxis
    frontend = context.socket(zmq.SUB)
    frontend.bind("tcp://*:5755")
    frontend.setsockopt_string(zmq.SUBSCRIBE, "")  # Suscribirse a todos los mensajes
    
    # Socket para reenviar mensajes al servidor
    backend = context.socket(zmq.PUB)
    backend.bind("tcp://*:5756")
    
    print("Broker iniciado - esperando mensajes...")
    
    try:
        # Proxy que reenvía mensajes entre frontend y backend
        zmq.proxy(frontend, backend)
    except KeyboardInterrupt:
        print("Broker terminando...")
    except zmq.ZMQError as e:
        print(f"Error de ZMQ: {e}")
    finally:
        # Cerrar los sockets y liberar el contexto de ZeroMQ
        frontend.close()
        backend.close()
        context.term()

if __name__ == "__main__":
    broker()
