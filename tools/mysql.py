import copy, os
import mariadb

from loguru import logger

class Mysql(): 
    """ 
    Classe de gestion des connexion SQL
    Auto remplacement des valeurs pour sécuriser 
    """
    _connection = None
    _last_id = 0
    _rowcount = 0
    _error = ""
    _valid = False
    __create_script = False
    _retry = False

    def __init__(self, create_script=False, configClass=None):
        self.__create_script = create_script
        self.config = configClass

        if configClass:
            self._settings = dict()
            self._settings['HOST'] = configClass.parms('DB_LOCAL_HOST')
            self._settings['LOGIN'] = configClass.parms('DB_LOCAL_LOGIN')
            self._settings['PASSWORD'] = configClass.parms('DB_LOCAL_PASSWORD')
            self._settings['NAME'] = configClass.parms('DB_LOCAL_NAME')
            self._settings['PORT'] = configClass.parms('DB_LOCAL_PORT')
        else:
            # Fallback si pas de config fournie
            self._settings = dict()
            self._settings['HOST'] = os.getenv('DB_LOCAL_HOST', 'localhost')
            self._settings['LOGIN'] = os.getenv('DB_LOCAL_LOGIN', 'root')
            self._settings['PASSWORD'] = os.getenv('DB_LOCAL_PASSWORD', '')
            self._settings['NAME'] = os.getenv('DB_LOCAL_NAME', 'database')
            self._settings['PORT'] = os.getenv('DB_LOCAL_PORT', '3306')

    def set_settings(self, host, login, password, dbName, port=3306):
        self._settings = dict()
        self._settings['HOST'] = host
        self._settings['LOGIN'] = login
        self._settings['PASSWORD'] = password
        self._settings['NAME'] = dbName
        self._settings['PORT'] = port

    @property
    def settings(self):
        try: 
            return self._settings
        except: 
            # Fallback si _settings n'existe pas
            self._settings = dict()
            if self.config:
                self._settings['HOST'] = self.config.parms('DB_LOCAL_HOST')
                self._settings['LOGIN'] = self.config.parms('DB_LOCAL_LOGIN')
                self._settings['PASSWORD'] = self.config.parms('DB_LOCAL_PASSWORD')
                self._settings['NAME'] = self.config.parms('DB_LOCAL_NAME')
                self._settings['PORT'] = self.config.parms('DB_LOCAL_PORT')
            else:
                self._settings['HOST'] = os.getenv('DB_LOCAL_HOST', 'localhost')
                self._settings['LOGIN'] = os.getenv('DB_LOCAL_LOGIN', 'root')
                self._settings['PASSWORD'] = os.getenv('DB_LOCAL_PASSWORD', '')
                self._settings['NAME'] = os.getenv('DB_LOCAL_NAME', 'database')
                self._settings['PORT'] = os.getenv('DB_LOCAL_PORT', '3306')

        return self._settings
              
    def init_connexion(self):
        """init connexion si pas initializé"""
        self._valid = False
        try:
            if self._connection == None:
                connection_params = {
                    'host': self.settings['HOST'],
                    'user': self.settings['LOGIN'],
                    'password': self.settings['PASSWORD'],
                    'database': self.settings['NAME'],
                    'port': int(self.settings['PORT']),                    
                }                
                self._connection = mariadb.connect(**connection_params)      
        except Exception as e:
            logger.critical('Erreur lors de la connection bdd')
            logger.critical(e)
            # Debug des paramètres de connexion si config disponible
            if self.config and hasattr(self.config, 'DEBUG') and self.config.DEBUG:
                logger.critical(self.settings)

    def check_server_connexion(self):
        try: 
            self.init_connexion()
        except mariadb.Error as e:
            logger.exception(e)
            return False
            
        return True
    
    def create_table(self):
        if not self.__create_script:
            logger.critical(self.__create_script)
            return False
        return self.query(self.__create_script)

    def query(self, request):
        """
            Utilise le cursor pour exécuter la requête SQL donnée par request.
            callback est une méthode qui est appelée pour chaque résultat extrait.
            Elle recevra en paramètre le tuple des valeurs des colonnes.
            chunck_size indique le nombre max de résultats récupérés en une fois.
        """
        try: 
            self.init_connexion()
        
            cursor = self._connection.cursor()
            cursor.execute(request)     
            self._connection.commit()
                            
            self._rowcount = cursor.rowcount
            self._valid = self._rowcount != -1

        except mariadb.Error as error:
            logger.debug(request)
            self._error = "Failed to fetch into MySQL table {}".format(error)            
            logger.debug("Failed to fetch into MySQL table {}".format(error))              
                        
            # if error.errno == 1146 and self.__create_script:
            #     # table n'existe pas
            #     logger.debug(f"\r\n\r\n-----------------------------\r\n------- CREATE TABLE --------\r\n-----------------------------\r\n{self.__create_script}")
            #     if not self._retry :
            #         self._retry = True
            #         self._error = ""
            #         self.create_table()
            #         return self.query(request)
        finally:
            self.close_connexion()
        return self

    def fetch(self, request, chunck_size=None, datas=False):        
        """
            Utilise le cursor pour exécuter la requête SQL donnée par request.
            callback est une méthode qui est appelée pour chaque résultat extrait.
            Elle recevra en paramètre le tuple des valeurs des colonnes.
            chunck_size indique le nombre max de résultats récupérés en une fois.
        """        
        try: 
            self.init_connexion()            
            cursor = self._connection.cursor()
            if datas:                   
                cursor.execute(request, datas)
            else:
                cursor.execute(request)
            
            while True:                
                if chunck_size is None:
                    resultats = cursor.fetchall()                    
                else:
                    resultats = cursor.fetchmany(chunck_size)

                if not resultats:
                    break
                
                columns = cursor.description
                result = []
                
                for value in resultats:
                    tmp = {}
                    for (index, column) in enumerate(value):
                        tmp[columns[index][0]] = column
                    result.append(tmp)

                try:
                    cursor.close()
                    self.close_connexion() 
                except Exception as e:
                    logger.trace(e)
                
                return result
        except mariadb.Error as error:
            # table n'existe pas
            logger.debug(str(request).format(datas))
            self._error = "Failed to fetch into MySQL table {}".format(error)
            logger.debug("Failed to fetch into MySQL table {}".format(error))
                        
            if error.errno == 1146 and self.__create_script:
                logger.debug(f"\r\n\r\n-----------------------------\r\n------- CREATE TABLE --------\r\n-----------------------------\r\n{self.__create_script}")
                if not self._retry:
                    self._retry = True
                    self._error = ""
                    self.create_table()
                    return self.fetch(request, chunck_size)

        except Exception as error:
            logger.trace(error)
            self._error = "Exception :  {}".format(error)
            logger.error("Exception :  {}".format(error))
        finally:
            try: 
                if self._connection != None:
                    cursor.close()
                    self.close_connexion()
            except: 
                pass
        
        return False

    def insert_auto(self, table, datas, replace_if_exist=False):
        self._last_id = 0
        self._rowcount = 0
        self._error = ""
        # logger.critical(f"fonction sql insert_auto: table: {table}")
        # logger.critical(f"fonction sql insert_auto: datas: {datas}")
        try:
            self.init_connexion()
            cols = ','.join([f'`{k}`' for k in datas.keys()])
            # Compose a string of placeholders for values
            vals = ','.join(['%s'] * len(datas))
            # Create the SQL statement
            stmt = f'INSERT INTO `{table}` ({cols}) VALUES ({vals})'
            if replace_if_exist:
                stmt = f'REPLACE INTO `{table}` ({cols}) VALUES ({vals})'

            cursor = self._connection.cursor()
            cursor.execute(stmt, tuple(datas.values()))
            self._connection.commit()
            
            self._last_id = cursor.lastrowid
            if replace_if_exist:                
                self._valid = True
            else:
                self._valid = self._last_id > 0
                
        except mariadb.Error as error:
            # table n'existe pas
            if error.errno == 1146 and self.__create_script:
                if not self._retry:
                    self._retry = True
                    self._error = ""
                    self.create_table()
                    return self.insert_auto(table, datas)

            self._error = "Failed to insert into MySQL table {}".format(error)
            logger.info("Failed to insert into MySQL table {}".format(error))
            logger.error(stmt)
        except Exception as error:
            self._error = "Exception :  {}".format(error)
            logger.error("Exception :  {}".format(error))
            logger.debug("Query :  {}".format(stmt))
        finally:
            try: 
                if self._connection != None:
                    cursor.close()
                    self.close_connexion()
            except: 
                pass

        return self
    
    def update_auto(self, table, datas, id=0, key="id", where=False):  
        """mise a jour d'une ligne en bdd suivant l'id"""
        self._last_id = 0
        self._rowcount = -1
        self._error = ""
        try:
            self.init_connexion()

            new_data = copy.copy(datas)
            # cols = ','.join([f'`{k}` = %s' for k in datas.keys()])
            cols = ""
            for k in datas.keys():
                if cols != "":
                    cols += ", "
                    
                if datas[k] == "NOW()":
                    cols += f"`{k}` = NOW()"
                    new_data.pop(k)
                    continue

                cols += f"`{k}` = %s"                
            
            # Create the SQL statement
            stmt = f"UPDATE `{table}` SET {cols} "
            if where: 
                stmt += f"WHERE {where}"
            
            if id:
                if type(id) is list: 
                    id = ','.join([f'{i}' for i in id])
                    stmt += f"WHERE {key} IN ({id})"    
                else:
                    stmt += f"WHERE {key} = '{id}'"
                                
            cursor = self._connection.cursor()
            cursor.execute(stmt, tuple(new_data.values()))
            self._connection.commit()
            self._rowcount = cursor.rowcount
            self._valid = self._rowcount >= 0

        except mariadb.Error as error:
            self._rowcount = -1
            self._error = "Failed to insert into MySQL table {}".format(error)
            logger.error("Failed to insert into MySQL table {}".format(error))
        finally:
            try: 
                if self._connection != None:
                    cursor.close()
                    self.close_connexion()
            except: 
                pass
            
        return self
    
    def delete(self, table, id, key=False):  
        """suppression d'une ligne en bdd suivant l'id"""
        self._last_id = 0
        self._rowcount = 0
        self._error = ""        
        try:
            self.init_connexion()
            
            if key: 
                stmt = f'DELETE FROM `{table}` WHERE {key} = {id}'
            else:
                stmt = f'DELETE FROM `{table}` WHERE id = {id}'
            cursor = self._connection.cursor()
            cursor.execute(stmt)
            self._connection.commit()
            
            self._rowcount = cursor.rowcount            
            self._valid = self._rowcount > 0

        except mariadb.Error as error:
            self._error = "Failed to delete into MySQL table {}".format(error)  
            logger.error("Failed to insert into MySQL table {}".format(error))
        finally:
            cursor.close()
            self.close_connexion()
        return self._rowcount > 0 

    def close_connexion(self):
        # if self._connection.is_connected():    
        if self._connection != None:    
            self._connection.close()
            self._connection = None         
            
    def getLastId(self):
        return self._last_id
    
    def getError(self):
        if len(self._error.strip()) == 0:
            return False
        return self._error
    
    def isValid(self) -> bool:    
        return self._valid

    def isUpdated(self):
        return self._rowcount != -1

    def rowCount(self):
        return self._rowcount