# 🚀 EARTH TO SPACE: NEW HORIZONS

**Plataforma de Análisis Comparativo entre la Tierra, la Luna y Marte**  
Desarrollado para el **NASA Space Apps Challenge** · Equipo QUEBRACHO COSMOS · Santiago del Estero, Argentina

---

## ¿Qué es?

EARTH TO SPACE: NEW HORIZONS es una aplicación web interactiva que identifica y compara cuantitativamente análogos terrestres para objetivos de exploración espacial (Polo Sur Lunar – Programa Artemis, Marte Arcadia Planitia y Marte Cráter Jezero).

Utiliza exclusivamente APIs públicas y gratuitas:
- **NASA POWER API** — Climatología satelital (temperatura, precipitación, radiación solar, humedad de suelo, albedo)
- **Open-Meteo Elevation API** — Modelos de elevación digital (DEM) para pendiente y rugosidad topográfica
- **NASA Trek WMTS** — Capas de imagen orbital de la Luna y Marte
- **Nominatim / OpenStreetMap** — Búsqueda de localizaciones por nombre

---

## Características

- 🔬 **Motor de similitud 6D** — Evalúa frío extremo, amplitud térmica, aridez/suelo, topografía, dinámica eólica y altitud/presión/solar
- 🌍 **Explorador Global Interactivo** — Mapa Folium con NASA Blue Marble, clic para evaluar cualquier punto del planeta
- 📊 **Análisis Detallado** — KPIs, radar multidimensional, estacionalidad mensual y superficie 3D de terreno real
- ⚖️ **Comparativa Directa** — Comparativa entre sitios poco estudiados vs. referencias históricas clásicas
- 🧪 **Laboratorio de Datos** — Dispersión paramétrica configurable y exportación CSV
- 🎯 **Penalizaciones de coherencia física** — Los rankings son científicamente diferenciados por objetivo

---

## Instalación

```bash
# Clonar el repositorio
git clone <repo-url>
cd nasa-analog-finder

# Crear entorno virtual e instalar dependencias
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt

# Lanzar la aplicación
streamlit run app.py
```

**Dependencias** (`requirements.txt`):
```
streamlit
pandas
numpy
requests
scikit-learn
plotly
folium
streamlit-folium
```

> No se requieren GDAL, rasterio ni geopandas. No se usa ninguna API key.

---

## Estructura del Proyecto

```
nasa-analog-finder/
├── app.py                      # Aplicación principal Streamlit
├── requirements.txt
├── .streamlit/
│   └── config.toml             # Tema oscuro Azul Francia
├── data/
│   ├── earth_analogs.csv       # Catálogo de 50 sitios análogos globales
│   └── earth_seasonality.json  # Estacionalidad mensual por sitio
├── src/
│   ├── earth_fetcher.py        # Consulta NASA POWER + Open-Meteo
│   ├── planetary_profiles.py   # Perfiles Luna y Marte (LRO, MOLA, MEDA)
│   └── similarity.py           # Motor cuantitativo multidimensional
└── scripts/
    └── build_dataset.py        # Construcción y actualización del catálogo
```

---

## Auditoría Científica del Ranking

El motor aplica **penalizaciones de coherencia física** diferenciadas por objetivo:

| Objetivo | Restricción principal | Qué se destaca |
|---|---|---|
| **Polo Sur Lunar** | t_min > 0°C o precipitación > 250 mm → penalización severa | Sitios gélidos, secos, con relieve de cráter |
| **Marte – Arcadia Planitia** | pendiente > 10° o rugosidad > 25 m → penalización progresiva | Llanuras frías, permafrost, terreno plano |
| **Marte – Cráter Jezero** | aridity < 0.50 o precipitación > 300 mm → penalización severa | Hiper-áridos, basalto volcánico, alta oscilación térmica |

Cráteres de impacto en climas húmedos reciben una penalización ambiental adicional (solo valen por morfología de cráter, no como análogo ambiental completo).

---

## Equipo — QUEBRACHO COSMOS

| Nombre | Rol | Usuario |
|---|---|---|
| **Bukret Brisa Abigail** | Team Owner | @bukretbrisa_5 |
| **Franzisco Pérez Real** | Miembro | @franzisco |
| **Jorge Nicolás Gómez Paz Maldonado** | Miembro | @nicolasgp.sgo26 |
| **Daniela Guadalupe Figueroa** | Miembro | @danich04 |
| **Mauricio Hernandez** | Miembro | @maurih |

**Argentina · NASA Space Apps Challenge**

---

## Datos y Precisión

Los datos de telemetría provienen de modelos satelitales públicos. La precisión está sujeta a la resolución espacial de los modelos (NASA POWER: ~0.5° × 0.5°, Open-Meteo DEM: ~90 m). Los perfiles planetarios se basan en datos de misiones LRO (Luna), MRO/Mars Odyssey (Arcadia) y Perseverance MEDA (Jezero).

**Ningún sitio terrestre puede eliminar la gravedad de 1G ni el blindaje magnetosférico terrestre.**
