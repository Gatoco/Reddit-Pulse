# Documentación de Cambios: Clases de Publicación y Archivado

Este documento detalla las nuevas clases implementadas en `reddit_ingestion_cf/main.py` para manejar la publicación de mensajes en Pub/Sub y el archivado de datos en Google Cloud Storage.

## 1. Clase `PubSubPublisher`

Esta clase se encarga de la comunicación con Google Cloud Pub/Sub para enviar los datos de los posts de Reddit.

### `__init__(self, project_id, topic_name)`
- **Propósito:** Inicializa el cliente de Pub/Sub.
- **Parámetros:**
    - `project_id` (str): El ID del proyecto de Google Cloud.
    - `topic_name` (str): El nombre del tópico de Pub/Sub al que se publicarán los mensajes.

### `publish_message(self, data)`
- **Propósito:** Publica un único mensaje en el tópico de Pub/Sub.
- **Parámetros:**
    - `data` (dict): Un diccionario con los datos del post a publicar.
- **Lógica de Reintentos:** La librería cliente de Google (`pubsub_v1`) gestiona automáticamente los reintentos en caso de errores transitorios, por lo que no es necesario implementarlos manualmente.

### `close(self)`
- **Propósito:** Cierra la conexión del cliente de Pub/Sub. Es una buena práctica para liberar recursos de manera ordenada.

## 2. Clase `GCSArchiver`

Esta clase gestiona la subida y el almacenamiento de los datos crudos en un bucket de Google Cloud Storage.

### `__init__(self, bucket_name)`
- **Propósito:** Inicializa el cliente de Google Cloud Storage.
- **Parámetros:**
    - `bucket_name` (str): El nombre del bucket donde se almacenarán los archivos.

### `upload_raw_data(self, data, file_path)`
- **Propósito:** Sube un archivo de datos al bucket de GCS.
- **Parámetros:**
    - `data` (dict): Los datos a subir, que se convertirán a formato JSON.
    - `file_path` (str): La ruta completa (incluyendo el nombre del archivo) donde se guardará el objeto en el bucket.

### `generate_file_path(self, post_data)`
- **Propósito:** Genera una ruta de archivo estructurada basada en la fecha de extracción del post.
- **Parámetros:**
    - `post_data` (dict): El diccionario de datos del post.
- **Formato de la Ruta:** `YYYY/MM/DD/post_{id}_{timestamp}.json`, lo que permite organizar los datos de manera jerárquica y facilita las consultas por fecha.