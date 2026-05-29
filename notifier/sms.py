import os


def envoyer(numero: str, message: str, config: dict) -> None:
    """Envoie un SMS via Africa's Talking (couverture Orange/Telecel Burkina Faso)."""
    import africastalking

    username = os.getenv("AT_USERNAME") or config["credentials"]["africastalking_username"]
    api_key  = os.getenv("AT_API_KEY")  or config["credentials"]["africastalking_api_key"]

    if not username or not api_key:
        raise ValueError("AT_USERNAME / AT_API_KEY manquants dans .env")

    africastalking.initialize(username, api_key)
    sms = africastalking.SMS
    # SMS limité à 160 caractères par segment
    sms.send(message[:160], [numero])
