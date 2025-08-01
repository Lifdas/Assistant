import json
from loguru import logger
from tools.mysql import Mysql
from datetime import datetime, date

_table = "expeditions"

class TableExpeditions(Mysql):
    
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
        CREATE TABLE `expeditions` (
            `id` INT(10) UNSIGNED NOT NULL AUTO_INCREMENT,
            `date_expedition` DATE NOT NULL,
            `secteur` INT(11) NOT NULL,
            `ressources` VARCHAR(50) NULL DEFAULT '' COLLATE 'utf8mb4_unicode_ci',
            `valeur_usm` INT(11) NULL DEFAULT NULL,
            `createdBy` INT(11) NOT NULL DEFAULT '0',
            `createdAt` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            `updatedBy` INT(11) NOT NULL DEFAULT '0',
            `updatedAt` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            `deleted` INT(11) NOT NULL DEFAULT '0',
            PRIMARY KEY (`id`) USING BTREE
        )
        COLLATE='utf8mb4_unicode_ci'
        ENGINE=InnoDB
        AUTO_INCREMENT=11
        ;
        """
    
    def format_for_db(self, datas):
        if 'new_expedition' in datas:
            del datas['new_expedition']
        if 'editing' in datas:
            del datas['editing']
        if 'has_changed' in datas:
            del datas['has_changed']
        return datas
    
    def format_from_db(self, datas):
        formatted = []
        for row in datas:
            d = row.get('date_expedition')
            if isinstance(d, datetime):
                try:
                    iso = d.isoformat()
                    row['date_expedition'] = iso[:16]  # Format to 'YYYY-MM-DD HH:MM'
                except ValueError:
                    pass
            row['has_changed'] = False
            row['editing'] = False
            formatted.append(row)

        # 3) Renvoie la liste prête à être sérialisée en JSON
        return formatted

    
    def get_all_datas(self, datas=None):
        query = f"""
            SELECT {_table}.id, {_table}.date_expedition, {_table}.secteur, {_table}.ressources, {_table}.valeur_usm, users.login
            FROM {_table}
            LEFT JOIN users ON users.id = {_table}.createdBy
            WHERE {_table}.deleted = 0
            ORDER BY {_table}.date_expedition DESC
            """
        rs = self.fetch(query)
        return self.format_from_db(rs)