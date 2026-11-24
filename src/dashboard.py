from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st


# Traemos los datos
RAIZ = Path(__file__).resolve().parent.parent

# La caché evita volver a leer los csv al cambiar los filtros.
@st.cache_data
def cargar_datos():
    # Los cuatro archivos se exportan desde el notebook.
    df = pd.read_csv(RAIZ / "data/processed/df_final.csv", sep=',')
    operadores = pd.read_csv(RAIZ / "outputs/tables/df_concesionarios.csv", sep=',', engine="python")
    puntos = pd.read_csv(RAIZ / "outputs/tables/tabla_puntos_criticos.csv", sep=',', engine="python")
    mensual = pd.read_csv(RAIZ / "outputs/tables/pqrs_mensual.csv", sep=';', decimal=',', parse_dates=['MES'])
    return df, operadores, puntos, mensual

perfil, df_concesionarios, tabla_puntos_criticos, pqrs_mensual = cargar_datos() #Llamamos a la función

# Función para no repetir acciones
# La función únicamente convierte los datos al formato usado en colombia para evitar confusiones
# Puntos para los miles
# Comas para los decimales
def formato(valor, decimales=0):
    return f"{valor:,.{decimales}f}".replace(",", "_").replace(".", ",").replace("_", ".")

# Configuración de la página
st.set_page_config(page_title="Aseo en Bogotá | DATA1002", layout="wide")
st.title("¿Dónde priorizar la mejora del servicio de aseo en Bogotá?")
st.caption(
    "Proyecto 2 · DATA1002 | Referencia: datos de 2025 | "
    "19 localidades urbanas y cinco concesionarios"
)
st.caption('Integrantes: Alejandro Chica, Natalia Rodriguez, Juan Sebastian Caballero, Emiliano Quintero')
st.write(
    "**Decisión:** identificar un concesionario para estudiar un piloto de mejora "
    "en 2027, considerando reclamaciones, puntos críticos y capacidad registrada "
    "de contenedores en relación con la población."
)


# Filtros
st.sidebar.header("Explorar los datos")
concesionarios = sorted(perfil["CONCESIONARIO"].unique()) #Obtenemos todos los concesionarios
concesionario = st.sidebar.selectbox("Concesionario", ["Todos"] + concesionarios)

# Realizamos el filtrado según concesionario
if concesionario == "Todos":
    filtrado = perfil.copy()
    por_operador = df_concesionarios.copy()
    puntos_filtrados = tabla_puntos_criticos.copy()
    mensual_filtrado = pqrs_mensual.copy()
    #Filtramos las 4 tablas porque todas tienen información diferentes y todas deben responder a la misma selección
else:
    filtrado = perfil[perfil["CONCESIONARIO"] == concesionario].copy()
    por_operador = df_concesionarios[df_concesionarios["CONCESIONARIO"] == concesionario].copy()
    puntos_filtrados = tabla_puntos_criticos[tabla_puntos_criticos["CONCESIONARIO"] == concesionario].copy()
    mensual_filtrado = pqrs_mensual[pqrs_mensual["CONCESIONARIO"] == concesionario].copy()


# KPIs y sidebar
st.subheader("Panorama de la selección")
a, b, c = st.columns(3)
a.metric("Población", formato(filtrado["POBLACION"].sum()), border=True)
b.metric("PQRS (2025)", formato(filtrado["NUM_PQRS"].sum()), border=True)
c.metric("Puntos registrados", formato(puntos_filtrados["TOTAL"].sum()), border=True)
d, e = st.columns(2)
d.metric("Puntos considerados activos", formato(filtrado["NUM_PUNTOS_CRITICOS"].sum()), border=True)
e.metric("Capacidad (L)", formato(filtrado["CAPACIDAD_TOTAL_CONTENEDORES"].sum()), border=True)
st.divider()


