#!/usr/bin/env python3
"""Point d'entrée CLI du système de veille emploi."""

import sys
from pathlib import Path

# Force UTF-8 sur Windows (évite les erreurs cp1252 avec les accents)
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

import click
import yaml
from dotenv import load_dotenv

load_dotenv()

CONFIG_PATH = Path(__file__).parent / "config.yaml"


def charger_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _scrapers_actifs(config: dict):
    from scrapers.linkedin import LinkedInScraper
    from scrapers.fasotuma import FasoTumaScraper

    sources = config.get("sources", {})
    scrapers = []
    if sources.get("linkedin", True):
        scrapers.append(LinkedInScraper(config))
    if sources.get("fasotuma", False):
        scrapers.append(FasoTumaScraper(config))
    return scrapers


@click.group()
def cli():
    """Système de veille d'offres d'emploi — Burkina Faso."""


@cli.command()
@click.option("--notifier", is_flag=True, default=False,
              help="Envoyer une notification pour les nouvelles offres trouvées.")
def scrape(notifier):
    """Lance le scraping de toutes les sources configurées."""
    from storage.db import init_db, sauvegarder, offres_non_notifiees, marquer_notifie

    init_db()
    config = charger_config()
    scrapers = _scrapers_actifs(config)

    total_nouvelles = 0
    for scraper in scrapers:
        click.echo(f"Scraping {scraper.nom}...")
        try:
            offres = scraper.scrape()
        except Exception as e:
            click.echo(f"  Erreur : {e}", err=True)
            continue

        nouvelles = 0
        for offre in offres:
            if sauvegarder(offre) is not None:
                nouvelles += 1
        click.echo(f"  {nouvelles} nouvelles offres sur {len(offres)} trouvées.")
        total_nouvelles += nouvelles

    click.echo(f"\nTotal : {total_nouvelles} nouvelle(s) offre(s) sauvegardée(s).")

    if notifier and total_nouvelles > 0:
        _envoyer_notifications(config)


@cli.command("list")
@click.option("--limite", default=20, show_default=True, help="Nombre d'offres à afficher.")
def list_jobs(limite):
    """Affiche les dernières offres trouvées."""
    from storage.db import init_db, lister_offres

    init_db()
    offres = lister_offres(limite)

    if not offres:
        click.echo("Aucune offre en base. Lancez d'abord : python main.py scrape")
        return

    for o in offres:
        notif = "✓" if o["notifie"] else "·"
        click.echo(
            f"[{notif}] #{o['id']:>4}  {o['titre'][:55]:<55}  "
            f"{o['source']:<15}  {o['date_trouve'][:10]}"
        )
        if o["entreprise"]:
            click.echo(f"          {o['entreprise']} — {o['localisation']}")
        click.echo(f"          {o['url']}")
        click.echo()


@cli.command("send-cv")
@click.argument("job_id", type=int)
@click.argument("email_recruteur")
@click.option("--cv", "cv_path", default=None, help="Chemin vers le CV (défaut : config.yaml).")
def send_cv(job_id, email_recruteur, cv_path):
    """Envoie votre CV par email pour l'offre JOB_ID.

    Exemple : python main.py send-cv 42 recruteur@entreprise.com
    """
    import os
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.application import MIMEApplication
    from storage.db import init_db, get_offre

    init_db()
    config = charger_config()
    cv_config = config["cv"]

    offre = get_offre(job_id)
    if not offre:
        click.echo(f"Offre #{job_id} introuvable.", err=True)
        sys.exit(1)

    chemin_cv = Path(cv_path or cv_config["fichier"])
    if not chemin_cv.exists():
        click.echo(f"CV introuvable : {chemin_cv}", err=True)
        sys.exit(1)

    template_path = Path(cv_config["message_template"])
    corps = template_path.read_text(encoding="utf-8").format(
        titre=offre["titre"],
        nom_complet=cv_config["nom_complet"],
    )

    objet = cv_config["objet_template"].format(titre=offre["titre"])
    expediteur = cv_config["email_expediteur"]
    password = os.getenv("GMAIL_APP_PASSWORD") or config["credentials"].get("gmail_app_password", "")

    if not password:
        click.echo("GMAIL_APP_PASSWORD manquant dans .env ou config.yaml.", err=True)
        sys.exit(1)

    msg = MIMEMultipart()
    msg["From"] = expediteur
    msg["To"] = email_recruteur
    msg["Subject"] = objet
    msg.attach(MIMEText(corps, "plain", "utf-8"))

    with open(chemin_cv, "rb") as f:
        attachment = MIMEApplication(f.read(), _subtype="pdf")
        attachment.add_header(
            "Content-Disposition", "attachment", filename=chemin_cv.name
        )
        msg.attach(attachment)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(expediteur, password)
        server.sendmail(expediteur, email_recruteur, msg.as_string())

    click.echo(f"CV envoyé à {email_recruteur} pour l'offre : {offre['titre']}")


