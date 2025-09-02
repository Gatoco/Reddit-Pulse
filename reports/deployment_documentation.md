# Documentación: Despliegue como Cloud Function

Este documento describe la estructura final del script `reddit_ingestion_cf/main.py` y cómo desplegarlo como una Google Cloud Function con un disparador HTTP.

## 1. Estructura del Script para Despliegue

El script ha sido refactorizado para ser un módulo desplegable y reutilizable.

### Inicialización Global de Clientes
- Los clientes para los servicios de Reddit, Pub/Sub, Google Cloud Storage y Monitoring (`RedditExtractor`, `PubSubPublisher`, `GCSArchiver`, `MetricsManager`) se inicializan en el ámbito global del script.
- **Razón:** Esta es una práctica recomendada por Google Cloud para las Cloud Functions. Permite que las conexiones y los clientes se reutilicen entre invocaciones, lo que reduce la latencia y el costo de las ejecuciones.

### Punto de Entrada HTTP: `http_trigger(request)`
- **Función Principal:** `http_trigger(request)` es el punto de entrada que se debe especificar al desplegar la Cloud Function.
- **Manejo de Peticiones:** La función está diseñada para recibir peticiones HTTP POST.
- **Parámetros Configurables:** Se puede configurar el comportamiento de la función enviando un cuerpo JSON en la petición con los siguientes parámetros:
  - `subreddits` (string): Una cadena de nombres de subreddits separados por comas (ej: `"technology,python,gaming"`).
  - `limit` (int): El número máximo de posts a extraer por cada subreddit.
- **Valores por Defecto:** Si no se proporcionan los parámetros en la petición, la función utilizará los valores definidos en las variables de entorno `SUBREDDITS_TO_PROCESS` y `DEFAULT_POST_LIMIT`.

### Bloque de Ejecución Local: `if __name__ == "__main__"`
- Se ha conservado un bloque `if __name__ == "__main__"` que permite ejecutar el script localmente para realizar pruebas de integración.
- Este bloque utiliza las variables de entorno para la configuración y no se ejecuta cuando el código se despliega en el entorno de Cloud Functions.

## 2. Proceso de Despliegue (usando `gcloud` CLI)

Para desplegar esta función, puedes usar el siguiente comando de `gcloud`. Asegúrate de estar en el directorio raíz de tu proyecto.

```bash
gcloud functions deploy reddit-pulse-ingestion \
  --gen2 \
  --runtime python310 \
  --region your-gcp-region \
  --source ./reddit_ingestion_cf \
  --entry-point http_trigger \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=\"your-gcp-project-id\",PUBSUB_TOPIC_NAME=\"your-pubsub-topic-name\",GCS_BUCKET_NAME=\"your-gcs-bucket-name\",DEAD_LETTER_TOPIC_NAME=\"your-dlq-topic-name\",SUBREDDITS_TO_PROCESS=\"news,worldnews\",DEFAULT_POST_LIMIT=\"25\"
```

### Notas del Comando:
- **`--gen2`**: Utiliza la segunda generación de Cloud Functions, que ofrece mejor rendimiento.
- **`--runtime`**: Especifica el entorno de ejecución de Python.
- **`--source`**: Apunta al directorio que contiene el código de la función y su `requirements.txt`.
- **`--entry-point`**: Define qué función dentro de tu script será la que se ejecute (`http_trigger`).
- **`--trigger-http`**: Define el disparador como una petición HTTP.
- **`--allow-unauthenticated`**: Permite que la función sea invocada públicamente. Elimina esta bandera si quieres controlar el acceso a través de IAM.
- **`--set-env-vars`**: **MUY IMPORTANTE.** Aquí debes configurar todas las variables de entorno que tu función necesita para operar. No olvides configurar también las credenciales de Reddit en el entorno de la función.

## 3. Ejemplo de Invocación HTTP

Una vez desplegada, puedes invocar la función usando una herramienta como `curl`:

```bash
curl -X POST \"YOUR_FUNCTION_URL\" \
  -H \"Content-Type: application/json\" \
  -d '{ "subreddits": "python,golang,rust", "limit": 50 }'
```

Reemplaza `YOUR_FUNCTION_URL` con la URL que te proporciona GCP después del despliegue.