# Gráficas PQRS
st.subheader("1. PQRS registradas durante 2025") #Añadimos un subtitulo para introducir de que vamos a hablar
st.caption("El naranja destaca el mayor valor de cada comparación.")
izquierda, derecha = st.columns(2) #Creamos dos espacio iguales para poner las graficas lado a lado
with izquierda:
    # Ordenamos los concesionarios de mayor a menor.
    datos = por_operador.sort_values("NUM_PQRS", ascending=False).copy() #Usamos copy para modificar el df original
    datos["ETIQUETA"] = datos["NUM_PQRS"].map(lambda valor: formato(valor, 0)) 
    #Para que las etiquetas sean más claras, usamos el punto para separar los miles

    # Creamos la gráfica de barras horizontales y sus etiquetas.
    fig = px.bar(
        datos, x="NUM_PQRS", y="CONCESIONARIO", orientation="h",
        text="ETIQUETA", title="Cantidad absoluta de PQRS",
        labels={"NUM_PQRS": "PQRS", "CONCESIONARIO": "Concesionario"},
        template="plotly_white"
    )

    # Para resaltar el concesionario con más pqrs absolutas, lo pintamos de naranja, los demás en gris. 
    fig.update_traces(
        marker_color=["#C65D21"] + ["#A6B0BA"] * (len(datos) - 1),
        textposition="outside", cliponaxis=False
    )

    # Mostramos el mayor valor arriba y dejamos espacio para las etiquetas.
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(showlegend=False, height=330, yaxis_title=None,
                      margin=dict(l=10, r=55, t=60, b=45), separators=",.")
    fig.update_xaxes(rangemode="tozero", range=[0, max(datos["NUM_PQRS"].max() * 1.25, 0.001)])
    st.plotly_chart(fig, use_container_width=True, key="NUM_PQRS")
with derecha:
    # Ordenamos los concesionarios de mayor a menor.
    datos = por_operador.sort_values("PQRS_POR_1000_HAB", ascending=False).copy()
    datos["ETIQUETA"] = datos["PQRS_POR_1000_HAB"].map(lambda valor: formato(valor, 2))

    # Creamos la gráfica de barras horizontales y sus etiquetas.
    fig = px.bar(
        datos, x="PQRS_POR_1000_HAB", y="CONCESIONARIO", orientation="h",
        text="ETIQUETA", title="PQRS relativas a la población",
        labels={"PQRS_POR_1000_HAB": "PQRS por 1.000 habitantes", "CONCESIONARIO": "Concesionario"},
        template="plotly_white"
    )

    # Usamos la misma jerarquía de colores
    fig.update_traces(
        marker_color=["#C65D21"] + ["#A6B0BA"] * (len(datos) - 1),
        textposition="outside", cliponaxis=False
    )

    # Mostramos el mayor valor arriba y dejamos espacio para las etiquetas.
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(showlegend=False, height=330, yaxis_title=None,
                      margin=dict(l=10, r=55, t=60, b=45), separators=",.")
    fig.update_xaxes(rangemode="tozero", range=[0, max(datos["PQRS_POR_1000_HAB"].max() * 1.25, 0.001)])
    st.plotly_chart(fig, use_container_width=True, key="PQRS_POR_1000_HAB")

# Hallazgo 1
st.markdown(
    "**Hallazgo:** Aunque Lime registra la mayor cantidad absoluta de PQRS, Bogotá Limpia presenta la mayor tasa relativa, con 36,26 PQRS por cada 1.000 habitantes."
)
# Mencionamos explicitamente que los hallazgos son estaticos y no cambian con los filtros.
st.caption(":red[**Los hallazgos corresponden al análisis general de los cinco concesionarios. El filtro permite explorar los datos individualmente.**]")
st.divider()


