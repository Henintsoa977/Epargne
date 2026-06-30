import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sqlite3
from database import init_db, get_connection
from models import methode_euler_epargne
from datetime import datetime

# Initialisation de la base de données
init_db()

st.set_page_config(page_title="Épargne Intelligente", layout="wide")

# Gestion des variables de session pour l'authentification
if "connected" not in st.session_state:
    st.session_state.connected = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "user_name" not in st.session_state:
    st.session_state.user_name = ""

# --- ÉCRAN D'AUTHENTIFICATION ---
if not st.session_state.connected:
    st.title("💰 Épargne Intelligente")
    
    auth_mode = st.radio("Choisissez une option :", ["Se connecter", "S'inscrire"], horizontal=True)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    if auth_mode == "S'inscrire":
        st.subheader("Créer un nouveau compte")
        nom = st.text_input("Nom d'utilisateur")
        email = st.text_input("Adresse Email")
        password = st.text_input("Mot de passe", type="password")
        
        if st.button("Créer mon compte", type="primary"):
            if nom and email and password:
                try:
                    cursor.execute(
                        "INSERT INTO utilisateurs (nom, email, password) VALUES (?, ?, ?)",
                        (nom, email, password)
                    )
                    conn.commit()
                    st.success("Compte créé avec succès ! Vous pouvez maintenant vous connecter.")
                except sqlite3.IntegrityError:
                    st.error("Cette adresse email est déjà enregistrée.")
            else:
                st.warning("Veuillez remplir tous les champs.")
                
    elif auth_mode == "Se connecter":
        st.subheader("Connexion à votre espace")
        email = st.text_input("Adresse Email")
        password = st.text_input("Mot de passe", type="password")
        
        if st.button("Se connecter", type="primary"):
            cursor.execute(
                "SELECT id, nom FROM utilisateurs WHERE email = ? AND password = ?", 
                (email, password)
            )
            user = cursor.fetchone()
            
            if user:
                st.session_state.connected = True
                st.session_state.user_id = user[0]
                st.session_state.user_name = user[1]
                st.rerun()
            else:
                st.error("Email ou mot de passe incorrect.")
                
    conn.close()

