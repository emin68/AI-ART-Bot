# utils_env.py
from dotenv import load_dotenv
import os

def load_env():
    """Charge les variables d'environnement depuis le fichier .env"""
    env_path = ".env"
    if not os.path.exists(env_path):
        raise FileNotFoundError(f"Fichier .env introuvable à la racine du projet")
    load_dotenv(env_path)
    print("✅ Variables d'environnement chargées avec succès.")

def get_env_var(key: str, default=None):
    """Récupère une variable du .env"""
    return os.getenv(key, default)
