import time
import requests
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


class ScraperBase(ABC):
    """Classe de base pour tous les scrapers d'offres d'emploi."""

    nom: str = "inconnu"

    def __init__(self, config: dict):
        self.mots_cles: list[str] = config["recherche"]["mots_cles"]
        self.localisations: list[str] = config["recherche"]["localisations"]
        self.timeout: int = config["scraping"]["timeout_secondes"]
        self.delai: float = config["scraping"]["delai_entre_requetes"]

    @abstractmethod
    def scrape(self) -> list[dict]:
        """Retourne une liste d'offres. Chaque offre est un dict avec les clés :
        titre, entreprise, localisation, description, url, date_pub, source
        """

    def _get(self, url: str, **kwargs) -> BeautifulSoup | None:
        try:
            time.sleep(self.delai)
            resp = requests.get(url, headers=HEADERS, timeout=self.timeout, **kwargs)
            resp.raise_for_status()
            return BeautifulSoup(resp.text, "lxml")
        except requests.RequestException as e:
            print(f"[{self.nom}] Erreur requête {url}: {e}")
            return None

    def _correspond(self, texte: str) -> bool:
        """Vérifie si le texte contient au moins un mot-clé recherché."""
        texte_lower = texte.lower()
        return any(kw.lower() in texte_lower for kw in self.mots_cles)
