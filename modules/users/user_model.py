import  bcrypt, time
from loguru import logger
from modules.users.user_bdd import TableUsers


regex_email = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
pattern = r'^(?=(?:.*[\W_]){2,})(?=.*[A-Z]).*$'
regex_password = r'^(?=(.*[!@#$%^&*(),.?":{}|<>]){2})(?=.*[A-Z]).*$'


class User():
    """ id = id user"""

    def __init__(self, config=None):
        self.config = config
        self._id = 0
    
    def get_users_list(self):
        db = TableUsers()
        users = db.get_all_datas()
        logger.debug(f"get_users_list: {users}")
        return users
    
    def check_data(self, datas):
        """ Vérification des données utilisateur """
        logger.critical(datas)
        if 'login' not in datas or not datas['login']:
            raise ValueError("Le login est obligatoire.")
        if 'password' not in datas or not datas['password']:
            raise ValueError("Le mot de passe est obligatoire.")

        return True
    
    def create_user(self, new_login, new_password):
        """ Crée un nouvel utilisateur """
        datas = {
            "login": new_login,
            "password": new_password,
            "deleted": 0
        }
        self.check_data(datas)
        db = TableUsers(configClass=self.config)
        db.create(datas)
        id = db.getLastId()
        if not db.isValid():
            raise ValueError("Utilisateur non créé en base de données")
        return {"rs": True, 
                "user": {
                    "id":   id,
                    "login": datas["login"],
                    }
                }
      
    def login(self, login, password):
        """ Authentifie un utilisateur """
        db = TableUsers(configClass=self.config)
        users = db.get_all_datas()
        for user in users:
            if user['login'] == login and user['password'] == password:
                self._id = user['id']
                return {"id": self._id, "login": user['login']}
        
        raise ValueError("Identifiants invalides")
   


    def search(self, searchKeys=False):
        """ recherche dans la bdd local"""
        searchKeysFiltered = dict()
        # Filtrage des clés venant du front
        if searchKeys :
            for k,v in searchKeys.items():
                if len(str(v).strip()) > 0 :
                    searchKeysFiltered[k] = v        

        # if not 'deleted' in searchKeys:
        #     searchKeysFiltered['deleted'] = 0

        db = Db()
        rs = db.search(filters=searchKeysFiltered)
        if not rs :
            rs = []

        return rs
    
