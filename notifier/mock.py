"""Notificateur fictif — affiche les messages dans le terminal sans rien envoyer."""

from datetime import datetime


def envoyer(numero: str, message: str, canal: str = "whatsapp") -> str:
    horodatage = datetime.now().strftime("%H:%M:%S")
    sep = "-" * 50
    print(f"\n{sep}")
    print(f"[MOCK {canal.upper()}] {horodatage} -> {numero}")
    print(sep)
    print(message)
    print(sep)
    return "MOCK_SID_OK"
