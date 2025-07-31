import os
from dotenv import load_dotenv

class DevelopmentConfig:
    def __init__(self):
        # Charger les variables d'environnement
        load_dotenv()
        
        # Définir les paramètres de configuration
        self.DB_LOCAL_HOST = os.getenv('DB_LOCAL_HOST', 'localhost')
        self.DB_LOCAL_LOGIN = os.getenv('DB_LOCAL_LOGIN', 'root')
        self.DB_LOCAL_PASSWORD = os.getenv('DB_LOCAL_PASSWORD', '')
        self.DB_LOCAL_NAME = os.getenv('DB_LOCAL_NAME', 'database')
        self.DB_LOCAL_PORT = os.getenv('DB_LOCAL_PORT', '3306')
        self.DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    def parms(self, key):
        """Méthode pour récupérer les paramètres de configuration"""
        return getattr(self, key, None)
    
    def __getitem__(self, key):
        """Permet d'utiliser config['KEY'] comme avec Flask"""
        return getattr(self, key, None)