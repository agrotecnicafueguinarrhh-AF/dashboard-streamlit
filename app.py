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
    background: #f4f1f8;
}
.block-container {
    padding-top: 2rem;
    padding-left: 3rem;
    padding-right: 3rem;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #25164f, #3d2b6f);
}
[data-testid="stSidebar"] * {
    color: white;
}
.titulo {
    font-size: 38px;
    font-weight: 900;
    color: #25164f;
    margin-bottom: 0px;
}
.subtitulo {
    color: #5f5870;
    font-size: 15px;
    margin-bottom: 25px;
}
.card {
    background: white;
    border-radius: 18px;
    padding: 18px 20px;
    min-height: 125px;
    box-shadow: 0px 4px 18px rgba(37, 22, 79, 0.12);
    border-bottom: 5px solid #39a96b;
    margin-bottom: 16px;
}
.card-title {
    font-size: 13px;
    font-weight: 800;
    color: #25164f;
    min-height: 38px;
}
.card-value {
    font-size: 34px;
    font-weight: 900;
    color: #25164f;
    margin-top: 8px;
}
.chart-card {
    background: white;
    border-radius: 18px;
    padding: 18px;
    box-shadow: 0px 4px 18px rgba(37, 22, 79, 0.10);
    margin-bottom: 18px;
}
.seccion {
    font-size: 18px;
    font-weight: 900;
    color: #25164f;
    margin-top: 20px;
    margin-bottom: 10px;
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
        "Categoria": "Categoría",
        "Cobertura por": "Motivo de cobertura",
        "Motivo cobertura": "Motivo de cobertura",
        "Motivo de Cobertura": "Motivo de cobertura"
    })

    return kpis, datos, seguimiento

kpis, datos, seguimiento = cargar_datos()

st.markdown('<div class="titulo">📊 Dashboard Personal Eventual</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitulo">Control interno de jornales, cobertura, desempeño y seguimiento de personal eventual</div>', unsafe_allow_html=True)

# =========================
# FILTROS
# =========================

df = datos.copy()

st.sidebar.title("Filtros")

if "Fecha" in df.columns:
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    fechas_validas = df["Fecha"].dropna()

    if not fechas_validas.empty:
        rango = st.sidebar.date_input(
            "Rango de fechas",
            value=(fechas_validas.min(), fechas_validas.max()),
            min_value=fechas_validas.min(),
            max_value=fechas_validas.max()
        )

        if len(rango) == 2:
            desde = pd.to_datetime(rango[0])
            hasta = pd.to_datetime(rango[1])
            df = df[(df["Fecha"] >= desde) & (df["Fecha"] <= hasta)]

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

# =========================
# KPIS EN CUADRITOS
# =========================

st.markdown('<div class="seccion">Resumen ejecutivo</div>', unsafe_allow_html=True)

col_indicador = next((c for c in kpis.columns if "indicador" in c.lower()), None)
col_resultado = next((c for c in kpis.columns if "resultado" in c.lower()), None)

if col_indicador and col_resultado:
    kpis_mostrar = kpis[[col_indicador, col_resultado]].dropna()

    cols_por_fila = 5

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
else:
    st.error("No encontré las columnas Indicador y Resultado en la Hoja 1.")

# =========================
# GRÁFICOS
# =========================

st.markdown('<div class="seccion">Análisis visual</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    if "Prestó Servicio" in df.columns:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)

        graf = df["Prestó Servicio"].astype(str).replace("nan", "Sin dato").value_counts().reset_index()
        graf.columns = ["Estado", "Cantidad"]

        fig = px.pie(
            graf,
            names="Estado",
            values="Cantidad",
            hole=0.55,
            title="Prestó Servicio",
            color_discrete_sequence=["#39a96b", "#7e57c2", "#bdbdbd"]
        )

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#25164f"
        )

        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

with col2:
    if "Jornal" in df.columns:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)

        graf = df["Jornal"].astype(str).replace("nan", "Sin dato").value_counts().reset_index()
        graf.columns = ["Jornal", "Cantidad"]

        fig = px.bar(
            graf,
            x="Jornal",
            y="Cantidad",
            text="Cantidad",
            title="Tipo de jornal",
            color_discrete_sequence=["#39a96b"]
        )

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#25164f"
        )

        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

col3, col4 = st.columns(2)

with col3:
    if "Turno" in df.columns:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)

        graf = df["Turno"].astype(str).replace("nan", "Sin dato").value_counts().reset_index()
        graf.columns = ["Turno", "Cantidad"]

        fig = px.bar(
            graf,
            x="Turno",
            y="Cantidad",
            text="Cantidad",
            title="Distribución por turno",
            color_discrete_sequence=["#7e57c2"]
        )

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#25164f"
        )

        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

with col4:
    if "Categoría" in df.columns:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)

        graf = df["Categoría"].astype(str).replace("nan", "Sin dato").value_counts().reset_index()
        graf.columns = ["Categoría", "Cantidad"]

        fig = px.bar(
            graf,
            x="Categoría",
            y="Cantidad",
            text="Cantidad",
            title="Distribución por categoría",
            color_discrete_sequence=["#39a96b"]
        )

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#25164f"
        )

        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

if "Tipo de servicio" in df.columns:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)

    graf = df["Tipo de servicio"].astype(str).replace("nan", "Sin dato").value_counts().reset_index()
    graf.columns = ["Tipo de servicio", "Cantidad"]

    fig = px.bar(
        graf,
        x="Cantidad",
        y="Tipo de servicio",
        orientation="h",
        text="Cantidad",
        title="Distribución por tipo de servicio",
        color_discrete_sequence=["#39a96b"]
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#25164f"
    )

    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

if "Motivo de cobertura" in df.columns:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)

    graf = df["Motivo de cobertura"].astype(str).replace("nan", "Sin dato").value_counts().reset_index()
    graf.columns = ["Motivo de cobertura", "Cantidad"]

    orden = [
        "Vacaciones",
        "Ausencia No Programada",
        "Enfermedad",
        "ART",
        "Franco",
        "Suspensión",
        "Suspension",
        "Otros"
    ]

    graf["orden"] = graf["Motivo de cobertura"].apply(
        lambda x: orden.index(x) if x in orden else 999
    )
    graf = graf.sort_values("orden")

    fig = px.bar(
        graf,
        x="Cantidad",
        y="Motivo de cobertura",
        orientation="h",
        text="Cantidad",
        title="Motivos de cobertura",
        color_discrete_sequence=["#7e57c2"]
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#25164f"
    )

    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# DETALLE
# =========================

st.markdown('<div class="seccion">Detalle de registros</div>', unsafe_allow_html=True)

columnas_detalle = [
    "Fecha",
    "Apellido y Nombre",
    "Categoría",
    "Turno",
    "Jornal",
    "Prestó Servicio",
    "Tipo de servicio",
    "Motivo de cobertura"
]

columnas_existentes = [c for c in columnas_detalle if c in df.columns]

st.dataframe(df[columnas_existentes], use_container_width=True)
