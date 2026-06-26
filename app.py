import streamlit as st
import pandas as pd
import plotly.express as px
import unicodedata

st.set_page_config(page_title="Dashboard Personal Eventual", layout="wide")

st.title("📊 Dashboard Personal Eventual")
st.caption("Control interno de jornales, cobertura y seguimiento de personal")

URL_KPIS = "https://docs.google.com/spreadsheets/d/1Ths5IKfLsLnBovb7l-Z-X8PgQ4VK6v0ombUThG375JE/export?format=csv&gid=0"
URL_DATOS = "https://docs.google.com/spreadsheets/d/1Ths5IKfLsLnBovb7l-Z-X8PgQ4VK6v0ombUThG375JE/export?format=csv&gid=1321247605"
URL_SEGUIMIENTO = "https://docs.google.com/spreadsheets/d/1Ths5IKfLsLnBovb7l-Z-X8PgQ4VK6v0ombUThG375JE/export?format=csv&gid=1937869204"

def limpiar_texto(x):
    if pd.isna(x):
        return ""
    return str(x).strip()

@st.cache_data(ttl=300)
def cargar_datos():
    kpis = pd.read_csv(URL_KPIS)
    datos = pd.read_csv(URL_DATOS)
    seguimiento = pd.read_csv(URL_SEGUIMIENTO)

    kpis.columns = kpis.columns.astype(str).str.strip()
    datos.columns = datos.columns.astype(str).str.strip()
    seguimiento.columns = seguimiento.columns.astype(str).str.strip()

    datos = datos.rename(columns={
        "Tipo de servicio ": "Tipo de servicio",
        "Presto Servicio": "Prestó Servicio"
    })

    datos = datos.dropna(how="all")
    seguimiento = seguimiento.dropna(how="all")

    return kpis, datos, seguimiento

kpis, datos, seguimiento = cargar_datos()

# Limpieza de columnas principales
datos["Fecha"] = pd.to_datetime(datos["Fecha"], errors="coerce")
datos["Apellido y Nombre"] = datos["Apellido y Nombre"].apply(limpiar_texto)
datos["Categoría"] = datos["Categoría"].apply(limpiar_texto)
datos["Turno"] = datos["Turno"].apply(limpiar_texto)
datos["Citado"] = datos["Citado"].apply(limpiar_texto)
datos["Jornal"] = datos["Jornal"].apply(limpiar_texto)
datos["Prestó Servicio"] = datos["Prestó Servicio"].apply(limpiar_texto)
datos["Tipo de servicio"] = datos["Tipo de servicio"].apply(limpiar_texto)

seguimiento["Estado"] = seguimiento["Estado"].apply(limpiar_texto)

# Filtros
st.sidebar.header("Filtros")

df = datos.copy()

fechas_validas = df["Fecha"].dropna()

if not fechas_validas.empty:
    fecha_min = fechas_validas.min()
    fecha_max = fechas_validas.max()

    rango_fechas = st.sidebar.date_input(
        "Rango de fechas",
        value=(fecha_min, fecha_max),
        min_value=fecha_min,
        max_value=fecha_max
    )

    if len(rango_fechas) == 2:
        desde = pd.to_datetime(rango_fechas[0])
        hasta = pd.to_datetime(rango_fechas[1])
        df = df[(df["Fecha"] >= desde) & (df["Fecha"] <= hasta)]

tipo_servicio = st.sidebar.multiselect(
    "Tipo de servicio",
    sorted(df["Tipo de servicio"].dropna().unique())
)

turno = st.sidebar.multiselect(
    "Turno",
    sorted(df["Turno"].dropna().unique())
)

categoria = st.sidebar.multiselect(
    "Categoría",
    sorted(df["Categoría"].dropna().unique())
)

if tipo_servicio:
    df = df[df["Tipo de servicio"].isin(tipo_servicio)]

if turno:
    df = df[df["Turno"].isin(turno)]

if categoria:
    df = df[df["Categoría"].isin(categoria)]

# KPIs principales
try:
    jornales_solicitados = kpis.loc[
        kpis["Indicador"].astype(str).str.contains("Jornales Solicitados", case=False, na=False),
        "Resultado"
    ].iloc[0]
except:
    jornales_solicitados = 0

jornales_informados = len(df)

jornales_validados = df[
    df["Prestó Servicio"].str.lower().str.contains("presto servicio|prestó servicio", na=False)
].shape[0]

no_presto = df[
    df["Prestó Servicio"].str.lower().str.contains("no presto servicio|no prestó servicio", na=False)
].shape[0]

diferencia = jornales_informados - jornales_validados

dobles = df[df["Jornal"].str.contains("Doble", case=False, na=False)].shape[0]
triples = df[df["Jornal"].str.contains("Triple", case=False, na=False)].shape[0]
extras = dobles + triples

recomendados = seguimiento[seguimiento["Estado"].str.lower() == "recomendado"].shape[0]
observados = seguimiento[seguimiento["Estado"].str.lower() == "observado"].shape[0]
no_convocar = seguimiento[seguimiento["Estado"].str.lower() == "no convocar"].shape[0]

cobertura = (jornales_validados / jornales_informados * 100) if jornales_informados > 0 else 0

# Tarjetas
st.subheader("Indicadores principales")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Jornales solicitados", jornales_solicitados)
col2.metric("Jornales informados GG", jornales_informados)
col3.metric("Jornales validados", jornales_validados)
col4.metric("Diferencia", diferencia)

col5, col6, col7, col8 = st.columns(4)
col5.metric("No prestó servicio", no_presto)
col6.metric("Dobles jornadas", dobles)
col7.metric("Triples jornadas", triples)
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
graf_tipo = df["Tipo de servicio"].replace("", "Sin dato").value_counts().reset_index()
graf_tipo.columns = ["Tipo de servicio", "Cantidad"]
fig = px.bar(graf_tipo, x="Cantidad", y="Tipo de servicio", orientation="h", text="Cantidad")
st.plotly_chart(fig, use_container_width=True)

st.divider()

st.subheader("Base filtrada")
st.dataframe(df, use_container_width=True)
