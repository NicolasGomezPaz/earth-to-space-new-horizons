"""
Earth To Space: New Horizons - Internationalization Layer (EN / ES)
==================================================================
Traduce dinámicamente la interfaz Streamlit, gráficos Plotly, mapas Folium,
DataFrames y mensajes científicos generados por los módulos internos sin
modificar la lógica de cálculo ni los nombres geográficos propios.
"""

import re
import copy
from typing import Any, Dict, List
import streamlit as st
from streamlit.delta_generator import DeltaGenerator
import folium
import pandas as pd

_CURRENT_LANG = "en"
_PATCHED = False
_ORIG_DG: Dict[str, Any] = {}
_ORIG_ST: Dict[str, Any] = {}
_ORIG_FOLIUM: Dict[str, Any] = {}

# Diccionario maestro de traducciones exactas (ES -> EN)
EXACT_ES_TO_EN: Dict[str, str] = {
    # Sidebar & Navegación
    "NEW HORIZONS // MISIÓN NASA": "NEW HORIZONS // NASA MISSION",
    "🎯 1. Objetivo Espacial": "🎯 1. Space Target",
    "Selecciona el destino:": "Select destination:",
    "Polo Sur Lunar (Cráter Shackleton / Artemis)": "Lunar South Pole (Shackleton Crater / Artemis)",
    "Marte - Arcadia Planitia (Hielo Somero / Base)": "Mars - Arcadia Planitia (Shallow Ice / Base)",
    "Marte - Cráter Jezero (Perseverance / Delta)": "Mars - Jezero Crater (Perseverance / Delta)",
    "📡 Telemetría Real de Misión NASA": "📡 Real NASA Mission Telemetry",
    "🔬 Mostrar solo Sitios Poco Estudiados": "🔬 Show Only Under-Studied Sites",
    "Excluye los sitios clásicos consagrados (como Atacama o Devon Island) para resaltar candidatos poco investigados.":
        "Excludes well-known benchmarks (such as Atacama or Devon Island) to highlight under-studied candidates.",
    "⚙️ 2. Modo de Misión": "⚙️ 2. Mission Mode",
    "Configuración científica:": "Scientific preset:",
    "🎚️ Calibración Manual de Pesos (6D)": "🎚️ Manual Weight Calibration (6D)",
    "Ajusta la importancia relativa de cada dimensión científica:": "Adjust the relative weight of each scientific dimension:",
    "Frío Extremo": "Extreme Cold",
    "Amplitud Térmica": "Thermal Amplitude",
    "Aridez & Suelo": "Aridity & Soil",
    "Relieve & Topografía": "Relief & Topography",
    "Viento & Dinámica Eólica": "Wind & Aeolian Dynamics",
    "Altitud & Radiación Solar": "Altitude & Solar Radiation",
    "📖 Glosario: ¿Qué mide cada variable?": "📖 Glossary: What Each Variable Measures",

    # Presets de Misión
    "Balanceado Científico General": "Balanced General Science",
    "Ponderación holística equilibrada entre clima, topografía, suelo y radiación.":
        "Balanced holistic weighting across climate, topography, soil, and radiation.",
    "Pruebas de Movilidad de Rover": "Rover Mobility Testing",
    "Prioriza el relieve (pendiente, rugosidad del terreno) y el suelo árido para evaluar tracción y navegación.":
        "Prioritizes terrain relief (slope, roughness) and arid soil to evaluate traction and navigation.",
    "Extracción de Hielo y Recursos In-Situ (ISRU)": "Ice Extraction & In-Situ Resources (ISRU)",
    "Enfocado en frío criogénico, permafrost, hiper-aridez y condiciones extremas de perforación.":
        "Focused on cryogenic cold, permafrost, hyper-aridity, and extreme drilling conditions.",
    "Suelo/Polvo y Paneles Solares": "Soil/Dust & Solar Arrays",
    "Optimizado para evaluar acumulación de polvo regolítico, albedo superficial y radiación solar.":
        "Optimized to evaluate regolith dust accumulation, surface albedo, and solar irradiance.",

    # Nombres cortos y geología
    "Polo Sur Lunar": "Lunar South Pole",
    "Marte · Arcadia Planitia": "Mars · Arcadia Planitia",
    "Marte · Cráter Jezero": "Mars · Jezero Crater",
    "Luna": "Moon",
    "Marte": "Mars",
    "Basalto Volcánico": "Volcanic Basalt",
    "Salar / Evaporita": "Salt Flat / Evaporite",
    "Cráter de Impacto": "Impact Crater",
    "Permafrost / Hielo": "Permafrost / Ice",
    "Regolito Hiperárido": "Hyper-arid Regolith",

    # Pestañas
    "🌍 Explorador Global": "🌍 Global Explorer",
    "🔬 Análisis Detallado": "🔬 Detailed Analysis",
    "⚖️ Comparativa Directa": "⚖️ Direct Comparison",
    "📊 Laboratorio": "📊 Data Lab",
    "🧪 Experimentos": "🧪 Experiments",

    # Pestaña 1: Explorador Global
    "**🔍 Búsqueda de Localizaciones (OpenStreetMap Nominatim):**": "**🔍 Location Search (OpenStreetMap Nominatim):**",
    "Ingresa un lugar del mundo:": "Enter any location worldwide:",
    "Ej. Desierto de Atacama, Volcán Askja, Salar de Uyuni...": "E.g., Atacama Desert, Askja Volcano, Salar de Uyuni...",
    "🔍 Buscar": "🔍 Search",
    "No se encontraron coordenadas para esa consulta.": "No coordinates found for that query.",
    "Coincidencias encontradas:": "Matches found:",
    "🚀 Evaluar este lugar en vivo": "🚀 Evaluate This Site Live",
    "Consultando datos de satélite y clima...": "Querying satellite and climate data...",
    "**📍 Consulta por Coordenadas Manuales:**": "**📍 Query by Manual Coordinates:**",
    "Latitud:": "Latitude:",
    "Longitud:": "Longitude:",
    "Nombre de referencia:": "Reference name:",
    "Coordenada Personalizada": "Custom Coordinate",
    "📡 Analizar Coordenadas": "📡 Analyze Coordinates",
    "Analizando terreno y climatología satelital...": "Analyzing terrain and satellite climatology...",
    "**🗺️ Mapa Global de Análogos (Haz clic para evaluar cualquier punto):**": "**🗺️ Global Analog Map (Click anywhere to evaluate):**",
    "🛰️ Satélite Esri": "🛰️ Esri Satellite",
    "🗺️ OpenStreetMap": "🗺️ OpenStreetMap",
    "🌍 NASA Blue Marble": "🌍 NASA Blue Marble",
    "🔬 Evaluar este punto clicado": "🔬 Evaluate Clicked Point",
    "Consultando variables climáticas y topográficas...": "Querying climate and topographic variables...",
    "##### 🏆 Top 3 Candidatos Destacados": "##### 🏆 Top 3 Highlighted Candidates",
    "#### 🏆 Clasificación de Similitud Global": "#### 🏆 Global Similarity Ranking",
    "Catálogo completo clasificado cuantitativamente según el modo de misión activo:":
        "Full catalog quantitatively ranked under the active mission mode:",
    "Cantidad de sitios a listar en la tabla:": "Number of sites to display in table:",

    # Pestaña 2: Análisis Detallado
    "Selecciona el sitio a evaluar:": "Select site to evaluate:",
    "Similitud Global": "Overall Similarity",
    "Similitud cuantitativa ponderada a través de las 6 dimensiones científicas.":
        "Weighted quantitative similarity across all 6 scientific dimensions.",
    "T° Mínima Anual": "Annual Min Temp",
    "Pendiente & Relieve": "Slope & Relief",
    "Suelo (GWETTOP)": "Soil (GWETTOP)",
    "Albedo de Suelo": "Surface Albedo",
    "Estrés Astrobiológico": "Astrobiology Stress",
    "##### 🧮 Justificación Cuantitativa del Puntaje": "##### 🧮 Quantitative Score Breakdown",
    "**📡 Perfil Multidimensional (Radar 6D vs. Ideal Espacial):**": "**📡 Multidimensional Profile (6D Radar vs. Space Ideal):**",
    "**📅 Curva Estacional Anual (Enero – Diciembre):**": "**📅 Annual Seasonal Curve (January – December):**",
    "Datos estacionales en proceso de consulta para este punto.": "Seasonal data is not available for this custom point.",
    "##### 🏔️ Reconstrucción Topográfica 3D del Terreno (Open-Meteo DEM 7x7)":
        "##### 🏔️ 3D Topographic Terrain Reconstruction (Open-Meteo DEM 7x7)",
    "Malla altimétrica real de 49 puntos (~2.8 km de radio) para inspeccionar obstáculos, pendientes y rugosidad:":
        "Real 49-point elevation mesh (~2.8 km radius) to inspect obstacles, slopes, and roughness:",
    "No se pudo reconstruir la malla 3D para este punto geográfico.": "Could not reconstruct the 3D terrain mesh for this location.",
    "##### 🛰️ Visor Dual: Terreno Terrestre vs. Cartografía Orbital NASA Trek":
        "##### 🛰️ Dual Viewer: Earth Terrain vs. NASA Trek Orbital Mapping",
    "##### ⚖️ Validez Científica y Limitaciones": "##### ⚖️ Scientific Validity & Limitations",
    "**✅ Dónde SÍ es Válida la Analogía:**": "**✅ Where the Analogy HOLDS:**",
    "**❌ Dónde SE ROMPE la Analogía:**": "**❌ Where the Analogy BREAKS DOWN:**",
    "**🛰️ Ensayos de Ingeniería Recomendados:**": "**🛰️ Recommended Engineering Tests:**",
    "📥 Descargar Informe Técnico (.md)": "📥 Download Technical Report (.md)",
    "📊 Descargar Métricas (.csv)": "📊 Download Metrics (.csv)",

    # Pestaña 3: Comparativa Directa
    "#### ⚖️ Comparativa Directa: Sitio Poco Estudiado vs. Referencia Histórica":
        "#### ⚖️ Direct Comparison: Under-Studied Site vs. Historical Benchmark",
    "Compara cara a cara el rendimiento de nuevos candidatos geológicos frente a los sitios tradicionales de prueba de la NASA.":
        "Compare newly identified geological candidates head-to-head against traditional NASA test sites.",
    "🔬 Sitio Poco Estudiado (Candidato):": "🔬 Under-Studied Site (Candidate):",
    "🏛️ Sitio de Referencia Histórica:": "🏛️ Historical Benchmark Site:",
    "**📡 Superposición de Perfiles (Radar Comparativo):**": "**📡 Profile Overlay (Comparative Radar):**",
    "**🌡️ Curva Térmica Mensual Comparada (Piel de Suelo):**": "**🌡️ Monthly Soil Skin Temperature Comparison:**",
    "Datos mensuales no disponibles para uno de los sitios en la comparativa.": "Monthly data unavailable for one of the sites in this comparison.",
    "##### 📊 Comparación Directa de Parámetros:": "##### 📊 Direct Parameter Comparison:",

    # Pestaña 4: Laboratorio
    "#### 📊 Laboratorio de Datos y Análisis Multivariado": "#### 📊 Data Laboratory & Multivariate Analysis",
    "Aplica filtros por rangos físicos para explorar patrones geofísicos y descargar conjuntos de datos personalizados:":
        "Filter by physical ranges to explore geophysical patterns and download custom datasets:",
    "Elevación (m):": "Elevation (m):",
    "Aridez:": "Aridity Index:",
    "Pendiente (°):": "Slope (°):",
    "Tipos Geológicos:": "Geological Types:",
    "Eje Horizontal (X):": "Horizontal Axis (X):",
    "Eje Vertical (Y):": "Vertical Axis (Y):",
    "Variable de Color:": "Color Variable:",
    "##### 📋 Catálogo Filtrado:": "##### 📋 Filtered Catalog:",
    "📥 Descargar Catálogo Filtrado (CSV)": "📥 Download Filtered Catalog (CSV)",

    # Pestaña 5: Experimentos
    "#### 🧪 Simulador de Experimentos de Ingeniería en Sitio": "#### 🧪 On-Site Engineering Experiment Simulator",
    "##### 🛞 Simulador 1 — Movilidad de Rover (1.0 G vs. Gravedad Espacial)":
        "##### 🛞 Simulator 1 — Rover Mobility (1.0 G vs. Space Gravity)",
    "Vehículo de referencia:": "Reference vehicle:",
    "Perseverance (1,025 kg)": "Perseverance (1,025 kg)",
    "VIPER Lunar (430 kg)": "VIPER Lunar (430 kg)",
    "Mini-Rover (60 kg)": "Mini-Rover (60 kg)",
    "Personalizado": "Custom",
    "Masa del rover (kg):": "Rover mass (kg):",
    "Velocidad de marcha (m/s):": "Travel speed (m/s):",
    "Tierra (1.0 G)": "Earth (1.0 G)",
    "Fuerza Pendiente (N)": "Slope Force (N)",
    "Fuerza Rodadura (N)": "Rolling Force (N)",
    "Potencia Requerida (W)": "Required Power (W)",
    "Potencia en Tierra (1.0 G)": "Power on Earth (1.0 G)",
    "##### ☀️ Simulador 2 — Presupuesto Solar y Atenuación por Polvo (12 Meses)":
        "##### ☀️ Simulator 2 — Solar Budget & Dust Attenuation (12 Months)",
    "ℹ️ Sitio evaluado en vivo: usando reconstrucción estacional aproximada a partir de sus medias anuales NASA.":
        "ℹ️ Live-evaluated site: using approximate seasonal reconstruction from annual NASA means.",
    "Área de paneles solares (m²):": "Solar panel area (m²):",
    "Eficiencia fotovoltaica (%):": "Photovoltaic efficiency (%):",
    "Consumo diario misión (Wh/día):": "Daily mission load (Wh/day):",
    "Meta Espacial Diaria": "Daily Space Target",
    "Mejor Mes en Sitio": "Best Month On-Site",
    "Mes Réplica Energética": "Energy-Match Month",
    "Meses Autosuficientes": "Self-Sufficient Months",
    "No hay datos estacionales suficientes para simular energía solar en este punto.":
        "Insufficient seasonal data to simulate solar power at this location.",
    "##### 📅 Ventana Óptima de Campaña y Bitácora de Investigación":
        "##### 📅 Optimal Campaign Window & Research Log",
    "Tipo de experimento a programar:": "Experiment type to schedule:",
    "Pruebas Criogénicas y Baterías": "Cryogenic & Battery Testing",
    "Movilidad Autónoma de Rover": "Autonomous Rover Mobility",
    "Energía Solar y Mitigación de Polvo": "Solar Power & Dust Mitigation",
    "Operaciones Humanas (EVA)": "Human Operations (EVA)",
    "➕ Guardar simulación en bitácora": "➕ Save Simulation to Log",
    "¡Experimento registrado en la bitácora!": "Experiment saved to research log!",
    "###### 📓 Tu Registro de Investigación": "###### 📓 Your Research Log",
    "📥 Descargar Bitácora (.csv)": "📥 Download Research Log (.csv)",
    "🗑️ Limpiar bitácora": "🗑️ Clear Log",

    # Mensajes de Planetary Profiles & Glosario & Tests
    "Exósfera colisionalmente despreciable (He, Ne, H2, Ar)": "Collisionless exosphere (He, Ne, H2, Ar)",
    "95.3% CO2, 2.6% N2, 1.9% Ar, trazas de vapor de agua y O2": "95.3% CO2, 2.6% N2, 1.9% Ar, trace water vapor and O2",
    "CO2 dominante; ciclos de condensación/sublimación polar estacional": "CO2 dominant; seasonal polar condensation/sublimation cycles",
    "Ensayos de movilidad en pendientes pronunciadas (>12°) con regolito suelto y simulación de ruedas elásticas Artemis.":
        "Mobility tests on steep slopes (>12°) with loose regolith and Artemis compliant-wheel simulation.",
    "Validación de reflectancia óptica y navegación autónoma LiDAR en entornos de alto contraste luz/sombra permanente.":
        "Optical reflectance validation and autonomous LiDAR navigation in high-contrast sunlit/permanently shadowed terrain.",
    "Pruebas de perforación percusiva criogénica para extracción de núcleos de permafrost o hielo volátil.":
        "Cryogenic percussive drilling tests for permafrost or volatile ice core extraction.",
    "Ensayo de mitigación de abrasión por polvo regolítico en juntas rotativas y trajes EVA.":
        "Regolith dust abrasion mitigation testing on rotary joints and EVA suits.",
    "Simulación de radar de penetración terrestre (GPR) para detección y mapeo volumétrico de hielo somero.":
        "Ground-penetrating radar (GPR) simulation for shallow subsurface ice detection and volumetric mapping.",
    "Pruebas de aterrizaje vertical y sustentación de zapatas en regolito sedimentario plano con baja rugosidad.":
        "Vertical landing and footpad load-bearing tests on flat sedimentary regolith with low roughness.",
    "Ensayos de sistemas ISRU de extracción de agua a partir de horizontes permafrost someros.":
        "ISRU water-extraction system trials on shallow permafrost horizons.",
    "Evaluación de degradación por depósito de polvo eólico sobre paneles solares horizontales.":
        "Degradation assessment from aeolian dust deposition on horizontal solar arrays.",
    "Navegación autónoma y evitación de obstáculos (AutoNav) en campos de cantos rodados y escarpes deltaicos.":
        "Autonomous navigation and hazard avoidance (AutoNav) across boulder fields and deltaic scarps.",
    "Calibración de instrumentos espectroscópicos de fluorescencia de rayos X y Raman (análogos a PIXL y SHERLOC).":
        "Calibration of X-ray fluorescence and Raman spectrometers (analogous to PIXL and SHERLOC).",
    "Muestreo y sellado de testigos de roca ígnea/basáltica y arcillas sedimentarias para retorno de muestras (MSR).":
        "Coring and sealing of igneous/basaltic rock and sedimentary clay samples for Mars Sample Return (MSR).",
    "Ensayos de abrasión y transporte eólico de arena sobre carcasas de instrumentación científica expuesta.":
        "Aeolian sand transport and abrasion testing on exposed scientific instrument housings.",

    # Glosario
    "Albedo Superficial (ALLSKY_SRF_ALB)": "Surface Albedo (ALLSKY_SRF_ALB)",
    "adimensional (0.0 a 1.0)": "dimensionless (0.0 to 1.0)",
    "Humedad del Suelo Superficial (GWETTOP)": "Surface Soil Wetness (GWETTOP)",
    "Presión Atmosférica Superficial (PS)": "Surface Atmospheric Pressure (PS)",
    "kilopascales (kPa)": "kilopascals (kPa)",
    "Amplitud Térmica Anual": "Annual Thermal Amplitude",
    "grados Celsius (°C)": "degrees Celsius (°C)",
    "Pendiente Topográfica (Método de Horn)": "Topographic Slope (Horn Method)",
    "grados sexagesimales (°)": "degrees (°)",
    "Rugosidad del Terreno": "Terrain Roughness",
    "metros (m)": "meters (m)",
    "Índice de Aridez Cuantitativo": "Quantitative Aridity Index",
    "escala normalizada (0.0 a 1.0)": "normalized scale (0.0 to 1.0)",
    "Índice de Estrés Astrobiológico": "Astrobiology Stress Index",
    "escala 0 a 100": "scale 0 to 100",
    "Indica qué fracción de la luz solar incidente es reflejada por el suelo. El basalto volcánico oscuro y el regolito lunar absorben gran parte de la radiación (albedo bajo ~0.12). En contraste, las arenas oxidadas brillantes y el polvo marciano reflejan más luz (~0.26).":
        "Fraction of incident sunlight reflected by the ground. Dark volcanic basalt and lunar regolith absorb most radiation (low albedo ~0.12), while bright oxidized sands and Martian dust reflect more (~0.26).",
    "Humedad volumétrica en los primeros 0 a 5 cm de la capa superficial del suelo. En la Luna y Marte el regolito es absolutamente anhidro (0.00). En la Tierra, los desiertos hiper-áridos extremos (como Atacama o Lut) alcanzan valores inferiores a 0.10.":
        "Volumetric wetness in the top 0–5 cm soil layer. Lunar and Martian regolith is completely anhydrous (0.00); extreme hyper-arid deserts on Earth fall below 0.10.",
    "Fuerza que ejerce la atmósfera sobre la superficie terrestre (a nivel del mar es ~101.3 kPa). La Luna posee un vacío casi absoluto (10⁻¹¹ kPa) y Marte una atmósfera extremadamente tenue (~0.6-0.8 kPa). Los altiplanos y cumbres volcánicas terrestres (>4.500 m) alcanzan entre 45 y 60 kPa, reduciendo la columna de aire.":
        "Atmospheric pressure at the surface (~101.3 kPa at sea level). The Moon is near-vacuum (10⁻¹¹ kPa) and Mars is ~0.6–0.8 kPa. High Andean/Tibetan plateaus (>4,500 m) drop to 45–60 kPa.",
    "Diferencia entre la temperatura máxima y mínima anual (T2M_MAX - T2M_MIN). En el espacio, al no haber vapor de agua ni vegetación amortiguadora, los cuerpos celestes sufren cambios térmicos brutales (>30°C a >150°C), sometiendo a rovers y trajes a severa fatiga térmica por dilatación y contracción.":
        "Spread between annual maximum and minimum temperature (T2M_MAX - T2M_MIN). Without atmospheric buffering, planetary surfaces undergo severe thermal cycling that stresses hardware and seals.",
    "Inclinación calculada sobre una cuadrícula 3x3 de elevaciones teniendo en cuenta la curvatura terrestre. Pendientes suaves (<4°) son ideales para aterrizaje seguro (como Arcadia Planitia), mientras que pendientes pronunciadas (>12°) replican las murallas de cráteres de impacto y escarpes deltaicos.":
        "Terrain inclination computed over a 3x3 elevation grid accounting for Earth's curvature. Gentle slopes (<4°) match flat plains like Arcadia, while steep slopes (>12°) mimic crater rims and delta scarps.",
    "Desviación estándar de las elevaciones en un radio de ~550 m. Cuantifica la presencia de peñascos, crestas rocosas y micro-barrancos. Esencial para evaluar el riesgo de vuelco y la tracción de ruedas.":
        "Standard deviation of elevations within a ~550 m neighborhood. Quantifies boulders, ridges, and micro-gullies—critical for rollover risk and wheel traction.",
    "Calculado combinando la precipitación media diaria y la humedad relativa a 2 m. 0.0 representa selvas hiper-húmedas, mientras que valores >0.85 indican hiper-aridez extrema análoga a la ausencia de agua libre en Marte y la Luna.":
        "Computed from mean daily precipitation and 2 m relative humidity. 0.0 represents wet rainforests, while values >0.85 indicate extreme hyper-aridity analogous to Mars and the Moon.",
    "Medida combinada de hostilidad ambiental para la biología terrestre: integra radiación solar/UV incidente, desecación extrema y choque por oscilaciones térmicas. Cuanto más alto, más estéril y desafiante es el hábitat.":
        "Composite measure of environmental hostility to terrestrial life combining solar/UV irradiance, extreme desiccation, and thermal shock.",

    # Columnas & Tablas
    "Sitio": "Site",
    "País": "Country",
    "Geología": "Geology",
    "Similitud": "Similarity",
    "Similitud (%)": "Similarity (%)",
    "Elevación (m)": "Elevation (m)",
    "Aridez": "Aridity",
    "Amplitud Térmica (°C)": "Thermal Amplitude (°C)",
    "Variable": "Variable",
    "Evaluación Relativa": "Relative Assessment",
    "🔬 Mayor afinidad en candidato": "🔬 Higher affinity in candidate",
    "🏛️ Mayor afinidad en referencia": "🏛️ Higher affinity in benchmark",
    "Depende del perfil de misión": "Depends on mission profile",
    "Similitud Global": "Overall Similarity",
    "Elevación": "Elevation",
    "Pendiente Topográfica": "Topographic Slope",
    "Rugosidad de Terreno": "Terrain Roughness",
    "Índice de Aridez": "Aridity Index",
    "Humedad del Suelo (GWETTOP)": "Surface Soil Wetness (GWETTOP)",
    "Amplitud Térmica Anual": "Annual Thermal Amplitude",
    "Estrés Astrobiológico": "Astrobiology Stress",
    "Frío": "Cold",
    "Ciclo Térmico": "Thermal Cycle",
    "Aridez/Suelo": "Aridity/Soil",
    "Relieve": "Relief",
    "Viento": "Wind",
    "Altitud/Solar": "Altitude/Solar",
    "Frío Extremo": "Extreme Cold",
    "Suelo & Aridez": "Soil & Aridity",
    "Relieve / Pendiente": "Relief / Slope",
    "Viento & Polvo": "Wind & Dust",
    "Altitud / Presión / Solar": "Altitude / Pressure / Solar",
    "Dimensión": "Dimension",
    "Afinidad (%)": "Affinity (%)",
    "Objetivo": "Target",
    "Experimento": "Experiment",
    "Mes Óptimo": "Optimal Month",
    "Rover (kg)": "Rover (kg)",
    "Potencia Tierra (W)": "Earth Power (W)",
    "Potencia Objetivo (W)": "Target Power (W)",
    "Masa Equiv (kg)": "Equiv. Mass (kg)",
    "Panel (m²)": "Panel (m²)",
    "Mes Réplica Solar": "Solar-Match Month",
    "Coordenada Clicada": "Clicked Coordinate",
    "Personalizado": "Custom",

    # Meses cortos
    "Ene": "Jan", "Abr": "Apr", "Ago": "Aug", "Dic": "Dec",
}

