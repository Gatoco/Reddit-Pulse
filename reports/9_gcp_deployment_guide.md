# Guía de Despliegue y Configuración en GCP

Esta guía detalla los pasos necesarios para configurar el entorno en Google Cloud Platform y desplegar la Cloud Function de `Reddit-pulse`.

## 1. Configuración de Secret Manager (Credenciales de Reddit)

Para almacenar de forma segura las credenciales de la API de Reddit, usaremos Secret Manager.

### Paso 1.1: Crear el Secreto

1.  Navega a **Secret Manager** en la Consola de GCP.
2.  Haz clic en **"Crear Secreto"**.
3.  **Nombre del secreto:** `reddit-api-credentials` (o el nombre que prefieras). Anota este nombre, ya que será el valor de la variable de entorno `REDDIT_SECRET_ID`.
4.  **Valor del secreto:** Pega el siguiente contenido JSON, reemplazando los valores de ejemplo con tus credenciales reales de Reddit.
    ```json
    {
      "client_id": "tu_client_id_de_reddit",
      "client_secret": "tu_client_secret_de_reddit",
      "user_agent": "tu_user_agent_de_reddit"
    }
    ```
5.  Deja las demás opciones por defecto y haz clic en **"Crear secreto"**.

### Paso 1.2: Conceder Permisos a la Cloud Function

La cuenta de servicio de tu Cloud Function necesita permiso para leer este secreto.

1.  Navega a la página principal de **Secret Manager**.
2.  Busca y selecciona el secreto `reddit-api-credentials` que acabas de crear.
3.  En el panel de la derecha, haz clic en **"Permisos"**.
4.  Haz clic en **"Añadir principal"**.
5.  **Nuevos principales:** Ingresa la dirección de correo electrónico de la cuenta de servicio que usará tu Cloud Function. Por defecto, tiene un formato como `PROJECT_NUMBER-compute@developer.gserviceaccount.com` o, si usas una cuenta de servicio dedicada, `your-service-account-name@your-project-id.iam.gserviceaccount.com`.
6.  **Asignar roles:** Selecciona el rol **`Descriptor de acceso a secretos de Secret Manager`** (`roles/secretmanager.secretAccessor`).
7.  Haz clic en **"Guardar"**.

## 2. Permisos Mínimos Requeridos (IAM)

La cuenta de servicio de la Cloud Function necesita los siguientes roles de IAM para operar correctamente:

-   **Cloud Functions Invoker** (`roles/cloudfunctions.invoker`): Para permitir que la función sea invocada a través de HTTP.
-   **Pub/Sub Publisher** (`roles/pubsub.publisher`): Para publicar mensajes en los tópicos de Pub/Sub (incluyendo el de dead-letter).
-   **Storage Object Creator** (`roles/storage.objectCreator`): Para crear archivos en el bucket de Google Cloud Storage.
-   **Secret Manager Secret Accessor** (`roles/secretmanager.secretAccessor`): Para leer las credenciales de Reddit desde Secret Manager.
-   **Monitoring Metric Writer** (`roles/monitoring.metricWriter`): Para escribir las métricas personalizadas en Cloud Monitoring.

Asegúrate de que la cuenta de servicio asociada a tu Cloud Function tenga todos estos roles asignados en la sección **IAM** de la consola de GCP.

## 3. Creación del Script de Despliegue (`deploy.sh`)

Crea un archivo llamado `deploy.sh` en la raíz de tu proyecto con el siguiente contenido. Este script automatiza el despliegue de la función.

```bash
#!/bin/bash

# ---
Configuración ---
GCP_PROJECT_ID="tu-id-de-proyecto"
GCP_REGION="tu-region" # ej. us-central1
FUNCTION_NAME="reddit-pulse-ingestion"
SERVICE_ACCOUNT="la-cuenta-de-servicio-de-tu-funcion@${GCP_PROJECT_ID}.iam.gserviceaccount.com"

# ---
Variables de Entorno para la Cloud Function ---
# No incluyas secretos aquí. Usa Secret Manager para eso.
ENV_VARS="GCP_PROJECT_ID=${GCP_PROJECT_ID},"
ENV_VARS+="PUBSUB_TOPIC_NAME=reddit-posts,"
ENV_VARS+="GCS_BUCKET_NAME=reddit-pulse-data-lake-raw,"
ENV_VARS+="DEAD_LETTER_TOPIC_NAME=reddit-posts-dlq,"
ENV_VARS+="SUBREDDITS_TO_PROCESS=technology,python,datascience,"
ENV_VARS+="DEFAULT_POST_LIMIT=25,"
ENV_VARS+="REDDIT_SECRET_ID=reddit-api-credentials"

# ---
Comando de Despliegue ---
echo "🚀 Desplegando la función ${FUNCTION_NAME}..."

gcloud functions deploy ${FUNCTION_NAME} \
  --gen2 \
  --runtime python310 \
  --region ${GCP_REGION} \
  --source ./reddit_ingestion_cf \
  --entry-point http_trigger \
  --trigger-http \
  --allow-unauthenticated \
  --service-account ${SERVICE_ACCOUNT} \
  --set-env-vars "${ENV_VARS}"

echo "✅ Despliegue completado."
```

### Cómo Usar `deploy.sh`:
1.  Reemplaza los valores de las variables en la sección de "Configuración" del script.
2.  Asegúrate de que el script tenga permisos de ejecución: `chmod +x deploy.sh`.
3.  Ejecútalo desde la raíz de tu proyecto: `./deploy.sh`.

Con estos pasos, tu entorno de GCP estará correctamente configurado y podrás desplegar la función de manera automatizada y segura.

## 4. Verificación y Pruebas Post-Despliegue

Una vez que el script de despliegue se ejecuta, es crucial verificar que la función se haya desplegado correctamente y probar su funcionalidad.

### 4.1. Confirmación del Despliegue

El despliegue se considera exitoso cuando la salida del comando `gcloud` muestra el estado `state: ACTIVE`. La terminal también proporcionará una URL pública (`url` o `uri`) que se usará para invocar la función.

### 4.2. Prueba Manual de Invocación

Para probar la función en vivo, se puede realizar una petición HTTP POST utilizando una herramienta como `curl`. Esto permite verificar que el disparador HTTP funciona y que la función se ejecuta.

**Comando de Ejemplo:**
```bash
curl -X POST "URL_DE_TU_FUNCION" \
  -H "Content-Type: application/json" \
  -d '{ "subreddits": "python,golang,rust", "limit": 5 }'
```
- **Importante:** Reemplaza `URL_DE_TU_FUNCION` por la URL real obtenida en el paso de despliegue.

La respuesta inmediata a este comando debería ser un mensaje de texto como `Batch processing started successfully.` con un código de estado `200 OK`.

### 4.3. Verificación de Resultados en GCP

Después de la invocación, se deben verificar los siguientes puntos en la Consola de Google Cloud para confirmar que el pipeline completo funcionó:

1.  **Cloud Logging:** Revisa los logs de la función. Deberías ver los registros estructurados en JSON que detallan cada paso de la ejecución.
2.  **Cloud Storage:** Confirma que los archivos JSON de los posts extraídos han sido creados en el bucket configurado (`reddit-pulse-data-lake-raw`), siguiendo la estructura de carpetas `YYYY/MM/DD/`.
3.  **Pub/Sub:** Verifica que se han publicado mensajes en el tópico `reddit-posts`.
4.  **Cloud Monitoring:** Explora las métricas personalizadas (`posts_extracted_total`, `pubsub_publish_duration_ms`, etc.) para asegurarte de que se están registrando nuevos puntos de datos.
