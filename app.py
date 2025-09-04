import streamlit as st
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta

st.set_page_config(page_title="Calculadora de Revisões", page_icon="🔧", layout="centered")
st.title("🔧 Calculadora de Revisões de Veículos")
st.caption("Informe a data de compra (e opcionalmente km atual) para ver o cronograma de revisões.")

# Entrada da data de compra
data_compra = st.date_input("📅 Selecione a data de compra:", format="DD/MM/YYYY")

# Campos opcionais
km_atual = st.number_input("📍 Quilometragem atual (opcional)", min_value=0, step=100, value=None, placeholder="Ex.: 3500")
data_km = st.date_input("📅 Data da medição da km (opcional)", format="DD/MM/YYYY") if km_atual else None

if data_compra:
    # Definição das revisões (meses / km)
    intervalos = [
        (1, 6, 1000),
        (2, 12, 6000),
        (3, 18, 12000),
        (4, 24, 18000),
        (5, 30, 24000),
        (6, 36, 30000),
        (7, 42, 36000),
        (8, 48, 42000),
        (9, 54, 48000),
    ]

    hoje = date.today()
    linhas = []

    # Se o usuário informou km atual, calcula a média diária
    media_km_dia = None
    if km_atual and data_km:
        dias_passados = (data_km - data_compra).days
        if dias_passados > 0:
            media_km_dia = km_atual / dias_passados

    for numero, meses, km_meta in intervalos:
        # Data oficial pela regra do fabricante
        data_rev_oficial = data_compra + relativedelta(months=meses)

        data_prevista = data_rev_oficial
        motivo = "⏳ Prazo (meses)"

        # Se o usuário informou km, prever antecipação
        if media_km_dia:
            falta_km = km_meta - km_atual
            if falta_km > 0:
                dias_para_atingir = round(falta_km / media_km_dia)
                data_prevista_km = data_km + pd.Timedelta(days=dias_para_atingir)

                # Só antecipa se cair antes da data oficial
                if data_prevista_km < data_rev_oficial:
                    data_prevista = data_prevista_km.date()
                    motivo = "📍 Quilometragem"

        # Status em relação a hoje
        if data_prevista < hoje:
            status = "❌ Atrasada"
        elif data_prevista == hoje:
            status = "⚠️ Hoje"
        else:
            status = "✔️ Em dia"

        faltam_dias = (data_prevista - hoje).days

        linhas.append({
            "Revisão": numero,
            "Intervalo": f"{meses} meses ou {km_meta:,} km",
            "Data da Revisão": pd.to_datetime(data_prevista),
            "Base": motivo,
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

    # Destaque extra para revisões atrasadas
    atrasadas = df[df["Status"].str.contains("Atrasada")]
    if not atrasadas.empty:
        st.markdown("### 🔴 Revisões em atraso")
        for _, row in atrasadas.iterrows():
            st.markdown(
                f"<span style='color:#d00000; font-weight:700;'>Revisão {int(row['Revisão'])} — {row['Intervalo']}: "
                f"{row['Data da Revisão'].date().strftime('%d/%m/%Y')} ({row['Status']}, {row['Base']})</span>",
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

    st.caption("Obs.: Se informado, a quilometragem só antecipa a revisão se for antes do prazo em meses.")
else:
    st.info("Selecione a data de compra para gerar o cronograma.")
