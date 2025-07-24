import os
import sys
import webview
from api import API

def resource_path(relative_path):
    """
    Retourne le chemin absolu vers les ressources,
    qu’on soit en mode dev (script) ou frozen (PyInstaller).
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller crée un dossier temporaire et expose son chemin ici
        base_path = sys._MEIPASS
    else:
        # En dev, on travaille depuis le dossier du script
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

if __name__ == '__main__':
    api = API()
    # Construit le chemin vers frontend/base.html
    index_html = resource_path(os.path.join('frontend', 'base.html'))
    # webview.create_window acceptera file://URL
    window = webview.create_window(
        title='Assistant de Calcul',
        url=f'file://{index_html}',
        js_api=api,
        width=800,
        height=600,
        resizable=True
    )
    webview.start(debug=True)
