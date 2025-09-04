import math
import streamlit as st
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta

st.set_page_config(page_title="Calculadora de Revisões", page_icon="🔧", layout="centered")
st.title("🔧 Calculadora de Revisões de Veículos")
st.caption("Informe a data de compra (e opcionalmente km atual) para ver o cronograma. "
           "Se informado, a quilometragem só antecipa a revisão se ocorrer ANTES da data oficial (o que ocorrer primeiro).")

# ---------- Entradas ----------
data_compra = st.date_input("📅 Data de compra:", format="DD/MM/YYYY")

usar_km = st.toggle("Informei a quilometragem atual")
km_atual = None
data_km = None
if usar_km:
    km_atual = st.number_input("📍 Quilometragem atual", min_value=0, step=50)
    data_km = st.date_input("📅 Data da medição da km", format="DD/MM/YYYY")

# ---------- Funções auxiliares ----------
def format_km_br(n: int) -> str:
    # 6.000, 12.000 etc.
    return f"{n:,}".replace(",", ".") + " km"

# ---------- Processamento ----------
if data_compra:
    ts_compra = pd.to_datetime(data_compra)
    hoje = pd.to_datetime(date.today())

    # Tabela de revisões: (número, meses, km-meta)
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

    # Média km/dia (opcional e validada)
    media_km_dia = None
    if usar_km and data_km is not None:
        ts_km = pd.to_datetime(data_km)
        # validação básica: medição não pode ser antes da compra
        if ts_km < ts_compra:
            st.warning("⚠️ A 'Data da medição da km' é anterior à data de compra. "
                       "A previsão por quilometragem será ignorada.")
        else:
            dias_passados = (ts_km - ts_compra).days
            if dias_passados > 0 and km_atual is not None and km_atual > 0:
                media_km_dia = km_atual / dias_passados
            elif km_atual is not None and km_atual == 0:
                media_km_dia = 0.0  # não roda nada por dia (evita divisão por zero)

    linhas = []
    for numero, meses, km_meta in intervalos:
        data_oficial = ts_compra + relativedelta(months=meses)  # Timestamp
        data_prevista = data_oficial
        base = "⏳ Prazo (meses)"

        # Previsão por km: só considerar se temos média > 0 e uma medição válida
        if media_km_dia is not None and media_km_dia > 0 and usar_km and data_km is not None and ts_km >= ts_compra:
            falta_km = km_meta - (km_atual or 0)

            # Calcular o dia (inteiro) em que a meta é/foi atingida
            if falta_km >= 0:
                dias_para_atingir = math.ceil(falta_km / media_km_dia)
            else:
                # já passou da meta -> estimar quando isso aconteceu (no passado)
                dias_para_atingir = math.floor(falta_km / media_km_dia)

            data_por_km = ts_km + pd.Timedelta(days=int(dias_para_atingir))

            # Só antecipa se a data por km ocorrer ANTES da data oficial
            if data_por_km < data_oficial:
                data_prevista = data_por_km
                base = "📍 Quilometragem"

        # Status
        if data_prevista < hoje:
            status = "❌ Atrasada"
        elif data_prevista == hoje:
            status = "⚠️ Hoje"
        else:
            status = "✔️ Em dia"

        faltam_dias = int((data_prevista - hoje).days)

        linhas.append({
            "Revisão": numero,
            "Tipo": f"{meses} meses ou {format_km_br(km_meta)}",
            "Data oficial (fabricante)": data_oficial,
            "Data prevista": data_prevista,
            "Base": base,
            "Status": status,
            "Faltam (dias)": faltam_dias
        })

    df = pd.DataFrame(linhas).sort_values("Revisão").reset_index(drop=True)

    st.subheader("📌 Cronograma de Revisões")
    st.dataframe(
        df,
        hide_index=True,
        column_config={
            "Data oficial (fabricante)": st.column_config.DateColumn("Data oficial (fabricante)", format="DD/MM/YYYY"),
            "Data prevista": st.column_config.DateColumn("Data prevista", format="DD/MM/YYYY"),
            "Faltam (dias)": st.column_config.NumberColumn("Faltam (dias)", help="Dias a partir de hoje"),
        },
        use_container_width=True,
    )

    # Destaque: revisões em atraso
    atrasadas = df[df["Status"] == "❌ Atrasada"]
    if not atrasadas.empty:
        st.markdown("### 🔴 Revisões em atraso")
        for _, row in atrasadas.iterrows():
            st.markdown(
                f"<span style='color:#d00000; font-weight:700;'>"
                f"Revisão {int(row['Revisão'])} — {row['Tipo']}: "
                f"{row['Data prevista'].strftime('%d/%m/%Y')} ({row['Base']})</span>",
                unsafe_allow_html=True
            )

    # Download do CSV
    csv = df.copy()
    csv["Data oficial (fabricante)"] = csv["Data oficial (fabricante)"].dt.strftime("%d/%m/%Y")
    csv["Data prevista"] = csv["Data prevista"].dt.strftime("%d/%m/%Y")
    st.download_button(
        "💾 Baixar cronograma (CSV)",
        data=csv.to_csv(index=False).encode("utf-8"),
        file_name="cronograma_revisoes.csv",
        mime="text/csv",
    )

    # Info extra
    if media_km_dia is not None:
        st.caption(f"Média estimada: {media_km_dia:.1f} km/dia (calculada entre {ts_compra.strftime('%d/%m/%Y')} "
                   f"e {ts_km.strftime('%d/%m/%Y')}).")
else:
    st.info("Selecione a data de compra para gerar o cronograma.")
