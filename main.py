import os
import sys
import webview

from dotenv import load_dotenv
from tools.config import DevelopmentConfig
from modules.api.api_model import API
from version import __version__


def resource_path(relative_path):
    """ adapté PyInstaller """
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base, relative_path)

def get_version():
    """ Récupère la version de l'application """
    return __version__

if __name__ == '__main__':
    # Charger les variables d'environnement
    dotenv_path = resource_path('.env')
    load_dotenv(dotenv_path)
    # Créer l'instance de configuration
    config = DevelopmentConfig()
    
    # Créer l'API avec la configuration
    api = API(config)
    
    index_html = resource_path('frontend/base.html')
    webview.create_window(
        title="Assistant d'optimisation",
        url=f'file://{index_html}',
        js_api=api,
        width=1300,
        height=700,
        resizable=False
    )
    webview.start(debug=False)