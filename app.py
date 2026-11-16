"""
EARTH TO SPACE: NEW HORIZONS
============================
Explorando análogos entre la Tierra, la Luna y Marte con datos reales de la NASA.
Plataforma interactiva de telemetría y evaluación cuantitativa de análogos planetarios.
"""

import os
import json
import math
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
import requests

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import folium
from streamlit_folium import st_folium

from src.earth_fetcher import analyze_earth_point, search_location, fetch_terrain_grid_7x7
from src.planetary_profiles import PLANETARY_TARGETS, get_planetary_target, list_planetary_targets
from src.similarity import (
    MISSION_PRESETS,
    VARIABLE_GLOSSARY,
    compute_similarity,
    generate_site_diagnosis,
    explain_score_in_plain_spanish,
    calculate_astrobiology_stress_index
)

from src.simulator import (
    simulate_rover_mobility,
    simulate_solar_budget,
    find_optimal_experiment_window,
    build_seasonality_from_site_row,
    MONTHS,
    MONTH_LABELS_ES
)

from src.environmental_tab import render_environmental_tab

# -----------------------------------------------------------------------------
# Configuración general de la página Streamlit
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="EARTH TO SPACE: NEW HORIZONS | NASA Analog Explorer",
    page_icon="🪐",
    layout="wide",
    initial_sidebar_state="expanded"
)

from src.i18n import setup_i18n
app_lang = st.sidebar.radio(
    "🌐 Language / Idioma",
    options=["en", "es"],
    format_func=lambda x: "🇬🇧 English" if x == "en" else "🇪🇸 Español",
    horizontal=True,
    index=0,
    key="app_language_selector"
)
setup_i18n(app_lang)

# Rutas de datos
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
CSV_PATH = os.path.join(DATA_DIR, "earth_analogs.csv")
JSON_PATH = os.path.join(DATA_DIR, "earth_seasonality.json")

# Traducción estandarizada de tipos geológicos
GEOLOGY_TRANSLATIONS = {
    "volcanic_basalt": "Basalto Volcánico",
    "evaporite_salar": "Salar / Evaporita",
    "impact_crater": "Cráter de Impacto",
    "permafrost": "Permafrost / Hielo",
    "hyperarid_regolith": "Regolito Hiperárido"
}

# Nombres cortos limpios para los objetivos espaciales
TARGET_SHORT_NAMES = {
    "lunar_south_pole": "Polo Sur Lunar",
    "mars_arcadia": "Marte · Arcadia Planitia",
    "mars_jezero": "Marte · Cráter Jezero"
}

