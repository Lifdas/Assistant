from datetime import datetime, timedelta
from loguru import logger
import os
import json

# api.py
class API:
    def __init__(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.expedition_file = os.path.join(base_dir, 'data', 'expeditions.json')

    def get_datas(self):
            try:
                with open(self.expedition_file, 'r', encoding='utf-8') as file:
                    datas = json.load(file)
                    return datas
            except FileNotFoundError:
                # si le dossier ou le fichier n'existe pas encore
                return {}
            except json.JSONDecodeError:
                # si le JSON est mal formé
                return {}
            
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
    
    def save_expeditions(self, expeditions):
        try:
            with open(self.expedition_file, 'w', encoding='utf-8') as file:
                json.dump(expeditions, file, ensure_ascii=False, indent=4)
            logger.info("Expéditions enregistrées avec succès.")
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement des expéditions : {e}")