from .base import ScraperBase

BASE_URL = "https://fasotuma-bf.com"


class FasoTumaScraper(ScraperBase):
    """Scraper pour FasoTuma-BF (anciennement FasoJob) — site local BF.
    Nécessite Playwright car le site est une SPA JavaScript (Supabase backend).
    """

    nom = "fasotuma-bf.com"

    def scrape(self) -> list[dict]:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print(f"[{self.nom}] Playwright non installé. Lancez : pip install playwright && playwright install chromium")
            return []

        offres = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                )
            )
            try:
                page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
                # Attendre que les offres soient chargées
                page.wait_for_selector("div.job-card, div.offre-card, div[class*=job]", timeout=10000)
                cards = page.query_selector_all("div.job-card, div.offre-card, div[class*=job]")
                for card in cards:
                    offre = self._extraire_offre_playwright(card)
                    if offre and self._correspond(offre["titre"] + " " + offre.get("description", "")):
                        offres.append(offre)
            except Exception as e:
                print(f"[{self.nom}] Erreur Playwright: {e}")
            finally:
                browser.close()
        return offres

    def _extraire_offre_playwright(self, card) -> dict | None:
        try:
            lien = card.query_selector("a[href]")
            titre_el = card.query_selector("h2, h3, .titre, .title, .job-title")

            if not titre_el:
                return None

            titre = titre_el.inner_text().strip()
            url = lien.get_attribute("href") if lien else BASE_URL
            if url and not url.startswith("http"):
                url = BASE_URL + url

            entreprise_el = card.query_selector(".entreprise, .company, .employer")
            localisation_el = card.query_selector(".location, .localisation, .ville")

            return {
                "titre": titre,
                "entreprise": entreprise_el.inner_text().strip() if entreprise_el else "",
                "localisation": localisation_el.inner_text().strip() if localisation_el else "Burkina Faso",
                "description": card.inner_text()[:400],
                "url": url,
                "date_pub": "",
                "source": self.nom,
            }
        except Exception:
            return None
