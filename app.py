from pathlib import Path

import pandas as pd
import streamlit as st

DOSSIER = Path(__file__).parent / "donnees"

st.set_page_config(page_title="L'électricité dans 12 quartiers", page_icon="⚡", layout="wide")

st.title("L'électricité dans 12 quartiers")
st.caption("Relevés mensuels de janvier 2024 à décembre 2025. Données fictives.")
st.write(
    "Une compagnie d'électricité fictive suit 12 quartiers de Port-au-Prince, "
    "Delmas, Pétion-Ville et Cap-Haïtien."
)

        # lecture du fichier propre
@st.cache_data
def charger():
    return pd.read_csv(DOSSIER / "consommation_propre.csv")


df = charger()

        # filtres dans la barre latérale
communes = sorted(df["commune"].unique())
choix = st.sidebar.multiselect("Communes", communes, default=communes)
annees = sorted(df["annee"].unique())
annee = st.sidebar.selectbox("Année", annees, index=len(annees) - 1)

if not choix:
    st.warning("Choisissez au moins une commune dans la barre latérale.")
    st.stop()

d_communes = df[df["commune"].isin(choix)]
d = d_communes[d_communes["annee"] == annee]

        # trois indicateurs
c1, c2, c3 = st.columns(3)
c1.metric("Consommation totale", f"{d['kwh'].sum() / 1e6:.2f} millions de kWh")
c2.metric("kWh par abonné", f"{d['kwh_par_abonne'].mean():.1f}")
c3.metric("Heures de courant par jour", f"{d['heures_courant'].mean():.1f}")

        # un onglet par question
t1, t2, t3, t4, t5 = st.tabs(
    ["Quartiers", "Évolution", "Chaleur ou courant ?", "Coupures", "Valeurs hors du lot"]
)

with t1:
    par_quartier = (
        d_communes.groupby("quartier")["kwh_par_abonne"].mean().round(1).sort_values(ascending=False)
    )
    st.bar_chart(par_quartier)
    st.write(
        f"{par_quartier.index[0]} consomme le plus par abonné "
        f"({par_quartier.iloc[0]} kWh en moyenne)."
    )

with t2:
    tab = d_communes.pivot_table(index="commune", columns="annee", values="kwh", aggfunc="sum")
    hausse = ((tab[2025] / tab[2024] - 1) * 100).sort_values(ascending=False)
    st.bar_chart(hausse.round(1))
    st.write(
        f"{hausse.index[0]} a la plus forte hausse entre 2024 et 2025 "
        f"({hausse.iloc[0]:.1f} %), {hausse.index[-1]} la plus faible ({hausse.iloc[-1]:.1f} %)."
    )
    par_mois = d_communes.groupby(["mois", "commune"])["kwh_par_abonne"].mean().unstack()
    st.line_chart(par_mois)

with t3:
    res = d_communes[d_communes["type"] == "Résidentiel"]
    st.scatter_chart(res, x="heures_courant", y="kwh_par_abonne")
    r_courant = res["kwh_par_abonne"].corr(res["heures_courant"])
    r_temp = res["kwh_par_abonne"].corr(res["temperature_c"])
    st.write(
        f"Quartiers résidentiels : corrélation de {r_courant:.2f} avec les heures de courant "
        f"et de {r_temp:.2f} avec la température."
    )

with t4:
    st.dataframe(
        d_communes.groupby("commune")["heures_courant"].describe()[["25%", "50%", "75%"]].round(1)
    )
    courtes = d_communes[(d_communes["annee"] == 2025) & (d_communes["heures_courant"] < 8)]
    st.write(
        f"{len(courtes)} relevés de 2025 ont moins de 8 heures de courant par jour : "
        f"{', '.join(courtes['quartier'])}."
    )

with t5:
    top3 = d_communes.nlargest(3, "kwh")[["mois", "quartier", "type", "kwh"]]
    st.dataframe(top3, hide_index=True)
    st.write(f"Le plus gros relevé est celui de {top3.iloc[0]['quartier']} en {top3.iloc[0]['mois']}.")

    #  conclusion et données
st.markdown(
    "### Conclusion\n"
    "Pour les quartiers résidentiels, la consommation par abonné suit les heures de courant "
    "(corrélation 0.76) bien plus que la chaleur (-0.15). "
    "Mais une corrélation ne prouve pas une cause."
)
with st.expander("Voir les données filtrées"):
    st.dataframe(d, hide_index=True)