@cli.command()
def notify():
    """Envoie les notifications pour toutes les offres non encore notifiées."""
    config = charger_config()
    _envoyer_notifications(config)


@cli.command("test-notif")
@click.option("--canal", type=click.Choice(["whatsapp", "sms"]), default=None,
              help="Canal à tester (défaut : celui de config.yaml).")
def test_notif(canal):
    """Envoie un message de test WhatsApp/SMS (ou simulation si mock: true)."""
    config = charger_config()
    canal  = canal or config["notifications"]["canal"]
    numero = config["notifications"]["numero"]
    mock   = config["notifications"].get("mock", False)

    message = (
        "Alerte Emploi - test de connexion\n"
        "--------------------\n"
        "Votre systeme de veille emploi est bien configure !\n"
        "Vous recevrez vos alertes ici."
    )

    if mock:
        from notifier.mock import envoyer
        envoyer(numero, message, canal)
        click.echo(f"\n[MOCK] Simulation OK — canal={canal}, numero={numero}")
        click.echo("Passez 'mock: false' dans config.yaml pour envoyer pour de vrai.")
        return

    try:
        if canal == "whatsapp":
            from notifier.whatsapp import envoyer
            sid = envoyer(numero, message, config)
            click.echo(f"WhatsApp envoyé (SID: {sid})")
        else:
            from notifier.sms import envoyer
            envoyer(numero, message, config)
            click.echo(f"SMS envoyé à {numero}")
    except Exception as e:
        click.echo(f"Erreur : {e}", err=True)
        click.echo("\nVérifiez votre fichier .env :", err=True)
        click.echo("  TWILIO_ACCOUNT_SID=ACxxxx", err=True)
        click.echo("  TWILIO_AUTH_TOKEN=xxxx", err=True)
        click.echo("  TWILIO_WHATSAPP_FROM=whatsapp:+14155238886", err=True)
        sys.exit(1)


def _envoyer_notifications(config: dict) -> None:
    from notifier.whatsapp import formatter_offre
    from storage.db import offres_non_notifiees, marquer_notifie

    offres = offres_non_notifiees()
    if not offres:
        click.echo("Aucune offre à notifier.")
        return

    canal  = config["notifications"]["canal"]
    numero = config["notifications"]["numero"]
    mock   = config["notifications"].get("mock", False)

    for offre in offres:
        message = formatter_offre(offre)
        try:
            if mock:
                from notifier.mock import envoyer
                envoyer(numero, message, canal)
            elif canal == "whatsapp":
                from notifier.whatsapp import envoyer
                envoyer(numero, message, config)
            else:
                from notifier.sms import envoyer
                envoyer(numero, message, config)
            marquer_notifie(offre["id"])
            click.echo(f"  {'[MOCK] ' if mock else ''}Notifié : {offre['titre']}")
        except Exception as e:
            click.echo(f"  Erreur pour #{offre['id']} : {e}", err=True)


if __name__ == "__main__":
    cli()
