@echo off
rem --- Configuración ---
set GCP_PROJECT_ID=helpful-helper-470301-b3
set GCP_REGION=us-central1
set FUNCTION_NAME=reddit-pulse-ingestion
set SERVICE_ACCOUNT=reddit-ingestion-sa@%GCP_PROJECT_ID%.iam.gserviceaccount.com

rem --- Variables de Entorno para la Cloud Function ---
rem No incluyas secretos aquí. Usa Secret Manager para eso.
set ENV_VARS=GCP_PROJECT_ID=%GCP_PROJECT_ID%
set ENV_VARS=%ENV_VARS%,PUBSUB_TOPIC_NAME=reddit-posts
set ENV_VARS=%ENV_VARS%,GCS_BUCKET_NAME=reddit-pulse-data-lake-raw
set ENV_VARS=%ENV_VARS%,DEAD_LETTER_TOPIC_NAME=reddit-posts-dlq
set ENV_VARS=%ENV_VARS%,SUBREDDITS_TO_PROCESS=technology;python;datascience
set ENV_VARS=%ENV_VARS%,DEFAULT_POST_LIMIT=25
set ENV_VARS=%ENV_VARS%,REDDIT_SECRET_ID=reddit-api-credentials

rem --- Comando de Despliegue ---
echo "🚀 Desplegando la funcion %FUNCTION_NAME%..."

gcloud functions deploy %FUNCTION_NAME% ^
  --gen2 ^
  --runtime python310 ^
  --region %GCP_REGION% ^
  --source ./reddit_ingestion_cf ^
  --entry-point http_trigger ^
  --trigger-http ^
  --allow-unauthenticated ^
  --service-account %SERVICE_ACCOUNT% ^
  --set-env-vars "%ENV_VARS%"

echo "✅ Despliegue completado."
pause