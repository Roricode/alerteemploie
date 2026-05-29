import time
import requests
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from .base import ScraperBase

GUEST_API = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
JOB_BASE  = "https://www.linkedin.com/jobs/view/"


class LinkedInScraper(ScraperBase):
    """Scraper LinkedIn via l'API guest publique (sans login)."""

    nom = "linkedin.com"

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "fr-FR,fr;q=0.9",
    }

    def scrape(self) -> list[dict]:
        offres = []
        for mot_cle in self.mots_cles:
            url = (
                f"{GUEST_API}"
                f"?keywords={quote_plus(mot_cle)}"
                f"&location={quote_plus('Burkina Faso')}"
                "&start=0"
            )
            try:
                time.sleep(self.delai)
                resp = requests.get(url, headers=self.HEADERS, timeout=self.timeout)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "lxml")
                offres.extend(self._parser_liste(soup))
            except Exception as e:
                print(f"[{self.nom}] Erreur '{mot_cle}': {e}")

        # Déduplication par URL
        vus = set()
        uniques = []
        for o in offres:
            if o["url"] not in vus:
                vus.add(o["url"])
                uniques.append(o)
        return uniques

    def _parser_liste(self, soup) -> list[dict]:
        offres = []
        for card in soup.select("li"):
            offre = self._extraire_offre(card)
            if offre:
                offres.append(offre)
        return offres

    def _extraire_offre(self, card) -> dict | None:
        lien = (
            card.select_one("a.base-card__full-link")
            or card.select_one("a[href*='/jobs/view/']")
        )
        titre_el = (
            card.select_one("h3.base-search-card__title")
            or card.select_one("h3")
        )
        if not titre_el:
            return None

        titre = titre_el.get_text(strip=True)
        if not titre or not self._correspond(titre):
            return None

        entreprise_el = card.select_one("h4.base-search-card__subtitle, h4")
        localisation_el = card.select_one("span.job-search-card__location")
        date_el = card.select_one("time")

        url = lien["href"].split("?")[0] if lien and lien.get("href") else ""
        if not url:
            return None

        return {
            "titre": titre,
            "entreprise": entreprise_el.get_text(strip=True) if entreprise_el else "",
            "localisation": localisation_el.get_text(strip=True) if localisation_el else "Burkina Faso",
            "description": "",
            "url": url,
            "date_pub": date_el.get("datetime", "") if date_el else "",
            "source": self.nom,
        }
