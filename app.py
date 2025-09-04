import streamlit as st
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta

st.set_page_config(page_title="Calculadora de Revisões", page_icon="🔧", layout="centered")
st.title("🔧 Calculadora de Revisões de Veículos")
st.caption("Insira a data de compra e veja o cronograma de revisões. Datas passadas são destacadas em vermelho.")

# Entrada da data de compra
data_compra = st.date_input("📅 Selecione a data de compra:", format="DD/MM/YYYY")

if data_compra:
    # Intervalos em meses (ex.: 6 meses ou 1k, 12 meses ou 6k, etc.)
    intervalos = [
        (1, 6, "1k"),
        (2, 12, "6k"),
        (3, 18, "12k"),
        (4, 24, "18k"),
        (5, 30, "24k"),
        (6, 36, "30k"),
        (7, 42, "36k"),
        (8, 48, "42k"),
        (9, 54, "48k"),
    ]

    hoje = date.today()
    linhas = []
    for numero, meses, km in intervalos:
        data_rev = data_compra + relativedelta(months=meses)
        status = "❌ Atrasada" if data_rev < hoje else ("⚠️ Hoje" if data_rev == hoje else "✔️ Em dia")
        faltam_dias = (data_rev - hoje).days
        linhas.append({
            "Revisão": numero,
            "Tipo": f"{meses} meses ou {km}",
            "Data da Revisão": pd.to_datetime(data_rev),
            "Status": status,
            "Faltam (dias)": faltam_dias
        })

    df = pd.DataFrame(linhas).sort_values("Revisão").reset_index(drop=True)

    st.subheader("📌 Cronograma de Revisões")
    st.dataframe(
        df,
        hide_index=True,
        column_config={
            "Data da Revisão": st.column_config.DateColumn("Data da Revisão", format="DD/MM/YYYY"),
            "Faltam (dias)": st.column_config.NumberColumn("Faltam (dias)", help="Número de dias a partir de hoje"),
        },
        use_container_width=True,
    )

    # Destaque visual: listar as atrasadas com texto vermelho
    atrasadas = df[df["Status"].str.contains("Atrasada")]
    if not atrasadas.empty:
        st.markdown("### 🔴 Revisões em atraso")
        for _, row in atrasadas.iterrows():
            st.markdown(
                f"<span style='color:#d00000; font-weight:700;'>Revisão {int(row['Revisão'])} — {row['Tipo']}: "
                f"{row['Data da Revisão'].date().strftime('%d/%m/%Y')} (atrasada)</span>",
                unsafe_allow_html=True
            )

    # Download do CSV
    csv = df.copy()
    csv["Data da Revisão"] = csv["Data da Revisão"].dt.strftime("%d/%m/%Y")
    st.download_button(
        "💾 Baixar cronograma (CSV)",
        data=csv.to_csv(index=False).encode("utf-8"),
        file_name="cronograma_revisoes.csv",
        mime="text/csv",
    )

    st.caption("Obs.: As datas são calculadas por meses corridos a partir da data de compra (relativedelta).")
else:
    st.info("Selecione a data de compra para gerar o cronograma.")
