# Documentación: Manejo de Errores Avanzado

Este documento detalla la implementación de un sistema de manejo de errores más robusto y granular en el script `reddit_ingestion_cf/main.py`.

## 1. Resiliencia ante Fallos Individuales

El procesamiento de posts se realiza de forma individual dentro de un bucle. Gracias a un bloque `try...except` a nivel de post, si un único post falla durante la validación o el envío a las tareas asíncronas, se registrará el error y el sistema continuará con el siguiente post. Esto asegura que un dato corrupto o un fallo aislado no detenga todo el proceso del batch.

## 2. Mecanismo de Reintentos Automáticos

Para mejorar la resiliencia ante problemas de red transitorios, se ha implementado una lógica de reintentos en las operaciones críticas de I/O.

### Extracción de Reddit (`RedditExtractor`)
- **Lógica:** Se ha añadido un bucle que reintenta la extracción de datos de la API de Reddit hasta un máximo de **3 intentos**.
- **Disparador:** Se activa al encontrar una excepción de tipo `PrawcoreException`, común en fallos de red.
- **Retardo:** Se aplica una espera de **5 segundos** entre cada reintento para no sobrecargar el servicio.

### Subida a Google Cloud Storage (`GCSArchiver`)
- **Lógica:** Similar a la extracción, se reintenta la subida de archivos hasta **3 veces**.
- **Disparador:** Se activa ante excepciones de tipo `google_exceptions.RetryError`, que son gestionadas por la propia librería cliente de Google.
- **Retardo:** También se aplica una espera de **5 segundos** entre intentos.

## 3. Implementación de "Dead-Letter Queue" (DLQ)

Para evitar la pérdida de datos que no pueden ser procesados por Pub/Sub después de varios intentos, se ha implementado una lógica de "cola de mensajes fallidos" (Dead-Letter Queue).

### `PubSubPublisher`
- **Configuración:** La clase ahora puede recibir un parámetro opcional `dead_letter_topic_name` durante su inicialización. Si se proporciona, se crea un segundo cliente de Pub/Sub apuntando a este tópico de DLQ.
- **Flujo de Fallo:**
    1. El sistema intenta publicar el mensaje en el tópico principal.
    2. Si la publicación falla de manera persistente (la librería cliente de Google ya gestiona reintentos internos), se captura la excepción.
    3. En lugar de descartar el mensaje, se intenta publicar en el tópico DLQ configurado.
    4. Si la publicación en la DLQ también falla, se registra un error crítico, ya que la recuperación manual sería necesaria.
- **Variable de Entorno:** La configuración se gestiona a través de la variable de entorno opcional `DEAD_LETTER_TOPIC_NAME`.

Esta arquitectura asegura que los mensajes problemáticos se aíslen para su posterior análisis sin interrumpir el flujo principal de datos.