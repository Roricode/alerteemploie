from urllib.parse import urljoin, quote_plus
from .base import ScraperBase

BASE_URL = "https://www.africawork.com"


class AfriqueItScraper(ScraperBase):
    """Scraper pour AfricaWork — offres d'emploi Afrique de l'Ouest."""

    nom = "africawork.com"

    def scrape(self) -> list[dict]:
        offres = []
        for mot_cle in self.mots_cles:
            # Filtrer sur Burkina Faso directement dans l'URL
            url = (
                f"{BASE_URL}/offres-emploi/burkina-faso"
                f"?q={quote_plus(mot_cle)}"
            )
            soup = self._get(url)
            if soup is None:
                continue
            offres.extend(self._parser_liste(soup))

        vus = set()
        uniques = []
        for o in offres:
            if o["url"] not in vus:
                vus.add(o["url"])
                uniques.append(o)
        return uniques

    def _parser_liste(self, soup) -> list[dict]:
        offres = []
        cards = (
            soup.select("div.job-offer-item")
            or soup.select("article.offer")
            or soup.select("div.offer-item")
            or soup.select("li.offer")
        )
        for card in cards:
            offre = self._extraire_offre(card)
            if offre and self._correspond(offre["titre"] + " " + offre.get("description", "")):
                offres.append(offre)
        return offres

    def _extraire_offre(self, card) -> dict | None:
        lien = (
            card.select_one("a.offer-title")
            or card.select_one("h2 a")
            or card.select_one("h3 a")
            or card.select_one("a")
        )
        if not lien or not lien.get("href"):
            return None

        titre = lien.get_text(strip=True)
        url = urljoin(BASE_URL, lien["href"])

        entreprise_el = card.select_one(".company, .employer, .entreprise")
        localisation_el = card.select_one(".location, .city, .ville")
        date_el = card.select_one("time, .date, .posted")

        return {
            "titre": titre,
            "entreprise": entreprise_el.get_text(strip=True) if entreprise_el else "",
            "localisation": localisation_el.get_text(strip=True) if localisation_el else "Burkina Faso",
            "description": card.get_text(" ", strip=True)[:500],
            "url": url,
            "date_pub": (date_el.get("datetime") or date_el.get_text(strip=True)) if date_el else "",
            "source": self.nom,
        }