# Países y términos frecuentes
COUNTRY_AND_TERMS: List[tuple] = [
    ("Arabia Saudita", "Saudi Arabia"),
    ("Estados Unidos", "United States"),
    ("España", "Spain"),
    ("Alemania", "Germany"),
    ("Etiopía", "Ethiopia"),
    ("Túnez", "Tunisia"),
    ("Sudáfrica", "South Africa"),
    ("Rusia", "Russia"),
    ("Perú", "Peru"),
    ("México", "Mexico"),
    ("Canadá", "Canada"),
    ("Antártida", "Antarctica"),
    ("Islandia", "Iceland"),
    ("Botsuana", "Botswana"),
    ("Irán", "Iran"),
    ("Omán", "Oman"),
    ("Turkmenistán", "Turkmenistan"),
    ("Mauritania", "Mauritania"),
]

# Reglas regex para frases dinámicas (diagnósticos, explicaciones, HTML, simulador)
REGEX_RULES: List[tuple] = [
    # Hero Banner & Footer
    (r"¿Qué lugares de la Tierra se parecen a la Luna y Marte\?",
     "Which Places on Earth Resemble the Moon and Mars?"),
    (r"Explorando análogos entre la Tierra, la Luna y Marte con datos reales de la NASA, modelos satelitales NASA POWER, topografía DEM de alta resolución y cartografía orbital\.",
     "Exploring terrestrial analogs for the Moon and Mars using real NASA POWER satellite climatology, high-resolution DEM topography, and orbital mapping."),
    (r"Nuestro enfoque: <strong>Tierra · Luna · Marte</strong>",
     "Our Focus: <strong>Earth · Moon · Mars</strong>"),
    (r"Los datos de telemetr(&#237;|í)a son p(&#250;|ú)blicos y sin API key\. Precisi(&#243;|ó)n cient(&#237;|í)fica sujeta a resoluci(&#243;|ó)n espacial de los modelos satelitales\.",
     "All telemetry is open and requires no API keys. Scientific accuracy is subject to satellite model spatial resolution."),
    (r"Telemetr(&#237;|í)a NASA POWER", "NASA POWER Telemetry"),

    # Sidebar
    (r"\*\*Referencia:\*\*", "**Reference:**"),
    (r"\*\*Gravedad:\*\*", "**Gravity:**"),
    (r"\*\*Presión:\*\*", "**Pressure:**"),
    (r"\*\*T° Superficie:\*\*", "**Surface Temp:**"),
    (r"\*\*Atmósfera:\*\*", "**Atmosphere:**"),

    # Tab 1
    (r"Mayor afinidad cuantitativa con \*\*(.*?)\*\*:", r"Highest quantitative affinity with **\1**:"),
    (r"Inspeccionar #(\d+) ", r"Inspect #\1 "),
    (r"¡Sitio '([^']+)' evaluado e incorporado a la tabla!", r"Site '\1' evaluated and added to the table!"),
    (r"¡Punto '([^']+)' analizado con éxito!", r"Point '\1' analyzed successfully!"),
    (r"¡Punto \(([^)]+)\) incorporado al ranking!", r"Point (\1) added to ranking!"),
    (r"📍 Punto seleccionado en el mapa: Lat `([^`]+)`, Lon `([^`]+)`", r"📍 Selected map point: Lat `\1`, Lon `\2`"),
    (r"Sitio '([^']+)' seleccionado para Análisis Detallado\.", r"Site '\1' selected for Detailed Analysis."),
    (r"⭐ \[NUEVO\] ", "⭐ [NEW] "),
    (r"⭐ Sitio Evaluado en Vivo:", "⭐ Live-Evaluated Site:"),
    (r"\(([0-9.]+)% afinidad con ([^)]+)\)", r"(\1% affinity with \2)"),
    (r"<b>País:</b>", "<b>Country:</b>"),
    (r"<b>Similitud:</b>", "<b>Similarity:</b>"),
    (r"<b>Geología:</b>", "<b>Geology:</b>"),
    (r"<b>Elevación:</b>", "<b>Elevation:</b>"),
    (r"<b>Aridez:</b>", "<b>Aridity:</b>"),
    (r"T° Mín:", "Min T:"),
    (r"Aridez:", "Aridity:"),

    # Tab 2 KPIs & Pills
    (r"Humedad Suelo \(GWETTOP\):", "Soil Wetness (GWETTOP):"),
    (r"Amplitud Térmica:", "Thermal Amplitude:"),
    (r"Pendiente \(Horn\):", "Slope (Horn):"),
    (r"Presión:", "Pressure:"),
    (r"Geología:", "Geology:"),
    (r"Ajuste: ([+-]?\d+) pts", r"Bonus: \1 pts"),
    (r"Media: ([^°]+)°C", r"Mean: \1°C"),
    (r"Rugosidad: ([^m]+)m", r"Roughness: \1m"),
    (r"Meta: ", "Target: "),
    (r"\*\*Afinidad Geológica:\*\* `([^`]+)` \(Bonus aplicado: `([^`]+)`\)",
     r"**Geological Affinity:** `\1` (Applied bonus: `\2`)"),
    (r"Notas geológicas:", "Geological notes:"),
    (r"Sin notas adicionales\.", "No additional notes."),
    (r"Relieve en (.*?) \(Min: (.*?) m \| Max: (.*?) m\)", r"Terrain Relief at \1 (Min: \2 m | Max: \3 m)"),
    (r"\*\*🌍 Sitio Terrestre \(Satélite Esri\):\*\*", "**🌍 Earth Site (Esri Satellite):**"),
    (r"\*\*🪐 Cartografía Orbital NASA Trek:\*\*", "**🪐 NASA Trek Orbital Map:**"),
    (r"🚀 Abrir en NASA (.*?) Trek 3D ↗", r"🚀 Open in NASA \1 Trek 3D ↗"),

    # Tab 3 & Tab 4
    (r"Afinidad con ", "Affinity with "),
    (r"\*\*Sitios que cumplen los criterios:\*\* `(\d+)` de `(\d+)`",
     r"**Sites matching filters:** `\1` of `\2`"),
    (r"Dispersión: (.*?) vs\. (.*)", r"Scatter: \1 vs. \2"),

    # Tab 5 Simulator
    (r"Evalúa el comportamiento físico de hardware y determina las ventanas de campaña en el terreno terrestre frente a \*\*(.*?)\*\*\.",
     r"Evaluate physical hardware performance and identify field campaign windows on Earth against **\1**."),
    (r"📍 Sitio de ensayo:", "📍 Test site:"),
    (r"Terreno real de \*\*(.*?)\*\*: Pendiente `([^`]+)` · Rugosidad `([^`]+)`",
     r"Real terrain at **\1**: Slope `\2` · Roughness `\3`"),
    (r"Potencia en ", "Power on "),
    (r"Fuerza: ", "Force: "),
    (r"Masa Equiv\. en Tierra", "Equiv. Mass on Earth"),
    (r"Descarga: ", "Offload: "),
    (r"🔧 \*\*Calibración en campo:\*\* ", "🔧 **Field Calibration:** "),
    (r"Para replicar la tracción real en (.*?), el banco de pruebas en Tierra debe usar un arnés de descarga gravitacional que contrarreste ([0-9.]+) kg \(([0-9.]+)% del peso\) del rover, dejando una masa efectiva de ([0-9.]+) kg\.",
     r"To replicate real traction on \1, the Earth test rig must use a gravity-offload harness counteracting \2 kg (\3% of rover weight), leaving an effective mass of \4 kg."),
    (r"Pérdida polvo: ", "Dust loss: "),
    (r"Referencia (.*?) \(([0-9.]+) Wh\)", r"Reference \1 (\2 Wh)"),
    (r"Consumo mínimo \(([0-9.]+) Wh\)", r"Minimum load (\1 Wh)"),
    (r"Generación en ", "Generation at "),
    (r"El sistema de ([0-9.]+) m² × ([0-9.]+)% eficiencia genera en (.*?) aproximadamente ([0-9.]+) Wh/día \(con ([0-9.]+)% de pérdida por polvo/ángulo\)\. En el sitio terrestre, el mes que mejor replica ese nivel energético es \*\*(.*?)\*\* \(([0-9.]+) Wh/día\)\.",
     r"A \1 m² array at \2% efficiency generates ~ \4 Wh/day on \3 (assuming \5% dust/angle loss). At this Earth site, **\6** (\7 Wh/day) best replicates that energy budget."),
    (r"🗓️ \*\*Mejor trimestre:\*\* (.*?) \(Pico: \*\*(.*?)\*\*\)",
     r"🗓️ **Best quarter:** \1 (Peak: **\2**)"),
    (r"\*\*Mes menos favorable:\*\* `([^`]+)`", r"**Least favorable month:** `\1`"),
    (r"El mes óptimo es \*\*([^*]+)\*\*, con la temperatura superficial más baja del año \(([^ ]+) °C media, ([^ ]+) °C mínima\), maximizando el estrés criogénico sobre baterías, lubricantes y sellados poliméricos\.",
     r"The optimal month is **\1**, featuring the lowest surface temperatures of the year (\2 °C mean, \3 °C min), maximizing cryogenic stress on batteries, lubricants, and polymer seals."),
    (r"El mes óptimo es \*\*([^*]+)\*\* \(T° media ([^ ]+) °C, viento ([^ ]+) m/s\), que combina condiciones térmicas tolerables para electrónica y visibilidad suficiente\.",
     r"The optimal month is **\1** (mean T \2 °C, wind \3 m/s), balancing electronics-safe thermal conditions and visibility."),
    (r"El mes óptimo es \*\*([^*]+)\*\* \(([^ ]+) kWh/m²/día, viento ([^ ]+) m/s\), con el mayor flujo solar del año para maximizar la generación fotovoltaica y estudiar la tasa de acumulación de polvo eólico sobre paneles horizontales\.",
     r"The optimal month is **\1** (\2 kWh/m²/day, wind \3 m/s), offering peak annual solar flux to test photovoltaic output and wind-driven dust accumulation."),
    (r"El mes óptimo es \*\*([^*]+)\*\* \(T° media ([^ ]+) °C, viento ([^ ]+) m/s\), que representa el entorno más habitable para un operador con traje EVA análogo sin llegar a extremos de hipotermia ni golpe de calor\.",
     r"The optimal month is **\1** (mean T \2 °C, wind \3 m/s), offering the safest thermal window for analog EVA suit field operations."),

    # Diagnósticos y Explicación Humana (similarity.py)
    (r"Excelente hiper-aridez y regolito desecado \(Score Suelo/Aridez: ([0-9.]+)%\)\. Humedad superficial mínima \(([^)]+)\) que emula el sustrato espacial anhidro\.",
     r"Strong hyper-aridity and desiccated regolith (Soil/Aridity Score: \1%). Minimal surface wetness (\2) closely emulates anhydrous planetary substrates."),
    (r"Régimen térmico riguroso \(Score Frío: ([0-9.]+)%\)\. Mínimas anuales de ([^°]+)°C aproximan el entorno criogénico de (.*?)\.",
     r"Harsh thermal regime (Cold Score: \1%). Annual minima of \2°C approach the cryogenic environment of \3."),
    (r"Topografía altamente representativa \(Score Relieve: ([0-9.]+)%\)\. Pendiente \(([^°]+)°\) y rugosidad \(([^ ]+) m\) ofrecen desafíos mecánicos realistas\.",
     r"Highly representative topography (Relief Score: \1%). Slope (\2°) and roughness (\3 m) provide realistic mechanical mobility challenges."),
    (r"Fuerte estrés cíclico térmico \(([^°]+)°C de oscilación\), ideal para pruebas de fatiga térmica en actuadores mecánicos y sellos poliméricos\.",
     r"Strong thermal cycling stress (\1°C swing), ideal for thermal fatigue testing of mechanical actuators and polymer seals."),
    (r"Elevada altitud \(([^ ]+) m\) con radiación solar intensa \(([^ ]+) kWh/m²/día\), optimizando la exposición UV/solar y minimizando la columna barométrica terrestre\.",
     r"High altitude (\1 m) with intense solar irradiance (\2 kWh/m²/day), maximizing UV/solar exposure while reducing atmospheric column density."),
    (r"Su mayor afinidad radica en la dimensión '([^']+)' \(([0-9.]+)% de similitud\)\.",
     r"Its strongest match lies in the '\1' dimension (\2% similarity)."),
    (r"Temperatura media anual \(([^°]+)°C\) considerablemente más cálida que los ([^°]+)°C reales del objetivo espacial\.",
     r"Annual mean temperature (\1°C) is significantly warmer than the \2°C actual planetary target."),
    (r"Niveles de humedad atmosférica y edáfica terrestre superiores a los valores anhidros espaciales\.",
     "Terrestrial atmospheric and soil moisture levels exceed anhydrous space conditions."),
    (r"Gravedad terrestre \(1\.00 G\) vs ([0-9.]+) G en (.*?): Los rovers y perforadores no experimentan la baja tracción ni la flotabilidad de regolito de baja gravedad\.",
     r"Earth gravity (1.00 G) vs. \1 G on \2: Rovers and drills do not experience reduced-gravity traction loss or regolith lofting."),
    (r"Presión y atmósfera terrestre \(~101 kPa, N2/O2\) vs ([^ ]+) kPa en (.*?): La disipación convectiva de calor y el rozamiento aerodinámico distorsionan el comportamiento térmico en vacío o CO2 tenue\.",
     r"Earth atmosphere (~101 kPa, N2/O2) vs. \1 kPa on \2: Convective heat dissipation and aerodynamic drag distort vacuum or thin-CO2 thermal behavior."),
    (r"Blindaje magnetosférico terrestre: El campo geomagnético y la capa de ozono protegen al sitio terrestre de rayos cósmicos galácticos \(GCR\) y radiación solar ionizante no atenuada\.",
     "Terrestrial magnetospheric shielding: Earth's magnetic field and ozone layer block galactic cosmic rays (GCR) and unattenuated ionizing solar radiation."),
    (r"Este análogo sobresale principalmente por su <strong>(.*?)</strong> \(([0-9.]+)% de afinidad\), donde una aridez de ([^ ]+) y una altitud de ([^ ]+) m proporcionan un banco de pruebas representativo para (.*?)\.",
     r"This analog excels primarily in <strong>\1</strong> (\2% affinity), where an aridity of \3 and \4 m elevation provide a representative testbed for \5."),
    (r"No alcanza una puntuación superior porque sus temperaturas \(media de ([^°]+)°C y mínima de ([^°]+)°C\) son mucho más cálidas que los ([^°]+)°C reales de (.*?)\.",
     r"It does not score higher because its temperatures (mean \1°C, min \2°C) remain much warmer than the \3°C actual conditions at \4."),
    (r"Su principal limitación es la presencia de trazas de humedad en aire y suelo, superando la aridez absoluta del vacío espacial\.",
     "Its main limitation is trace air and soil moisture exceeding the absolute dryness of space."),
    (r"El relieve presenta diferencias geométricas: su pendiente de ([^°]+)° no replica con exactitud la topografía objetivo de (.*?)\.",
     r"Terrain geometry differs: its \1° slope does not exactly match the target topography of \2."),
    (r"La mayor divergencia se encuentra en '([^']+)' \(([0-9.]+)%\), marcando el límite con el ambiente espacial\.",
     r"The largest gap occurs in '\1' (\2%), marking the boundary with the space environment."),
    (r"Adicionalmente, ningún sitio terrestre puede eliminar la gravedad de 1\.00 G \(frente a ([0-9.]+) G en (.*?)\) ni el escudo magnético protector terrestre\.",
     r"Additionally, no Earth location can remove 1.00 G gravity (vs. \1 G on \2) or Earth's protective magnetic shield."),

    # Sub-etiquetas dentro de explain_score_in_plain_spanish
    (r"régimen térmico criogénico", "cryogenic thermal regime"),
    (r"gran amplitud térmica día/noche", "large day/night thermal amplitude"),
    (r"hiper-aridez y regolito desecado", "hyper-aridity and desiccated regolith"),
    (r"perfil topográfico de pendiente y rugosidad", "slope and roughness topography"),
    (r"dinámica de vientos y polvo", "wind and dust dynamics"),
    (r"baja presión atmosférica e intensa radiación solar", "low atmospheric pressure and intense solar radiation"),
]


