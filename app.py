import streamlit as st
import pandas as pd
import plotly.express as px
import unicodedata

st.set_page_config(page_title="Dashboard Personal Eventual", layout="wide")

st.title("📊 Dashboard Personal Eventual")
st.caption("Control interno de jornales, cobertura y seguimiento de personal")

# LINKS CSV POR HOJA
URL_KPIS = "https://docs.google.com/spreadsheets/d/1Ths5IKfLsLnBovb7l-Z-X8PgQ4VK6v0ombUThG375JE/export?format=csv&gid=0"

# IMPORTANTE:
# Estos dos links los tenemos que reemplazar por el gid correcto de cada hoja.
URL_DATOS = "PEGAR_ACA_LINK_CSV_DE_DATOS_MENSUALES"
URL_SEGUIMIENTO = "PEGAR_ACA_LINK_CSV_DE_SEGUIMIENTO"

def normalizar(texto):
    texto = str(texto).replace("\xa0", " ").strip().lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = " ".join(texto.split())
    return texto

def preparar_columnas(df):
    df.columns = df.columns.astype(str).str.strip()
    df = df.rename(columns={
        "Tipo de servicio ": "Tipo de servicio",
        "Presto Servicio": "Prestó Servicio"
    })
    return df

@st.cache_data(ttl=300)
def cargar_datos():
    kpis = preparar_columnas(pd.read_csv(URL_KPIS))
    datos = preparar_columnas(pd.read_csv(URL_DATOS))
    seguimiento = preparar_columnas(pd.read_csv(URL_SEGUIMIENTO))
    return kpis, datos, seguimiento

kpis, datos, seguimiento = cargar_datos()

# Limpieza
datos["Prestó Servicio"] = datos["Prestó Servicio"].astype(str).str.strip()
datos["Jornal"] = datos["Jornal"].astype(str).str.strip()
datos["Tipo de servicio"] = datos["Tipo de servicio"].astype(str).str.strip()
datos["Turno"] = datos["Turno"].astype(str).str.strip()
datos["Categoría"] = datos["Categoría"].astype(str).str.strip()
seguimiento["Estado"] = seguimiento["Estado"].astype(str).str.strip()

# KPIs
try:
    jornales_solicitados = kpis.loc[
        kpis["Indicador"].astype(str).str.contains("Jornales Solicitados", case=False, na=False),
        "Resultado"
    ].iloc[0]
except:
    jornales_solicitados = 0

jornales_informados = len(datos)

jornales_validados = datos[
    datos["Prestó Servicio"].str.lower().str.contains("presto servicio|prestó servicio", na=False)
].shape[0]

diferencia = jornales_informados - jornales_validados

dobles = datos[datos["Jornal"].str.contains("Doble", case=False, na=False)].shape[0]
triples = datos[datos["Jornal"].str.contains("Triple", case=False, na=False)].shape[0]
extras = dobles + triples

recomendados = seguimiento[seguimiento["Estado"].str.lower() == "recomendado"].shape[0]
observados = seguimiento[seguimiento["Estado"].str.lower() == "observado"].shape[0]
no_convocar = seguimiento[seguimiento["Estado"].str.lower() == "no convocar"].shape[0]

cobertura = (jornales_validados / jornales_informados * 100) if jornales_informados > 0 else 0

# Filtros
st.sidebar.header("Filtros")

tipo_servicio = st.sidebar.multiselect(
    "Tipo de servicio",
    sorted(datos["Tipo de servicio"].dropna().unique())
)

turno = st.sidebar.multiselect(
    "Turno",
    sorted(datos["Turno"].dropna().unique())
)

categoria = st.sidebar.multiselect(
    "Categoría",
    sorted(datos["Categoría"].dropna().unique())
)

df = datos.copy()

if tipo_servicio:
    df = df[df["Tipo de servicio"].isin(tipo_servicio)]

if turno:
    df = df[df["Turno"].isin(turno)]

if categoria:
    df = df[df["Categoría"].isin(categoria)]

# Tarjetas
st.subheader("Indicadores principales")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Jornales solicitados", jornales_solicitados)
col2.metric("Jornales informados GG", jornales_informados)
col3.metric("Jornales validados", jornales_validados)
col4.metric("Diferencia", diferencia)

col5, col6, col7, col8 = st.columns(4)
col5.metric("Dobles jornadas", dobles)
col6.metric("Triples jornadas", triples)
col7.metric("Jornales extras", extras)
col8.metric("Cobertura real", f"{cobertura:.1f}%")

col9, col10, col11 = st.columns(3)
col9.metric("Recomendados", recomendados)
col10.metric("Observados", observados)
col11.metric("No convocar", no_convocar)

st.divider()

# Gráficos
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Prestó Servicio")
    graf_servicio = df["Prestó Servicio"].value_counts().reset_index()
    graf_servicio.columns = ["Estado", "Cantidad"]
    fig = px.pie(graf_servicio, names="Estado", values="Cantidad", hole=0.4)
    st.plotly_chart(fig, use_container_width=True)

with col_b:
    st.subheader("Jornales")
    graf_jornal = df["Jornal"].value_counts().reset_index()
    graf_jornal.columns = ["Jornal", "Cantidad"]
    fig = px.bar(graf_jornal, x="Jornal", y="Cantidad", text="Cantidad")
    st.plotly_chart(fig, use_container_width=True)

col_c, col_d = st.columns(2)

with col_c:
    st.subheader("Distribución por turno")
    graf_turno = df["Turno"].value_counts().reset_index()
    graf_turno.columns = ["Turno", "Cantidad"]
    fig = px.bar(graf_turno, x="Turno", y="Cantidad", text="Cantidad")
    st.plotly_chart(fig, use_container_width=True)

with col_d:
    st.subheader("Distribución por categoría")
    graf_cat = df["Categoría"].value_counts().reset_index()
    graf_cat.columns = ["Categoría", "Cantidad"]
    fig = px.bar(graf_cat, x="Categoría", y="Cantidad", text="Cantidad")
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Distribución por tipo de servicio")
graf_tipo = df["Tipo de servicio"].value_counts().reset_index()
graf_tipo.columns = ["Tipo de servicio", "Cantidad"]
fig = px.bar(graf_tipo, x="Cantidad", y="Tipo de servicio", orientation="h", text="Cantidad")
st.plotly_chart(fig, use_container_width=True)

st.divider()

st.subheader("Base filtrada")
st.dataframe(df, use_container_width=True)
