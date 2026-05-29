"""Notificateur WhatsApp via CallMeBot — gratuit, sans compte Twilio.

Activation (1 fois depuis votre telephone) :
  1. Ajoutez +34 644 59 72 05 dans vos contacts WhatsApp
  2. Envoyez-lui : "I allow callmebot to send me messages"
  3. Vous recevez votre cle API par WhatsApp
  4. Mettez la cle dans .env : CALLMEBOT_API_KEY=xxxxxx
"""

import os
import time
import requests
from urllib.parse import quote


API_URL = "https://api.callmebot.com/whatsapp.php"


def envoyer(numero: str, message: str, config: dict) -> None:
    """Envoie un message WhatsApp via CallMeBot.

    numero : format international sans '+' ni espaces, ex: 22670000000
    """
    api_key = os.getenv("CALLMEBOT_API_KEY") or config["credentials"].get("callmebot_api_key", "")

    if not api_key:
        raise ValueError(
            "CALLMEBOT_API_KEY manquant dans .env\n"
            "Activez CallMeBot : envoyez 'I allow callmebot to send me messages' "
            "au +34 644 59 72 05 sur WhatsApp."
        )

    # Nettoyer le numero : enlever +, espaces, tirets
    numero_propre = numero.replace("+", "").replace(" ", "").replace("-", "")

    params = {
        "phone": numero_propre,
        "text": message,
        "apikey": api_key,
    }

    resp = requests.get(API_URL, params=params, timeout=15)

    # CallMeBot retourne 200 meme en cas d'erreur — on verifie le corps
    if resp.status_code != 200 or "error" in resp.text.lower():
        raise RuntimeError(f"Erreur CallMeBot : {resp.text[:200]}")

    # Respecter la limite : 1 message/seconde
    time.sleep(1)
