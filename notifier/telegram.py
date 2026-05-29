"""Notificateur Telegram — gratuit, sans carte bancaire.

Activation (2 min) :
  1. Ouvrez Telegram → cherchez @BotFather → /newbot
  2. Suivez les instructions pour obtenir votre TOKEN
  3. Envoyez /start à votre bot
  4. Visitez https://api.telegram.org/bot<TOKEN>/getUpdates pour trouver votre chat_id
  5. Ajoutez dans .env :
       TELEGRAM_TOKEN=1234567890:ABCdefGHI...
       TELEGRAM_CHAT_ID=123456789
"""

import os
import requests


API_BASE = "https://api.telegram.org/bot{token}/sendMessage"


def envoyer(message: str, config: dict) -> None:
    token   = os.getenv("TELEGRAM_TOKEN")   or config["credentials"].get("telegram_token", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID") or config["credentials"].get("telegram_chat_id", "")

    if not token or not chat_id:
        raise ValueError(
            "TELEGRAM_TOKEN et TELEGRAM_CHAT_ID manquants dans .env\n"
            "Suivez les instructions dans notifier/telegram.py"
        )

    url  = API_BASE.format(token=token)
    resp = requests.post(url, json={
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
    }, timeout=15)

    data = resp.json()
    if not data.get("ok"):
        raise RuntimeError(f"Erreur Telegram : {data.get('description', resp.text)}")


def formatter_offre(offre) -> str:
    titre        = offre["titre"]
    entreprise   = offre["entreprise"] or "—"
    localisation = offre["localisation"] or "—"
    url          = offre["url"]
    source       = offre["source"]

    return (
        f"*Nouvelle offre d'emploi*\n"
        f"--------------------\n"
        f"*{titre}*\n"
        f"Entreprise : {entreprise}\n"
        f"Lieu : {localisation}\n"
        f"Source : {source}\n"
        f"--------------------\n"
        f"{url}"
    )
