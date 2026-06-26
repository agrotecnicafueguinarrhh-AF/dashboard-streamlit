import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard Personal Eventual", layout="wide")

URL_KPIS = "https://docs.google.com/spreadsheets/d/1Ths5IKfLsLnBovb7l-Z-X8PgQ4VK6v0ombUThG375JE/export?format=csv&gid=0"
URL_DATOS = "https://docs.google.com/spreadsheets/d/1Ths5IKfLsLnBovb7l-Z-X8PgQ4VK6v0ombUThG375JE/export?format=csv&gid=1321247605"
URL_SEGUIMIENTO = "https://docs.google.com/spreadsheets/d/1Ths5IKfLsLnBovb7l-Z-X8PgQ4VK6v0ombUThG375JE/export?format=csv&gid=1937869204"

st.markdown("""
<style>
.main {
    background-color: #eef8f4;
}
.block-container {
    padding-top: 2rem;
}
.titulo {
    font-size: 36px;
    font-weight: 800;
    color: #1f2937;
}
.subtitulo {
    color: #6b7280;
    font-size: 15px;
    margin-bottom: 25px;
}
.card {
    background-color: white;
    padding: 20px;
    border-radius: 16px;
    box-shadow: 0px 4px 12px rgba(0,0,0,0.08);
    border-left: 6px solid #8ee3a2;
}
.card-title {
    font-size: 13px;
    color: #6b7280;
    text-transform: uppercase;
    font-weight: 700;
}
.card-value {
    font-size: 30px;
    font-weight: 800;
    color: #111827;
}
.seccion {
    background-color: #1f2937;
    color: white;
    padding: 10px 16px;
    border-radius: 10px;
    font-weight: 700;
    margin-top: 20px;
    margin-bottom: 15px;
}
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def cargar_datos():
    kpis = pd.read_csv(URL_KPIS).dropna(how="all")
    datos = pd.read_csv(URL_DATOS).dropna(how="all")
    seguimiento = pd.read_csv(URL_SEGUIMIENTO).dropna(how="all")

    kpis.columns = kpis.columns.astype(str).str.strip()
    datos.columns = datos.columns.astype(str).str.strip()
    seguimiento.columns = seguimiento.columns.astype(str).str.strip()

    datos = datos.rename(columns={
        "Presto Servicio": "Prestó Servicio",
        "Tipo de servicio ": "Tipo de servicio",
        "Categoria": "Categoría"
    })

    return kpis, datos, seguimiento

kpis, datos, seguimiento = cargar_datos()

st.markdown('<div class="titulo">📊 Dashboard Personal Eventual</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitulo">Control interno de jornales, cobertura, desempeño y seguimiento de personal eventual</div>', unsafe_allow_html=True)

# Detectar columnas KPIs
col_indicador = [c for c in kpis.columns if "indicador" in c.lower()][0]
col_resultado = [c for c in kpis.columns if "resultado" in c.lower()][0]

kpis_dict = dict(zip(kpis[col_indicador].astype(str), kpis[col_resultado]))

def buscar_indicador(texto):
    for k, v in kpis_dict.items():
        if texto.lower() in k.lower():
            return v
    return 0

# KPIs ordenados como gerente
resumen = {
    "Jornales solicitados": buscar_indicador("Jornales Solicitados"),
    "Jornales informados GG": buscar_indicador("Jornales Informados"),
    "Jornales validados": buscar_indicador("Jornales Validados"),
    "Diferencia": buscar_indicador("Diferencia"),
}

operativo = {
    "Cobertura real": buscar_indicador("Cobertura"),
    "No prestó servicio": buscar_indicador("No Prestó"),
    "Dobles jornadas": buscar_indicador("Doble"),
    "Triples jornadas": buscar_indicador("Triple"),
}

seguimiento_kpis = {
    "Recomendados": buscar_indicador("Recomendado"),
    "Observados": buscar_indicador("Observado"),
    "No convocar": buscar_indicador("No Convocar"),
}

def tarjeta(titulo, valor):
    st.markdown(f"""
    <div class="card">
        <div class="card-title">{titulo}</div>
        <div class="card-value">{valor}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<div class="seccion">Resumen ejecutivo</div>', unsafe_allow_html=True)

cols = st.columns(4)
for col, (titulo, valor) in zip(cols, resumen.items()):
    with col:
        tarjeta(titulo, valor)

st.markdown('<div class="seccion">Control operativo</div>', unsafe_allow_html=True)

cols = st.columns(4)
for col, (titulo, valor) in zip(cols, operativo.items()):
    with col:
        tarjeta(titulo, valor)

st.markdown('<div class="seccion">Calidad del personal</div>', unsafe_allow_html=True)

cols = st.columns(3)
for col, (titulo, valor) in zip(cols, seguimiento_kpis.items()):
    with col:
        tarjeta(titulo, valor)

st.sidebar.header("Filtros")

df = datos.copy()

if "Fecha" in df.columns:
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    fechas = df["Fecha"].dropna()
    if not fechas.empty:
        rango = st.sidebar.date_input(
            "Rango de fechas",
            value=(fechas.min(), fechas.max()),
            min_value=fechas.min(),
            max_value=fechas.max()
        )
        if len(rango) == 2:
            df = df[(df["Fecha"] >= pd.to_datetime(rango[0])) & (df["Fecha"] <= pd.to_datetime(rango[1]))]

for columna in ["Tipo de servicio", "Turno", "Categoría", "Jornal", "Prestó Servicio"]:
    if columna in df.columns:
        opciones = sorted(df[columna].dropna().astype(str).unique())
        seleccion = st.sidebar.multiselect(columna, opciones)
        if seleccion:
            df = df[df[columna].astype(str).isin(seleccion)]

if "Apellido y Nombre" in df.columns:
    buscar = st.sidebar.text_input("Buscar colaborador")
    if buscar:
        df = df[df["Apellido y Nombre"].astype(str).str.contains(buscar, case=False, na=False)]

st.markdown('<div class="seccion">Análisis visual</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    if "Prestó Servicio" in df.columns:
        graf = df["Prestó Servicio"].astype(str).value_counts().reset_index()
        graf.columns = ["Estado", "Cantidad"]
        fig = px.pie(graf, names="Estado", values="Cantidad", hole=0.45)
        fig.update_layout(title="Prestó servicio", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

with col2:
    if "Jornal" in df.columns:
        graf = df["Jornal"].astype(str).value_counts().reset_index()
        graf.columns = ["Jornal", "Cantidad"]
        fig = px.bar(graf, x="Jornal", y="Cantidad", text="Cantidad")
        fig.update_layout(title="Tipo de jornal", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

col3, col4 = st.columns(2)

with col3:
    if "Turno" in df.columns:
        graf = df["Turno"].astype(str).value_counts().reset_index()
        graf.columns = ["Turno", "Cantidad"]
        fig = px.bar(graf, x="Turno", y="Cantidad", text="Cantidad")
        fig.update_layout(title="Distribución por turno", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

with col4:
    if "Categoría" in df.columns:
        graf = df["Categoría"].astype(str).value_counts().reset_index()
        graf.columns = ["Categoría", "Cantidad"]
        fig = px.bar(graf, x="Categoría", y="Cantidad", text="Cantidad")
        fig.update_layout(title="Distribución por categoría", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

if "Tipo de servicio" in df.columns:
    graf = df["Tipo de servicio"].astype(str).value_counts().reset_index()
    graf.columns = ["Tipo de servicio", "Cantidad"]
    fig = px.bar(graf, x="Cantidad", y="Tipo de servicio", orientation="h", text="Cantidad")
    fig.update_layout(title="Distribución por tipo de servicio", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)

st.markdown('<div class="seccion">Detalle de registros</div>', unsafe_allow_html=True)
st.dataframe(df, use_container_width=True)
