# My-Uber

Simulación de un sistema de transporte distribuido, inspirado en Uber, desarrollado como parte del curso de Sistemas Distribuidos. El proyecto emplea ZeroMQ para la comunicación entre los diferentes procesos, y utiliza enfoques de resiliencia y manejo de fallas para asegurar la disponibilidad continua del sistema.

## Integrantes

- Daniel Carvajal
- Daniela Moreno
- Adrian Ruiz

### Profesor
- Osberth De Castro

## Descripción General

El sistema My-Uber modela una ciudad dividida en una cuadrícula, donde varios taxis, ejecutados como procesos autónomos, se desplazan por la ciudad y responden a solicitudes de los usuarios. Un Servidor Central es responsable de gestionar estas interacciones, mientras que un Servidor Réplica toma el relevo si el servidor principal experimenta alguna falla. Además, se implementa un proceso de Health-Check que supervisa la operatividad del Servidor Central.

### Componentes Principales

1. **Servidor Central**: Actúa como el nodo principal, coordinando las solicitudes de los usuarios y la asignación de taxis en la ciudad.
2. **Servidor Réplica**: Funciona como respaldo del Servidor Central, asegurando la continuidad de los servicios si el nodo principal falla.
3. **Usuarios**: Son simulados como hilos que envían solicitudes de taxis y esperan recibir un taxi disponible.
4. **Taxis**: Procesos independientes que reportan su ubicación y responden a las solicitudes de servicio de los usuarios.
5. **Health-Check**: Un mecanismo que vigila el estado del Servidor Central y garantiza que el Servidor Réplica se active en caso de que el servidor principal falle.

## Tecnologías Utilizadas

- **ZeroMQ**: Middleware de comunicación utilizado para garantizar una transmisión eficiente y confiable de mensajes entre los diferentes elementos del sistema.
- **Python**: Lenguaje de programación empleado para la implementación de los componentes del sistema.
- **JSON**: Formato utilizado para el almacenamiento persistente de datos relacionados con las posiciones de los taxis y los servicios proporcionados.

## Estructura del Proyecto

La estructura del proyecto contiene los siguientes archivos y directorios:

- [**servidorPrincipal.py**](./servidorcentral.py): Implementación del Servidor Central que gestiona la lógica principal del sistema.
- [**servidorReplica.py**](./servidorreplica.py): Implementación del Servidor Réplica que toma el control si el Servidor Central falla.
- [**taxi.py**](./taxi.py): Código que simula el comportamiento de los taxis, incluyendo su movimiento y respuestas a las solicitudes.
- [**usuarios.py**](./usuarios.py): Código que simula los usuarios que envían solicitudes para solicitar taxis.
- [**healthcheck.py**](./healthcheck.py): Código del proceso de monitoreo (Health-Check).
- [**dataBase.json**](./dataBase.json): Archivo JSON que almacena datos relacionados con las posiciones de los taxis y los servicios realizados.
- [**broker.py**](./broker.py): Código responsable de la gestión de mensajes entre los diferentes componentes del sistema.
- [**broker2.py**](./broker2.py): Código responsable de la gestión de mensajes entre los diferentes componentes del sistema.
- [**README.md**](./README.md): Documentación general sobre el funcionamiento del sistema.
- [**funcionamiento.md**](./funcionamiento.md): Documentación detallada sobre la operación del sistema.


