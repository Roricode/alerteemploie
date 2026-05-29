"""Lance le scraping automatique selon l'intervalle défini dans config.yaml."""

import yaml
from pathlib import Path
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

CONFIG_PATH = Path(__file__).parent / "config.yaml"


def charger_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def run_scraping():
    """Tâche planifiée : scrape toutes les sources puis notifie."""
    import subprocess, sys
    subprocess.run(
        [sys.executable, "main.py", "scrape", "--notifier"],
        check=False,
    )


if __name__ == "__main__":
    config = charger_config()
    heures = config["scraping"]["intervalle_heures"]

    scheduler = BlockingScheduler()
    scheduler.add_job(
        run_scraping,
        trigger=IntervalTrigger(hours=heures),
        id="scraping_auto",
        name=f"Scraping toutes les {heures}h",
        replace_existing=True,
    )

    print(f"Scheduler démarré — scraping toutes les {heures} heures.")
    print("Appuyez sur Ctrl+C pour arrêter.\n")

    # Premier passage immédiat au démarrage
    run_scraping()

    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("\nScheduler arrêté.")
