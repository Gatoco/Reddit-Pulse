# Guía de Configuración de Cloud Scheduler

Esta guía explica cómo configurar un job de Cloud Scheduler para invocar periódicamente la Cloud Function `reddit-pulse-ingestion`.

## 1. ¿Por Qué Usar Cloud Scheduler?

Cloud Scheduler es el servicio de cron gestionado de GCP. Nos permite automatizar la ejecución de nuestra función sin depender de `cron` en una máquina virtual o de ejecuciones manuales. Invocará el trigger HTTP de nuestra función según la programación que definamos.

## 2. Permisos de IAM para Cloud Scheduler

Para que Cloud Scheduler pueda invocar de forma segura nuestra Cloud Function, la cuenta de servicio asociada a Cloud Scheduler necesita el permiso adecuado.

1.  **Navega a la página de IAM** en la Consola de GCP.
2.  Busca la cuenta de servicio de **Cloud Scheduler**. Generalmente tiene un formato como: `service-PROJECT_NUMBER@gcp-sa-cloudscheduler.iam.gserviceaccount.com`.
3.  Haz clic en el ícono del lápiz para **editar los permisos** de esa cuenta de servicio.
4.  **Añade el rol:** `Cloud Functions Invoker` (`roles/cloudfunctions.invoker`).
5.  **Guarda** los cambios.

Este permiso le da a Cloud Scheduler la autoridad para realizar peticiones HTTP a tus Cloud Functions.

## 3. Creación del Job de Cloud Scheduler

Puedes crear el job usando el siguiente comando de `gcloud`. Reemplaza `URL_DE_TU_FUNCION` con tu dato.

```bash
## 3. Creación del Job de Cloud Scheduler

Puedes crear el job usando el siguiente comando de `gcloud` en una sola línea. Reemplaza `URL_DE_TU_FUNCION` con tu dato.

```bash
gcloud scheduler jobs create http reddit-ingestion-job --schedule "*/10 * * * *" --uri "URL_DE_TU_FUNCION" --http-method POST --headers "Content-Type=application/json" --message-body '{"subreddits": "technology;datascience;python", "limit": 50}' --time-zone "America/Mexico_City" --max-retry-attempts 3 --min-backoff 60s
```

**Nota Importante:** Si recibes un error sobre la `location` (ubicación), significa que necesitas especificar la región. Usa el siguiente comando, añadiendo el flag `--location` (ajusta `us-central1` si tu función está en otra región):

```bash
gcloud scheduler jobs create http reddit-ingestion-job --schedule "*/10 * * * *" --location="us-central1" --uri "URL_DE_TU_FUNCION" --http-method POST --headers "Content-Type=application/json" --message-body '{"subreddits": "technology;datascience;python", "limit": 50}' --time-zone "America/Mexico_City" --max-retry-attempts 3 --min-backoff 60s
```

### Desglose del Comando:

-   **`--schedule "*/10 * * * *"`**: Define la frecuencia de ejecución. En este caso, "cada 10 minutos".
-   **`--uri "URL_DE_TU_FUNCION"`**: La URL pública de tu Cloud Function que obtuviste en el despliegue.
-   **`--http-method POST`**: El método HTTP que usará para la petición.
-   **`--headers "Content-Type=application/json"`**: Especifica que el cuerpo de la petición es un JSON.
-   **`--message-body '{"subreddits": "...", "limit": 50}'`**: El cuerpo JSON que se enviará en la petición. Aquí puedes configurar los subreddits y el límite que quieres para las ejecuciones automáticas. **Nota:** Usamos punto y coma (`;`) como separador.
-   **`--time-zone "America/Mexico_City"`**: La zona horaria para la programación del job.
-   **`--max-retry-attempts 3`**: El número de reintentos en caso de que la función falle (devuelva un código de error).
-   **`--min-backoff 60s`**: El tiempo mínimo de espera (60 segundos) antes de realizar el primer reintento.

Una vez ejecutado este comando, tu pipeline de datos estará completamente automatizado.
