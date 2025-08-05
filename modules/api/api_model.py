from datetime import datetime, timedelta
from loguru import logger
from version import __version__
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from modules.users.user_model import User
from modules.api.expeditions_bdd import TableExpeditions
from modules.api.address_bdd import TableAddress

class API():
    def __init__(self, config=None):
        self.config = config
        self._id = 0
        self._login = None
    
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

    def get_datas(self):
        db = TableExpeditions(configClass=self.config)
        datas = db.get_all_datas()  # Passer un paramètre vide pour éviter l'erreur
        return datas
            
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
        if expedition['ressources'] != 'objet' and expedition['ressources'] != 'pirates' and expedition['ressources'] != 'aliens' and expedition['ressources'] != 'rien':
            logger.info("ça boucle")
            try:
                float(expedition['valeur_usm'])
            except ValueError:
                raise ValueError("Les ressources doivent être un nombre valide.")
        return True
        
    # expeditions

    def save_expedition(self, expedition):
        self.check_fields(expedition)
        expedition['createdBy'] = self._id
        db = TableExpeditions(configClass=self.config)
        rs = db.create(expedition)
        return True
    
    def update_expedition(self, expedition):
        self.check_fields(expedition)
        expedition['updatedBy'] = self._id
        db = TableExpeditions(configClass=self.config)
        rs = db.update(expedition['id'], expedition)
        return True
                
    def delete_expedition(self, id):
        db = TableExpeditions(configClass=self.config)
        rs = db.delete(id)
        return True

    #Utilisateurs    
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
            self._id = user['id']
            self._login = user['login']
            return user
        raise ValueError("Identifiants invalides")
    
    #Coordonées
    def create_address(self, address):
        db = TableAddress(configClass=self.config)
        address['createdBy'] = self._id
        rs = db.create(address)
        if rs:
            return True
        raise ValueError("Erreur lors de la création de la planète")

    def get_all_addresses(self):
        db = TableAddress(configClass=self.config)
        addresses = db.get_all_planets()
        return addresses