import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard Personal Eventual", layout="wide")

URL_KPIS = "https://docs.google.com/spreadsheets/d/1Ths5IKfLsLnBovb7l-Z-X8PgQ4VK6v0ombUThG375JE/export?format=csv&gid=0"
URL_DATOS = "https://docs.google.com/spreadsheets/d/1Ths5IKfLsLnBovb7l-Z-X8PgQ4VK6v0ombUThG375JE/export?format=csv&gid=1321247605"
URL_SEGUIMIENTO = "https://docs.google.com/spreadsheets/d/1Ths5IKfLsLnBovb7l-Z-X8PgQ4VK6v0ombUThG375JE/export?format=csv&gid=1937869204"

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #f3f0fa 0%, #eef3ef 55%, #e4f4ea 100%);
}
.block-container {
    padding-top: 2rem;
}
[data-testid="stSidebar"] {
    background-color: #30264f;
}
[data-testid="stSidebar"] * {
    color: white;
}
.titulo {
    font-size: 38px;
    font-weight: 800;
    color: #2e254f;
}
.subtitulo {
    font-size: 15px;
    color: #6b647a;
    margin-bottom: 25px;
}
.seccion {
    background: #d8cdec;
    color: #2e254f;
    padding: 10px 16px;
    border-radius: 10px;
    font-weight: 800;
    margin-top: 20px;
    margin-bottom: 15px;
}
.card {
    background: white;
    border-radius: 16px;
    padding: 18px;
    box-shadow: 0px 4px 14px rgba(45, 37, 79, 0.15);
    border-bottom: 5px solid #59b887;
    min-height: 120px;
}
.card-title {
    font-size: 13px;
    color: #4b3d6d;
    font-weight: 800;
}
.card-value {
    font-size: 30px;
    color: #2e254f;
    font-weight: 900;
    margin-top: 10px;
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
        "Tipo de servicio ": "Tipo de servicio",
        "Presto Servicio": "Prestó Servicio",
        "Categoria": "Categoría",
        "Cobertura por": "Motivo de cobertura"
    })

    return kpis, datos, seguimiento

kpis, datos, seguimiento = cargar_datos()

st.markdown('<div class="titulo">📊 Dashboard Personal Eventual</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitulo">Control interno de jornales, cobertura, desempeño y seguimiento de personal eventual</div>', unsafe_allow_html=True)

# KPIs hoja 1
col_indicador = next((c for c in kpis.columns if "indicador" in c.lower()), None)
col_resultado = next((c for c in kpis.columns if "resultado" in c.lower()), None)

if col_indicador and col_resultado:
    kpis_mostrar = kpis[[col_indicador, col_resultado]].dropna()
else:
    kpis_mostrar = pd.DataFrame(columns=["Indicador", "Resultado"])

st.markdown('<div class="seccion">Resumen ejecutivo</div>', unsafe_allow_html=True)

cols_por_fila = 4
for i in range(0, len(kpis_mostrar), cols_por_fila):
    cols = st.columns(cols_por_fila)
    fila = kpis_mostrar.iloc[i:i + cols_por_fila]

    for col, (_, row) in zip(cols, fila.iterrows()):
        indicador = str(row[col_indicador])
        resultado = row[col_resultado]
        with col:
            st.markdown(f"""
            <div class="card">
                <div class="card-title">{indicador}</div>
                <div class="card-value">{resultado}</div>
            </div>
            """, unsafe_allow_html=True)

# Datos
df = datos.copy()

st.sidebar.header("Filtros")

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

for columna in ["Tipo de servicio", "Motivo de cobertura", "Turno", "Categoría", "Jornal", "Prestó Servicio"]:
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
        graf = df["Prestó Servicio"].astype(str).replace("nan", "Sin dato").value_counts().reset_index()
        graf.columns = ["Estado", "Cantidad"]
        fig = px.pie(graf, names="Estado", values="Cantidad", hole=0.45)
        fig.update_layout(title="Prestó servicio", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

with col2:
    if "Jornal" in df.columns:
        graf = df["Jornal"].astype(str).replace("nan", "Sin dato").value_counts().reset_index()
        graf.columns = ["Jornal", "Cantidad"]
        fig = px.bar(graf, x="Jornal", y="Cantidad", text="Cantidad")
        fig.update_layout(title="Tipo de jornal", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

col3, col4 = st.columns(2)

with col3:
    if "Turno" in df.columns:
        graf = df["Turno"].astype(str).replace("nan", "Sin dato").value_counts().reset_index()
        graf.columns = ["Turno", "Cantidad"]
        fig = px.bar(graf, x="Turno", y="Cantidad", text="Cantidad")
        fig.update_layout(title="Distribución por turno", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

with col4:
    if "Categoría" in df.columns:
        graf = df["Categoría"].astype(str).replace("nan", "Sin dato").value_counts().reset_index()
        graf.columns = ["Categoría", "Cantidad"]
        fig = px.bar(graf, x="Categoría", y="Cantidad", text="Cantidad")
        fig.update_layout(title="Distribución por categoría", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

if "Tipo de servicio" in df.columns:
    graf = df["Tipo de servicio"].astype(str).replace("nan", "Sin dato").value_counts().reset_index()
    graf.columns = ["Tipo de servicio", "Cantidad"]
    fig = px.bar(graf, x="Cantidad", y="Tipo de servicio", orientation="h", text="Cantidad")
    fig.update_layout(title="Distribución por tipo de servicio", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)

if "Motivo de cobertura" in df.columns:
    graf = df["Motivo de cobertura"].astype(str).replace("nan", "Sin dato").value_counts().reset_index()
    graf.columns = ["Motivo de cobertura", "Cantidad"]
    fig = px.bar(graf, x="Cantidad", y="Motivo de cobertura", orientation="h", text="Cantidad")
    fig.update_layout(title="Motivos de cobertura", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)

st.markdown('<div class="seccion">Detalle de registros</div>', unsafe_allow_html=True)
st.dataframe(df, use_container_width=True)

st.markdown('<div class="seccion">Indicadores hoja 1</div>', unsafe_allow_html=True)
st.dataframe(kpis_mostrar, use_container_width=True)
