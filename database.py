import sqlite3

def get_connection():
    return sqlite3.connect("epargne.db")

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Création de la table utilisateurs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS utilisateurs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    # 2. Création de la table simulations (si elle n'existe pas du tout)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS simulations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_utilisateur INTEGER,
        nom_objectif TEXT,
        montant_cible REAL,
        epargne_initiale REAL,
        depot_mensuel REAL,
        taux REAL,
        duree INTEGER,
        montant_final REAL,
        interets REAL,
        date_creation TEXT,
        FOREIGN KEY(id_utilisateur) REFERENCES utilisateurs(id)
    )
    """)

   
    cursor.execute("PRAGMA table_info(simulations)")
    colonnes = [col[1] for col in cursor.fetchall()]
    
    if "id_utilisateur" not in colonnes:
        try:
            cursor.execute("ALTER TABLE simulations ADD COLUMN id_utilisateur INTEGER")
            conn.commit()
        except sqlite3.OperationalError:
            pass 

    conn.commit()
    conn.close()