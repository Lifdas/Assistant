import json
from loguru import logger
from tools.mysql import Mysql
from datetime import datetime, date, timedelta

_table = "expeditions"
_users = "users"

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
            `date_expedition` DATETIME NOT NULL,
            `secteur` INT(11) NOT NULL,
            `ressources` VARCHAR(50) NULL DEFAULT '' COLLATE 'utf8mb4_unicode_ci',
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
        if 'new_expedition' in datas:
            del datas['new_expedition']
        if 'editing' in datas:
            del datas['editing']
        if 'has_changed' in datas:
            del datas['has_changed']
        if 'login' in datas:
            del datas['login']
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

        return formatted

    
    def get_all_datas(self, datas=None):
        query = f"""
            SELECT {_table}.id, {_table}.date_expedition, {_table}.secteur, {_table}.ressources, {_users}.login
            FROM {_table}
            LEFT JOIN {_users} ON {_users}.id = {_table}.createdBy
            WHERE {_table}.deleted = 0
            ORDER BY {_table}.date_expedition DESC
            """
        rs = self.fetch(query)
        return self.format_from_db(rs)
    
    def get_latest_expeditions(self, secteur=False):
        where_str= ""
        if secteur:
            where_str = f" AND {_table}.secteur = {secteur}"

        query = f"""
            SELECT  {_table}.id, {_table}.date_expedition, {_table}.secteur, {_table}.ressources, {_users}.login
            FROM {_table}
            JOIN( 
                SELECT 
                secteur,
                MAX(date_expedition) AS max_date
                FROM {_table}
                WHERE deleted = 0
                GROUP BY secteur
                
            ) AS time
            ON {_table}.secteur = time.secteur
            AND {_table}.date_expedition = time.max_date

            LEFT JOIN {_users} ON {_users}.id = {_table}.createdBy

            WHERE {_table}.deleted = 0 {where_str}
            ORDER BY {_table}.secteur

        """
        rs = self.fetch(query)
        return rs
    
    