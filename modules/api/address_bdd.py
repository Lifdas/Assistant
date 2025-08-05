import json
from loguru import logger
from tools.mysql import Mysql
from datetime import datetime, date

_table = "address"
_users = "users"

class TableAddress(Mysql):

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
        CREATE TABLE `address` (
            `id` INT(10) UNSIGNED NOT NULL AUTO_INCREMENT,
            `nom` VARCHAR(50) NOT NULL,
            `galaxie` INT(11) NOT NULL,
            `secteur` INT(11) NOT NULL,
            `emplacement` int(11) NOT NULL,
            `notes` LONGTEXT DEFAULT NULL COLLATE 'utf8mb4_unicode_ci',
            `lune` BOOLEAN NOT NULL DEFAULT '0',
            `porte` BOOLEAN NOT NULL DEFAULT '0',
            `createdAt` DATETIME NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
            `createdBy` INT(10) UNSIGNED NOT NULL,
            `updatedAt` DATETIME NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
            `updatedBy` INT(10) UNSIGNED NOT NULL DEFAULT '0',
            `deleted` INT(11) NOT NULL DEFAULT '0',
            PRIMARY KEY (`id`) USING BTREE,
            INDEX `createdBy` (`createdBy`) USING BTREE
        )
        COLLATE='utf8mb4_unicode_ci'
        ENGINE=InnoDB
        AUTO_INCREMENT=81
        ;

        """
    
    def format_for_db(self, datas):
        return datas
    
    def format_from_db(self, datas):
        if isinstance(datas, list):
            result = []
            for row in datas:
                result.append({
                    'login': row['login'],
                    'planetes': json.loads(row['planetes'])
                })
        return result
    
    def get_all_planets(self):
        
        query = f"""
            SELECT
            {_users}.login AS login,
            JSON_ARRAYAGG(
                JSON_OBJECT(
                'nom',            {_table}.nom,
                'galaxie',        {_table}.galaxie,
                'secteur',        {_table}.secteur,
                'emplacement',    {_table}.emplacement,
                'notes',          COALESCE({_table}.notes, ''),
                'lune',           {_table}.lune,
                'porte',          {_table}.porte,
                'createdByStr',   {_users}.login
                )
            ) AS planetes
            FROM {_table}
            JOIN users  ON {_users}.id = {_table}.createdBy
            WHERE {_table}.deleted = 0
            GROUP BY {_users}.login;

            """
       
        rs = self.fetch(query)
        if rs:
            return self.format_from_db(rs)
        return []