# Gráfica puntos críticos
st.subheader("2. Puntos críticos considerados activos") 
izquierda, derecha = st.columns(2)
with izquierda:
    # Ordenamos los concesionarios de mayor a menor.
    datos = por_operador.sort_values("NUM_PUNTOS_CRITICOS", ascending=False).copy()
    datos["ETIQUETA"] = datos["NUM_PUNTOS_CRITICOS"].map(lambda valor: formato(valor, 0))

    # Creamos la gráfica de barras horizontales y sus etiquetas.
    fig = px.bar(
        datos, x="NUM_PUNTOS_CRITICOS", y="CONCESIONARIO", orientation="h",
        text="ETIQUETA", title="Cantidad absoluta de puntos activos",
        labels={"NUM_PUNTOS_CRITICOS": "Puntos activos", "CONCESIONARIO": "Concesionario"},
        template="plotly_white"
    )

    
    fig.update_traces(
        marker_color=["#C65D21"] + ["#A6B0BA"] * (len(datos) - 1),
        textposition="outside", cliponaxis=False
    )

    
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(showlegend=False, height=330, yaxis_title=None,
                      margin=dict(l=10, r=55, t=60, b=45), separators=",.")
    fig.update_xaxes(rangemode="tozero", range=[0, max(datos["NUM_PUNTOS_CRITICOS"].max() * 1.25, 0.001)])
    st.plotly_chart(fig, use_container_width=True, key="NUM_PUNTOS_CRITICOS")
with derecha:
    datos = por_operador.sort_values("PUNTOS_CRITICOS_POR_1000_HAB", ascending=False).copy()
    datos["ETIQUETA"] = datos["PUNTOS_CRITICOS_POR_1000_HAB"].map(lambda valor: formato(valor, 3))

    fig = px.bar(
        datos, x="PUNTOS_CRITICOS_POR_1000_HAB", y="CONCESIONARIO", orientation="h",
        text="ETIQUETA", title="Puntos activos relativos a la población",
        labels={"PUNTOS_CRITICOS_POR_1000_HAB": "Puntos activos por 1.000 habitantes", "CONCESIONARIO": "Concesionario"},
        template="plotly_white"
    )

   
    fig.update_traces(
        marker_color=["#C65D21"] + ["#A6B0BA"] * (len(datos) - 1),
        textposition="outside", cliponaxis=False
    )

    fig.update_yaxes(autorange="reversed")
    fig.update_layout(showlegend=False, height=330, yaxis_title=None,
                      margin=dict(l=10, r=55, t=60, b=45), separators=",.")
    fig.update_xaxes(rangemode="tozero", range=[0, max(datos["PUNTOS_CRITICOS_POR_1000_HAB"].max() * 1.25, 0.001)])
    st.plotly_chart(fig, use_container_width=True, key="PUNTOS_CRITICOS_POR_1000_HAB")

# Hallazgo 2
st.markdown(
    "**Hallazgo:** Lime registra la mayor cantidad de puntos considerados activos (177). Sin embargo, Bogotá Limpia presenta la mayor tasa relativa, con 0,076 puntos por cada 1.000 habitantes."
)
st.divider()


# Gráfica capacidad contenerización
st.subheader("3. Capacidad de contenerización")
izquierda, derecha = st.columns(2)
with izquierda:
    datos = por_operador.sort_values("CAPACIDAD_TOTAL_CONTENEDORES", ascending=False).copy()
    datos["ETIQUETA"] = datos["CAPACIDAD_TOTAL_CONTENEDORES"].map(lambda valor: formato(valor, 0))

    fig = px.bar(
        datos, x="CAPACIDAD_TOTAL_CONTENEDORES", y="CONCESIONARIO", orientation="h",
        text="ETIQUETA", title="Capacidad absoluta",
        labels={"CAPACIDAD_TOTAL_CONTENEDORES": "Litros", "CONCESIONARIO": "Concesionario"},
        template="plotly_white"
    )

    fig.update_traces(
        marker_color=["#C65D21"] + ["#A6B0BA"] * (len(datos) - 1),
        textposition="outside", cliponaxis=False
    )

    fig.update_yaxes(autorange="reversed")
    fig.update_layout(showlegend=False, height=330, yaxis_title=None,
                      margin=dict(l=10, r=55, t=60, b=45), separators=",.")
    fig.update_xaxes(rangemode="tozero", range=[0, max(datos["CAPACIDAD_TOTAL_CONTENEDORES"].max() * 1.25, 0.001)])
    st.plotly_chart(fig, use_container_width=True, key="CAPACIDAD_TOTAL_CONTENEDORES")