def translate_text(val: Any) -> Any:
    """Traduce strings del español al inglés cuando _CURRENT_LANG == 'en'."""
    if _CURRENT_LANG != "en" or not isinstance(val, str) or not val:
        return val
    if val in EXACT_ES_TO_EN:
        return EXACT_ES_TO_EN[val]
    out = val
    for es, en in COUNTRY_AND_TERMS:
        if es in out:
            out = out.replace(es, en)
    for pattern, repl in REGEX_RULES:
        out = re.sub(pattern, repl, out)
    # También aplicar reemplazos exactos de frases clave dentro de strings más largos
    for es, en in EXACT_ES_TO_EN.items():
        if len(es) > 8 and es in out:
            out = out.replace(es, en)
    return out


def _translate_plotly_fig(fig: Any) -> Any:
    """Traduce títulos, ejes, leyendas y anotaciones de gráficos Plotly sin mutar datos."""
    if _CURRENT_LANG != "en":
        return fig
    try:
        fig_copy = copy.deepcopy(fig)
        layout = fig_copy.layout
        if layout.title and layout.title.text:
            layout.title.text = translate_text(layout.title.text)
        for ax_name in ["xaxis", "yaxis", "yaxis2"]:
            ax = getattr(layout, ax_name, None)
            if ax and ax.title and ax.title.text:
                ax.title.text = translate_text(ax.title.text)
        if layout.scene:
            for ax_name in ["xaxis", "yaxis", "zaxis"]:
                ax = getattr(layout.scene, ax_name, None)
                if ax and ax.title and ax.title.text:
                    ax.title.text = translate_text(ax.title.text)
        if layout.coloraxis and layout.coloraxis.colorbar and layout.coloraxis.colorbar.title:
            if layout.coloraxis.colorbar.title.text:
                layout.coloraxis.colorbar.title.text = translate_text(layout.coloraxis.colorbar.title.text)
        if layout.annotations:
            for ann in layout.annotations:
                if ann.text:
                    ann.text = translate_text(ann.text)
        for tr_obj in fig_copy.data:
            if getattr(tr_obj, "name", None):
                tr_obj.name = translate_text(tr_obj.name)
            if getattr(tr_obj, "colorbar", None) and getattr(tr_obj.colorbar, "title", None):
                if tr_obj.colorbar.title.text:
                    tr_obj.colorbar.title.text = translate_text(tr_obj.colorbar.title.text)
            for axis_attr in ("x", "y"):
                seq = getattr(tr_obj, axis_attr, None)
                if isinstance(seq, (list, tuple)) and seq and isinstance(seq[0], str):
                    setattr(tr_obj, axis_attr, [translate_text(x) for x in seq])
        return fig_copy
    except Exception:
        return fig

