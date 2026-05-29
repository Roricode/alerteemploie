import os
from twilio.rest import Client


def _client(config: dict) -> tuple[Client, str]:
    sid   = os.getenv("TWILIO_ACCOUNT_SID")   or config["credentials"]["twilio_account_sid"]
    token = os.getenv("TWILIO_AUTH_TOKEN")     or config["credentials"]["twilio_auth_token"]
    from_ = os.getenv("TWILIO_WHATSAPP_FROM") or config["credentials"]["twilio_whatsapp_from"]
    if not sid or not token:
        raise ValueError("TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN manquants dans .env")
    return Client(sid, token), from_


def envoyer(numero: str, message: str, config: dict) -> str:
    """Envoie un message WhatsApp. Retourne le SID Twilio du message."""
    client, from_ = _client(config)
    to = f"whatsapp:{numero}" if not numero.startswith("whatsapp:") else numero
    msg = client.messages.create(body=message, from_=from_, to=to)
    return msg.sid


def formatter_offre(offre) -> str:
    """Formate une offre (sqlite3.Row ou dict) en message WhatsApp lisible."""
    titre       = offre["titre"]
    entreprise  = offre["entreprise"] or "—"
    localisation = offre["localisation"] or "—"
    url         = offre["url"]
    source      = offre["source"]

    return (
        f"Nouvelle offre d'emploi\n"
        f"--------------------\n"
        f"*{titre}*\n"
        f"Entreprise : {entreprise}\n"
        f"Lieu : {localisation}\n"
        f"Source : {source}\n"
        f"--------------------\n"
        f"{url}"
    )
