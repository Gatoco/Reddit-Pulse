# Documentación: Implementación de Monitoreo

Este documento describe la implementación de un sistema de monitoreo con métricas personalizadas en `reddit_ingestion_cf/main.py` utilizando Google Cloud Monitoring.

## 1. Nueva Clase: `MetricsManager`

Se ha introducido la clase `MetricsManager` para encapsular toda la lógica relacionada con la creación y publicación de métricas en Google Cloud Monitoring.

### `__init__(self, project_id)`
- **Propósito:** Inicializa el cliente de `monitoring_v3.MetricServiceClient` y configura el nombre del proyecto de GCP.

### Métodos de Métricas
- **`increment_posts_extracted(self, count=1)`**
  - **Métrica:** `custom.googleapis.com/posts_extracted_total` (CONTADOR)
  - **Descripción:** Incrementa un contador cada vez que se extraen posts de un subreddit.
- **`record_pubsub_latency(self, duration_ms)`**
  - **Métrica:** `custom.googleapis.com/pubsub_publish_duration_ms` (GAUGE)
  - **Descripción:** Registra la latencia (en milisegundos) de cada operación de publicación en Pub/Sub.
- **`increment_gcs_uploads(self, success=True)`**
  - **Métricas:**
    - `custom.googleapis.com/gcs_upload_success_total` (CONTADOR)
    - `custom.googleapis.com/gcs_upload_failure_total` (CONTADOR)
  - **Descripción:** Incrementa un contador de éxito o de fallo según el resultado de la operación de subida a Google Cloud Storage. La tasa de éxito (`success_rate`) se puede calcular en la consola de Cloud Monitoring con la fórmula: `success / (success + failure)`.

## 2. Integración en el Flujo de Trabajo

La instancia de `MetricsManager` se crea en el bloque de ejecución principal y se pasa a las clases `RedditExtractor`, `PubSubPublisher` y `GCSArchiver` durante su inicialización.

- **`RedditExtractor`:** Llama a `increment_posts_extracted()` después de una extracción exitosa.
- **`PubSubPublisher`:** Mide el tiempo de la operación de publicación y llama a `record_pubsub_latency()` con el resultado.
- **`GCSArchiver`:** Llama a `increment_gcs_uploads()` con `success=True` o `success=False` dependiendo del resultado de la subida.

## 3. Nueva Dependencia

Se ha añadido la librería `google-cloud-monitoring` al archivo `reddit_ingestion_cf/requirements.txt`.

Esta implementación proporciona una visibilidad detallada del rendimiento y la fiabilidad del pipeline de ingestión de datos, permitiendo la creación de dashboards y alertas en Google Cloud Monitoring.