def _translate_col_config(cc: dict) -> dict:
    out = {}
    for k, v in cc.items():
        if isinstance(v, dict) and isinstance(v.get("label"), str):
            v = dict(v)
            v["label"] = translate_text(v["label"])
        out[translate_text(k)] = v
    return out

def _translate_df(data: Any) -> Any:
    """Traduce encabezados y columnas categóricas de DataFrames antes de renderizar."""
    if _CURRENT_LANG != "en" or not isinstance(data, pd.DataFrame):
        return data
    df_c = data.copy()
    df_c.columns = [translate_text(str(c)) for c in df_c.columns]
    for col in df_c.columns:
        if df_c[col].dtype == object or pd.api.types.is_string_dtype(df_c[col]):
            df_c[col] = df_c[col].apply(lambda x: translate_text(x) if isinstance(x, str) else x)
    return df_c


def _wrap_func(orig_fn, arg_positions=(0,), kw_names=("label", "help", "placeholder", "caption", "annotation_text")):
    def wrapper(*args, **kwargs):
        if _CURRENT_LANG == "en":
            new_args = list(args)
            for idx in arg_positions:
                if idx < len(new_args):
                    if isinstance(new_args[idx], str):
                        new_args[idx] = translate_text(new_args[idx])
                    elif isinstance(new_args[idx], list) and new_args[idx] and isinstance(new_args[idx][0], str):
                        new_args[idx] = [translate_text(x) for x in new_args[idx]]
            new_kwargs = dict(kwargs)
            for kw in kw_names:
                if kw in new_kwargs and isinstance(new_kwargs[kw], str):
                    new_kwargs[kw] = translate_text(new_kwargs[kw])
            if "format_func" not in new_kwargs and any(isinstance(a, (list, tuple)) and "Personalizado" in a for a in list(new_args) + [new_kwargs.get("options")]):
                new_kwargs["format_func"] = translate_text
            if "format_func" in new_kwargs and callable(new_kwargs["format_func"]):
                orig_ff = new_kwargs["format_func"]
                new_kwargs["format_func"] = lambda item, _f=orig_ff: translate_text(_f(item))
            if "column_config" in new_kwargs and isinstance(new_kwargs["column_config"], dict):
                new_kwargs["column_config"] = {translate_text(k): v for k, v in new_kwargs["column_config"].items()}
            args = tuple(new_args)
            kwargs = new_kwargs
        return orig_fn(*args, **kwargs)
    return wrapper


