# Guía de Configuración de Credenciales de GCP

Este documento explica cómo obtener un archivo de credenciales (clave de cuenta de servicio) de Google Cloud Platform (GCP) y cómo configurarlo en tu entorno local para que las librerías de Google puedan autenticarse.

## Mecanismo de Autenticación: ADC

Las librerías cliente de Google para Python utilizan una estrategia llamada **Application Default Credentials (ADC)**. Buscan credenciales en varios lugares, pero el método más común y explícito para el desarrollo local es a través de una variable de entorno llamada `GOOGLE_APPLICATION_CREDENTIALS`.

Esta variable contiene la ruta a un archivo JSON que representa la identidad de una cuenta de servicio.

---

## Paso 1: Ubicar tu Cuenta de Servicio

1.  **Navega a "Cuentas de servicio"** en la consola de GCP. La puedes encontrar en el menú de navegación bajo `IAM y Administración` > `Cuentas de servicio`.
2.  **Identifica tu cuenta:** Busca la cuenta de servicio que creaste para este proyecto. El nombre debería ser similar a `reddit-ingestion-sa@<tu-proyecto-id>.iam.gserviceaccount.com`.

## Paso 2: Crear y Descargar la Clave JSON

1.  **Haz clic en el nombre** de tu cuenta de servicio para ir a su página de detalles.
2.  **Ve a la pestaña "CLAVES"** (KEYS).
3.  **Crea una nueva clave:**
    *   Haz clic en el botón **"AGREGAR CLAVE"** (ADD KEY).
    *   Selecciona la opción **"Crear nueva clave"** (Create new key).
4.  **Elige el formato JSON:**
    *   Asegúrate de que el tipo de clave seleccionado sea **JSON**.
    *   Haz clic en **"CREAR"** (CREATE).

En este momento, tu navegador descargará automáticamente el archivo de clave JSON. El nombre del archivo será largo y contendrá el ID de tu proyecto.

### **¡ADVERTENCIA DE SEGURIDAD!**

**Este archivo JSON es una credencial privada y poderosa.** Trátalo como una contraseña. **NUNCA** lo subas a un repositorio de Git público o privado. El archivo `.gitignore` que hemos configurado ya previene que los archivos `.json` en la raíz sean subidos, pero es tu responsabilidad mantenerlo seguro.

## Paso 3: Configurar el Archivo `.env`

1.  **Mueve el archivo JSON:** Para mantener el proyecto ordenado, te recomiendo crear una nueva carpeta en la raíz de tu proyecto llamada `secrets`. Mueve el archivo JSON que acabas de descargar a esa carpeta. (Añadiré `secrets/` a tu `.gitignore` para mayor seguridad).

2.  **Actualiza tu archivo `.env`:**
    *   Abre el archivo `.env` que se encuentra en la raíz de tu proyecto.
    *   Busca la línea `GOOGLE_APPLICATION_CREDENTIALS="path/to/your/credentials.json"`.
    *   **Modifica la ruta** para que apunte a la ubicación de tu archivo. Si seguiste la recomendación del paso 1, la línea debería verse así:
        ```
        GOOGLE_APPLICATION_CREDENTIALS="secrets/nombre-de-tu-archivo-clave.json"
        ```
    *   Reemplaza `nombre-de-tu-archivo-clave.json` con el nombre real del archivo que descargaste.

Una vez que guardes el archivo `.env`, tu entorno estará listo. La función `load_dotenv()` en el script cargará esta variable de entorno, y las librerías de GCP la usarán automáticamente para autenticarse.
