import os
import praw
from google.cloud import pubsub_v1
from google.cloud import storage

# --- Cargar Credenciales de Reddit (desde variables de entorno) ---
# Asegúrate de haber configurado las siguientes variables de entorno
# en tu sistema o en el entorno de ejecución de la Cloud Function:
# REDDIT_CLIENT_ID: El client ID de tu aplicación de Reddit.
# REDDIT_CLIENT_SECRET: El client secret de tu aplicación de Reddit.
# REDDIT_USER_AGENT: Un user agent descriptivo (ej. "web:com.example.my-app:v1.0.0 (by /u/yourusername)").

reddit_client_id = os.environ.get("REDDIT_CLIENT_ID")
reddit_client_secret = os.environ.get("REDDIT_CLIENT_SECRET")
reddit_user_agent = os.environ.get("REDDIT_USER_AGENT")

# Inicializar la instancia de PRAW
reddit = praw.Reddit(
    client_id=reddit_client_id,
    client_secret=reddit_client_secret,
    user_agent=reddit_user_agent,
)
