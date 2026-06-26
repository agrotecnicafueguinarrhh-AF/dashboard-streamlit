import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard Personal Eventual", layout="wide")

URL_KPIS = "https://docs.google.com/spreadsheets/d/1Ths5IKfLsLnBovb7l-Z-X8PgQ4VK6v0ombUThG375JE/export?format=csv&gid=0"
URL_DATOS = "https://docs.google.com/spreadsheets/d/1Ths5IKfLsLnBovb7l-Z-X8PgQ4VK6v0ombUThG375JE/export?format=csv&gid=1321247605"

st.markdown("""
<style>
.stApp { background: #f4f1f8; }
.block-container { padding-top: 2rem; padding-left: 3rem; padding-right: 3rem; }
[data-testid="stSidebar"] { background: linear-gradient(180deg, #25164f, #3d2b6f); }
[data-testid="stSidebar"] * { color: white; }

.titulo {
    font-size: 38px;
    font-weight: 900;
    color: #25164f;
}
.subtitulo {
    color: #5f5870;
    font-size: 15px;
    margin-bottom: 25px;
}
.seccion {
    font-size: 22px;
    font-weight: 900;
    color: #25164f;
    margin-top: 25px;
    margin-bottom: 15px;
    padding-bottom: 6px;
    border-bottom: 3px solid #39a96b;
}
.card {
    background: white;
    border-radius: 18px;
    padding: 18px;
    min-height: 125px;
    box-shadow: 0px 4px 18px rgba(37, 22, 79, 0.12);
    border-bottom: 5px solid #39a96b;
    margin-bottom: 16px;
}
.card-title {
    font-size: 13px;
    font-weight: 800;
    color: #25164f;
    min-height: 42px;
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
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def cargar_datos():
    kpis = pd.read_csv(URL_KPIS).dropna(how="all")
    datos = pd.read_csv(URL_DATOS).dropna(how="all")

    kpis.columns = kpis.columns.astype(str).str.strip()
    datos.columns = datos.columns.astype(str).str.strip()

    datos = datos.rename(columns={
        "Presto Servicio": "Prestó Servicio",
        "Tipo de servicio ": "Tipo de servicio",
        "Categoria": "Categoría",
        "Cobertura por": "Motivo de cobertura",
        "Motivo cobertura": "Motivo de cobertura",
        "Motivo de Cobertura": "Motivo de cobertura"
    })

    return kpis, datos

kpis, datos = cargar_datos()

st.markdown('<div class="titulo">📊 Dashboard Personal Eventual</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitulo">Control interno de jornales, servicios, cobertura y complementos</div>', unsafe_allow_html=True)

col_indicador = next((c for c in kpis.columns if "indicador" in c.lower()), None)
col_resultado = next((c for c in kpis.columns if "resultado" in c.lower()), None)
col_porcentaje = next((c for c in kpis.columns if "%" in c.lower() or "porcentaje" in c.lower()), None)

if col_indicador is None or col_resultado is None:
    st.error("No encontré las columnas Indicador y Resultado en la Hoja 1.")
    st.write(list(kpis.columns))
    st.stop()

kpis[col_indicador] = kpis[col_indicador].astype(str).str.strip()

def buscar_valor(nombre):
    fila = kpis[kpis[col_indicador].str.lower() == nombre.lower()]
    if not fila.empty:
        return fila.iloc[0][col_resultado]
    return "-"

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
# RESUMEN EJECUTIVO
# =========================

st.markdown('<div class="seccion">RESUMEN EJECUTIVO</div>', unsafe_allow_html=True)

resumen = [
    "Jornales Solicitados MENSUAL",
    "Jornales Informados GG",
    "Jornales Validados",
    "Diferencia",
    "Dobles Jornadas",
    "Triples Jornadas",
    "Jornales Extras (Doble + Triple)",
    "Personal Observado",
    "Personal No Recomendado",
    "Cobertura Real (%)",
    "Total complementos a pagar"
]

cols_por_fila = 4

for i in range(0, len(resumen), cols_por_fila):
    cols = st.columns(cols_por_fila)
    fila = resumen[i:i + cols_por_fila]

    for col, indicador in zip(cols, fila):
        with col:
            st.markdown(f"""
            <div class="card">
                <div class="card-title">{indicador}</div>
                <div class="card-value">{buscar_valor(indicador)}</div>
            </div>
            """, unsafe_allow_html=True)

# =========================
# SERVICIOS
# =========================

st.markdown('<div class="seccion">SERVICIOS</div>', unsafe_allow_html=True)

servicios = [
    "% Barrido Manual",
    "% Barrido Mecanico",
    "% Chofer de Recoleccion",
    "% Chofer Traslado de Personal",
    "% Peon de Recoleccion",
    "% Imbornales",
    "% Espacio Verde Publico",
    "% Limpieza de Canales",
    "% Corte de Cesped",
    "% Areas Turisticas",
    "% Mantenimiento",
    "% IASA",
    "% Maquinista",
    "% Relleno San Javier"
]

datos_servicios = []

for servicio in servicios:
    fila = kpis[kpis[col_indicador].str.lower() == servicio.lower()]
    if not fila.empty:
        cantidad = fila.iloc[0][col_resultado]
        porcentaje = fila.iloc[0][col_porcentaje] if col_porcentaje else ""
        datos_servicios.append({
            "Servicio": servicio.replace("% ", ""),
            "Cantidad": cantidad,
            "%": porcentaje
        })

df_servicios = pd.DataFrame(datos_servicios)

if not df_servicios.empty:
    df_servicios["Cantidad_num"] = pd.to_numeric(df_servicios["Cantidad"], errors="coerce").fillna(0)

    col_graf, col_tabla = st.columns([2, 1])

    with col_graf:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        fig = px.pie(
            df_servicios,
            names="Servicio",
            values="Cantidad_num",
            hole=0.45,
            title="Distribución de servicios"
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#25164f"
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_tabla:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.dataframe(
            df_servicios[["Servicio", "Cantidad", "%"]],
            use_container_width=True,
            hide_index=True
        )
        st.markdown('</div>', unsafe_allow_html=True)
else:
    st.warning("No encontré los indicadores de servicios en la Hoja 1.")

# =========================
# MOTIVO DE COBERTURA
# =========================

st.markdown('<div class="seccion">MOTIVO DE COBERTURA</div>', unsafe_allow_html=True)

motivos = [
    "Vacaciones",
    "Ausencia No Programada",
    "Enfermedad",
    "ART",
    "Franco",
    "Suspensión",
    "Suspension",
    "Otros"
]

df_motivos = pd.DataFrame()

if "Motivo de cobertura" in df.columns:
    df_motivos = df["Motivo de cobertura"].astype(str).replace("nan", "Sin dato").value_counts().reset_index()
    df_motivos.columns = ["Motivo de cobertura", "Cantidad"]

    df_motivos = df_motivos[df_motivos["Motivo de cobertura"].isin(motivos)]

    orden = {motivo: i for i, motivo in enumerate(motivos)}
    df_motivos["orden"] = df_motivos["Motivo de cobertura"].map(orden)
    df_motivos = df_motivos.sort_values("orden")

if not df_motivos.empty:
    col_motivo_graf, col_motivo_tabla = st.columns([2, 1])

    with col_motivo_graf:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        fig = px.bar(
            df_motivos,
            x="Cantidad",
            y="Motivo de cobertura",
            orientation="h",
            text="Cantidad",
            title="Motivos de cobertura"
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#25164f"
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_motivo_tabla:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.dataframe(
            df_motivos[["Motivo de cobertura", "Cantidad"]],
            use_container_width=True,
            hide_index=True
        )
        st.markdown('</div>', unsafe_allow_html=True)
else:
    st.warning("No encontré datos de Motivo de cobertura.")

# =========================
# DETALLE
# =========================

st.markdown('<div class="seccion">DETALLE DE REGISTROS</div>', unsafe_allow_html=True)

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
