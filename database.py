import sqlite3

def get_connection():
    conn = sqlite3.connect("epargne.db")
    return conn

def init_db():
    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS simulations(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom_objectif TEXT,
        montant_cible REAL,
        epargne_initiale REAL,
        depot_mensuel REAL,
        taux REAL,
        duree INTEGER,
        montant_final REAL,
        interets REAL,
        date_creation TEXT
    )
    """)

    conn.commit()
    conn.close()