def _wrap_method(orig_fn, arg_positions=(1,), kw_names=("label", "help", "placeholder", "caption")):
    def wrapper(self, *args, **kwargs):
        if _CURRENT_LANG == "en":
            new_args = list(args)
            for idx in arg_positions:
                raw_idx = idx - 1  # args no incluye self
                if raw_idx < len(new_args):
                    if isinstance(new_args[raw_idx], str):
                        new_args[raw_idx] = translate_text(new_args[raw_idx])
                    elif isinstance(new_args[raw_idx], list) and new_args[raw_idx] and isinstance(new_args[raw_idx][0], str):
                        new_args[raw_idx] = [translate_text(x) for x in new_args[raw_idx]]
            new_kwargs = dict(kwargs)
            for kw in kw_names:
                if kw in new_kwargs and isinstance(new_kwargs[kw], str):
                    new_kwargs[kw] = translate_text(new_kwargs[kw])
            if "format_func" not in new_kwargs and any(isinstance(a, (list, tuple)) and "Personalizado" in a for a in list(new_args) + [new_kwargs.get("options")]):
                new_kwargs["format_func"] = translate_text
            if "format_func" in new_kwargs and callable(new_kwargs["format_func"]):
                orig_ff = new_kwargs["format_func"]
                new_kwargs["format_func"] = lambda item, _f=orig_ff: translate_text(_f(item))
            if "column_config" in new_kwargs and isinstance(new_kwargs["column_config"], dict):
                new_kwargs["column_config"] = {translate_text(k): v for k, v in new_kwargs["column_config"].items()}
            args = tuple(new_args)
            kwargs = new_kwargs
        return orig_fn(self, *args, **kwargs)
    return wrapper


