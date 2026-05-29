# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**alerteemploie** — Système de veille d'offres d'emploi en Python, conçu pour Ouagadougou (Burkina Faso).  
Scrape automatiquement les sites d'emploi locaux et régionaux, notifie par WhatsApp/SMS dès qu'une offre correspond aux mots-clés configurés, et permet d'envoyer son CV directement depuis la CLI.

## Commandes principales

```bash
# Installer les dépendances
pip install -r requirements.txt

# Scraper toutes les sources (sans notification)
python main.py scrape

# Scraper et notifier immédiatement les nouvelles offres
python main.py scrape --notifier

# Afficher les dernières offres en base
python main.py list
python main.py list --limite 50

# Envoyer son CV pour une offre (par son ID)
python main.py send-cv 42 recruteur@entreprise.com

# Envoyer les notifications pour les offres non encore notifiées
python main.py notify

# Lancer le scheduler automatique (tourne en continu)
python scheduler.py
```

## Architecture

```
main.py          CLI Click — commandes : scrape, list, send-cv, notify
scheduler.py     APScheduler — relance scrape --notifier toutes les N heures
config.yaml      Configuration utilisateur (mots-clés, numéro, credentials)
.env             Credentials API (jamais commité)

scrapers/
  base.py        Classe abstraite ScraperBase : _get(), _correspond()
  emploi_bf.py   emploi.bf (site local #1 BF)
  afrique_it.py  AfricaWork (Afrique de l'Ouest)

storage/
  db.py          SQLite : init_db, sauvegarder, est_connue, lister_offres,
                 offres_non_notifiees, marquer_notifie, get_offre

notifier/        WhatsApp via Twilio, SMS via Africa's Talking
cv_sender/       Envoi email avec pièce jointe via smtplib + Gmail App Password
templates/       cv_message.txt — corps du mail de candidature
```

## Flux de données

1. `scrape` → chaque scraper retourne `list[dict]`
2. `storage.db.sauvegarder()` insère si l'URL est nouvelle (déduplication par SHA-256)
3. `notify` → lit `offres WHERE notifie=0` → Twilio WhatsApp ou Africa's Talking SMS → `marquer_notifie()`
4. `send-cv` → récupère l'offre par ID → envoie email avec CV en pièce jointe

## Ajouter un nouveau scraper

1. Créer `scrapers/nom_site.py` héritant de `ScraperBase`
2. Implémenter `scrape() -> list[dict]` — chaque dict doit contenir : `titre`, `url`, `source`, et optionnellement `entreprise`, `localisation`, `description`, `date_pub`
3. Ajouter la source dans `config.yaml` sous `sources:`
4. L'instancier dans `_scrapers_actifs()` dans `main.py`

## Variables d'environnement requises (.env)

| Variable | Usage |
|---|---|
| `TWILIO_ACCOUNT_SID` | Notification WhatsApp |
| `TWILIO_AUTH_TOKEN` | Notification WhatsApp |
| `TWILIO_WHATSAPP_FROM` | Numéro sandbox Twilio (`whatsapp:+14155238886`) |
| `AT_USERNAME` | SMS Africa's Talking |
| `AT_API_KEY` | SMS Africa's Talking |
| `GMAIL_APP_PASSWORD` | Envoi CV par email |

## Sources configurées

| Source | Couverture | Scraper |
|---|---|---|
| emploi.bf | Burkina Faso — site principal | `scrapers/emploi_bf.py` |
| africawork.com | Afrique de l'Ouest | `scrapers/afrique_it.py` |
| ANPE BF | À implémenter (Phase 2) | — |
| LinkedIn | À implémenter (Phase 2) | — |
