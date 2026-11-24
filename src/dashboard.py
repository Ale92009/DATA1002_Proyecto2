from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Aseo en Bogotá | DATA1002", layout="wide")
RAIZ = Path(__file__).resolve().parent.parent


@st.cache_data
def cargar_datos():
    df = pd.read_csv(RAIZ / "data/processed/df_final.csv", encoding="utf-8-sig")

    puntos = pd.read_csv(
        RAIZ / "data/raw/sigab_puntoscriticos.csv", sep="|", encoding="latin-1"
    )
    puntos["ID_CONCESIONARIO"] = puntos["CONCESIONARIO"].str.extract(r"(ASE\d{2})")
    estado = puntos["OBSERVACION"].astype("string").str.strip().str.upper()
    sin_estado = estado.isna() | estado.eq("")
    puntos["SUPUESTO_ACTIVO"] = sin_estado.fillna(False).astype(int)
    puntos["ES_ACTIVO"] = (estado.eq("ACTIVO") | sin_estado).fillna(False).astype(int)

    conteos = puntos.groupby(
        ["IDLOCALID", "ID_CONCESIONARIO"], as_index=False
    ).agg(
        PUNTOS_REPORTADOS=("CODIGOINTE", "count"),
        PUNTOS_ACTIVOS=("ES_ACTIVO", "sum"),
        PUNTOS_ACTIVOS_ASUMIDOS=("SUPUESTO_ACTIVO", "sum"),
    )

    df = df.drop(columns=["NUM_PUNTOS_CRITICOS"])
    df = df.merge(
        conteos,
        left_on=["ID_LOCALIDAD", "ID_CONCESIONARIO"],
        right_on=["IDLOCALID", "ID_CONCESIONARIO"],
        how="left", validate="one_to_one"
    ).drop(columns="IDLOCALID")

    cols = ["PUNTOS_REPORTADOS", "PUNTOS_ACTIVOS", "PUNTOS_ACTIVOS_ASUMIDOS"]
    df[cols] = df[cols].fillna(0).astype(int)
    return df


perfil = cargar_datos()

st.title("¿Dónde priorizar la mejora del servicio de aseo en Bogotá?")
st.caption(
    "Proyecto 2 · DATA1002 | Referencia: datos de 2025 | "
    "19 localidades urbanas y cinco concesionarios"
)
st.write(
    "**Decisión:** identificar un concesionario para estudiar un piloto de mejora "
    "en 2027, considerando reclamaciones, puntos críticos y capacidad registrada "
    "de contenedores en relación con la población."
)

# Filtros: todas las métricas y gráficas se calculan sobre la misma selección.
st.sidebar.header("Explorar los datos")
concesionarios = sorted(perfil["CONCESIONARIO"].unique())
concesionario = st.sidebar.selectbox("Concesionario", ["Todos"] + concesionarios)

opciones = perfil if concesionario == "Todos" else perfil[
    perfil["CONCESIONARIO"] == concesionario
]
localidades = sorted(opciones["LOCALIDAD"].unique())
localidad = st.sidebar.selectbox("Localidad", ["Todas"] + localidades)

filtrado = opciones.copy()
if localidad != "Todas":
    filtrado = filtrado[filtrado["LOCALIDAD"] == localidad]

# Agrupar antes de dividir: nunca sumar tasas por localidad.
por_operador = filtrado.groupby("CONCESIONARIO", as_index=False).agg(
    POBLACION=("POBLACION", "sum"),
    PQRS=("NUM_PQRS", "sum"),
    CAPACIDAD=("CAPACIDAD_TOTAL_CONTENEDORES", "sum"),
    PUNTOS=("PUNTOS_ACTIVOS", "sum"),
    PUNTOS_ASUMIDOS=("PUNTOS_ACTIVOS_ASUMIDOS", "sum"),
)
por_operador["PQRS_1000"] = por_operador["PQRS"] / por_operador["POBLACION"] * 1000
por_operador["CAPACIDAD_1000"] = por_operador["CAPACIDAD"] / por_operador["POBLACION"] * 1000
por_operador["PUNTOS_1000"] = por_operador["PUNTOS"] / por_operador["POBLACION"] * 1000

poblacion = int(filtrado["POBLACION"].sum())
pqrs = int(filtrado["NUM_PQRS"].sum())
puntos_activos = int(filtrado["PUNTOS_ACTIVOS"].sum())
asumidos = int(filtrado["PUNTOS_ACTIVOS_ASUMIDOS"].sum())