with derecha:
    datos = por_operador.sort_values("CAPACIDAD_TOTAL_CONTENEDORES_POR_1000_HAB", ascending=False).copy()
    datos["ETIQUETA"] = datos["CAPACIDAD_TOTAL_CONTENEDORES_POR_1000_HAB"].map(lambda valor: formato(valor, 2))
    
    fig = px.bar(
        datos, x="CAPACIDAD_TOTAL_CONTENEDORES_POR_1000_HAB", y="CONCESIONARIO", orientation="h",
        text="ETIQUETA", title="Capacidad relativa a la población",
        labels={"CAPACIDAD_TOTAL_CONTENEDORES_POR_1000_HAB": "Litros por 1.000 habitantes", "CONCESIONARIO": "Concesionario"},
        template="plotly_white"
    )

    fig.update_traces(
        marker_color=["#C65D21"] + ["#A6B0BA"] * (len(datos) - 1),
        textposition="outside", cliponaxis=False
    )

    fig.update_yaxes(autorange="reversed")
    fig.update_layout(showlegend=False, height=330, yaxis_title=None,
                      margin=dict(l=10, r=55, t=60, b=45), separators=",.")
    fig.update_xaxes(rangemode="tozero", range=[0, max(datos["CAPACIDAD_TOTAL_CONTENEDORES_POR_1000_HAB"].max() * 1.25, 0.001)])
    st.plotly_chart(fig, use_container_width=True, key="CAPACIDAD_TOTAL_CONTENEDORES_POR_1000_HAB")

# Hallazgo 3
st.markdown(
    "**Hallazgo:** Bogotá Limpia presenta la mayor capacidad relativa de contenerización (2.790,49 litros por cada 1.000 habitantes), a pesar de liderar las tasas de PQRS y puntos activos. La capacidad registrada no explica por sí sola la problemática."
)
st.divider()


# Gráfica estados puntos críticos
st.subheader("4. Estados de los puntos críticos")
# Obtenemos las tasas por estado a partir de los conteos y la población.
estados = puntos_filtrados.merge(por_operador[["CONCESIONARIO", "POBLACION"]], on="CONCESIONARIO")
estados["Considerados activos"] = estados["P_ACTIVOS"] / estados["POBLACION"] * 1000
estados["Otros estados"] = estados["P_OTROS"] / estados["POBLACION"] * 1000
estados = estados.sort_values("TOTAL_POR_1000_HAB", ascending=False)

#Melt es una función que consultamos que nos permitió transformar el dataFrame de formato ancho a formato largo
estados = estados.melt(id_vars="CONCESIONARIO", value_vars=["Considerados activos", "Otros estados"], var_name="Estado", value_name="TASA")

fig_estados = px.bar(
    estados, x="TASA", y="CONCESIONARIO", color="Estado", orientation="h",
    barmode="stack", text="TASA", color_discrete_map={"Considerados activos": "#84919E", "Otros estados": "#D0D5DA"},
    labels={"TASA": "Puntos registrados por 1.000 habitantes", "CONCESIONARIO": "Concesionario"},
    template="plotly_white"
)
fig_estados.update_layout(height=350, yaxis_title=None, legend_title_text="")
fig_estados.update_traces(hovertemplate="%{y}: %{x:.3f} por 1.000 habitantes", texttemplate="%{x:.3f}", textposition="inside")

