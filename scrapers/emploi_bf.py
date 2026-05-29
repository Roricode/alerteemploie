from urllib.parse import urljoin, quote_plus
from .base import ScraperBase

BASE_URL = "https://www.emploi.bf"


class EmploiBfScraper(ScraperBase):
    """Scraper pour emploi.bf — premier site d'offres d'emploi au Burkina Faso."""

    nom = "emploi.bf"

    def scrape(self) -> list[dict]:
        offres = []
        for mot_cle in self.mots_cles:
            url = f"{BASE_URL}/recherche-emplois?search={quote_plus(mot_cle)}"
            soup = self._get(url)
            if soup is None:
                continue
            offres.extend(self._parser_liste(soup))
        # Déduplication par URL avant retour
        vus = set()
        uniques = []
        for o in offres:
            if o["url"] not in vus:
                vus.add(o["url"])
                uniques.append(o)
        return uniques

    def _parser_liste(self, soup) -> list[dict]:
        offres = []
        # emploi.bf liste ses offres dans des cards avec classe "job-item" ou similaire
        # Sélecteurs ajustés selon le HTML réel du site
        cards = (
            soup.select("div.job-item")
            or soup.select("article.job")
            or soup.select("div.offre-item")
            or soup.select("li.job-listing")
        )

        if not cards:
            # Fallback : cherche tous les liens contenant "/emploi/" ou "/offre/"
            cards = [
                a.find_parent("div") or a.find_parent("li")
                for a in soup.select("a[href*='/emploi/'], a[href*='/offre/']")
                if a.find_parent("div") or a.find_parent("li")
            ]

        for card in cards:
            offre = self._extraire_offre(card)
            if offre and self._correspond(offre["titre"] + " " + offre.get("description", "")):
                offres.append(offre)
        return offres

    def _extraire_offre(self, card) -> dict | None:
        # Titre : premier lien texte significatif dans la card
        lien = (
            card.select_one("a.job-title")
            or card.select_one("h2 a")
            or card.select_one("h3 a")
            or card.select_one("a[href*='/emploi/']")
            or card.select_one("a[href*='/offre/']")
            or card.select_one("a")
        )
        if not lien or not lien.get("href"):
            return None

        titre = lien.get_text(strip=True)
        url = urljoin(BASE_URL, lien["href"])

        entreprise_el = (
            card.select_one(".company-name")
            or card.select_one(".entreprise")
            or card.select_one("span.company")
        )
        localisation_el = (
            card.select_one(".location")
            or card.select_one(".localisation")
            or card.select_one("span.city")
        )
        date_el = (
            card.select_one(".date")
            or card.select_one("time")
            or card.select_one(".posted-date")
        )

        return {
            "titre": titre,
            "entreprise": entreprise_el.get_text(strip=True) if entreprise_el else "",
            "localisation": localisation_el.get_text(strip=True) if localisation_el else "Burkina Faso",
            "description": card.get_text(" ", strip=True)[:500],
            "url": url,
            "date_pub": (date_el.get("datetime") or date_el.get_text(strip=True)) if date_el else "",
            "source": self.nom,
        }
