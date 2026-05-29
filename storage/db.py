import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "offres.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS offres (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                url_hash    TEXT UNIQUE NOT NULL,
                titre       TEXT NOT NULL,
                entreprise  TEXT,
                localisation TEXT,
                description TEXT,
                url         TEXT NOT NULL,
                source      TEXT NOT NULL,
                date_pub    TEXT,
                date_trouve TEXT NOT NULL,
                notifie     INTEGER NOT NULL DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS envois_cv (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                offre_id      INTEGER NOT NULL REFERENCES offres(id),
                email_dest    TEXT NOT NULL,
                date_envoi    TEXT NOT NULL,
                mock          INTEGER NOT NULL DEFAULT 0,
                statut        TEXT NOT NULL DEFAULT 'envoye'
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_notifie  ON offres(notifie)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_source   ON offres(source)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_envoi_of ON envois_cv(offre_id)")


def _hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()


def est_connue(url: str) -> bool:
    with _connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM offres WHERE url_hash = ?", (_hash(url),)
        ).fetchone()
    return row is not None


def sauvegarder(offre: dict) -> int | None:
    """Insère une offre. Retourne l'id si insérée, None si déjà connue."""
    url_hash = _hash(offre["url"])
    now = datetime.now().isoformat(timespec="seconds")
    try:
        with _connect() as conn:
            cur = conn.execute(
                """INSERT INTO offres
                   (url_hash, titre, entreprise, localisation, description,
                    url, source, date_pub, date_trouve)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    url_hash,
                    offre.get("titre", ""),
                    offre.get("entreprise", ""),
                    offre.get("localisation", ""),
                    offre.get("description", ""),
                    offre["url"],
                    offre.get("source", "inconnu"),
                    offre.get("date_pub", ""),
                    now,
                ),
            )
            return cur.lastrowid
    except sqlite3.IntegrityError:
        return None


def offres_non_notifiees() -> list[sqlite3.Row]:
    with _connect() as conn:
        return conn.execute(
            "SELECT * FROM offres WHERE notifie = 0 ORDER BY date_trouve DESC"
        ).fetchall()


def marquer_notifie(offre_id: int) -> None:
    with _connect() as conn:
        conn.execute("UPDATE offres SET notifie = 1 WHERE id = ?", (offre_id,))


def lister_offres(limite: int = 20) -> list[sqlite3.Row]:
    with _connect() as conn:
        return conn.execute(
            "SELECT * FROM offres ORDER BY date_trouve DESC LIMIT ?", (limite,)
        ).fetchall()


def get_offre(offre_id: int) -> sqlite3.Row | None:
    with _connect() as conn:
        return conn.execute(
            "SELECT * FROM offres WHERE id = ?", (offre_id,)
        ).fetchone()


def enregistrer_envoi_cv(offre_id: int, email_dest: str, mock: bool = False) -> int:
    now = datetime.now().isoformat(timespec="seconds")
    with _connect() as conn:
        cur = conn.execute(
            """INSERT INTO envois_cv (offre_id, email_dest, date_envoi, mock)
               VALUES (?, ?, ?, ?)""",
            (offre_id, email_dest, now, int(mock)),
        )
        return cur.lastrowid


def historique_cv(offre_id: int | None = None) -> list[sqlite3.Row]:
    with _connect() as conn:
        if offre_id:
            return conn.execute(
                """SELECT e.*, o.titre, o.entreprise FROM envois_cv e
                   JOIN offres o ON o.id = e.offre_id
                   WHERE e.offre_id = ? ORDER BY e.date_envoi DESC""",
                (offre_id,),
            ).fetchall()
        return conn.execute(
            """SELECT e.*, o.titre, o.entreprise FROM envois_cv e
               JOIN offres o ON o.id = e.offre_id
               ORDER BY e.date_envoi DESC LIMIT 50"""
        ).fetchall()
