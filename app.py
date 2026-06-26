import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard Personal Eventual", layout="wide")

st.title("📊 Dashboard Personal Eventual")
st.caption("Control interno de personal eventual - Grupo Gestión")

URL_KPIS = "https://docs.google.com/spreadsheets/d/1Ths5IKfLsLnBovb7l-Z-X8PgQ4VK6v0ombUThG375JE/export?format=csv&gid=0"
URL_DATOS = "https://docs.google.com/spreadsheets/d/1Ths5IKfLsLnBovb7l-Z-X8PgQ4VK6v0ombUThG375JE/export?format=csv&gid=1321247605"
URL_SEGUIMIENTO = "https://docs.google.com/spreadsheets/d/1Ths5IKfLsLnBovb7l-Z-X8PgQ4VK6v0ombUThG375JE/export?format=csv&gid=1937869204"

@st.cache_data(ttl=300)
def cargar_datos():
    kpis = pd.read_csv(URL_KPIS).dropna(how="all")
    datos = pd.read_csv(URL_DATOS).dropna(how="all")
    seguimiento = pd.read_csv(URL_SEGUIMIENTO).dropna(how="all")

    kpis.columns = kpis.columns.astype(str).str.strip()
    datos.columns = datos.columns.astype(str).str.strip()
    seguimiento.columns = seguimiento.columns.astype(str).str.strip()

    return kpis, datos, seguimiento

kpis, datos, seguimiento = cargar_datos()

st.subheader("Indicadores principales")

# Detecta columnas de KPIs
col_indicador = None
col_resultado = None

for col in kpis.columns:
    if "indicador" in col.lower():
        col_indicador = col
    if "resultado" in col.lower():
        col_resultado = col

if col_indicador is None or col_resultado is None:
    st.error("No encontré las columnas Indicador y Resultado en la Hoja 1.")
    st.write("Columnas encontradas:")
    st.write(list(kpis.columns))
    st.stop()

kpis_limpios = kpis[[col_indicador, col_resultado]].dropna()

# Tarjetas dinámicas
cantidad_columnas = 4
filas = [
    kpis_limpios.iloc[i:i + cantidad_columnas]
    for i in range(0, len(kpis_limpios), cantidad_columnas)
]

for fila in filas:
    cols = st.columns(cantidad_columnas)
    for i, (_, row) in enumerate(fila.iterrows()):
        indicador = str(row[col_indicador])
        resultado = row[col_resultado]
        cols[i].metric(indicador, resultado)

st.divider()

# Preparar hoja de datos
datos.columns = datos.columns.astype(str).str.strip()

# Renombres posibles
datos = datos.rename(columns={
    "Presto Servicio": "Prestó Servicio",
    "Tipo de servicio ": "Tipo de servicio",
    "Categoria": "Categoría"
})

st.sidebar.header("Filtros")

df = datos.copy()

# Filtro fecha
if "Fecha" in df.columns:
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
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

# Filtros dinámicos
for columna in ["Tipo de servicio", "Turno", "Categoría", "Jornal", "Prestó Servicio"]:
    if columna in df.columns:
        opciones = sorted(df[columna].dropna().astype(str).unique())
        seleccion = st.sidebar.multiselect(columna, opciones)

        if seleccion:
            df = df[df[columna].astype(str).isin(seleccion)]

# Buscar colaborador
if "Apellido y Nombre" in df.columns:
    buscar = st.sidebar.text_input("Buscar colaborador")
    if buscar:
        df = df[df["Apellido y Nombre"].astype(str).str.contains(buscar, case=False, na=False)]

st.subheader("Gráficos")

col1, col2 = st.columns(2)

with col1:
    if "Prestó Servicio" in df.columns:
        st.markdown("### Prestó Servicio")
        graf = df["Prestó Servicio"].astype(str).value_counts().reset_index()
        graf.columns = ["Estado", "Cantidad"]
        fig = px.pie(graf, names="Estado", values="Cantidad", hole=0.4)
        st.plotly_chart(fig, use_container_width=True)

with col2:
    if "Jornal" in df.columns:
        st.markdown("### Jornales")
        graf = df["Jornal"].astype(str).value_counts().reset_index()
        graf.columns = ["Jornal", "Cantidad"]
        fig = px.bar(graf, x="Jornal", y="Cantidad", text="Cantidad")
        st.plotly_chart(fig, use_container_width=True)

col3, col4 = st.columns(2)

with col3:
    if "Turno" in df.columns:
        st.markdown("### Distribución por turno")
        graf = df["Turno"].astype(str).value_counts().reset_index()
        graf.columns = ["Turno", "Cantidad"]
        fig = px.bar(graf, x="Turno", y="Cantidad", text="Cantidad")
        st.plotly_chart(fig, use_container_width=True)

with col4:
    if "Categoría" in df.columns:
        st.markdown("### Distribución por categoría")
        graf = df["Categoría"].astype(str).value_counts().reset_index()
        graf.columns = ["Categoría", "Cantidad"]
        fig = px.bar(graf, x="Categoría", y="Cantidad", text="Cantidad")
        st.plotly_chart(fig, use_container_width=True)

if "Tipo de servicio" in df.columns:
    st.markdown("### Distribución por tipo de servicio")
    graf = df["Tipo de servicio"].astype(str).value_counts().reset_index()
    graf.columns = ["Tipo de servicio", "Cantidad"]
    fig = px.bar(graf, x="Cantidad", y="Tipo de servicio", orientation="h", text="Cantidad")
    st.plotly_chart(fig, use_container_width=True)

st.divider()

st.subheader("Base filtrada")
st.dataframe(df, use_container_width=True)

st.subheader("Hoja de indicadores completa")
st.dataframe(kpis_limpios, use_container_width=True)
