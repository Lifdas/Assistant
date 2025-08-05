import json
from loguru import logger
from tools.mysql import Mysql
from datetime import datetime, date

_table = "users"

class TableUsers(Mysql):
    
    def __init__(self, configClass=None):     
        super().__init__(create_script=self.create_script(), configClass=configClass)
          
    def create(self, datas):
        return self.insert_auto(table=_table, datas=self.format_for_db(datas))
              
    def update(self, id, datas):
        return self.update_auto(table=_table, id=id, datas=self.format_for_db(datas))      

    def delete(self, id):    
        query = f"DELETE FROM {_table} WHERE {_table}.id = {id}"
        rs = self.query(query)
        return rs
    
    def create_script(self):
        return f"""
        CREATE TABLE `users` (
            `id` INT(10) UNSIGNED NOT NULL AUTO_INCREMENT,
            `login` VARCHAR(50) NOT NULL DEFAULT '' COLLATE 'utf8mb4_unicode_ci',
            `password` VARCHAR(50) NOT NULL DEFAULT '' COLLATE 'utf8mb4_unicode_ci',
            `deleted` INT(11) NOT NULL DEFAULT '0',
            PRIMARY KEY (`id`) USING BTREE
        )
        COLLATE='utf8mb4_unicode_ci'
        ENGINE=InnoDB
        ;

    """

    def get_all_datas(self):
        query = f"SELECT * FROM {_table} WHERE deleted = 0"
        rs = self.fetch(query)
        return self.format_from_db(rs)
    
    def format_for_db(self, datas):
        return datas
    
    def format_from_db(self, datas):
        return datas