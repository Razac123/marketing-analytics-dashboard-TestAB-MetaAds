# dashboard_marketing.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Dashboard d'Analyse Marketing",
    page_icon="📊",
    layout="wide"
)

# --- FONCTION DE CHARGEMENT ET NETTOYAGE (AVEC CACHE) ---
# Le cache permet de ne pas recharger et nettoyer les données à chaque interaction
@st.cache_data
def load_and_clean_data(file_path):
    """Charge les données depuis un fichier CSV et effectue le nettoyage."""
    data = pd.read_csv(file_path)
    
    # 1. Supprimer les colonnes entièrement vides
    cols_to_drop = [col for col in data.columns if data[col].count() == 0]
    data.drop(columns=cols_to_drop, inplace=True)
    
    # 2. Supprimer les colonnes redondantes
    redundant_cols = ['Ads', 'Ad name', 'Delivery level', 'Attribution setting', 'Objective.1', 'Reporting starts', 'Reporting ends']
    existing_redundant_cols = [col for col in redundant_cols if col in data.columns]
    data.drop(columns=existing_redundant_cols, inplace=True)
    
    # 3. Remplacer les NaN numériques par 0
    numeric_cols = data.select_dtypes(include=np.number).columns
    data[numeric_cols] = data[numeric_cols].fillna(0)
    
    # 4. Conversion des types
    data['Day'] = pd.to_datetime(data['Day'])
    count_cols = ['Results', 'Reach', 'Impressions', 'Link clicks', 'Clicks (all)', 'Landing page views', 'Content views', 'Website content views']
    for col in count_cols:
        if col in data.columns:
            data[col] = data[col].astype(int)
            
    return data

# --- CHARGEMENT DES DONNÉES ---
# ATTENTION : Assurez-vous que votre fichier s'appelle bien 'ab_data.csv'
try:
    df = load_and_clean_data('ab_data.csv')
except FileNotFoundError:
    st.error("Erreur : Le fichier de données 'ab_data.csv' n'a pas été trouvé. Assurez-vous qu'il se trouve dans le même dossier que le script.")
    st.stop()


# --- BARRE LATÉRALE POUR LES FILTRES ---
st.sidebar.header("Filtres Interactifs")

# Filtre par Campagne
selected_campaign = st.sidebar.multiselect(
    'Sélectionner la Campagne',
    options=df['Campaign name'].unique(),
    default=df['Campaign name'].unique()
)

# Filtre par Ensemble de Publicités
selected_ad_set = st.sidebar.multiselect(
    'Sélectionner l\'Ensemble de Publicités',
    options=df['Ad Set Name'].unique(),
    default=df['Ad Set Name'].unique()
)

# Filtre par Genre
selected_gender = st.sidebar.multiselect(
    'Sélectionner le Genre',
    options=df['Gender'].unique(),
    default=df['Gender'].unique()
)

# Filtre par Âge
selected_age = st.sidebar.multiselect(
    'Sélectionner la Tranche d\'Âge',
    options=df['Age'].unique(),
    default=df['Age'].unique()
)

# Filtre par Date
min_date = df['Day'].min()
max_date = df['Day'].max()
selected_date_range = st.sidebar.date_input(
    'Sélectionner une plage de dates',
    [min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

# --- APPLICATION DES FILTRES ---
df_filtered = df[
    df['Campaign name'].isin(selected_campaign) &
    df['Ad Set Name'].isin(selected_ad_set) &
    df['Gender'].isin(selected_gender) &
    df['Age'].isin(selected_age) &
    (df['Day'] >= pd.to_datetime(selected_date_range[0])) &
    (df['Day'] <= pd.to_datetime(selected_date_range[1]))
]

if df_filtered.empty:
    st.warning("Aucune donnée disponible pour les filtres sélectionnés.")
    st.stop()

# --- AFFICHAGE DU DASHBOARD ---
st.title("📊 Dashboard d'Analyse des Performances Marketing")
st.markdown("Utilisez les filtres dans la barre latérale pour explorer les données.")


# --- KPIs PRINCIPAUX ---
st.header("Vue d'Ensemble des Performances")

total_spent = df_filtered['Amount spent (USD)'].sum()
total_impressions = df_filtered['Impressions'].sum()
total_link_clicks = df_filtered['Link clicks'].sum()

# Calculs sécurisés pour éviter la division par zéro
cpc = total_spent / total_link_clicks if total_link_clicks > 0 else 0
ctr = (total_link_clicks / total_impressions) * 100 if total_impressions > 0 else 0
cpm = (total_spent / total_impressions) * 1000 if total_impressions > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Montant Dépensé (USD)", f"${total_spent:,.2f}")
col2.metric("Clics sur le lien", f"{total_link_clicks:,}")
col3.metric("CPC Moyen", f"${cpc:,.2f}")
col4.metric("CTR Moyen", f"{ctr:,.2f}%")


# --- GRAPHIQUES ---
st.header("Analyse Détaillée")

# 1. Analyse Temporelle
daily_performance = df_filtered.groupby('Day').agg({'Amount spent (USD)': 'sum', 'Link clicks': 'sum'}).reset_index()
fig_temporal = px.line(daily_performance, x='Day', y=['Amount spent (USD)', 'Link clicks'], 
                       title="Évolution Journalière des Dépenses et des Clics",
                       labels={'value': 'Valeur', 'variable': 'Métrique'},
                       markers=True)
fig_temporal.update_layout(yaxis_title=None)
st.plotly_chart(fig_temporal, use_container_width=True)


# 2. Analyse par Ensemble de Publicités
col_perf, col_budget = st.columns(2)

with col_perf:
    st.subheader("Performance par Ensemble de Publicités")
    ad_set_perf = df_filtered.groupby('Ad Set Name').agg({
        'Amount spent (USD)': 'sum',
        'Link clicks': 'sum',
        'Impressions': 'sum'
    }).reset_index()
    ad_set_perf['CPC'] = ad_set_perf['Amount spent (USD)'] / ad_set_perf['Link clicks']
    ad_set_perf['CTR'] = (ad_set_perf['Link clicks'] / ad_set_perf['Impressions']) * 100
    ad_set_perf.fillna(0, inplace=True)
    
    fig_ad_set_cpc = px.bar(ad_set_perf.sort_values('CPC'), x='CPC', y='Ad Set Name', 
                            orientation='h', title="CPC par Ensemble de Publicités",
                            color='CPC', color_continuous_scale='Reds')
    st.plotly_chart(fig_ad_set_cpc, use_container_width=True)

with col_budget:
    st.subheader("Répartition du Budget")
    fig_ad_set_budget = px.pie(ad_set_perf, names='Ad Set Name', values='Amount spent (USD)',
                               title="Répartition des Dépenses par Ensemble de Publicités")
    st.plotly_chart(fig_ad_set_budget, use_container_width=True)


# --- VUE DES DONNÉES BRUTES ---
with st.expander("Voir les données filtrées"):
    st.dataframe(df_filtered)