#Para seguir con la jerarquía de colores usamos otro tono de naranja y gris. 
for barra in fig_estados.data:
    if barra.name == "Considerados activos":
        barra.marker.color = ["#C65D21"] + ["#84919E"] * (len(barra.y) - 1)
    else:
        barra.marker.color = ["#E9B28D"] + ["#D0D5DA"] * (len(barra.y) - 1) 
fig_estados.update_yaxes(autorange="reversed")
st.plotly_chart(fig_estados, use_container_width=True)

# Hallazgo 4
st.markdown(
    "**Hallazgo:** Bogotá Limpia presenta la mayor tasa total de puntos críticos registrados (0,216 por cada 1.000 habitantes). PromoAmbiental no registra puntos considerados activos, pero sí puntos en otros estados."
)
st.divider()


# Evolución mensual grafica
st.subheader("5. Evolución mensual de PQRS")
# Utilizamos directamente la tabla mensual filtrada por concesionario.
mensual = mensual_filtrado.copy()
# Resaltar el concesionario con mayor tasa anual de PQRS en la selección.
lider_anual = por_operador.loc[por_operador["PQRS_POR_1000_HAB"].idxmax(), "CONCESIONARIO"]
colores = {nombre: "#C65D21" if nombre == lider_anual else "#A6B0BA"
           for nombre in por_operador["CONCESIONARIO"]}
fig_mensual = px.line(
    mensual.sort_values("MES"), x="MES", y="PQRS_POR_1000_HAB", color="CONCESIONARIO",
    color_discrete_map=colores, markers=True, template="plotly_white",
    labels={"MES": "Mes", "PQRS_POR_1000_HAB": "PQRS por 1.000 habitantes", "CONCESIONARIO": "Concesionario"},
    hover_data={"NUM_PQRS": True}
)
# Cambiamos el ancho de la linea para resaltar al concesionario con mayor tasa anual
for linea in fig_mensual.data:
    if linea.name == lider_anual:
        linea.line.width = 4
    else:
        linea.line.width = 2

fig_mensual.update_xaxes(dtick="M1", tickformat="%m/%Y")
fig_mensual.update_layout(height=400, separators=",.")
st.plotly_chart(fig_mensual, use_container_width=True)

# Hallazgo 5
st.markdown(
    "**Hallazgo:** Bogotá Limpia presenta la mayor tasa mensual de PQRS en 10 de los 12 meses de 2025, con picos en marzo y septiembre. Esto indica que las tasas elevadas no se limitan a un único mes."
)
st.divider()

st.caption("La disminución de diciembre podría corresponder a una cobertura incompleta del periodo, no se ha confirmado su causa.")


# Decisión final y notas metodológicas
st.subheader("Decisión sugerida para 2027")
st.write("**Análisis general de los cinco concesionarios:** ....Pendiente...")

# Agregamos la tabla que resulto de todo el análisis para quien desee consultarla
with st.expander("Detalle por localidad"):
    st.dataframe(filtrado[["CONCESIONARIO", "LOCALIDAD", "POBLACION", "NUM_PQRS", "NUM_PUNTOS_CRITICOS", "CAPACIDAD_TOTAL_CONTENEDORES"]], hide_index=True)


with st.expander("Fuentes, supuestos y limitaciones"):
    st.write("Los 105 puntos de Ciudad Limpia sin estado original se consideran activos bajo el supuesto metodológico del proyecto. Los criterios de clasificación pueden diferir entre operadores.")
    st.write("Las PQRS se asignan mediante la cobertura territorial, no identifican necesariamente al responsable directo. La población de las localidades aproxima la población atendida. La capacidad registrada no mide utilización ni frecuencia de vaciado. Los indicadores no demuestran causalidad.")
    st.caption("Fuentes: SIGAB/UAESP y datos demográficos por localidad. Preparación: notebooks/desarrollo.ipynb.")