# -----------------------------------------------------------------------------
# Estilos CSS - Dashboard Espacial Moderno en Azul Francia y Azul Noche
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #F1F5F9;
    }
    
    h1, h2, h3, h4, .hero-title, .sidebar-brand {
        font-family: 'Space Grotesk', sans-serif !important;
        letter-spacing: -0.02em;
    }

    /* Hero Banner Espacial con degradado Azul Francia */
    .hero-banner {
        background: linear-gradient(135deg, #060D21 0%, #0F2557 52%, #081229 100%);
        border: 1px solid rgba(56, 189, 248, 0.35);
        border-radius: 18px;
        padding: 24px 30px;
        box-shadow: 0 10px 32px rgba(15, 37, 87, 0.40);
        margin-bottom: 22px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        overflow: hidden;
        position: relative;
    }
    
    .hero-insignia {
        display: inline-block;
        background: rgba(37, 99, 235, 0.25);
        color: #38BDF8;
        border: 1px solid rgba(56, 189, 248, 0.5);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.76rem;
        font-weight: 700;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-bottom: 8px;
    }
    
    .hero-title {
        font-size: 1.85rem;
        font-weight: 700;
        background: linear-gradient(135deg, #FFFFFF 0%, #E0F2FE 60%, #93C5FD 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 4px 0 6px 0;
        line-height: 1.25;
    }
    
    .hero-desc {
        font-size: 0.95rem;
        color: #94A3B8;
        max-width: 620px;
        margin: 0;
        line-height: 1.5;
    }
    
    .hero-focus-box {
        background: rgba(12, 25, 56, 0.85);
        border: 1px solid rgba(59, 130, 246, 0.35);
        border-radius: 10px;
        padding: 6px 14px;
        font-size: 0.78rem;
        color: #CBD5E1;
        text-align: center;
        margin-top: 8px;
    }

    /* Pestañas tipo píldoras modernas */
    .stTabs [data-baseweb="tab-list"] {
        background: #0C1938 !important;
        border: 1px solid rgba(37, 99, 235, 0.28) !important;
        border-radius: 12px !important;
        padding: 6px !important;
        gap: 8px !important;
        margin-bottom: 16px !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px !important;
        padding: 8px 18px !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.92rem !important;
        color: #94A3B8 !important;
        border: none !important;
        transition: all 0.2s ease !important;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        color: #F8FAFC !important;
        background: rgba(37, 99, 235, 0.15) !important;
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #1D4ED8 0%, #2563EB 100%) !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 16px rgba(29, 78, 216, 0.45) !important;
    }

    /* Tarjetas flotantes glassmorphism */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(10, 22, 50, 0.74) !important;
        border: 1px solid rgba(59, 130, 246, 0.32) !important;
        box-shadow: 0 4px 20px rgba(29, 78, 216, 0.16) !important;
        border-radius: 16px !important;
    }

    /* Tarjeta Top 3 compacta */
    .top3-card {
        background: rgba(15, 28, 54, 0.85);
        border: 1px solid rgba(37, 99, 235, 0.3);
        border-radius: 10px;
        padding: 12px 14px;
        margin-bottom: 10px;
        transition: all 0.2s ease;
    }
    .top3-card:hover {
        border-color: #38BDF8;
        transform: translateY(-2px);
    }

    /* Píldoras de variables clave en Azul Francia */
    .variable-pill {
        display: inline-flex;
        align-items: center;
        background: rgba(30, 58, 138, 0.4);
        border: 1px solid rgba(56, 189, 248, 0.35);
        border-radius: 20px;
        padding: 6px 14px;
        font-size: 0.83rem;
        color: #E2E8F0;
        font-family: 'Space Grotesk', sans-serif;
    }

    /* Badges refinados */
    .badge-blue {
        display: inline-block;
        background: rgba(37, 99, 235, 0.20);
        color: #60A5FA;
        border: 1px solid rgba(96, 165, 250, 0.45);
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.74rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    .badge-amber {
        display: inline-block;
        background: rgba(245, 158, 11, 0.18);
        color: #FBBF24;
        border: 1px solid rgba(251, 191, 36, 0.45);
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.74rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    
    /* Caja de explicación científica */
    .explanation-box {
        background: rgba(15, 28, 54, 0.85);
        border-left: 4px solid #2563EB;
        border-radius: 8px;
        padding: 16px 20px;
        font-size: 0.95rem;
        line-height: 1.65;
        color: #E2E8F0;
        margin-bottom: 14px;
    }

    /* Botones primarios en degradado Azul Francia */
    .stButton > button {
        background: linear-gradient(135deg, #1E40AF 0%, #2563EB 100%) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(56, 189, 248, 0.4) !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #2563EB 0%, #38BDF8 100%) !important;
        box-shadow: 0 4px 16px rgba(37, 99, 235, 0.4) !important;
    }
[data-testid="InputInstructions"] { display: none !important; }
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Funciones cacheadas para alto rendimiento
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_analogs_data() -> pd.DataFrame:
    """Carga el catálogo de sitios análogos terrestres."""
    if os.path.exists(CSV_PATH):
        return pd.read_csv(CSV_PATH)
    return pd.DataFrame()

@st.cache_data(show_spinner=False)
def load_seasonality_data() -> Dict[str, Any]:
    """Carga los registros mensuales de estacionalidad."""
    if os.path.exists(JSON_PATH):
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

@st.cache_data(show_spinner="Consultando NASA POWER y Open-Meteo...")
def cached_analyze_point(lat: float, lon: float, name: str) -> Dict[str, Any]:
    """Consulta y cachea el análisis de un punto geográfico en tiempo real."""
    return analyze_earth_point(lat, lon, name)

@st.cache_data(show_spinner="Generando cuadrícula altimétrica 3D...")
def cached_terrain_grid(lat: float, lon: float) -> Dict[str, Any]:
    """Consulta y cachea la matriz de elevaciones 7x7."""
    return fetch_terrain_grid_7x7(lat, lon)


# Inicialización de estado de sesión
if "custom_sites" not in st.session_state:
    st.session_state["custom_sites"] = []
if "selected_site_name" not in st.session_state:
    st.session_state["selected_site_name"] = "Campos de Lava Harrat Khaybar"
if "last_map_click" not in st.session_state:
    st.session_state["last_map_click"] = None
if "experiment_log" not in st.session_state:
    st.session_state["experiment_log"] = []

# Carga de datos base
df_base = load_analogs_data()
seasonality_base = load_seasonality_data()


# -----------------------------------------------------------------------------
# Barra Lateral: Consola de Misión
# -----------------------------------------------------------------------------
st.sidebar.markdown(
    '<div class="sidebar-brand" style="font-size: 1.35rem; font-weight: 700; color: #38BDF8;">'
    'EARTH TO SPACE'
    '</div>'
    '<div style="font-size: 0.74rem; color: #94A3B8; letter-spacing: 1px; margin-bottom: 14px;">'
    'NEW HORIZONS // MISIÓN NASA'
    '</div>',
    unsafe_allow_html=True
)

# 1. Selector de Objetivo Planetario
st.sidebar.subheader("🎯 1. Objetivo Espacial")
target_options = {
    "lunar_south_pole": "Polo Sur Lunar (Cráter Shackleton / Artemis)",
    "mars_arcadia": "Marte - Arcadia Planitia (Hielo Somero / Base)",
    "mars_jezero": "Marte - Cráter Jezero (Perseverance / Delta)"
}

selected_target_key = st.sidebar.selectbox(
    "Selecciona el destino:",
    options=list(target_options.keys()),
    format_func=lambda k: target_options[k],
    index=2
)

target_profile = get_planetary_target(selected_target_key)
real_metrics = target_profile["real_planetary_metrics"]

with st.sidebar.expander("📡 Telemetría Real de Misión NASA", expanded=False):
    st.markdown(f"**Referencia:** `{target_profile['scientific_mission_reference']}`")
    st.markdown(f"**Gravedad:** `{real_metrics['surface_gravity_g']} G` ({real_metrics['surface_gravity_ms2']} m/s²)")
    st.markdown(f"**Presión:** `{real_metrics['atmospheric_pressure_kpa']} kPa`")
    st.markdown(f"**T° Superficie:** `{real_metrics['surface_temperature_range_c'][0]}°C a {real_metrics['surface_temperature_range_c'][1]}°C` (Media: `{real_metrics['mean_surface_temp_c']}°C`)")
    st.markdown(f"**Atmósfera:** {real_metrics['atmospheric_composition']}")

st.sidebar.markdown("---")

# 2. Filtro de Sitios Poco Estudiados
filter_hidden_gems_only = st.sidebar.toggle(
    "🔬 Mostrar solo Sitios Poco Estudiados",
    value=True,
    help="Excluye los sitios clásicos consagrados (como Atacama o Devon Island) para resaltar candidatos poco investigados."
)

# 3. Modo de Misión y Ponderadores
st.sidebar.subheader("⚙️ 2. Modo de Misión")
preset_names = {k: v["name"] for k, v in MISSION_PRESETS.items()}
selected_preset_key = st.sidebar.selectbox(
    "Configuración científica:",
    options=list(preset_names.keys()),
    format_func=lambda k: preset_names[k],
    index=0
)

active_preset = MISSION_PRESETS[selected_preset_key]
st.sidebar.caption(active_preset["description"])

with st.sidebar.expander("🎚️ Calibración Manual de Pesos (6D)", expanded=False):
    st.caption("Ajusta la importancia relativa de cada dimensión científica:")
    w_cold = st.slider("Frío Extremo", 0.0, 1.0, float(active_preset["weights"]["cold_extreme"]), 0.02)
    w_thermal = st.slider("Amplitud Térmica", 0.0, 1.0, float(active_preset["weights"]["thermal_amplitude"]), 0.02)
    w_aridity = st.slider("Aridez & Suelo", 0.0, 1.0, float(active_preset["weights"]["aridity_soil"]), 0.02)
    w_topo = st.slider("Relieve & Topografía", 0.0, 1.0, float(active_preset["weights"]["terrain_topography"]), 0.02)
    w_wind = st.slider("Viento & Dinámica Eólica", 0.0, 1.0, float(active_preset["weights"]["aeolian_wind"]), 0.02)
    w_alt = st.slider("Altitud & Radiación Solar", 0.0, 1.0, float(active_preset["weights"]["altitude_pressure_solar"]), 0.02)
    
custom_weights = {
    "cold_extreme": w_cold,
    "thermal_amplitude": w_thermal,
    "aridity_soil": w_aridity,
    "terrain_topography": w_topo,
    "aeolian_wind": w_wind,
    "altitude_pressure_solar": w_alt
}

st.sidebar.markdown("---")

# 4. Glosario Científico
with st.sidebar.expander("📖 Glosario: ¿Qué mide cada variable?", expanded=False):
    for key, item in VARIABLE_GLOSSARY.items():
        st.markdown(f"**{item['title']}** (`{item['unit']}`)")
        st.caption(item["definition"])
        st.markdown("---")


# -----------------------------------------------------------------------------
# Procesamiento de Similitud Global
# -----------------------------------------------------------------------------
all_sites_df = df_base.copy()
if st.session_state["custom_sites"]:
    custom_df = pd.DataFrame(st.session_state["custom_sites"])
    all_sites_df = pd.concat([all_sites_df, custom_df], ignore_index=True)

scored_df = compute_similarity(all_sites_df, target_key=selected_target_key, preset_or_weights=custom_weights)

if filter_hidden_gems_only:
    display_df = scored_df[scored_df["is_famous"] == False].copy()
else:
    display_df = scored_df.copy()

display_df["rank"] = range(1, len(display_df) + 1)


# -----------------------------------------------------------------------------
# HERO BANNER SUPERIOR (Diseño Espacial Azul Francia + SVG)
# -----------------------------------------------------------------------------
hero_banner_html = """<div class="hero-banner">
<div style="flex: 1; padding-right: 20px;">
<div class="hero-insignia">🪐 EARTH TO SPACE: NEW HORIZONS</div>
<div class="hero-title">¿Qué lugares de la Tierra se parecen a la Luna y Marte?</div>
<p class="hero-desc">Explorando análogos entre la Tierra, la Luna y Marte con datos reales de la NASA, modelos satelitales NASA POWER, topografía DEM de alta resolución y cartografía orbital.</p>
</div>
<div style="display: flex; flex-direction: column; align-items: center; justify-content: center;">
<svg width="220" height="75" viewBox="0 0 220 75" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M 35 40 Q 110 15 185 38" stroke="rgba(56, 189, 248, 0.35)" stroke-dasharray="3 3" stroke-width="1.5" />
<defs>
<radialGradient id="earthGrad" cx="35%" cy="35%" r="65%">
<stop offset="0%" stop-color="#38BDF8" />
<stop offset="60%" stop-color="#2563EB" />
<stop offset="100%" stop-color="#0B132B" />
</radialGradient>
<radialGradient id="moonGrad" cx="35%" cy="35%" r="65%">
<stop offset="0%" stop-color="#F1F5F9" />
<stop offset="65%" stop-color="#64748B" />
<stop offset="100%" stop-color="#1E293B" />
</radialGradient>
<radialGradient id="marsGrad" cx="35%" cy="35%" r="65%">
<stop offset="0%" stop-color="#FB923C" />
<stop offset="60%" stop-color="#C2410C" />
<stop offset="100%" stop-color="#431407" />
</radialGradient>
</defs>
<circle cx="35" cy="40" r="23" fill="url(#earthGrad)" />
<path d="M 25 35 Q 31 29 37 33 Q 43 39 40 48 Q 32 47 27 43 Z" fill="#10B981" opacity="0.45" />
<path d="M 36 46 Q 42 43 45 49 Q 42 55 36 53 Z" fill="#10B981" opacity="0.4" />
<circle cx="108" cy="27" r="12" fill="url(#moonGrad)" />
<circle cx="104" cy="24" r="2.2" fill="#334155" opacity="0.6" />
<circle cx="111" cy="29" r="1.6" fill="#334155" opacity="0.6" />
<circle cx="106" cy="31" r="1.3" fill="#334155" opacity="0.5" />
<circle cx="185" cy="38" r="19" fill="url(#marsGrad)" />
<ellipse cx="185" cy="22" rx="6.5" ry="2.2" fill="#FFFFFF" opacity="0.9" />
<path d="M 175 38 Q 183 34 193 40 Q 187 46 177 44 Z" fill="#7C2D12" opacity="0.5" />
</svg>
<div class="hero-focus-box">Nuestro enfoque: <strong>Tierra · Luna · Marte</strong></div>
</div>
</div>"""
st.html(hero_banner_html)


# -----------------------------------------------------------------------------
# 5 PESTAÑAS PRINCIPALES (PÍLDORAS MODERNAS EN AZUL FRANCIA)
# -----------------------------------------------------------------------------
tab_discovery, tab_deep_dive, tab_duel, tab_laboratory, tab_experiments, tab_env = st.tabs([
    "🌍 Explorador Global",
    "🔬 Análisis Detallado",
    "⚖️ Comparativa Directa",
    "📊 Laboratorio",
    "🧪 Experimentos",
    "🌿 Ambiental"
])


# =============================================================================
# PESTAÑA 1: Explorador Global
# =============================================================================
with tab_discovery:
    # Barra de Búsqueda y Coordenadas Manuales
    col_sb1, col_sb2 = st.columns([0.62, 0.38])
    with col_sb1:
        st.markdown("**🔍 Búsqueda de Localizaciones (OpenStreetMap Nominatim):**")
        with st.form("search_location_form", border=False):
            sf_col1, sf_col2 = st.columns([0.75, 0.25])
            search_query = sf_col1.text_input(
                "Ingresa un lugar del mundo:",
                placeholder="Ej. Desierto de Atacama, Volcán Askja, Salar de Uyuni...",
                label_visibility="collapsed"
            )
            submitted_search = sf_col2.form_submit_button("🔍 Buscar", use_container_width=True)
        if submitted_search and search_query:
            results = search_location(search_query, limit=4)
            if results:
                st.session_state["search_results"] = results
            else:
                st.warning("No se encontraron coordenadas para esa consulta.")
                    
        if "search_results" in st.session_state and st.session_state["search_results"]:
            chosen_res = st.selectbox(
                "Coincidencias encontradas:",
                options=st.session_state["search_results"],
                format_func=lambda x: f"{x['display_name'][:75]}... (lat: {x['lat']:.3f}, lon: {x['lon']:.3f})"
            )
            if st.button("🚀 Evaluar este lugar en vivo", key="btn_analyze_search"):
                with st.spinner("Consultando datos de satélite y clima..."):
                    raw_parts = [p.strip() for p in chosen_res["display_name"].split(",")]
                    # Evitar nombres truncados de una sola palabra
                    if len(raw_parts) > 1 and len(raw_parts[0]) < 12:
                        site_label = f"{raw_parts[0]} ({raw_parts[1]})"
                    else:
                        site_label = raw_parts[0]
                        
                    analyzed = cached_analyze_point(chosen_res["lat"], chosen_res["lon"], name=site_label)
                    analyzed["country"] = raw_parts[-1]
                    analyzed["geology_type"] = "hyperarid_regolith"
                    analyzed["is_famous"] = False
                    analyzed["geology_notes"] = "Sitio explorado en vivo vía consulta Nominatim y telemetría de satélite NASA."
                    st.session_state["custom_sites"].append(analyzed)
                    st.session_state["selected_site_name"] = analyzed["name"]
                    st.session_state["exp_site_selector"] = st.session_state["selected_site_name"]
                    st.success(f"¡Sitio '{analyzed['name']}' evaluado e incorporado a la tabla!")
                    st.rerun()

    with col_sb2:
        st.markdown("**📍 Consulta por Coordenadas Manuales:**")
        c_lat, c_lon = st.columns(2)
        in_lat = c_lat.number_input("Latitud:", value=-24.500, min_value=-90.0, max_value=90.0, step=0.1, format="%.4f")
        in_lon = c_lon.number_input("Longitud:", value=-69.250, min_value=-180.0, max_value=180.0, step=0.1, format="%.4f")
        in_name = st.text_input("Nombre de referencia:", value="Coordenada Personalizada")
        if st.button("📡 Analizar Coordenadas", key="btn_analyze_manual"):
            with st.spinner("Analizando terreno y climatología satelital..."):
                analyzed = cached_analyze_point(in_lat, in_lon, name=in_name)
                analyzed["country"] = "Personalizado"
                analyzed["geology_type"] = "hyperarid_regolith"
                analyzed["is_famous"] = False
                analyzed["geology_notes"] = f"Coordenada evaluada en vivo ({in_lat:.3f}, {in_lon:.3f})."
                st.session_state["custom_sites"].append(analyzed)
                st.session_state["selected_site_name"] = in_name
                st.session_state["exp_site_selector"] = st.session_state["selected_site_name"]
                st.success(f"¡Punto '{in_name}' analizado con éxito!")
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # SECCIÓN SUPERIOR: Proporción [1.65, 1] -> Mapa a la izquierda, Top 3 compacto a la derecha
    col_map, col_top3 = st.columns([1.65, 1.0])
    
    with col_map:
        st.markdown("**🗺️ Mapa Global de Análogos (Haz clic para evaluar cualquier punto):**")
        
        # Mapa con NASA GIBS Blue Marble como capa activa POR DEFECTO
        m_earth = folium.Map(
            location=[20.0, 0.0],
            zoom_start=2,
            tiles=None,
            control_scale=True
        )

        # Capa 1 (secundaria): Satélite Óptico Esri — desactivada al inicio
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="Esri World Imagery",
            name="🛰️ Satélite Esri",
            overlay=False,
            control=True,
            show=False
        ).add_to(m_earth)

        # Capa 2 (secundaria): OpenStreetMap — desactivada al inicio
        folium.TileLayer(
            tiles="OpenStreetMap",
            name="🗺️ OpenStreetMap",
            overlay=False,
            control=True,
            show=False
        ).add_to(m_earth)

        # Capa 3 (POR DEFECTO activa): NASA GIBS Blue Marble — se agrega al último para ser la activa
        folium.TileLayer(
            tiles="https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/BlueMarble_NextGeneration/default/GoogleMapsCompatible_Level8/{z}/{y}/{x}.jpeg",
            attr="NASA Global Imagery Browse Services (GIBS)",
            name="🌍 NASA Blue Marble",
            overlay=False,
            control=True,
            show=True
        ).add_to(m_earth)

        folium.LayerControl(position="topright", collapsed=True).add_to(m_earth)
        
        custom_names = {s["name"] for s in st.session_state["custom_sites"]}

        # Marcadores de sitios evaluados
        for _, row in display_df.iterrows():
            sim_score = row["overall_similarity"]
            is_custom = row["name"] in custom_names
            is_gem = not row["is_famous"]
            color = "#10B981" if is_custom else ("#38BDF8" if is_gem else "#F59E0B")
            radius = 9 if is_custom else (6 if is_gem else 7)
            geo_es = GEOLOGY_TRANSLATIONS.get(row["geology_type"], row["geology_type"])
            
            popup_html = f"""
            <div style="font-family: sans-serif; color: #0F172A; min-width: 175px;">
                <h4 style="margin: 0 0 6px 0; color: #1E40AF;">{row['name']}</h4>
                <b>País:</b> {row['country']}<br>
                <b>Similitud:</b> {sim_score:.1f}%<br>
                <b>Geología:</b> {geo_es}<br>
                <b>Elevación:</b> {row.get('elevation_m', 'N/D')} m<br>
                <b>Aridez:</b> {row.get('aridity_index', 'N/D')}
            </div>
            """
            
            folium.CircleMarker(
                location=[row["latitude"], row["longitude"]],
                radius=radius,
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=f"{'⭐ [NUEVO] ' if is_custom else ''}{row['name']} ({sim_score:.1f}%)",
                color="#FFFFFF" if is_custom else color,
                fill=True,
                fill_color=color,
                fill_opacity=0.95 if is_custom else 0.88,
                weight=2.5 if is_custom else 1.5
            ).add_to(m_earth)

            if is_custom:
                folium.Marker(
                    location=[row["latitude"], row["longitude"]],
                    popup=folium.Popup(popup_html, max_width=250),
                    tooltip=f"⭐ Sitio Evaluado en Vivo: {row['name']}",
                    icon=folium.Icon(color="green", icon="star", prefix="fa")
                ).add_to(m_earth)
            
        map_key = f"folium_global_map_{len(display_df)}_{len(custom_names)}_{selected_target_key}"
        map_output = st_folium(m_earth, width="100%", height=480, key=map_key)
        
        if map_output and map_output.get("last_clicked"):
            clicked = map_output["last_clicked"]
            c_lat = clicked["lat"]
            c_lon = clicked["lng"]
            
            if st.session_state["last_map_click"] != (c_lat, c_lon):
                st.session_state["last_map_click"] = (c_lat, c_lon)
                st.info(f"📍 Punto seleccionado en el mapa: Lat `{c_lat:.4f}`, Lon `{c_lon:.4f}`")
                if st.button("🔬 Evaluar este punto clicado", key="btn_analyze_click"):
                    with st.spinner("Consultando variables climáticas y topográficas..."):
                        analyzed = cached_analyze_point(c_lat, c_lon, name=f"Punto ({c_lat:.2f}, {c_lon:.2f})")
                        analyzed["country"] = "Coordenada Clicada"
                        analyzed["geology_type"] = "hyperarid_regolith"
                        analyzed["is_famous"] = False
                        analyzed["geology_notes"] = f"Punto terrestre evaluado vía clic directo en ({c_lat:.3f}, {c_lon:.3f})."
                        st.session_state["custom_sites"].append(analyzed)
                        st.session_state["selected_site_name"] = analyzed["name"]
                        st.session_state["exp_site_selector"] = st.session_state["selected_site_name"]       
                        st.success(f"¡Punto ({c_lat:.2f}, {c_lon:.2f}) incorporado al ranking!")
                        st.rerun()

    with col_top3:
        with st.container(border=True):
            st.markdown("##### 🏆 Top 3 Candidatos Destacados")
            st.caption(f"Mayor afinidad cuantitativa con **{TARGET_SHORT_NAMES.get(selected_target_key, target_profile['name'].split('(')[0].strip())}**:")
            
            top3_df = display_df.head(3)
            for i, (_, r) in enumerate(top3_df.iterrows(), start=1):
                medal = "🥇" if i == 1 else ("🥈" if i == 2 else "🥉")
                geo_es = GEOLOGY_TRANSLATIONS.get(r["geology_type"], r["geology_type"])
                
                st.markdown(f"""
                <div class="top3-card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                        <span style="font-size: 1.05rem; font-weight: 700; color: #F8FAFC;">{medal} #{i} {r['name']}</span>
                        <span class="badge-blue" style="font-size: 0.85rem; font-weight: 700;">{r['overall_similarity']:.1f}%</span>
                    </div>
                    <div style="font-size: 0.82rem; color: #94A3B8; margin-bottom: 6px;">
                        📍 <strong>{r['country']}</strong> &nbsp;·&nbsp; ⛰️ <strong>{geo_es}</strong>
                    </div>
                    <div style="display: flex; gap: 10px; font-size: 0.78rem; color: #CBD5E1;">
                        <span>Alt: <strong>{r.get('elevation_m', 'N/D')}m</strong></span>
                        <span>·</span>
                        <span>Aridez: <strong>{r.get('aridity_index', 'N/D')}</strong></span>
                        <span>·</span>
                        <span>T° Mín: <strong>{r.get('t2m_min_ann', 'N/D')}°C</strong></span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"Inspeccionar #{i} {r['name'][:20]}...", key=f"btn_inspect_top3_{i}", use_container_width=True):
                    st.session_state["selected_site_name"] = r["name"]
                    st.session_state["exp_site_selector"] = st.session_state["selected_site_name"]       
                    st.success(f"Sitio '{r['name']}' seleccionado para Análisis Detallado.")
                    st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # SECCIÓN INFERIOR: Tabla completa al 100% de ancho (use_container_width=True)
    st.markdown("#### 🏆 Clasificación de Similitud Global")
    st.caption("Catálogo completo clasificado cuantitativamente según el modo de misión activo:")
    
    top_n = st.slider("Cantidad de sitios a listar en la tabla:", min_value=5, max_value=len(display_df), value=min(15, len(display_df)))
    top_df = display_df.head(top_n)
    
    table_view = top_df[["rank", "name", "country", "geology_type", "overall_similarity"]].copy()
    table_view["Geología"] = table_view["geology_type"].map(lambda g: GEOLOGY_TRANSLATIONS.get(g, g))
    table_view = table_view[["rank", "name", "country", "Geología", "overall_similarity"]]
    table_view.columns = ["#", "Sitio", "País", "Geología", "Similitud (%)"]
    
    st.dataframe(
        table_view,
        use_container_width=True,
        hide_index=True,
        column_config={
            "#": st.column_config.NumberColumn("#", width=60),
            "Sitio": st.column_config.TextColumn("Sitio", width=260),
            "País": st.column_config.TextColumn("País", width=160),
            "Geología": st.column_config.TextColumn("Geología", width=200),
            "Similitud (%)": st.column_config.ProgressColumn(
                "Similitud",
                format="%.1f%%",
                min_value=0,
                max_value=100
            )
        }
    )


# =============================================================================
# PESTAÑA 2: Análisis Detallado (Tierra vs. Espacio)
# =============================================================================
with tab_deep_dive:
    available_sites = scored_df["name"].tolist()
    default_idx = available_sites.index(st.session_state["selected_site_name"]) if st.session_state["selected_site_name"] in available_sites else 0
    current_site_name = st.selectbox("Selecciona el sitio a evaluar:", options=available_sites, index=default_idx)
    st.session_state["selected_site_name"] = current_site_name
    
    site_row = scored_df[scored_df["name"] == current_site_name].iloc[0].to_dict()
    dim_scores = {
        "cold_extreme": site_row["sim_cold_extreme"],
        "thermal_amplitude": site_row["sim_thermal_amplitude"],
        "aridity_soil": site_row["sim_aridity_soil"],
        "terrain_topography": site_row["sim_terrain_topography"],
        "aeolian_wind": site_row["sim_aeolian_wind"],
        "altitude_pressure_solar": site_row["sim_altitude_pressure_solar"]
    }
    
    diagnosis = generate_site_diagnosis(site_row, selected_target_key, dim_scores)
    geo_translated = GEOLOGY_TRANSLATIONS.get(site_row.get("geology_type"), site_row.get("geology_type"))
    
    # Píldoras de Variables Clave en Azul Francia
    st.markdown(f"""
    <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; margin-bottom: 18px;">
        <div class="variable-pill">💧 Humedad Suelo (GWETTOP): <strong>{site_row.get('soil_wetness_ann', 'N/D')}</strong></div>
        <div class="variable-pill">🌡️ Amplitud Térmica: <strong>{site_row.get('thermal_amplitude_c', 'N/D')} °C</strong></div>
        <div class="variable-pill">📐 Pendiente (Horn): <strong>{site_row.get('slope_deg', 'N/D')}°</strong></div>
        <div class="variable-pill">☀️ Albedo: <strong>{site_row.get('surface_albedo_ann', 'N/D')}</strong></div>
        <div class="variable-pill">💨 Presión: <strong>{site_row.get('ps_ann', 'N/D')} kPa</strong></div>
        <div class="variable-pill">⛰️ Geología: <strong>{geo_translated}</strong></div>
    </div>
    """, unsafe_allow_html=True)
    
    # Tarjetas KPI Superiores envueltas en contenedor estilizado
    with st.container(border=True):
        k1, k2, k3, k4, k5, k6 = st.columns(6)
        k1.metric(
            "Similitud Global",
            f"{site_row['overall_similarity']:.1f}%",
            f"Ajuste: {site_row.get('geology_bonus', 0):+.0f} pts",
            help="Similitud cuantitativa ponderada a través de las 6 dimensiones científicas."
        )
        k2.metric(
            "T° Mínima Anual",
            f"{site_row.get('t2m_min_ann', 'N/D')} °C",
            f"Media: {site_row.get('ts_ann', 'N/D')}°C",
            help=VARIABLE_GLOSSARY["thermal_amplitude"]["definition"]
        )
        k3.metric(
            "Pendiente & Relieve",
            f"{site_row.get('slope_deg', 'N/D')}°",
            f"Rugosidad: {site_row.get('roughness_m', 'N/D')}m",
            help=f"{VARIABLE_GLOSSARY['slope_deg']['definition']}"
        )
        k4.metric(
            "Suelo (GWETTOP)",
            f"{site_row.get('soil_wetness_ann', 'N/D')}",
            f"Aridez: {site_row.get('aridity_index', 'N/D')}",
            help=VARIABLE_GLOSSARY["gwettop"]["definition"]
        )
        k5.metric(
            "Albedo de Suelo",
            f"{site_row.get('surface_albedo_ann', 'N/D')}",
            f"Meta: {target_profile.get('target_albedo', 'N/D')}",
            help=VARIABLE_GLOSSARY["albedo"]["definition"]
        )
        k6.metric(
            "Estrés Astrobiológico",
            f"{site_row.get('astrobiology_stress_index', 0):.0f} / 100",
            f"Alt: {site_row.get('elevation_m', 'N/D')}m",
            help=VARIABLE_GLOSSARY["astrobiology_stress"]["definition"]
        )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Bloque: Desglose Cuantitativo y Explicación en Lenguaje Humano
    with st.container(border=True):
        st.markdown("##### 🧮 Justificación Cuantitativa del Puntaje")
        col_b_chart, col_b_text = st.columns([0.48, 0.52])
        
        with col_b_chart:
            dim_labels_es = {
                "cold_extreme": "Frío Extremo",
                "thermal_amplitude": "Ciclo Térmico",
                "aridity_soil": "Suelo & Aridez",
                "terrain_topography": "Relieve / Pendiente",
                "aeolian_wind": "Viento & Polvo",
                "altitude_pressure_solar": "Altitud / Presión / Solar"
            }
            
            chart_df = pd.DataFrame([
                {"Dimensión": dim_labels_es[k], "Afinidad (%)": v}
                for k, v in dim_scores.items()
            ])
            
            fig_bar = px.bar(
                chart_df,
                x="Afinidad (%)",
                y="Dimensión",
                orientation="h",
                color="Afinidad (%)",
                color_continuous_scale=["#1E3A8A", "#2563EB", "#38BDF8"],
                range_x=[0, 100],
                text=chart_df["Afinidad (%)"].apply(lambda x: f"{x:.1f}%")
            )
            fig_bar.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(15, 28, 54, 0.4)",
                height=250,
                margin=dict(l=10, r=10, t=10, b=10),
                coloraxis_showscale=False
            )
            fig_bar.update_traces(textposition='inside', textfont=dict(color='white'))
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with col_b_text:
            explanation_plain = explain_score_in_plain_spanish(site_row, selected_target_key, dim_scores)
            st.markdown(f'<div class="explanation-box">{explanation_plain}</div>', unsafe_allow_html=True)
            st.markdown(f"**Afinidad Geológica:** `{geo_translated}` (Bonus aplicado: `{site_row.get('geology_bonus', 0):+.1f} pts`)")
            st.caption(f"Notas geológicas: {site_row.get('geology_notes', 'Sin notas adicionales.')}")

    st.markdown("<br>", unsafe_allow_html=True)

    # Radar 6D y Curva de Estacionalidad Climatológica
    col_rad, col_seas = st.columns([0.48, 0.52])
    
    with col_rad:
        with st.container(border=True):
            st.markdown("**📡 Perfil Multidimensional (Radar 6D vs. Ideal Espacial):**")
            categories = [dim_labels_es[k] for k in dim_scores.keys()]
            values = list(dim_scores.values())
            
            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=[100] * len(categories) + [100],
                theta=categories + [categories[0]],
                fill='toself',
                name=f'Ideal {target_profile["body"]}',
                line=dict(color='rgba(255, 255, 255, 0.25)', dash='dot'),
                fillcolor='rgba(255, 255, 255, 0.04)'
            ))
            fig_radar.add_trace(go.Scatterpolar(
                r=values + [values[0]],
                theta=categories + [categories[0]],
                fill='toself',
                name=site_row['name'],
                line=dict(color='#38BDF8', width=2.5),
                fillcolor='rgba(37, 99, 235, 0.35)'
            ))
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=9, color="#94A3B8")),
                    bgcolor="rgba(15, 28, 54, 0.4)"
                ),
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                height=340,
                margin=dict(l=35, r=35, t=20, b=20),
                legend=dict(orientation="h", y=-0.12)
            )
            st.plotly_chart(fig_radar, use_container_width=True)

    with col_seas:
        with st.container(border=True):
            st.markdown(f"**📅 Curva Estacional Anual (Enero – Diciembre):**")
            site_seasonality = seasonality_base.get(current_site_name, {})
            
            if site_seasonality and "TS" in site_seasonality:
                months = list(site_seasonality["TS"].keys())
                t_max_m = [site_seasonality.get("T2M_MAX", {}).get(m, np.nan) for m in months]
                t_min_m = [site_seasonality.get("T2M_MIN", {}).get(m, np.nan) for m in months]
                ts_m = [site_seasonality.get("TS", {}).get(m, np.nan) for m in months]
                ws_m = [site_seasonality.get("WS10M", {}).get(m, np.nan) for m in months]
                
                fig_clim = go.Figure()
                fig_clim.add_trace(go.Scatter(x=months, y=t_max_m, mode='lines+markers', name='T° Máx 2m (°C)', line=dict(color='#F87171', width=2)))
                fig_clim.add_trace(go.Scatter(x=months, y=ts_m, mode='lines', name='T° Piel Suelo (°C)', line=dict(color='#FBBF24', width=1.5, dash='dash')))
                fig_clim.add_trace(go.Scatter(x=months, y=t_min_m, mode='lines+markers', name='T° Mín 2m (°C)', line=dict(color='#60A5FA', width=2)))
                fig_clim.add_trace(go.Scatter(x=months, y=ws_m, mode='lines', name='Viento 10m (m/s)', line=dict(color='#34D399', width=1.5), yaxis='y2'))
                
                fig_clim.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(15, 28, 54, 0.4)",
                    height=340,
                    margin=dict(l=10, r=20, t=20, b=20),
                    legend=dict(orientation="h", y=-0.18),
                    yaxis=dict(title="Temperatura (°C)", gridcolor="rgba(255,255,255,0.06)"),
                    yaxis2=dict(title="Viento (m/s)", overlaying='y', side='right', gridcolor="rgba(0,0,0,0)")
                )
                st.plotly_chart(fig_clim, use_container_width=True)
            else:
                st.info("Datos estacionales en proceso de consulta para este punto.")

    st.markdown("<br>", unsafe_allow_html=True)

    # Modelo Topográfico 3D
    with st.container(border=True):
        st.markdown("##### 🏔️ Reconstrucción Topográfica 3D del Terreno (Open-Meteo DEM 7x7)")
        st.caption("Malla altimétrica real de 49 puntos (~2.8 km de radio) para inspeccionar obstáculos, pendientes y rugosidad:")
        
        t_grid = cached_terrain_grid(site_row["latitude"], site_row["longitude"])
        if t_grid.get("status") == "success" and t_grid.get("grid_7x7"):
            z_data = np.array(t_grid["grid_7x7"])
            x_km = t_grid["x_km"]
            y_km = t_grid["y_km"]
            
            fig_3d = go.Figure(data=[go.Surface(
                z=z_data,
                x=x_km,
                y=y_km,
                colorscale="Viridis",
                colorbar=dict(title="Elevación (m)", thickness=14, len=0.75),
                contours=dict(z=dict(show=True, usecolormap=True, highlightcolor="#38BDF8", project_z=True))
            )])
            
            fig_3d.update_layout(
                title=f"Relieve en {site_row['name']} (Min: {t_grid['elevation_min']} m | Max: {t_grid['elevation_max']} m)",
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                height=450,
                margin=dict(l=10, r=10, t=40, b=10),
                scene=dict(
                    xaxis_title="Oeste - Este (km)",
                    yaxis_title="Sur - Norte (km)",
                    zaxis_title="Altitud (m)",
                    aspectratio=dict(x=1, y=1, z=0.42)
                )
            )
            st.plotly_chart(fig_3d, use_container_width=True)
        else:
            st.warning("No se pudo reconstruir la malla 3D para este punto geográfico.")

    st.markdown("<br>", unsafe_allow_html=True)

    # Visor Dual: Sitio Terrestre vs. NASA Trek Corregido
    with st.container(border=True):
        st.markdown("##### 🛰️ Visor Dual: Terreno Terrestre vs. Cartografía Orbital NASA Trek")
        col_dual_e, col_dual_s = st.columns(2)
        
        with col_dual_e:
            st.markdown(f"**🌍 Sitio Terrestre (Satélite Esri):** `{site_row['name']}` ({site_row['latitude']:.3f}, {site_row['longitude']:.3f})")
            m_local_earth = folium.Map(
                location=[site_row["latitude"], site_row["longitude"]],
                zoom_start=9,
                tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                attr="Esri World Imagery"
            )
            folium.Marker(
                location=[site_row["latitude"], site_row["longitude"]],
                popup=site_row['name'],
                icon=folium.Icon(color="blue", icon="crosshairs", prefix="fa")
            ).add_to(m_local_earth)
            st_folium(m_local_earth, width="100%", height=320, key=f"dual_earth_{site_row['name']}")
            
        with col_dual_s:
            trek_conf = target_profile["trek_layer"]
            st.markdown(f"**🪐 Cartografía Orbital NASA Trek:** `{trek_conf['title']}`")
            
            m_space = folium.Map(
                location=[trek_conf["center_lat"], trek_conf["center_lon"]],
                zoom_start=trek_conf["default_zoom"],
                crs="EPSG4326",
                tiles=None,
                control_scale=False
            )
            folium.TileLayer(
                tiles=trek_conf["tile_url_template"],
                attr=f"NASA Planetary Data System (PDS) - {trek_conf['layer_id']}",
                name=trek_conf["title"],
                overlay=False
            ).add_to(m_space)
            folium.Marker(
                location=[trek_conf["center_lat"], trek_conf["center_lon"]],
                popup=target_profile['name'],
                icon=folium.Icon(color="red", icon="star", prefix="fa")
            ).add_to(m_space)
            st_folium(m_space, width="100%", height=320, key=f"dual_space_{selected_target_key}")
            
            st.link_button(
                f"🚀 Abrir en NASA {target_profile['body']} Trek 3D ↗",
                trek_conf["trek_url"],
                use_container_width=True
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # Panel Validez Científica y Limitaciones
    with st.container(border=True):
        st.markdown("##### ⚖️ Validez Científica y Limitaciones")
        col_v1, col_v2, col_v3 = st.columns(3)
        
        with col_v1:
            st.markdown("**✅ Dónde SÍ es Válida la Analogía:**")
            for s in diagnosis["strengths"]:
                st.markdown(f"• {s}")
                
        with col_v2:
            st.markdown("**❌ Dónde SE ROMPE la Analogía:**")
            for l in diagnosis["limitations"]:
                st.markdown(f"• {l}")
                
        with col_v3:
            st.markdown("**🛰️ Ensayos de Ingeniería Recomendados:**")
            for r in diagnosis["recommended_tests"]:
                st.markdown(f"• {r}")

    # Descarga de Informes
    st.markdown("<br>", unsafe_allow_html=True)
    report_md = f"""# INFORME TÉCNICO // EARTH TO SPACE: NEW HORIZONS
Plataforma: Earth To Space: New Horizons
Subtítulo: Explorando análogos entre la Tierra, la Luna y Marte con datos reales de la NASA
Fecha: 2026-11-14
Objetivo Espacial: {target_profile['name']} ({target_profile['body']})
Referencia de Misión NASA: {target_profile['scientific_mission_reference']}

## SITIO TERRESTRE
Nombre: {site_row['name']}
País: {site_row['country']}
Coordenadas: Lat {site_row['latitude']}, Lon {site_row['longitude']}
Elevación: {site_row.get('elevation_m')} m | Pendiente: {site_row.get('slope_deg')}° | Rugosidad: {site_row.get('roughness_m')} m
Geología: {geo_translated}
Similitud Global: {site_row['overall_similarity']:.2f}%

## DESGLOSE DE SIMILITUD (6D)
- Frío Extremo: {dim_scores['cold_extreme']:.1f}%
- Amplitud Térmica: {dim_scores['thermal_amplitude']:.1f}%
- Suelo & Aridez: {dim_scores['aridity_soil']:.1f}% (GWETTOP: {site_row.get('soil_wetness_ann')}, Albedo: {site_row.get('surface_albedo_ann')})
- Relieve Topográfico: {dim_scores['terrain_topography']:.1f}%
- Viento & Dinámica Eólica: {dim_scores['aeolian_wind']:.1f}%
- Altitud, Presión y Radiación Solar: {dim_scores['altitude_pressure_solar']:.1f}%
- Estrés Astrobiológico: {site_row.get('astrobiology_stress_index', 0):.1f} / 100

## VALIDEZ CIENTÍFICA
{explanation_plain}

### Dónde Sí es Válida
{chr(10).join(['- ' + s for s in diagnosis['strengths']])}

### Dónde Se Rompe la Analogía
{chr(10).join(['- ' + l for l in diagnosis['limitations']])}

### Protocolos Recomendados
{chr(10).join(['- ' + r for r in diagnosis['recommended_tests']])}
"""
    
    b_col1, b_col2, _ = st.columns([0.28, 0.28, 0.44])
    b_col1.download_button(
        "📥 Descargar Informe Técnico (.md)",
        data=report_md,
        file_name=f"EarthToSpace_{site_row['name'].replace(' ', '_')}.md",
        mime="text/markdown"
    )
    b_col2.download_button(
        "📊 Descargar Métricas (.csv)",
        data=pd.DataFrame([site_row]).to_csv(index=False),
        file_name=f"EarthToSpace_Metricas_{site_row['name'].replace(' ', '_')}.csv",
        mime="text/csv"
    )


# =============================================================================
# PESTAÑA 3: Comparativa Directa
# =============================================================================
with tab_duel:
    st.markdown("#### ⚖️ Comparativa Directa: Sitio Poco Estudiado vs. Referencia Histórica")
    st.caption("Compara cara a cara el rendimiento de nuevos candidatos geológicos frente a los sitios tradicionales de prueba de la NASA.")
    
    gems_list = scored_df[scored_df["is_famous"] == False]["name"].tolist()
    famous_list = scored_df[scored_df["is_famous"] == True]["name"].tolist()
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        site_a_name = st.selectbox("🔬 Sitio Poco Estudiado (Candidato):", options=gems_list, index=0)
    with col_c2:
        site_b_name = st.selectbox("🏛️ Sitio de Referencia Histórica:", options=famous_list, index=0)
        
    site_a = scored_df[scored_df["name"] == site_a_name].iloc[0].to_dict()
    site_b = scored_df[scored_df["name"] == site_b_name].iloc[0].to_dict()
    
    col_ca, col_cvs, col_cb = st.columns([0.45, 0.10, 0.45])
    
    target_short_duel = TARGET_SHORT_NAMES.get(selected_target_key, target_profile['name'].split('(')[0].strip())

    with col_ca:
        st.markdown(f"""
        <div class="metric-card" style="border-left: 5px solid #2563EB; padding: 16px 22px;">
            <span class="badge-blue">Sitio Poco Estudiado</span>
            <h3 style="margin: 8px 0 0 0; color: #F8FAFC;">{site_a['name']}</h3>
            <p style="color: #94A3B8; font-size: 0.85rem; margin-bottom: 8px;">{site_a['country']} | Geología: {GEOLOGY_TRANSLATIONS.get(site_a.get('geology_type'), site_a.get('geology_type'))}</p>
            <div style="font-family: 'Space Grotesk', sans-serif; font-size: 1.65rem; font-weight: 700; color: #38BDF8;">{site_a['overall_similarity']:.2f}%</div>
            <div style="font-size: 0.8rem; color: #94A3B8;">Afinidad con {target_short_duel}</div>
        </div>
        """, unsafe_allow_html=True)

    with col_cvs:
        st.markdown('<div style="text-align: center; padding-top: 45px; font-family: Space Grotesk; font-size: 1.8rem; color: #64748B;">VS</div>', unsafe_allow_html=True)

    with col_cb:
        st.markdown(f"""
        <div class="metric-card" style="border-left: 5px solid #F59E0B; padding: 16px 22px;">
            <span class="badge-amber">Referencia Histórica</span>
            <h3 style="margin: 8px 0 0 0; color: #F8FAFC;">{site_b['name']}</h3>
            <p style="color: #94A3B8; font-size: 0.85rem; margin-bottom: 8px;">{site_b['country']} | Geología: {GEOLOGY_TRANSLATIONS.get(site_b.get('geology_type'), site_b.get('geology_type'))}</p>
            <div style="font-family: 'Space Grotesk', sans-serif; font-size: 1.65rem; font-weight: 700; color: #FBBF24;">{site_b['overall_similarity']:.2f}%</div>
            <div style="font-size: 0.8rem; color: #94A3B8;">Afinidad con {target_short_duel}</div>
        </div>
        """, unsafe_allow_html=True)

    col_cd_radar, col_cd_therm = st.columns(2)
    
    with col_cd_radar:
        with st.container(border=True):
            st.markdown("**📡 Superposición de Perfiles (Radar Comparativo):**")
            cat_d = ["Frío", "Ciclo Térmico", "Aridez/Suelo", "Relieve", "Viento", "Altitud/Solar"]
            v_a = [site_a["sim_cold_extreme"], site_a["sim_thermal_amplitude"], site_a["sim_aridity_soil"], site_a["sim_terrain_topography"], site_a["sim_aeolian_wind"], site_a["sim_altitude_pressure_solar"]]
            v_b = [site_b["sim_cold_extreme"], site_b["sim_thermal_amplitude"], site_b["sim_aridity_soil"], site_b["sim_terrain_topography"], site_b["sim_aeolian_wind"], site_b["sim_altitude_pressure_solar"]]
            
            fig_dr = go.Figure()
            fig_dr.add_trace(go.Scatterpolar(r=v_a + [v_a[0]], theta=cat_d + [cat_d[0]], fill='toself', name=f"🔬 {site_a['name']}", line=dict(color='#38BDF8', width=2), fillcolor='rgba(37, 99, 235, 0.25)'))
            fig_dr.add_trace(go.Scatterpolar(r=v_b + [v_b[0]], theta=cat_d + [cat_d[0]], fill='toself', name=f"🏛️ {site_b['name']}", line=dict(color='#F59E0B', width=2), fillcolor='rgba(245, 158, 11, 0.2)'))
            fig_dr.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=8)), bgcolor="rgba(15, 28, 54, 0.4)"),
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                height=340,
                margin=dict(l=30, r=30, t=20, b=20),
                legend=dict(orientation="h", y=-0.12)
            )
            st.plotly_chart(fig_dr, use_container_width=True)
        
    with col_cd_therm:
        with st.container(border=True):
            st.markdown("**🌡️ Curva Térmica Mensual Comparada (Piel de Suelo):**")
            sa_ts = seasonality_base.get(site_a_name, {}).get("TS", {})
            sb_ts = seasonality_base.get(site_b_name, {}).get("TS", {})
            
            if sa_ts and sb_ts:
                mk = list(sa_ts.keys())
                fig_dt = go.Figure()
                fig_dt.add_trace(go.Scatter(x=mk, y=[sa_ts.get(m, np.nan) for m in mk], mode='lines+markers', name=f"🔬 {site_a_name}", line=dict(color='#38BDF8', width=2.5)))
                fig_dt.add_trace(go.Scatter(x=mk, y=[sb_ts.get(m, np.nan) for m in mk], mode='lines+markers', name=f"🏛️ {site_b_name}", line=dict(color='#F59E0B', width=2.5, dash='dash')))
                fig_dt.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(15, 28, 54, 0.4)",
                    height=340,
                    margin=dict(l=10, r=10, t=20, b=20),
                    legend=dict(orientation="h", y=-0.15),
                    yaxis=dict(title="Temperatura Piel Suelo (°C)", gridcolor="rgba(255,255,255,0.06)")
                )
                st.plotly_chart(fig_dt, use_container_width=True)
            else:
                st.info("Datos mensuales no disponibles para uno de los sitios en la comparativa.")

    # Tabla Head-to-Head
    st.markdown("##### 📊 Comparación Directa de Parámetros:")
    metrics_compare = [
        ("Similitud Global", f"{site_a['overall_similarity']:.2f}%", f"{site_b['overall_similarity']:.2f}%", site_a['overall_similarity'] > site_b['overall_similarity']),
        ("Elevación", f"{site_a.get('elevation_m', 0)} m", f"{site_b.get('elevation_m', 0)} m", site_a.get('elevation_m', 0) > site_b.get('elevation_m', 0)),
        ("Pendiente Topográfica", f"{site_a.get('slope_deg', 0)}°", f"{site_b.get('slope_deg', 0)}°", None),
        ("Rugosidad de Terreno", f"{site_a.get('roughness_m', 0)} m", f"{site_b.get('roughness_m', 0)} m", None),
        ("Índice de Aridez", f"{site_a.get('aridity_index', 0):.3f}", f"{site_b.get('aridity_index', 0):.3f}", site_a.get('aridity_index', 0) > site_b.get('aridity_index', 0)),
        ("Humedad del Suelo (GWETTOP)", f"{site_a.get('soil_wetness_ann', 'N/D')}", f"{site_b.get('soil_wetness_ann', 'N/D')}", site_a.get('soil_wetness_ann', 1) < site_b.get('soil_wetness_ann', 1)),
        ("Amplitud Térmica Anual", f"{site_a.get('thermal_amplitude_c', 0)} °C", f"{site_b.get('thermal_amplitude_c', 0)} °C", site_a.get('thermal_amplitude_c', 0) > site_b.get('thermal_amplitude_c', 0)),
        ("Estrés Astrobiológico", f"{site_a.get('astrobiology_stress_index', 0):.1f}", f"{site_b.get('astrobiology_stress_index', 0):.1f}", site_a.get('astrobiology_stress_index', 0) > site_b.get('astrobiology_stress_index', 0))
    ]
    
    comp_df = pd.DataFrame([
        {
            "Variable": m[0],
            f"🔬 {site_a_name}": m[1],
            f"🏛️ {site_b_name}": m[2],
            "Evaluación Relativa": "🔬 Mayor afinidad en candidato" if m[3] is True else ("🏛️ Mayor afinidad en referencia" if m[3] is False else "Depende del perfil de misión")
        }
        for m in metrics_compare
    ])
    st.table(comp_df)


# =============================================================================
# PESTAÑA 4: Laboratorio de Datos
# =============================================================================
with tab_laboratory:
    st.markdown("#### 📊 Laboratorio de Datos y Análisis Multivariado")
    st.caption("Aplica filtros por rangos físicos para explorar patrones geofísicos y descargar conjuntos de datos personalizados:")
    
    with st.container(border=True):
        f1, f2, f3, f4 = st.columns(4)
        with f1:
            min_elev, max_elev = float(scored_df["elevation_m"].min()), float(scored_df["elevation_m"].max())
            elev_range = st.slider("Elevación (m):", min_value=min_elev, max_value=max_elev, value=(min_elev, max_elev), step=100.0)
        with f2:
            min_aridity, max_aridity = float(scored_df["aridity_index"].min()), float(scored_df["aridity_index"].max())
            arid_range = st.slider("Aridez:", min_value=min_aridity, max_value=max_aridity, value=(min_aridity, max_aridity), step=0.02)
        with f3:
            min_slope, max_slope = float(scored_df["slope_deg"].min()), float(scored_df["slope_deg"].max())
            slope_range = st.slider("Pendiente (°):", min_value=min_slope, max_value=max_slope, value=(min_slope, max_slope), step=0.5)
        with f4:
            all_geologies = scored_df["geology_type"].unique().tolist()
            sel_geologies = st.multiselect(
                "Tipos Geológicos:",
                options=all_geologies,
                default=all_geologies,
                format_func=lambda g: GEOLOGY_TRANSLATIONS.get(g, g)
            )
        
    filtered_df = scored_df[
        (scored_df["elevation_m"].between(elev_range[0], elev_range[1])) &
        (scored_df["aridity_index"].between(arid_range[0], arid_range[1])) &
        (scored_df["slope_deg"].between(slope_range[0], slope_range[1])) &
        (scored_df["geology_type"].isin(sel_geologies))
    ].copy()
    
    st.markdown(f"**Sitios que cumplen los criterios:** `{len(filtered_df)}` de `{len(scored_df)}`")
    
    # Dispersión Multivariable
    with st.container(border=True):
        s1, s2, s3 = st.columns(3)
        axis_opts = {
            "elevation_m": "Elevación (m)",
            "aridity_index": "Índice de Aridez",
            "slope_deg": "Pendiente (°)",
            "roughness_m": "Rugosidad (m)",
            "thermal_amplitude_c": "Amplitud Térmica (°C)",
            "t2m_min_ann": "T° Mínima Anual (°C)",
            "overall_similarity": "Similitud Global (%)",
            "astrobiology_stress_index": "Estrés Astrobiológico"
        }
        with s1:
            x_axis = st.selectbox("Eje Horizontal (X):", options=list(axis_opts.keys()), index=0, format_func=lambda k: axis_opts[k])
        with s2:
            y_axis = st.selectbox("Eje Vertical (Y):", options=list(axis_opts.keys()), index=6, format_func=lambda k: axis_opts[k])
        with s3:
            color_choice = st.selectbox("Variable de Color:", options=["geology_type", "is_famous", "overall_similarity", "astrobiology_stress_index"], index=2)
            
        filtered_plot_df = filtered_df.copy()
        filtered_plot_df["Geología"] = filtered_plot_df["geology_type"].map(lambda g: GEOLOGY_TRANSLATIONS.get(g, g))
        
        fig_sc = px.scatter(
            filtered_plot_df,
            x=x_axis,
            y=y_axis,
            size="roughness_m",
            color="Geología" if color_choice == "geology_type" else color_choice,
            hover_name="name",
            hover_data={"country": True, "Geología": True, "overall_similarity": ":.1f%"},
            labels=axis_opts,
            title=f"Dispersión: {axis_opts[x_axis]} vs. {axis_opts[y_axis]}",
            color_continuous_scale="Viridis" if color_choice in ["overall_similarity", "astrobiology_stress_index"] else None
        )
        fig_sc.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(15, 28, 54, 0.4)",
            height=480
        )
        st.plotly_chart(fig_sc, use_container_width=True)
    
    st.markdown("##### 📋 Catálogo Filtrado:")
    table_filtered_view = filtered_df[["rank", "name", "country", "geology_type", "elevation_m", "aridity_index", "thermal_amplitude_c", "overall_similarity"]].copy()
    table_filtered_view["Geología"] = table_filtered_view["geology_type"].map(lambda g: GEOLOGY_TRANSLATIONS.get(g, g))
    table_filtered_view = table_filtered_view[["rank", "name", "country", "Geología", "elevation_m", "aridity_index", "thermal_amplitude_c", "overall_similarity"]]
    table_filtered_view.columns = ["#", "Sitio", "País", "Geología", "Elevación (m)", "Aridez", "Amplitud Térmica (°C)", "Similitud (%)"]
    
    st.dataframe(table_filtered_view, use_container_width=True, hide_index=True)
    
    st.download_button(
        "📥 Descargar Catálogo Filtrado (CSV)",
        data=filtered_df.to_csv(index=False),
        file_name="EarthToSpace_NewHorizons_Catalogo.csv",
        mime="text/csv"
    )

# =============================================================================
# PESTAÑA 5: Simulador de Experimentos de Ingeniería
# =============================================================================
with tab_experiments:
    st.markdown("#### 🧪 Simulador de Experimentos de Ingeniería en Sitio")
    st.caption(
        f"Evalúa el comportamiento físico de hardware y determina las ventanas de campaña en el terreno terrestre "
        f"frente a **{TARGET_SHORT_NAMES.get(selected_target_key, target_profile['body'])}**."
    )

    exp_sites = scored_df["name"].tolist()
    if "exp_site_selector" not in st.session_state or st.session_state["exp_site_selector"] not in exp_sites:
        st.session_state["exp_site_selector"] = (
            st.session_state["selected_site_name"]
            if st.session_state["selected_site_name"] in exp_sites
            else exp_sites[0]
        )

    def _on_exp_site_change():
        st.session_state["selected_site_name"] = st.session_state["exp_site_selector"]

    exp_site_name = st.selectbox(
        "📍 Sitio de ensayo:",
        options=exp_sites,
        key="exp_site_selector",
        on_change=_on_exp_site_change
    )
    exp_site = scored_df[scored_df["name"] == exp_site_name].iloc[0].to_dict()

    # Obtener estacionalidad real del JSON, del sitio en vivo o reconstrucción sinusoidal
    exp_seasonality = seasonality_base.get(exp_site_name)
    if not exp_seasonality and isinstance(exp_site.get("seasonality"), dict):
        exp_seasonality = exp_site.get("seasonality")
    if not exp_seasonality or "TS" not in exp_seasonality:
        exp_seasonality = build_seasonality_from_site_row(exp_site)

    # --- SIMULADOR 1: MOVILIDAD DE ROVER ---
    with st.container(border=True):
        st.markdown("##### 🛞 Simulador 1 — Movilidad de Rover (1.0 G vs. Gravedad Espacial)")
        col_r_ctrl, col_r_res = st.columns([0.38, 0.62])

        if "exp_rover_mass" not in st.session_state:
            st.session_state["exp_rover_mass"] = 1025

        def _sync_rover_mass():
            sel = st.session_state["exp_rover_preset"]
            if "Perseverance" in sel:
                st.session_state["exp_rover_mass"] = 1025
            elif "VIPER" in sel:
                st.session_state["exp_rover_mass"] = 430
            elif "Mini" in sel:
                st.session_state["exp_rover_mass"] = 60

        with col_r_ctrl:
            preset_rover = st.radio(
                "Vehículo de referencia:",
                ["Perseverance (1,025 kg)", "VIPER Lunar (430 kg)", "Mini-Rover (60 kg)", "Personalizado"],
                horizontal=False,
                key="exp_rover_preset",
                on_change=_sync_rover_mass
            )
            rover_mass = st.slider("Masa del rover (kg):", 20, 1500, step=10, key="exp_rover_mass")
            rover_speed = st.slider("Velocidad de marcha (m/s):", 0.05, 1.00, 0.20, 0.05, key="exp_rover_speed")
            st.caption(
                f"Terreno real de **{exp_site_name}**: Pendiente `{exp_site.get('slope_deg', 0):.2f}°` · "
                f"Rugosidad `{exp_site.get('roughness_m', 0):.1f} m`"
            )

        rover_sim = simulate_rover_mobility(
            rover_mass_kg=float(rover_mass),
            slope_deg=float(exp_site.get("slope_deg", 2.0)),
            roughness_m=float(exp_site.get("roughness_m", 10.0)),
            target_key=selected_target_key,
            speed_ms=float(rover_speed)
        )

        with col_r_res:
            rm1, rm2, rm3 = st.columns(3)
            rm1.metric("Potencia en Tierra (1.0 G)", f"{rover_sim['earth']['power_W']} W", f"Fuerza: {rover_sim['earth']['force_total_N']} N")
            rm2.metric(f"Potencia en {rover_sim['target_name']}", f"{rover_sim['target']['power_W']} W", f"Fuerza: {rover_sim['target']['force_total_N']} N")
            rm3.metric("Masa Equiv. en Tierra", f"{rover_sim['earth_test']['equivalent_mass_kg']} kg", f"Descarga: -{rover_sim['earth_test']['offload_pct']}%")

            fig_rover = go.Figure(data=[
                go.Bar(
                    name="Tierra (1.0 G)",
                    x=["Fuerza Pendiente (N)", "Fuerza Rodadura (N)", "Potencia Requerida (W)"],
                    y=[rover_sim["earth"]["force_slope_N"], rover_sim["earth"]["force_rolling_N"], rover_sim["earth"]["power_W"]],
                    marker_color="#2563EB"
                ),
                go.Bar(
                    name=rover_sim["target_name"],
                    x=["Fuerza Pendiente (N)", "Fuerza Rodadura (N)", "Potencia Requerida (W)"],
                    y=[rover_sim["target"]["force_slope_N"], rover_sim["target"]["force_rolling_N"], rover_sim["target"]["power_W"]],
                    marker_color="#F59E0B"
                )
            ])
            fig_rover.update_layout(
                barmode="group",
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(15, 28, 54, 0.4)",
                height=240,
                margin=dict(l=10, r=10, t=20, b=10),
                legend=dict(orientation="h", y=1.15)
            )
            st.plotly_chart(fig_rover, use_container_width=True)
            st.info(f"🔧 **Calibración en campo:** {rover_sim['earth_test']['note']}")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- SIMULADOR 2: PRESUPUESTO SOLAR ANUAL ---
    with st.container(border=True):
        st.markdown("##### ☀️ Simulador 2 — Presupuesto Solar y Atenuación por Polvo (12 Meses)")
        if exp_seasonality:
            if exp_seasonality.get("_synthetic"):
                st.caption("ℹ️ Sitio evaluado en vivo: usando reconstrucción estacional aproximada a partir de sus medias anuales NASA.")
            cs1, cs2, cs3 = st.columns(3)
            panel_area = cs1.slider("Área de paneles solares (m²):", 1.0, 40.0, 6.0, 0.5, key="exp_panel_area")
            panel_eff = cs2.slider("Eficiencia fotovoltaica (%):", 10, 35, 22, 1, key="exp_panel_eff")
            daily_load = cs3.slider("Consumo diario misión (Wh/día):", 500, 15000, 2500, 250, key="exp_daily_load")

            solar_sim = simulate_solar_budget(
                seasonality_site=exp_seasonality,
                panel_area_m2=float(panel_area),
                efficiency_pct=float(panel_eff),
                daily_load_wh=float(daily_load),
                target_key=selected_target_key,
                wind_ms=float(exp_site.get("ws10m_ann", 4.0))
            )

            sm1, sm2, sm3, sm4 = st.columns(4)
            sm1.metric("Meta Espacial Diaria", f"{solar_sim['daily_target_wh']:.0f} Wh/día", f"Ref: {solar_sim['solar_ref_target_kwh_m2_day']} kWh/m²")
            sm2.metric("Mejor Mes en Sitio", solar_sim["months_labels"][solar_sim["best_month"]], f"{solar_sim['best_month_wh']:.0f} Wh/día")
            sm3.metric("Mes Réplica Energética", solar_sim["months_labels"][solar_sim["analog_month"]], f"{solar_sim['analog_month_wh']:.0f} Wh/día")
            sm4.metric("Meses Autosuficientes", f"{len(solar_sim['surplus_months'])} / 12", f"Pérdida polvo: -{solar_sim['dust_loss_earth_pct']}%")

            m_labels = [MONTH_LABELS_ES[m] for m in MONTHS]
            earth_wh_vals = [solar_sim["monthly_earth_wh"][m] for m in MONTHS]

            fig_sol = go.Figure()
            fig_sol.add_trace(go.Scatter(x=m_labels, y=earth_wh_vals, mode="lines+markers", name=f"Generación en {exp_site_name}", line=dict(color="#38BDF8", width=3)))
            fig_sol.add_hline(y=solar_sim["daily_target_wh"], line_dash="dash", line_color="#F59E0B", annotation_text=f"Referencia {solar_sim['target_name']} ({solar_sim['daily_target_wh']:.0f} Wh)")
            fig_sol.add_hline(y=float(daily_load), line_dash="dot", line_color="#EF4444", annotation_text=f"Consumo mínimo ({daily_load} Wh)")
            fig_sol.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(15, 28, 54, 0.4)",
                height=310,
                margin=dict(l=10, r=10, t=25, b=10),
                yaxis_title="Energía (Wh / día)"
            )
            st.plotly_chart(fig_sol, use_container_width=True)
            st.markdown(solar_sim["interpretation"])
        else:
            st.warning("No hay datos estacionales suficientes para simular energía solar en este punto.")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- SIMULADOR 3: VENTANA ÓPTIMA + BITÁCORA DE INVESTIGACIÓN ---
    with st.container(border=True):
        st.markdown("##### 📅 Ventana Óptima de Campaña y Bitácora de Investigación")
        exp_types = {
            "cryogenic": "Pruebas Criogénicas y Baterías",
            "rover_mobility": "Movilidad Autónoma de Rover",
            "solar_dust": "Energía Solar y Mitigación de Polvo",
            "eva_human": "Operaciones Humanas (EVA)"
        }
        sel_exp_type = st.selectbox("Tipo de experimento a programar:", options=list(exp_types.keys()), format_func=lambda k: exp_types[k], key="exp_window_type")

        if exp_seasonality:
            win_res = find_optimal_experiment_window(exp_seasonality, sel_exp_type)
            wc1, wc2 = st.columns([0.55, 0.45])
            with wc1:
                st.success(f"🗓️ **Mejor trimestre:** {' · '.join(win_res['optimal_quarter'])} (Pico: **{win_res['optimal_month_label']}**)")
                st.markdown(win_res["justification"])
            with wc2:
                st.markdown(f"**Mes menos favorable:** `{win_res['worst_month_label']}`")
                if st.button("➕ Guardar simulación en bitácora", key="btn_save_log", use_container_width=True):
                    st.session_state["experiment_log"].append({
                        "Sitio": exp_site_name,
                        "Objetivo": TARGET_SHORT_NAMES.get(selected_target_key, selected_target_key),
                        "Experimento": exp_types[sel_exp_type],
                        "Mes Óptimo": win_res["optimal_month_label"],
                        "Rover (kg)": rover_mass,
                        "Potencia Tierra (W)": rover_sim["earth"]["power_W"],
                        "Potencia Objetivo (W)": rover_sim["target"]["power_W"],
                        "Masa Equiv (kg)": rover_sim["earth_test"]["equivalent_mass_kg"],
                        "Panel (m²)": panel_area if exp_seasonality else "N/D",
                        "Mes Réplica Solar": solar_sim["months_labels"][solar_sim["analog_month"]] if exp_seasonality else "N/D"
                    })
                    st.success("¡Experimento registrado en la bitácora!")

        if st.session_state["experiment_log"]:
            st.markdown("###### 📓 Tu Registro de Investigación")
            log_df = pd.DataFrame(st.session_state["experiment_log"])
            st.dataframe(log_df, use_container_width=True, hide_index=True)
            dl1, dl2, _ = st.columns([0.25, 0.25, 0.50])
            dl1.download_button("📥 Descargar Bitácora (.csv)", data=log_df.to_csv(index=False), file_name="EarthToSpace_Bitacora_Experimentos.csv", mime="text/csv")
            if dl2.button("🗑️ Limpiar bitácora"):
                st.session_state["experiment_log"] = []
                st.rerun()

with tab_env:
    try:
        render_environmental_tab(scored_df, seasonality_base, st.session_state["selected_site_name"], app_lang)
    except Exception as _env_err:
        st.warning(f"Environmental module notice: {_env_err}")

st.markdown("---")
st.html("""<div style="background: linear-gradient(135deg, #060D21 0%, #0F2557 60%, #081229 100%); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 14px; padding: 28px 36px; margin-top: 10px; text-align: center; font-family: Space Grotesk, sans-serif;">
<div style="font-size: 1.15rem; font-weight: 700; color: #38BDF8; margin-bottom: 6px;">&#x1F680; QUEBRACHO COSMOS &nbsp;&middot;&nbsp; <span style="font-size: 0.85rem; font-weight: 500; color: #94A3B8; letter-spacing: 1px;">NASA SPACE APPS CHALLENGE &middot; ARGENTINA</span></div>
<div style="font-size: 0.82rem; color: #CBD5E1; margin-bottom: 20px;">EARTH TO SPACE: NEW HORIZONS &nbsp;|&nbsp; Telemetr&#237;a NASA POWER &middot; Open-Meteo &middot; NASA Trek &middot; Nominatim OSM</div>
<div style="display: flex; justify-content: center; flex-wrap: wrap; gap: 14px; margin-bottom: 12px;">
<div style="background: rgba(37,99,235,0.15); border: 1px solid rgba(96,165,250,0.3); border-radius: 10px; padding: 12px 20px; min-width: 200px;"><div style="font-weight: 700; color: #F1F5F9; font-size: 0.88rem;">Bukret Brisa Abigail</div><div style="color: #60A5FA; font-size: 0.78rem; margin-top: 3px;">Team Owner &middot; @bukretbrisa_5</div></div>
<div style="background: rgba(37,99,235,0.15); border: 1px solid rgba(96,165,250,0.3); border-radius: 10px; padding: 12px 20px; min-width: 200px;"><div style="font-weight: 700; color: #F1F5F9; font-size: 0.88rem;">Franzisco P&#233;rez Real</div><div style="color: #60A5FA; font-size: 0.78rem; margin-top: 3px;">@franzisco</div></div>
<div style="background: rgba(37,99,235,0.15); border: 1px solid rgba(96,165,250,0.3); border-radius: 10px; padding: 12px 20px; min-width: 200px;"><div style="font-weight: 700; color: #F1F5F9; font-size: 0.88rem;">Jorge Nicol&#225;s G&#243;mez Paz Maldonado</div><div style="color: #60A5FA; font-size: 0.78rem; margin-top: 3px;">@nicolasgp.sgo26</div></div>
<div style="background: rgba(37,99,235,0.15); border: 1px solid rgba(96,165,250,0.3); border-radius: 10px; padding: 12px 20px; min-width: 200px;"><div style="font-weight: 700; color: #F1F5F9; font-size: 0.88rem;">Daniela Guadalupe Figueroa</div><div style="color: #60A5FA; font-size: 0.78rem; margin-top: 3px;">@danich04</div></div>
<div style="background: rgba(37,99,235,0.15); border: 1px solid rgba(96,165,250,0.3); border-radius: 10px; padding: 12px 20px; min-width: 200px;"><div style="font-weight: 700; color: #F1F5F9; font-size: 0.88rem;">Mauricio Hernandez</div><div style="color: #60A5FA; font-size: 0.78rem; margin-top: 3px;">@maurih</div></div>
</div>
<div style="font-size: 0.72rem; color: #475569; margin-top: 8px;">Los datos de telemetr&#237;a son p&#250;blicos y sin API key. Precisi&#243;n cient&#237;fica sujeta a resoluci&#243;n espacial de los modelos satelitales.</div>
</div>""")
