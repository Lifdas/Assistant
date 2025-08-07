from datetime import datetime, timedelta
import json
import os
import sys
from loguru import logger
from tools.config import DevelopmentConfig
from version import __version__
import requests
import webview
from pathlib import Path

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from modules.users.user_model import User
from modules.api.expeditions_bdd import TableExpeditions
from modules.api.address_bdd import TableAddress

class API():
    def __init__(self, config=None):
        self.config = config
        self._user_id = 0
        self._login = None
        self.child_windows = []  # Stocker les références des fenêtres enfants
           
    
    def get_version(self):
        return __version__

    def fetch_latest(self):
        """Récupère latest.json depuis ton serveur de mises à jour."""
        url = 'http://217.154.121.75/updates/latest.json'
        session = requests.Session()
        retries = Retry(
            total=2,
            backoff_factor=0.3,
            status_forcelist=[502, 503, 504],
            raise_on_status=False
        )
        session.mount('http://', HTTPAdapter(max_retries=retries))

        try:
            res = session.get(url, timeout=(5, 10))
            res.raise_for_status()
            return res.json()
        except Exception as e:
            # On renvoie une structure uniforme en cas d’erreur
            return {'error': str(e)}


            
    def calculer_delai(self, voulu: float, actuel: float, gagne_par_heure: float):
        voulu = float(voulu)
        actuel = float(actuel)
        gagne_par_heure = float(gagne_par_heure)
        reste = voulu - actuel
        if reste > 0 and gagne_par_heure > 0:
            # minutes totales nécessaires
            minutes_totales = (reste / gagne_par_heure) * 60

            # décomposition jours/heures/minutes
            jours   = int(minutes_totales // (24 * 60))
            heures  = int((minutes_totales - jours * 24 * 60) // 60)
            minutes = int((minutes_totales - jours * 24 * 60 - heures * 60) + 0.999)

            parts = []
            if jours   > 0: parts.append(f"{jours} j")
            if heures  > 0: parts.append(f"{heures} h")
            if minutes > 0: parts.append(f"{minutes} min")
            temps_necessaire = " ".join(parts) or "0 min"

            # date de fin
            now    = datetime.now()
            finish = now + timedelta(minutes=minutes_totales)
            date_fin = finish.strftime("%d/%m/%Y %H:%M")
        else:
            temps_necessaire = "0 min"
            date_fin         = "--/--/---- --:--"

        return {
            "temps_necessaire": temps_necessaire,
            "date_fin": date_fin
        }
    
    def calculer_date_future(self, jours: int, heures: int, minutes: int):
        """
        À partir d'un intervalle j/h/m, renvoie la date future 'JJ/MM/AAAA HH:MM'
        """
        now    = datetime.now()
        delta  = timedelta(days=jours, hours=heures, minutes=minutes)
        finish = now + delta
        return finish.strftime("%d/%m/%Y %H:%M")
    
    def check_fields(self, expedition):
        logger.critical(expedition)
        if 'date_expedition' not in expedition or not expedition['date_expedition']:
            raise ValueError("La date d'expédition est obligatoire.")
        if 'secteur' not in expedition or not expedition['secteur']:
            raise ValueError("Le secteur est obligatoire.")

        return True
    
   ###################
   ### Expeditions ###
   ###################
    def get_datas(self):
        db = TableExpeditions(configClass=self.config)
        expeditions = db.get_all_datas() 
        echecs = ['aliens', 'pirates', 'rien']

        joueurs_map = {}
        for row in expeditions:
            login = row['login']
            if login not in joueurs_map:
                joueurs_map[login] = {'login': login, 'total': 0, 'exp_reussie': 0}
            joueur = joueurs_map[login]

            if row['ressources'] not in echecs:
                joueur['exp_reussie'] += 1
            joueur['total'] += 1

        for joueur in joueurs_map.values():
            taux = (joueur['exp_reussie'] * 100) / joueur['total'] if joueur['total'] else 0
            joueur['rate'] = round(taux, 2)

        #les datas des joueurs
        joueurs = list(joueurs_map.values())
        #les dernières expeiditions selon les secteurs
        latest_expeditions = db.get_latest_expeditions()

        datas = {}
        datas['expeditions'] = latest_expeditions
        datas['rate_success'] = joueurs

        return datas

    def save_expedition(self, expedition):
        self.check_fields(expedition)
        expedition['createdBy'] = self._user_id
        db = TableExpeditions(configClass=self.config)
        rs = db.create(expedition)
        return True
    
    def update_expedition(self, expedition):
        self.check_fields(expedition)
        expedition['updatedBy'] = self._user_id
        db = TableExpeditions(configClass=self.config)
        rs = db.update(expedition['id'], expedition)
        return True
                
    def delete_expedition(self, id):
        db = TableExpeditions(configClass=self.config)
        rs = db.delete(id)
        return True

   ##################
   ## Utilisateurs ##
   ##################

    def get_users_list(self):
        logger.info('api déclenchée')
        user_model = User(config=self.config)
        users = user_model.get_users_list()
        return users
    
    def create_user(self, new_login, new_password):
        user_model = User(config=self.config)
        rs = user_model.create_user(new_login=new_login, new_password=new_password)
        if rs:
            return rs
        raise ValueError("Erreur lors de la création de l'utilisateur")
    
    def login(self, login, password):
        user_model = User(config=self.config)
        user = user_model.login(login=login, password=password)
        if user:
            self._user_id = user['id']
            self._login = user['login']
            return {'error': False, 'user': user} 
        raise ValueError("Identifiants invalides")
    
   ##################
   ### Coordonées ###
   ##################

    # création d'une fenêtre enfant
    def open_planet_window(self, planet_id):
        project_root = Path(__file__).resolve().parents[2]
        planete_html = project_root / "frontend" / "pages" / "planete.html"
        file_uri = planete_html.resolve().as_uri()
        url      = f"{file_uri}#id={planet_id}"

        webview.create_window(
            title=f"Détails planète {planet_id}",
            url=url,
            js_api=self,
            width=560,
            height=765,
            resizable=True
        )

    def _get_main_window(self):
        """Trouve la fenêtre principale de manière dynamique"""
        try:
            for window in webview.windows:
                if "Assistant d'optimisation" in window.title:
                    return window
        except Exception as e:
            print(f"Erreur lors de la recherche de la fenêtre principale: {e}")
        return None

    #Get planetes
    def get_all_addresses(self):
        db = TableAddress(configClass=self.config)
        addresses = db.get_all_planets()
        return addresses
    
    def get_planet(self, planet_id):
        db = TableAddress(configClass=self.config)
        address = db.get_planet(planet_id)
        return address
    
    #Create planetes
    def create_address(self, address):
        db = TableAddress(configClass=self.config)
        address['createdBy'] = self._user_id
        rs = db.create(address)
        if rs:
            self.notify_planet_created(address)
            return True
        raise ValueError("Erreur lors de la création de la planète")
    
    def notify_planet_created(self, planet_data):
        """Notifie la fenêtre parent qu'une planète a été créée"""
        try:
            main_window = self._get_main_window()  # ← Récupération paresseuse

            if main_window:
                js_code = f"""
                    if (window.handlePlanetCreate) {{
                        window.handlePlanetCreate({json.dumps(planet_data)});
                    }}
                """
                main_window.evaluate_js(js_code)
                return True
        except Exception as e:
            print(f"Erreur notification création: {e}")
        return False
    
    #update planetes
    def update_planet(self, datas):
        db = TableAddress(configClass=self.config)
        datas['updatedBy'] = self._user_id
        db.update(datas['id'], datas)
        if not db.isValid():
            raise ValueError("Modification non sauvegardée en base de données")
        self.notify_planet_updated(datas['id'], datas)
        return True
    
    def notify_planet_updated(self, planet_id, updated_data):
        """Notifie la fenêtre parent qu'une planète a été mise à jour"""
        try:
            main_window = self._get_main_window()  # ← Récupération paresseuse
            if main_window:
                js_code = f"""
                    if (window.handlePlanetUpdate) {{
                        window.handlePlanetUpdate({planet_id}, {json.dumps(updated_data)});
                    }}
                """
                main_window.evaluate_js(js_code)
                return True
        except Exception as e:
            print(f"Erreur notification mise à jour: {e}")
        return False


    
    #Delete planetes
    def delete_planet(self, planet_id):
        db = TableAddress(configClass=self.config)
        datas = {}
        datas['deleted'] = True
        db.update(planet_id, datas)
        if not db.isValid():
            raise ValueError('Suppression échouée en base de données')
        self.notify_planet_deleted(planet_id)
        return True
    
    def notify_planet_deleted(self, planet_id):
        """Notifie la fenêtre parent qu'une planète a été supprimée"""
        try:
            main_window = self._get_main_window()  # ← Récupération paresseuse

            if main_window:
                js_code = f"""
                    if (window.handlePlanetDelete) {{
                        window.handlePlanetDelete({planet_id});
                    }}
                """
                main_window.evaluate_js(js_code)
                return True
        except Exception as e:
            print(f"Erreur notification suppression: {e}")
        return False
    