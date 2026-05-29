# Alerte Emploie

Système de veille d'offres d'emploi en Python, conçu pour le **Burkina Faso**.

Scrape automatiquement LinkedIn et les sites locaux, envoie une notification **WhatsApp ou SMS** dès qu'une nouvelle offre correspond à vos mots-clés, et vous permet d'envoyer votre CV directement au recruteur en une commande.

---

## Fonctionnalités

- **Scraping automatique** — LinkedIn (sans login), FasoTuma-BF
- **Déduplication** — une offre n'est jamais notifiée deux fois
- **Notification WhatsApp** via Twilio (ou SMS via Africa's Talking)
- **Envoi de CV par email** depuis la CLI avec corps de mail personnalisable
- **Historique** des candidatures envoyées
- **Mode simulation** (mock) pour tester sans credentials réels
- **Scheduler** — scraping automatique toutes les N heures

---

## Installation

```bash
git clone https://github.com/Roricode/alerteemploie.git
cd alerteemploie
pip install -r requirements.txt
```

---

## Configuration

### 1. Mots-clés et canal de notification

Éditez `config.yaml` :

```yaml
recherche:
  mots_cles:
    - "développeur"
    - "data"
    - "réseau"
  localisations:
    - "Ouagadougou"
    - "Burkina Faso"

notifications:
  canal: "whatsapp"          # ou "sms"
  numero: "+22670000000"     # votre numéro
  mock: true                 # false pour envoyer pour de vrai

cv:
  fichier: "cv.pdf"
  nom_complet: "Votre Nom"
  email_expediteur: "votre@gmail.com"
```

### 2. Credentials API

Copiez `.env.example` en `.env` et remplissez vos clés :

```bash
cp .env.example .env
```

```env
# Twilio (WhatsApp)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886

# Africa's Talking (SMS Burkina Faso — Orange/Telecel)
AT_USERNAME=votre_username
AT_API_KEY=votre_api_key

# Gmail (envoi CV)
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
```

> **WhatsApp sandbox Twilio** : envoyez `join <votre-code>` au **+1 415 523 8886** depuis votre WhatsApp pour activer le sandbox.

---

## Utilisation

```bash
# Scraper toutes les sources configurées
python main.py scrape

# Scraper et notifier immédiatement
python main.py scrape --notifier

# Voir les offres trouvées
python main.py list
python main.py list --limite 50

# Envoyer son CV pour une offre
python main.py send-cv 10 recruteur@entreprise.com
python main.py send-cv 10 recruteur@entreprise.com --cv monvrai_cv.pdf

# Historique des candidatures
python main.py cv-history

# Tester la connexion WhatsApp/SMS
python main.py test-notif

# Lancer le scraping automatique (toutes les 6h)
python scheduler.py
```

---

## Exemple de notification WhatsApp

```
Nouvelle offre d'emploi
--------------------
*Data Center Technician - BF - Ouagadougou - On-site*
Entreprise : Reboot Monkey
Lieu : Ouagadougou, Centre, Burkina Faso
Source : linkedin.com
--------------------
https://bf.linkedin.com/jobs/view/...
```

---

## Architecture

```
alerteemploie/
├── main.py              # CLI (scrape, list, notify, send-cv, cv-history, test-notif)
├── scheduler.py         # Scraping automatique via APScheduler
├── config.yaml          # Configuration utilisateur
├── .env                 # Credentials API (non commité)
│
├── scrapers/
│   ├── base.py          # Classe abstraite commune
│   ├── linkedin.py      # LinkedIn via API guest publique
│   └── fasotuma.py      # FasoTuma-BF (nécessite Playwright)
│
├── notifier/
│   ├── whatsapp.py      # Twilio WhatsApp API
│   ├── sms.py           # Africa's Talking SMS
│   └── mock.py          # Simulation terminal
│
├── cv_sender/
│   └── mailer.py        # Envoi email Gmail (SMTP SSL)
│
├── storage/
│   └── db.py            # SQLite — offres + historique envois CV
│
└── templates/
    └── cv_message.txt   # Corps du mail de candidature
```

---

## Ajouter un scraper

1. Créez `scrapers/mon_site.py` héritant de `ScraperBase`
2. Implémentez `scrape() -> list[dict]` — chaque dict : `titre`, `url`, `source`, `entreprise`, `localisation`, `description`, `date_pub`
3. Activez la source dans `config.yaml` sous `sources:`
4. Instanciez-la dans `_scrapers_actifs()` dans `main.py`

---

## Sources configurées

| Source | Couverture | Statut |
|---|---|---|
| LinkedIn (guest API) | Burkina Faso & international | Actif |
| FasoTuma-BF | Burkina Faso local | Playwright requis |
| ANPE BF | Agence nationale emploi | À venir |

---

## Pré-requis

- Python 3.11+
- Compte [Twilio](https://twilio.com) (gratuit) pour WhatsApp
- Compte [Africa's Talking](https://africastalking.com) pour SMS (couverture Orange/Telecel BF)
- Gmail avec [mot de passe d'application](https://myaccount.google.com/apppasswords) pour l'envoi de CV

---

## Licence

MIT
