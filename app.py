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

def normalizar(texto):
    texto = str(texto).replace("\xa0", " ").strip().lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = " ".join(texto.split())
    return texto

def limpiar_texto(x):
    if pd.isna(x):
        return ""
    return str(x).strip()

def buscar_columna(df, opciones):
    columnas_norm = {normalizar(col): col for col in df.columns}
    for opcion in opciones:
        opcion_norm = normalizar(opcion)
        if opcion_norm in columnas_norm:
            return columnas_norm[opcion_norm]
    return None

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

col_fecha = buscar_columna(datos, ["Fecha"])
col_nombre = buscar_columna(datos, ["Apellido y Nombre", "Nombre", "Colaborador"])
col_categoria = buscar_columna(datos, ["Categoría", "Categoria"])
col_turno = buscar_columna(datos, ["Turno"])
col_citado = buscar_columna(datos, ["Citado"])
col_jornal = buscar_columna(datos, ["Jornal"])
col_servicio = buscar_columna(datos, ["Prestó Servicio", "Presto Servicio", "Servicio"])
col_tipo = buscar_columna(datos, ["Tipo de servicio", "Tipo Servicio", "Servicio asignado"])

col_estado = buscar_columna(seguimiento, ["Estado"])
col_indicador = buscar_columna(kpis, ["Indicador"])
col_resultado = buscar_columna(kpis, ["Resultado"])

faltantes = []

for nombre, col in {
    "Fecha": col_fecha,
    "Apellido y Nombre": col_nombre,
    "Categoría": col_categoria,
    "Turno": col_turno,
    "Jornal": col_jornal,
    "Prestó Servicio": col_servicio,
    "Tipo de servicio": col_tipo
}.items():
    if col is None:
        faltantes.append(nombre)

if faltantes:
    st.error("Faltan columnas o cambiaron de nombre en la hoja 2.")
    st.write("Columnas que no pude encontrar:")
    st.write(faltantes)
    st.write("Columnas encontradas en hoja 2:")
    st.write(list(datos.columns))
    st.stop()

if col_estado is None:
    st.warning("No encontré la columna Estado en la hoja 3. Los indicadores de seguimiento quedarán en 0.")

df_base = pd.DataFrame()

df_base["Fecha"] = pd.to_datetime(datos[col_fecha], errors="coerce")
df_base["Apellido y Nombre"] = datos[col_nombre].apply(limpiar_texto)
df_base["Categoría"] = datos[col_categoria].apply(limpiar_texto)
df_base["Turno"] = datos[col_turno].apply(limpiar_texto)
df_base["Jornal"] = datos[col_jornal].apply(limpiar_texto)
df_base["Prestó Servicio"] = datos[col_servicio].apply(limpiar_texto)
df_base["Tipo de servicio"] = datos[col_tipo].apply(limpiar_texto)

if col_citado:
    df_base["Citado"] = datos[col_citado].apply(limpiar_texto)

df = df_base.copy()

st.sidebar.header("Filtros")

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
    sorted(df["Tipo de servicio"].replace("", "Sin dato").dropna().unique())
)

turno = st.sidebar.multiselect(
    "Turno",
    sorted(df["Turno"].replace("", "Sin dato").dropna().unique())
)

categoria = st.sidebar.multiselect(
    "Categoría",
    sorted(df["Categoría"].replace("", "Sin dato").dropna().unique())
)

buscar = st.sidebar.text_input("Buscar colaborador")

if tipo_servicio:
    df = df[df["Tipo de servicio"].isin(tipo_servicio)]

if turno:
    df = df[df["Turno"].isin(turno)]

if categoria:
    df = df[df["Categoría"].isin(categoria)]

if buscar:
    df = df[df["Apellido y Nombre"].str.contains(buscar, case=False, na=False)]

try:
    if col_indicador and col_resultado:
        jornales_solicitados = kpis.loc[
            kpis[col_indicador].astype(str).str.contains("Jornales Solicitados", case=False, na=False),
            col_resultado
        ].iloc[0]
    else:
        jornales_solicitados = 0
except:
    jornales_solicitados = 0

jornales_informados = len(df)

jornales_validados = df[
    df["Prestó Servicio"].str.lower().str.contains("presto servicio|prestó servicio|si|sí", na=False)
].shape[0]

no_presto = df[
    df["Prestó Servicio"].str.lower().str.contains("no presto servicio|no prestó servicio|no", na=False)
].shape[0]

diferencia = jornales_informados - jornales_validados

dobles = df[df["Jornal"].str.contains("Doble", case=False, na=False)].shape[0]
triples = df[df["Jornal"].str.contains("Triple", case=False, na=False)].shape[0]
extras = dobles + triples

if col_estado:
    estados = seguimiento[col_estado].astype(str).str.strip().str.lower()
    recomendados = estados[estados == "recomendado"].shape[0]
    observados = estados[estados == "observado"].shape[0]
    no_convocar = estados[estados == "no convocar"].shape[0]
else:
    recomendados = 0
    observados = 0
    no_convocar = 0

cobertura = (jornales_validados / jornales_informados * 100) if jornales_informados > 0 else 0

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

col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Prestó Servicio")
    graf_servicio = df["Prestó Servicio"].replace("", "Sin dato").value_counts().reset_index()
    graf_servicio.columns = ["Estado", "Cantidad"]
    fig = px.pie(graf_servicio, names="Estado", values="Cantidad", hole=0.4)
    st.plotly_chart(fig, use_container_width=True)

with col_b:
    st.subheader("Jornales")
    graf_jornal = df["Jornal"].replace("", "Sin dato").value_counts().reset_index()
    graf_jornal.columns = ["Jornal", "Cantidad"]
    fig = px.bar(graf_jornal, x="Jornal", y="Cantidad", text="Cantidad")
    st.plotly_chart(fig, use_container_width=True)

col_c, col_d = st.columns(2)

with col_c:
    st.subheader("Distribución por turno")
    graf_turno = df["Turno"].replace("", "Sin dato").value_counts().reset_index()
    graf_turno.columns = ["Turno", "Cantidad"]
    fig = px.bar(graf_turno, x="Turno", y="Cantidad", text="Cantidad")
    st.plotly_chart(fig, use_container_width=True)

with col_d:
    st.subheader("Distribución por categoría")
    graf_cat = df["Categoría"].replace("", "Sin dato").value_counts().reset_index()
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
