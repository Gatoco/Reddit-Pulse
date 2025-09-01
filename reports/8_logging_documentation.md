# Documentación: Logging Estructurado

Este documento describe la implementación de un sistema de logging estructurado en formato JSON en el script `reddit_ingestion_cf/main.py`.

## 1. Configuración del Logger

Se ha añadido una configuración centralizada para el módulo `logging` de Python al inicio del script.

### `JsonFormatter`
- Se ha creado una clase `JsonFormatter` personalizada que hereda de `logging.Formatter`.
- Su propósito es formatear cada registro de log como un objeto JSON.
- Cada log JSON contiene información clave como:
  - `timestamp`: Fecha y hora del evento.
  - `level`: Nivel de severidad (INFO, WARNING, ERROR, CRITICAL).
  - `message`: El mensaje del log.
  - `module`, `function`, `line`: El contexto exacto en el código donde se originó el log.
  - `exception`: Información de la traza de la excepción si el log fue de un error.

### `setup_logging()`
- Una función que se ejecuta al importar el módulo.
- Configura el logger raíz para que utilice el `JsonFormatter`, asegurando que todos los logs generados en el script sigan el formato JSON.

## 2. Niveles de Log Utilizados

Se han reemplazado todas las sentencias `print()` por llamadas al logger con niveles de severidad apropiados:

- **`logging.INFO`**: Utilizado para registrar eventos de operaciones normales y exitosas.
  - *Ejemplos:* "Instancia de PRAW creada", "Mensaje publicado con ID...", "Archivo subido a GCS...".
- **`logging.WARNING`**: Utilizado para situaciones que no son errores fatales pero que requieren atención.
  - *Ejemplos:* "Error de red, reintentando...", "Enviando mensaje a la Dead-Letter Queue...".
- **`logging.ERROR`**: Utilizado para fallos que impiden que una operación específica se complete, pero que no detienen la aplicación.
  - *Ejemplos:* "Error de validación en un post", "Fallo final en la subida a GCS después de reintentos".
- **`logging.CRITICAL`**: Utilizado para errores graves que impiden el funcionamiento normal de una parte importante del proceso.
  - *Ejemplos:* "Fallo al procesar un subreddit completo", "Excepción no controlada en el flujo principal".

Este sistema de logging estructurado es fundamental para la observabilidad en producción, ya que permite que los logs sean fácilmente ingeridos, parseados y analizados por servicios como Google Cloud Logging.