# Guía de Configuración de Recursos en GCP

Este documento proporciona una guía paso a paso para configurar los recursos necesarios en la Google Cloud Platform (GCP) para el proyecto Reddit-Pulse, utilizando la consola web de GCP.

---

## 1. Configuración de Pub/Sub

### 1.1. Crear un Tópico de Pub/Sub

Un tópico de Pub/Sub es un canal nombrado al que enviamos los mensajes (en nuestro caso, los posts de Reddit).

1.  **Navega a Pub/Sub:** En la consola de GCP, usa la barra de búsqueda o el menú de navegación para ir a `Pub/Sub`.
2.  **Crea el Tópico:**
    *   Haz clic en **"Crear Tópico"**.
    *   En el campo **"ID del Tópico"**, ingresa `reddit-posts`.
    *   Deja las demás opciones con sus valores por defecto (ej. esquema de encriptación gestionado por Google).
    *   Haz clic en **"Crear"**.

### 1.2. Crear una Suscripción de Prueba

Una suscripción nos permite "escuchar" los mensajes enviados a un tópico. Crearemos una para poder verificar que los mensajes llegan correctamente.

1.  **Navega a Suscripciones:** Dentro de la sección de Pub/Sub, ve a la pestaña **"Suscripciones"**.
2.  **Crea la Suscripción:**
    *   Haz clic en **"Crear Suscripción"**.
    *   En el campo **"ID de la Suscripción"**, ingresa `reddit-posts-test`.
    *   En la sección **"Selecciona un tópico de Cloud Pub/Sub"**, elige el tópico `reddit-posts` que acabas de crear.
    *   Deja los demás valores por defecto (Tipo de entrega: `Pull`, Plazo de confirmación: `10 segundos`).
    *   Haz clic en **"Crear"**.

---

## 2. Configuración de Cloud Storage

### 2.1. Crear un Bucket de Cloud Storage

Un bucket es un contenedor para almacenar objetos (archivos) en Cloud Storage. Lo usaremos como nuestro Data Lake en la capa "raw".

1.  **Navega a Cloud Storage:** En la consola de GCP, busca o navega a `Cloud Storage`.
2.  **Crea el Bucket:**
    *   Haz clic en **"Crear Bucket"**.
    *   **Nombre:** Ingresa `reddit-pulse-data-lake-raw`. **Importante:** Los nombres de los buckets deben ser únicos a nivel global en todo Google Cloud. Si este nombre ya está en uso, puedes añadirle un sufijo único (ej. `reddit-pulse-data-lake-raw-TU_ID_UNICO`).
    *   **Ubicación:** Elige un tipo de ubicación (`Region`) y selecciona la región que prefieras (ej. `us-central1`).
    *   **Clase de Almacenamiento:** Deja la opción por defecto, `Standard`.
    *   **Control de Acceso:** Elige `Uniforme`.
    *   Deja las demás opciones por defecto y haz clic en **"Crear"**.

### 2.2. Configurar Política de Ciclo de Vida (Lifecycle)

Esta política eliminará automáticamente los archivos del bucket después de un tiempo determinado, ayudando a gestionar costos.

1.  **Selecciona tu Bucket:** En la lista de buckets de Cloud Storage, haz clic en el nombre `reddit-pulse-data-lake-raw`.
2.  **Ve a la Pestaña de Ciclo de Vida:** Haz clic en la pestaña **"CICLO DE VIDA"**.
3.  **Añade una Regla:**
    *   Haz clic en **"Añadir una regla"**.
    *   En **"1. Seleccionar una acción"**, elige **"Borrar"**.
    *   Haz clic en **"Continuar"**.
    *   En **"2. Seleccionar condiciones del objeto"**, elige **"Antigüedad"**.
    *   En el campo de texto, ingresa `30` (días).
    *   Haz clic en **"Continuar"** y luego en **"Guardar"** para activar la regla.

---

## 3. Verificación de Permisos (IAM)

Es crucial verificar que la cuenta de servicio (`reddit-ingestion-sa`) que usará nuestra Cloud Function tenga los permisos correctos.

1.  **Navega a IAM:** Ve a la sección `IAM y Administración` > `IAM`.
2.  **Busca la Cuenta de Servicio:** En la lista de principales, busca tu cuenta de servicio. Su nombre será similar a `reddit-ingestion-sa@<tu-proyecto-id>.iam.gserviceaccount.com`.
3.  **Verifica los Roles:** En la columna **"Rol"** para esa cuenta de servicio, asegúrate de que tenga asignados los siguientes roles:
    *   `Editor de Pub/Sub` (o `Publicador de Pub/Sub` que es más restrictivo y preferible).
    *   `Creador de objetos de Storage`.

Si los roles no están asignados, puedes hacer clic en el ícono del lápiz (Editar principal) para añadirlos.

### Alternativa: Verificar en el Recurso

También puedes ver los permisos directamente en el tópico y en el bucket:

*   **Para el Tópico:**
    1.  Ve a `Pub/Sub` > `Tópicos` y haz clic en `reddit-posts`.
    2.  A la derecha, busca un panel de información. Haz clic en **"PERMISOS"**.
    3.  Asegúrate de que tu cuenta de servicio (`reddit-ingestion-sa@...`) aparezca en la lista con el rol `Publicador de Pub/Sub`.
*   **Para el Bucket:**
    1.  Ve a `Cloud Storage` > `Buckets` y haz clic en `reddit-pulse-data-lake-raw`.
    2.  Ve a la pestaña **"PERMISOS"**.
    3.  Verifica que tu cuenta de servicio tenga un rol que le permita escribir objetos, como `Creador de objetos de Storage`.