def setup_i18n(lang: str = "en") -> None:
    """Activa el idioma elegido ('en' o 'es') e instala los wrappers seguros una única vez."""
    global _CURRENT_LANG, _PATCHED
    _CURRENT_LANG = lang if lang in ("en", "es") else "en"

    if _PATCHED:
        return

    # 1. Métodos de DeltaGenerator (cubre st.sidebar.*, columnas, containers)
    dg_text_methods = [
        ("markdown", (1,)), ("subheader", (1,)), ("caption", (1,)), ("title", (1,)),
        ("header", (1,)), ("text", (1,)), ("info", (1,)), ("success", (1,)),
        ("warning", (1,)), ("error", (1,)), ("html", (1,)), ("tabs", (1,)),
        ("expander", (1,)), ("button", (1,)), ("form_submit_button", (1,)),
        ("link_button", (1,)), ("download_button", (1,)), ("toggle", (1,)),
        ("selectbox", (1,)), ("multiselect", (1,)), ("radio", (1,)),
        ("slider", (1,)), ("text_input", (1,)), ("number_input", (1,)),
        ("metric", (1, 2, 3)),
    ]
    for name, pos in dg_text_methods:
        if hasattr(DeltaGenerator, name):
            orig = getattr(DeltaGenerator, name)
            _ORIG_DG[name] = orig
            setattr(DeltaGenerator, name, _wrap_method(orig, arg_positions=pos))

    # Plotly y Dataframes en DeltaGenerator
    if hasattr(DeltaGenerator, "plotly_chart"):
        orig_pc = DeltaGenerator.plotly_chart
        _ORIG_DG["plotly_chart"] = orig_pc
        def _dg_plotly(self, figure_or_data, *a, **kw):
            return orig_pc(self, _translate_plotly_fig(figure_or_data), *a, **kw)
        DeltaGenerator.plotly_chart = _dg_plotly

    for tbl_name in ("dataframe", "table"):
        if hasattr(DeltaGenerator, tbl_name):
            orig_tb = getattr(DeltaGenerator, tbl_name)
            _ORIG_DG[tbl_name] = orig_tb
            def _dg_tbl(self, data=None, *a, _o=orig_tb, **kw):
                if "column_config" in kw and isinstance(kw["column_config"], dict) and _CURRENT_LANG == "en":
                    kw = dict(kw)
                    kw["column_config"] = _translate_col_config(kw["column_config"])
                return _o(self, _translate_df(data), *a, **kw)
            setattr(DeltaGenerator, tbl_name, _dg_tbl)

    # 2. Funciones de nivel superior st.* (métodos ya enlazados en st._main)
    for name, pos in [
        ("markdown", (0,)), ("subheader", (0,)), ("caption", (0,)), ("title", (0,)),
        ("header", (0,)), ("text", (0,)), ("info", (0,)), ("success", (0,)),
        ("warning", (0,)), ("error", (0,)), ("html", (0,)), ("tabs", (0,)),
        ("expander", (0,)), ("button", (0,)), ("form_submit_button", (0,)),
        ("link_button", (0,)), ("download_button", (0,)), ("toggle", (0,)),
        ("selectbox", (0,)), ("multiselect", (0,)), ("radio", (0,)),
        ("slider", (0,)), ("text_input", (0,)), ("number_input", (0,)),
        ("metric", (0, 1, 2)),
    ]:
        if hasattr(st, name):
            orig_st = getattr(st, name)
            _ORIG_ST[name] = orig_st
            setattr(st, name, _wrap_func(orig_st, arg_positions=pos))

    if hasattr(st, "plotly_chart"):
        orig_st_pc = st.plotly_chart
        _ORIG_ST["plotly_chart"] = orig_st_pc
        st.plotly_chart = lambda fig, *a, **kw: orig_st_pc(_translate_plotly_fig(fig), *a, **kw)

    for tbl_name in ("dataframe", "table"):
        if hasattr(st, tbl_name):
            orig_st_tb = getattr(st, tbl_name)
            _ORIG_ST[tbl_name] = orig_st_tb
            def _st_tbl(data=None, *a, _o=orig_st_tb, **kw):
                if "column_config" in kw and isinstance(kw["column_config"], dict) and _CURRENT_LANG == "en":
                    kw = dict(kw)
                    kw["column_config"] = _translate_col_config(kw["column_config"])
                return _o(_translate_df(data), *a, **kw)
            setattr(st, tbl_name, _st_tbl)

    # 3. Folium (popups, tooltips y nombres de capas)
    _ORIG_FOLIUM["Popup"] = folium.Popup
    def _popup_wrap(html=None, *a, **kw):
        return _ORIG_FOLIUM["Popup"](translate_text(html) if isinstance(html, str) else html, *a, **kw)
    folium.Popup = _popup_wrap

    _ORIG_FOLIUM["TileLayer"] = folium.TileLayer
    def _tile_wrap(*a, **kw):
        if _CURRENT_LANG == "en" and "name" in kw and isinstance(kw["name"], str):
            kw = dict(kw)
            kw["name"] = translate_text(kw["name"])
        return _ORIG_FOLIUM["TileLayer"](*a, **kw)
    folium.TileLayer = _tile_wrap

    for m_cls_name in ("CircleMarker", "Marker"):
        orig_cls = getattr(folium, m_cls_name)
        _ORIG_FOLIUM[m_cls_name] = orig_cls
        def _marker_wrap(*a, _c=orig_cls, **kw):
            if _CURRENT_LANG == "en" and "tooltip" in kw and isinstance(kw["tooltip"], str):
                kw = dict(kw)
                kw["tooltip"] = translate_text(kw["tooltip"])
            return _c(*a, **kw)
        setattr(folium, m_cls_name, _marker_wrap)

    _PATCHED = True
