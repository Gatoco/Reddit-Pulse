# Documentación: Solución de Problemas de Despliegue

Este documento detalla el proceso de diagnóstico y resolución de los problemas encontrados durante el primer despliegue y prueba de la Cloud Function `reddit-pulse-ingestion`.

## 1. Resumen del Problema Inicial

Tras un despliegue aparentemente exitoso, al invocar la función con `curl`, se obtenía la siguiente respuesta:

```
Internal Server Error: Clients not initialized. Check logs for details.
```

Este era un mensaje de error controlado, programado para ser devuelto si los clientes globales (Reddit, Pub/Sub, etc.) no se inicializaban correctamente. Sin embargo, al revisar los logs en Cloud Logging, no aparecía ningún error de nivel `CRITICAL` con la traza de la excepción, lo que dificultaba el diagnóstico.

## 2. Proceso de Depuración

Se siguió un proceso iterativo para forzar al sistema a revelar la causa raíz del fallo.

### Paso 2.1: Inyección de Logs de Prueba

Se añadió un log de alta severidad (`logging.critical`) al inicio de la función `http_trigger` para verificar si el sistema de logging funcionaba correctamente. Tras redesplegar, este log sí apareció, confirmando que el problema estaba específicamente en el bloque de inicialización de los clientes globales.

### Paso 2.2: Devolución de la Excepción en la Respuesta HTTP

Dado que el log crítico de la excepción no se encontraba fácilmente, se modificó el código para capturar la excepción de inicialización en una variable global. Luego, la función `http_trigger` se adaptó para devolver el mensaje de esta excepción directamente en la respuesta HTTP. **Esta fue la técnica clave que nos permitió ver los errores.**

## 3. Análisis de Causa Raíz y Solución

Gracias a la depuración, se identificaron y solucionaron los siguientes errores en secuencia:

### Error 1: `json.decoder.JSONDecodeError: Expecting value`
- **Causa:** El secreto en Google Secret Manager había sido creado, pero su valor estaba vacío. El código fallaba al intentar parsear un string vacío como JSON.
- **Solución:** Se añadieron las credenciales de Reddit al secreto, creando una nueva versión con el contenido JSON correcto.

### Error 2: `json.decoder.JSONDecodeError: Expecting property name enclosed in double quotes`
- **Causa:** Después de añadir las credenciales, el error cambió. Este nuevo error indicaba que el formato del JSON en el secreto era inválido, específicamente porque las claves (`"client_id"`, etc.) estaban escritas con comillas simples (`'`) en lugar de las comillas dobles (`"`) que exige el estándar JSON.
- **Solución:** Se creó un archivo de plantilla (`reddit_credentials.json.template`) para asegurar el formato correcto. Se actualizó la versión del secreto con el JSON validado.

### Error 3: `NameError: name 'load_dotenv' is not defined`
- **Causa:** Este fue el error final y fue un fallo introducido durante las refactorizaciones para la depuración. Una reescritura incorrecta del archivo `main.py` por parte de la herramienta omitió las sentencias de importación necesarias, causando que la función `load_dotenv()` no estuviera definida al momento de ser llamada.
- **Solución:** Se reconstruyó el archivo `main.py` de forma manual y completa, asegurando que todas las importaciones, clases y funciones estuvieran presentes y en el orden correcto. Se eliminó la lógica de depuración y se desplegó la versión final y limpia.

## 4. Lecciones Aprendidas

- La ausencia de logs de error no siempre significa que no haya errores, sino que pueden no estar siendo capturados o visualizados correctamente.
- Devolver excepciones en la respuesta HTTP es una técnica de depuración poderosa para entornos remotos, pero debe usarse con cuidado y eliminarse en producción.
- La validación de formatos (como JSON) y la correcta secuenciación de las importaciones y ejecuciones son cruciales, especialmente en el arranque de una aplicación.