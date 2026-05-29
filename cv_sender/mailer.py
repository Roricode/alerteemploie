import os
import smtplib
from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path


def envoyer(
    offre: object,
    email_dest: str,
    config: dict,
    cv_path: Path | None = None,
) -> None:
    """Envoie le CV par email (Gmail SMTP SSL).

    Lit les credentials depuis .env (GMAIL_APP_PASSWORD) ou config.yaml.
    """
    cv_config = config["cv"]
    chemin_cv = cv_path or Path(cv_config["fichier"])

    if not chemin_cv.exists():
        raise FileNotFoundError(f"CV introuvable : {chemin_cv}")

    corps = _lire_template(cv_config, offre)
    objet = cv_config["objet_template"].format(titre=offre["titre"])
    expediteur = cv_config["email_expediteur"]
    password = os.getenv("GMAIL_APP_PASSWORD") or cv_config.get("gmail_app_password", "")

    if not password:
        raise ValueError(
            "GMAIL_APP_PASSWORD manquant. Ajoutez-le dans .env ou config.yaml."
        )

    msg = _construire_email(expediteur, email_dest, objet, corps, chemin_cv)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(expediteur, password)
        server.sendmail(expediteur, email_dest, msg.as_string())


def envoyer_mock(offre: object, email_dest: str, config: dict, cv_path: Path | None = None) -> None:
    """Simule l'envoi du CV — affiche un résumé dans le terminal."""
    cv_config = config["cv"]
    chemin_cv = cv_path or Path(cv_config["fichier"])
    corps = _lire_template(cv_config, offre)
    objet = cv_config["objet_template"].format(titre=offre["titre"])
    expediteur = cv_config["email_expediteur"]

    sep = "-" * 50
    print(f"\n{sep}")
    print(f"[MOCK EMAIL] {datetime.now().strftime('%H:%M:%S')}")
    print(f"De      : {expediteur}")
    print(f"A       : {email_dest}")
    print(f"Objet   : {objet}")
    print(f"PJ      : {chemin_cv.name} {'(fichier present)' if chemin_cv.exists() else '(MANQUANT)'}")
    print(sep)
    print(corps)
    print(sep)


def _lire_template(cv_config: dict, offre: object) -> str:
    template_path = Path(cv_config["message_template"])
    if not template_path.exists():
        return f"Candidature pour le poste : {offre['titre']}"
    return template_path.read_text(encoding="utf-8").format(
        titre=offre["titre"],
        nom_complet=cv_config["nom_complet"],
    )


def _construire_email(
    expediteur: str,
    destinataire: str,
    objet: str,
    corps: str,
    chemin_cv: Path,
) -> MIMEMultipart:
    msg = MIMEMultipart()
    msg["From"] = expediteur
    msg["To"] = destinataire
    msg["Subject"] = objet
    msg.attach(MIMEText(corps, "plain", "utf-8"))

    with open(chemin_cv, "rb") as f:
        pj = MIMEApplication(f.read(), _subtype="pdf")
        pj.add_header("Content-Disposition", "attachment", filename=chemin_cv.name)
        msg.attach(pj)

    return msg
