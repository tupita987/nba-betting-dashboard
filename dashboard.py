import streamlit as st
import pandas as pd
from scipy.stats import norm

# ======================================================
# CONFIGURATION STREAMLIT (OBLIGATOIRE EN PREMIER)
# ======================================================
st.set_page_config(
    page_title="Tableau de bord Paris NBA",
    layout="wide"
)

# ======================================================
# CHARGEMENT DES DONNEES (CLOUD SAFE - PARQUET)
# ======================================================
@st.cache_data
def charger_donnees():
    matchs = pd.read_parquet("data_export/games.parquet")
    moyennes = pd.read_parquet("data_export/agg.parquet")
    defenses = pd.read_parquet("data_export/defense.parquet")
    props = pd.read_parquet("data_export/props.parquet")
    return matchs, moyennes, defenses, props

matchs, moyennes, defenses, props = charger_donnees()

# ======================================================
# COEFFICIENT DEFENSIF
# ======================================================
defenses["COEF_DEF"] = defenses["DEF_RATING"] / defenses["DEF_RATING"].mean()

# ======================================================
# TITRE
# ======================================================
st.title("Tableau de bord Paris NBA")
st.write("Analyse des joueurs NBA basee sur les 7 derniers matchs")

st.divider()

# ===============================
