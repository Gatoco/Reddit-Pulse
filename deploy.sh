#!/bin/bash

# --- Configuración ---
GCP_PROJECT_ID="helpful-helper-470301-b3"
GCP_REGION="us-central1"
FUNCTION_NAME="reddit-pulse-ingestion"
SERVICE_ACCOUNT="reddit-ingestion-sa@helpful-helper-470301-b3.iam.gserviceaccount.com"

# --- Variables de Entorno para la Cloud Function ---
# No incluyas secretos aquí. Usa Secret Manager para eso.
ENV_VARS="GCP_PROJECT_ID=${GCP_PROJECT_ID},"
ENV_VARS+="PUBSUB_TOPIC_NAME=reddit-posts,"
ENV_VARS+="GCS_BUCKET_NAME=reddit-pulse-data-lake-raw,"
ENV_VARS+="DEAD_LETTER_TOPIC_NAME=reddit-posts-dlq,"
ENV_VARS+="SUBREDDITS_TO_PROCESS=technology,python,datascience,"
ENV_VARS+="DEFAULT_POST_LIMIT=25,"
ENV_VARS+="REDDIT_SECRET_ID=reddit-api-credentials"

# --- Comando de Despliegue ---
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
