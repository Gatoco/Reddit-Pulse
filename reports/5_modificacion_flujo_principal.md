# Documentación: Modificación del Flujo Principal

Este documento describe la refactorización del flujo de ejecución principal en `reddit_ingestion_cf/main.py`. Se ha introducido una nueva función de orquestación y se ha modificado el bloque de ejecución principal para hacerlo más modular y configurable.

## 1. Nueva Función: `process_subreddit_batch()`

Se ha creado la función `process_subreddit_batch()` para centralizar la lógica de procesamiento de los subreddits.

### Parámetros
- `subreddits` (list): Una lista de nombres de subreddits a procesar.
- `extractor` (RedditExtractor): Una instancia del extractor de Reddit.
- `publisher` (PubSubPublisher): Una instancia del publicador de Pub/Sub.
- `archiver` (GCSArchiver): Una instancia del archivador de Google Cloud Storage.

### Lógica de Procesamiento por Post
Por cada post extraído, la función realiza las siguientes operaciones:

1.  **Validación de Datos:** Llama a `validate_post_data()` para asegurar que el post contiene los campos requeridos (`id`, `title`, `author`, etc.).
2.  **Añadir Timestamp de Procesamiento:** Agrega un campo `processing_timestamp` al diccionario del post para registrar cuándo fue procesado.
3.  **Publicación en Pub/Sub:** Envía el post a un tópico de Pub/Sub.
4.  **Subida Asíncrona a GCS:** Sube el post a Google Cloud Storage en un hilo separado utilizando `concurrent.futures.ThreadPoolExecutor` para no bloquear el procesamiento de otros posts.
5.  **Logging:** Imprime mensajes en la consola para indicar el progreso y los errores de cada operación.

## 2. Modificación del Bloque `if __name__ == "__main__"`

El bloque de ejecución principal ha sido actualizado para utilizar la nueva función `process_subreddit_batch`.

### Cambios Clave:

1.  **Configuración Basada en Variables de Entorno:**
    - `GCP_PROJECT_ID`: ID del proyecto de GCP.
    - `PUBSUB_TOPIC_NAME`: Nombre del tópico de Pub/Sub.
    - `GCS_BUCKET_NAME`: Nombre del bucket de Cloud Storage.
    - `SUBREDDITS_TO_PROCESS`: Una lista de subreddits separados por comas (ej. "technology,python,datascience").
2.  **Inicialización de Clases:** Se instancian las clases `RedditExtractor`, `PubSubPublisher` y `GCSArchiver` con la configuración cargada desde el entorno.
3.  **Llamada a la Función de Orquestación:** Se invoca a `process_subreddit_batch()` con las instancias y la lista de subreddits.
4.  **Manejo de Errores y Cierre de Recursos:** Se utiliza un bloque `try...except...finally` para capturar errores y asegurar que la conexión del publicador de Pub/Sub se cierre correctamente al finalizar.