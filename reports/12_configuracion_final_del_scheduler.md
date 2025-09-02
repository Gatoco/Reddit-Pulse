# Documentación: Configuración Final del Scheduler

Este documento detalla el último paso de la configuración del proyecto: la creación del job en Cloud Scheduler para automatizar la ejecución del pipeline.

## 1. Objetivo

El objetivo era crear un trabajo programado (`cron job`) que invocara el disparador HTTP de la Cloud Function `reddit-pulse-ingestion` de forma periódica y automática.

## 2. Error Inicial y Solución

Al ejecutar el primer intento del comando para crear el job, se encontró el siguiente error:

```
ERROR: (gcloud.scheduler.jobs.create.http) Please use the location flag to manually specify a location.
```

-   **Causa del Error:** A diferencia de otros servicios de GCP que pueden inferir la región, Cloud Scheduler requiere que se le especifique explícitamente la ubicación (`location`) donde debe residir el job. Es una medida de claridad para asegurar que los recursos se crean en la región deseada.
-   **Solución:** Se corrigió el comando añadiendo el flag `--location`. Se eligió la región `us-central1` para que el job de Scheduler se ejecute en la misma ubicación que la Cloud Function, lo cual es una buena práctica para reducir la latencia de red.

El comando corregido y final fue:
```bash
gcloud scheduler jobs create http reddit-ingestion-job --schedule "*/10 * * * *" --location="us-central1" --uri "URL_DE_TU_FUNCION" ...
```

## 3. Resultado Exitoso

La ejecución del comando corregido arrojó una descripción completa del job creado, confirmando el éxito de la operación. Los puntos clave del resultado son:

-   **`name: .../jobs/reddit-ingestion-job`**: El job se ha creado con el nombre especificado.
-   **`state: ENABLED`**: El job está activo y comenzará a ejecutarse según la programación.
-   **`schedule: '*/10 * * * *'`**: La frecuencia está correctamente configurada para ejecutarse cada 10 minutos.
-   **`timeZone: America/Mexico_City`**: La zona horaria se ha establecido correctamente.
-   **`retryConfig: { retryCount: 3, minBackoffDuration: 60s }`**: La política de reintentos está configurada como se solicitó.
-   **`uri: ...`**: La URL de destino es la correcta para nuestra Cloud Function.

## 4. Conclusión del Proyecto

Con la creación exitosa de este job en Cloud Scheduler, el proyecto **Reddit Pulse** ha alcanzado su estado final y deseado:

-   **Un pipeline de datos funcional** que extrae, transforma y carga datos.
-   **Seguro**, gracias al uso de Secret Manager.
-   **Observable**, a través de logging estructurado y métricas personalizadas.
-   **Robusto**, con un sistema de reintentos y "dead-letter queue".
-   **Totalmente automatizado**, gracias a Cloud Scheduler.