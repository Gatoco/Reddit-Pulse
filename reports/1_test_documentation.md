# Documentación de Pruebas: RedditExtractor

Este documento detalla las pruebas unitarias implementadas para el script `reddit_ingestion_cf/main.py`, enfocándose en la clase `RedditExtractor` y las funciones auxiliares.

**Frameworks y Librerías Utilizadas:**
- **Pytest:** Framework principal para la ejecución de pruebas.
- **unittest.mock:** Para simular (`mockear`) las respuestas de la API de Reddit (PRAW) y controlar las dependencias externas como las variables de entorno.

---

## Resumen de Casos de Prueba

El archivo `tests/test_reddit_extractor.py` contiene los siguientes casos de prueba:

### 1. `test_format_post_data`
- **Propósito:** Verificar que la función estática `RedditExtractor.format_post_data` convierte correctamente un objeto `Submission` (simulado) de PRAW al formato de diccionario definido en nuestro esquema de datos.
- **Verifica:**
    - Que las claves del diccionario son las correctas (`id`, `title`, `author`, etc.).
    - Que los valores se asignan correctamente.
    - Que el campo `created_utc` (un timestamp) se convierte a una cadena de texto en formato ISO.

### 2. `test_format_post_data_deleted_author`
- **Propósito:** Asegurar que el formateo de datos no falla si un post fue escrito por un usuario que luego eliminó su cuenta.
- **Verifica:**
    - Que si el atributo `author` del post es `None`, el campo `author` en el diccionario resultante es la cadena de texto `"None"`, evitando errores en el procesamiento posterior.

### 3. `test_extract_posts`
- **Propósito:** Probar la lógica principal de extracción de la clase `RedditExtractor` sin hacer una llamada real a la API de Reddit.
- **Verifica:**
    - Que se instancia un cliente de `praw.Reddit`.
    - Que se llama al método `subreddit()` con el nombre correcto del subreddit.
    - Que la función devuelve una lista de diccionarios con los datos de los posts formateados.

### 4. `test_load_credentials_failure`
- **Propósito:** Garantizar que el sistema falle de manera predecible si no se han configurado las credenciales de la API de Reddit.
- **Verifica:**
    - Que se lanza una excepción `ValueError` cuando las variables de entorno (`REDDIT_CLIENT_ID`, etc.) no están disponibles.
    - Esta prueba simula un entorno "limpio" para asegurar que la validación funciona de forma aislada.

### 5. `test_load_credentials_success`
- **Propósito:** Confirmar que la función `load_reddit_credentials` lee y devuelve correctamente las credenciales cuando las variables de entorno están presentes.
- **Verifica:**
    - Que el diccionario devuelto contiene los valores correctos extraídos del entorno.
