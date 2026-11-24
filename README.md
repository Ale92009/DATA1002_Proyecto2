# DATA1002 | Proyecto 2: servicio de aseo en Bogotá

## Pregunta de análisis

¿Qué concesionario de aseo de la zona urbana de Bogotá debería priorizarse para implementar un plan piloto de mejora durante 2027, considerando la cantidad de puntos críticos activos, las PQRS registradas durante 2025 y la capacidad de contenerización disponible en relación con la población atendida?


El análisis usa información de 2025 como referencia para orientar la decisión. Compara cinco concesionarios en las 19 localidades incluidas en el análisis urbano.

## Tablero interactivo

[Consultar el tablero del servicio de aseo en Bogotá en Streamlit](https://proyecto-aseo-bogota.streamlit.app/)

El dashboard interactivo está desarrollado en
[src/dashboard.py](src/dashboard.py).

Utiliza los datos integrados del proyecto y permite
comparar los cinco concesionarios de aseo mediante
indicadores de PQRS, puntos críticos y capacidad
registrada de contenedores.

Incluye filtros por concesionario y localidad.
Los indicadores por cada 1.000 habitantes se
recalculan según la selección realizada.
## Instalación y ejecución

El análisis se ejecutó con Python 3.14.7. Desde la raíz del repositorio, crea un entorno virtual e instala las dependencias. En Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m jupyterlab
```

En JupyterLab, abre [notebooks/desarrollo.ipynb](notebooks/desarrollo.ipynb), selecciona el kernel de Python del entorno y ejecuta todas las celdas en orden. El notebook usa rutas relativas a la carpeta `notebooks/`.

## Datos y método

El notebook combina los registros de SIGAB sobre contenedores, puntos críticos y PQRS por localidad con los datos de población de 2025 y una tabla de correspondencia de localidades. Los archivos de entrada están en [data/raw/](data/raw/).

1. Se prepara una tabla por localidad y concesionario con la población, las PQRS y los indicadores de infraestructura y puntos críticos.
2. Para los contenedores, se usa el estado `UC` (ubicación confirmada) para calcular la cantidad y la capacidad registrada.
3.  Para el análisis de puntos críticos, los 105 registros de Ciudad Limpia que originalmente no tenían información de estado se clasifican como activos. Esta clasificación es un supuesto metodológico y no una confirmación de su estado original. El dashboard conserva la posibilidad de identificar cuántos registros fueron clasificados de esta forma.
4. Se agregan los conteos y la población por concesionario antes de calcular las tasas por cada 1.000 habitantes. También se compara la evolución mensual de las PQRS de 2025.

La ubicación confirmada indica dónde figura el contenedor en el inventario. El indicador de capacidad describe la infraestructura registrada y permite orientar la revisión junto con los puntos críticos y las PQRS.

## Archivos del proyecto

| Ruta | Contenido |
| --- | --- |
| [notebooks/desarrollo.ipynb](notebooks/desarrollo.ipynb) | Preparación de las fuentes, indicadores y gráficos del análisis. |
| [data/processed/df_final.csv](data/processed/df_final.csv) | Tabla consolidada por localidad y concesionario. |
| [outputs/tables/](outputs/tables/) | Resumen por concesionario, comparación de estados de puntos críticos y serie mensual de PQRS. |
| [outputs/figures/](outputs/figures/) | Gráficos exportados en PNG. |
| [reports/Datos.docx](reports/Datos.docx) | Documento de trabajo sobre los datos del proyecto. |

Al ejecutar el notebook, los resultados se muestran en sus celdas. Los CSV y PNG de las carpetas de resultados son exportaciones guardadas por separado.