#  APPLICATION PRINCIPALE 
else:
    st.sidebar.write(f"👋 Bienvenue, **{st.session_state.user_name}** !")
    if st.sidebar.button("Se déconnecter", type="secondary"):
        st.session_state.connected = False
        st.session_state.user_id = None
        st.session_state.user_name = ""
        st.rerun()

    st.title("💰 Prévision d'Épargne")

    # Sidebar Navigation
    st.sidebar.header("Navigation")
    page = st.sidebar.radio("", ["Nouvelle Simulation", "Comparer des Scénarios", "Mes Simulations", "A propos"])

    if page == "Nouvelle Simulation":
        st.header("Créer une nouvelle simulation")
        
        col1, col2 = st.columns(2)
        
        with col1:
            nom_objectif = st.text_input("Nom de l'objectif", "Achat de moto")
            montant_cible = st.number_input("Montant cible (MGA)", min_value=10000, value=500000)
            epargne_initiale = st.number_input("Épargne initiale", min_value=0, value=0)
        
        with col2:
            depot_mensuel = st.number_input("Dépôt mensuel (MGA)", min_value=5000, value=25000)
            taux = st.slider("Taux d'intérêt annuel (%)", 0.0, 15.0, 6.5, 0.1)
            duree = st.slider("Durée maximale (mois)", 6, 120, 36)
        
        if st.button("🚀 Lancer le calcul ", type="primary"):
            resultats = methode_euler_epargne(epargne_initiale, depot_mensuel, taux, duree)
            df = pd.DataFrame(resultats)
            
            # Sauvegarde liée à l'ID utilisateur connecté
            conn = get_connection()
            conn.execute("""
            INSERT INTO simulations(
                id_utilisateur, nom_objectif, montant_cible, epargne_initiale, 
                depot_mensuel, taux, duree, montant_final, interets, date_creation
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                st.session_state.user_id,
                nom_objectif,
                montant_cible,
                epargne_initiale,
                depot_mensuel,
                taux,
                duree,
                df["epargne"].iloc[-1],
                df["interet"].sum(),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            conn.commit()
            conn.close()
            
            mois_objectif = df[df['epargne'] >= montant_cible].index.min() + 1
            
            colA, colB, colC = st.columns(3)
            colA.metric("Montant final", f"{df['epargne'].iloc[-1]:,.0f} MGA")
            colB.metric("Intérêts gagnés", f"{df['interet'].sum():,.0f} MGA")
            if pd.notna(mois_objectif):
                colC.metric("Objectif atteint en", f"{mois_objectif} mois", delta="✅")
            else:
                colC.metric("Objectif atteint en", "> " + str(duree) + " mois", delta="❌")
            
            st.subheader("Évolution de l'épargne")
            
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(df['mois'], df['epargne'], label="Montant d'épargne", color='blue', linewidth=2.5)
            ax.axhline(y=montant_cible, color='red', linestyle='--', linewidth=2, label="Objectif")
            ax.fill_between(df['mois'], df['epargne'], alpha=0.3)
            ax.set_xlabel("Nombre de mois")
            ax.set_ylabel("Montant (MGA)")
            ax.legend()
            ax.grid(True, alpha=0.3)
            st.pyplot(fig)
            
            st.subheader("Détail des 12 premiers mois")
            st.dataframe(df.head(12).style.format({
                'epargne': '{:,.0f}', 
                'interet': '{:,.0f}',
                'depot': '{:,.0f}'
            }), use_container_width=True)

    elif page == "Comparer des Scénarios":
        st.header("Comparer plusieurs scénarios")
        st.info("Comparez différents dépôts ou taux d'intérêt")
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Scénario 1")
            d1 = st.number_input("Dépôt mensuel Sc1", value=20000, key="d1")
            t1 = st.slider("Taux Sc1 (%)", 0.0, 15.0, 5.0, key="t1")
        
        with col2:
            st.subheader("Scénario 2")
            d2 = st.number_input("Dépôt mensuel Sc2", value=35000, key="d2")
            t2 = st.slider("Taux Sc2 (%)", 0.0, 15.0, 7.0, key="t2")
        
        duree_comp = st.slider("Durée de comparaison (mois)", 12, 84, 36)
        
        res1 = methode_euler_epargne(0, d1, t1, duree_comp)
        res2 = methode_euler_epargne(0, d2, t2, duree_comp)
        
        df1 = pd.DataFrame(res1)
        df2 = pd.DataFrame(res2)
        
        fig, ax = plt.subplots(figsize=(11, 7))
        ax.plot(df1['mois'], df1['epargne'], label=f"Sc1 : {d1} MGA/mois ({t1}%)", linewidth=2.5)
        ax.plot(df2['mois'], df2['epargne'], label=f"Sc2 : {d2} MGA/mois ({t2}%)", linewidth=2.5)
        ax.set_xlabel("Mois")
        ax.set_ylabel("Épargne (MGA)")
        ax.legend()
        ax.grid(True)
        st.pyplot(fig)
        
        st.success(f"Après {duree_comp} mois :\n"
                  f"Scénario 1 → **{df1['epargne'].iloc[-1]:,.0f} MGA**\n"
                  f"Scénario 2 → **{df2['epargne'].iloc[-1]:,.0f} MGA**")

    elif page == "Mes Simulations":
        st.header("📂 Mes simulations")

        conn = get_connection()
        cursor = conn.cursor()

       
        cursor.execute("""
        SELECT
            id, nom_objectif, montant_cible, montant_final, taux, depot_mensuel, date_creation
        FROM simulations
        WHERE id_utilisateur = ?
        ORDER BY date_creation DESC
        """, (st.session_state.user_id,))

        simulations = cursor.fetchall()
        conn.close()

        if simulations:
            df_sims = pd.DataFrame(
                simulations,
                columns=["ID", "Objectif", "Montant cible", "Montant final", "Taux (%)", "Dépôt mensuel", "Date"]
            )
            st.dataframe(df_sims, use_container_width=True)
        else:
            st.info("Aucune simulation enregistrée pour votre compte.")

    else:
        st.header("À propos")
        st.markdown("""
        **Épargne Intelligente** est une application qui vous aide à planifier votre épargne en fonction de vos objectifs financiers.
        Vous pouvez créer des simulations, comparer différents scénarios et suivre vos progrès au fil du temps.
        
        - **Technologies utilisées**: Streamlit, Pandas, Matplotlib, SQLite
        - **Version**: 1.0.0
        """)