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
@click.option("--cv", "cv_path", default=None, help="Chemin vers le CV (defaut : config.yaml).")
def send_cv(job_id, email_recruteur, cv_path):
    """Envoie votre CV par email pour l'offre JOB_ID.

    Exemple : python main.py send-cv 10 recruteur@entreprise.com
    """
    from cv_sender.mailer import envoyer, envoyer_mock
    from storage.db import init_db, get_offre, enregistrer_envoi_cv

    init_db()
    config = charger_config()
    mock = config["notifications"].get("mock", False)

    offre = get_offre(job_id)
    if not offre:
        click.echo(f"Offre #{job_id} introuvable. Lancez 'python main.py list' pour voir les IDs.", err=True)
        sys.exit(1)

    chemin_cv = Path(cv_path) if cv_path else None

    click.echo(f"Offre    : {offre['titre']}")
    click.echo(f"Societe  : {offre['entreprise'] or '—'}")
    click.echo(f"Email    : {email_recruteur}")
    click.echo(f"Mode     : {'SIMULATION' if mock else 'REEL'}")
    click.echo()

    try:
        if mock:
            envoyer_mock(offre, email_recruteur, config, chemin_cv)
        else:
            envoyer(offre, email_recruteur, config, chemin_cv)

        enregistrer_envoi_cv(offre["id"], email_recruteur, mock=mock)
        statut = "[MOCK] Simule" if mock else "Envoye"
        click.echo(f"{statut} : CV pour '{offre['titre']}' -> {email_recruteur}")

    except FileNotFoundError as e:
        click.echo(f"Erreur : {e}", err=True)
        click.echo("Deposez votre CV.pdf a la racine du projet ou precisez --cv chemin/vers/cv.pdf", err=True)
        sys.exit(1)
    except ValueError as e:
        click.echo(f"Erreur configuration : {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Erreur envoi : {e}", err=True)
        sys.exit(1)


@cli.command("cv-history")
@click.option("--job", "job_id", default=None, type=int, help="Filtrer par ID d'offre.")
def cv_history(job_id):
    """Affiche l'historique des CV envoyes."""
    from storage.db import init_db, historique_cv

    init_db()
    envois = historique_cv(job_id)

    if not envois:
        click.echo("Aucun CV envoye pour l'instant.")
        return

    for e in envois:
        mock_tag = " [MOCK]" if e["mock"] else ""
        click.echo(
            f"{e['date_envoi']}{mock_tag}  ->  {e['email_dest']}"
        )
        click.echo(f"   Offre #{e['offre_id']} : {e['titre']} ({e['entreprise']})")
        click.echo()


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
        if canal == "callmebot":
            from notifier.callmebot import envoyer
            envoyer(numero, message, config)
            click.echo(f"WhatsApp CallMeBot envoye a {numero}")
        elif canal == "whatsapp":
            from notifier.whatsapp import envoyer
            sid = envoyer(numero, message, config)
            click.echo(f"WhatsApp Twilio envoye (SID: {sid})")
        else:
            from notifier.sms import envoyer
            envoyer(numero, message, config)
            click.echo(f"SMS envoye a {numero}")
    except Exception as e:
        click.echo(f"Erreur : {e}", err=True)
        click.echo("\nPour CallMeBot : ajoutez CALLMEBOT_API_KEY=xxxxxx dans .env", err=True)
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
            elif canal == "callmebot":
                from notifier.callmebot import envoyer
                envoyer(numero, message, config)
            elif canal == "whatsapp":
                from notifier.whatsapp import envoyer
                envoyer(numero, message, config)
            else:
                from notifier.sms import envoyer
                envoyer(numero, message, config)
            marquer_notifie(offre["id"])
            click.echo(f"  {'[MOCK] ' if mock else ''}Notifie : {offre['titre']}")
        except Exception as e:
            click.echo(f"  Erreur pour #{offre['id']} : {e}", err=True)


if __name__ == "__main__":
    cli()
