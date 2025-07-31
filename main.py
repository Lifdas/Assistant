import os
import sys
import webview

from dotenv import load_dotenv
from tools.config import DevelopmentConfig
from api_model import API

def resource_path(relative_path):
    """
    Résout le chemin vers les ressources
    que ce soit en dev ou dans le bundle PyInstaller.
    """
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

if __name__ == '__main__':
    # Charger les variables d'environnement
    load_dotenv()
    
    # Créer l'instance de configuration
    config = DevelopmentConfig()
    
    # Créer l'API avec la configuration
    api = API(config)
    
    index_html = resource_path('frontend/base.html')
    webview.create_window(
        title="Assistant d'optimisation",
        url=f'file://{index_html}',
        js_api=api,
        width=1100,
        height=600,
        resizable=False
    )
    webview.start(debug=False)