st.subheader("Panorama de la selección")
a, b, c, d = st.columns(4)
a.metric("Población", f"{poblacion:,.0f}")
b.metric("PQRS (2025)", f"{pqrs:,.0f}")
c.metric("PQRS por 1.000 hab.", f"{pqrs / poblacion * 1000:.2f}")
d.metric("Puntos considerados activos", f"{puntos_activos:,.0f}")

st.caption(
    f"De los {puntos_activos} puntos considerados activos en la selección, "
    f"{asumidos} fueron clasificados como activos por facilidad metodológica"
)

st.subheader("Comparación entre concesionarios")
izquierda, derecha = st.columns(2)

with izquierda:
    fig_pqrs = px.bar(
        por_operador.sort_values("PQRS_1000"),
        x="PQRS_1000", y="CONCESIONARIO", orientation="h",
        title="Reclamaciones relativas a la población",
        labels={"PQRS_1000": "PQRS por 1.000 habitantes", "CONCESIONARIO": ""},
        hover_data={"PQRS": True, "POBLACION": True},
    )
    st.plotly_chart(fig_pqrs, width="stretch")

with derecha:
    fig_puntos = px.bar(
        por_operador.sort_values("PUNTOS_1000"),
        x="PUNTOS_1000", y="CONCESIONARIO", orientation="h",
        title="Puntos considerados activos relativos a la población",
        labels={"PUNTOS_1000": "Puntos por 1.000 habitantes", "CONCESIONARIO": ""},
        hover_data={"PUNTOS": True, "PUNTOS_ASUMIDOS": True},
    )
    st.plotly_chart(fig_puntos, width="stretch")

fig_capacidad = px.bar(
    por_operador.sort_values("CAPACIDAD_1000"),
    x="CAPACIDAD_1000", y="CONCESIONARIO", orientation="h",
    title="Capacidad de contenedores registrada por habitante",
    labels={"CAPACIDAD_1000": "Litros por 1.000 habitantes", "CONCESIONARIO": ""},
    hover_data={"CAPACIDAD": True},
)
st.plotly_chart(fig_capacidad, width="stretch")

st.subheader("Detalle por localidad")
if concesionario != "Todos" and localidad == "Todas":
    por_localidad = filtrado.copy()
    por_localidad["PQRS_1000"] = (
        por_localidad["NUM_PQRS"] / por_localidad["POBLACION"] * 1000
    )
    fig_local = px.bar(
        por_localidad.sort_values("PQRS_1000"),
        x="PQRS_1000", y="LOCALIDAD", orientation="h",
        title=f"Diferencias entre localidades de {concesionario}",
        labels={"PQRS_1000": "PQRS por 1.000 habitantes", "LOCALIDAD": ""},
    )
    st.plotly_chart(fig_local, width="stretch")

detalle = filtrado[[
    "CONCESIONARIO", "LOCALIDAD", "POBLACION", "NUM_PQRS",
    "NUM_CONTENEDORES", "CAPACIDAD_TOTAL_CONTENEDORES",
    "PUNTOS_REPORTADOS", "PUNTOS_ACTIVOS", "PUNTOS_ACTIVOS_ASUMIDOS"
]].copy()
detalle["PQRS por 1.000 hab."] = (detalle["NUM_PQRS"] / detalle["POBLACION"] * 1000).round(2)
st.dataframe(detalle, width="stretch", hide_index=True)

st.subheader("Interpretación y límites")
st.write(
    "Las PQRS, los puntos críticos y la infraestructura son señales para orientar "
    "una revisión, pero **no prueban por sí solos la calidad del servicio ni las "
    "causas de las reclamaciones**. La capacidad registrada tampoco equivale "
    "a cobertura efectiva de todas las zonas."
)
st.info(
    "**Supuesto metodológico:** a sugerencia del profesor, los 105 puntos "
    "de Ciudad Limpia sin estado original se consideran activos en el análisis. "
    "El dashboard informa cuántos resultados dependen de esa decisión."
)
st.caption(
    "Fuentes: SIGAB/UAESP (contenedores, puntos críticos, PQRS) y datos "
    "demográficos por localidad. Preparación e integración documentadas "
    "en notebooks/desarrollo.ipynb."
)
