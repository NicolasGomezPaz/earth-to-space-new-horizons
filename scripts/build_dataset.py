"""
TerraSim - Curated Earth Analogs Dataset Builder
================================================
Construye el catálogo científico curado de ~50 análogos terrestres reales distribuidos
globalmente en todos los continentes, consultando en batch NASA POWER y Open-Meteo.
Genera 'data/earth_analogs.csv' y 'data/earth_seasonality.json'.
"""

import sys
import os
import json
import time
import logging
from typing import List, Dict, Any
import pandas as pd

# Asegurar importación de módulos en src/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.earth_fetcher import analyze_earth_point
from src.similarity import compute_similarity, generate_site_diagnosis

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("build_dataset")

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
CSV_PATH = os.path.join(DATA_DIR, "earth_analogs.csv")
JSON_PATH = os.path.join(DATA_DIR, "earth_seasonality.json")

# Catálogo curado de 50 sitios con tipos geológicos estandarizados:
# "volcanic_basalt", "evaporite_salar", "impact_crater", "permafrost", "hyperarid_regolith"
CATALOG_SITES: List[Dict[str, Any]] = [
    # ---------------------------------------------------------
    # 8 Sitios Famosos de Referencia (is_famous=True)
    # ---------------------------------------------------------
    {
        "name": "Desierto de Atacama (Yungay)",
        "country": "Chile",
        "geology_type": "hyperarid_regolith",
        "lat": -24.08,
        "lon": -69.87,
        "is_famous": True,
        "geology_notes": "Núcleo hiper-árido de Atacama; límite seco para la vida utilizado por NASA Viking y Mars 2020."
    },
    {
        "name": "Cráter Haughton",
        "country": "Canadá",
        "geology_type": "impact_crater",
        "lat": 75.38,
        "lon": -89.68,
        "is_famous": True,
        "geology_notes": "Cráter de impacto de 23 km en Devon Island, base polar del NASA HMP en permafrost continuo."
    },
    {
        "name": "Valles Secos de McMurdo",
        "country": "Antártida",
        "geology_type": "permafrost",
        "lat": -77.50,
        "lon": 162.00,
        "is_famous": True,
        "geology_notes": "Desierto frío antártico hiper-árido libre de nieve perenne, análogo por frío extremo y desecación."
    },
    {
        "name": "Mauna Kea",
        "country": "Estados Unidos",
        "geology_type": "volcanic_basalt",
        "lat": 19.82,
        "lon": -155.47,
        "is_famous": True,
        "geology_notes": "Estratovolcán basáltico a 4.200 m snm con regolito volcánico y pruebas históricas de rovers NASA."
    },
    {
        "name": "Río Tinto",
        "country": "España",
        "geology_type": "volcanic_basalt",
        "lat": 37.70,
        "lon": -6.55,
        "is_famous": True,
        "geology_notes": "Río ácido rico en sulfatos férricos y jarosita, análogo geoquímico directo de Meridiani Planum en Marte."
    },
    {
        "name": "Askja",
        "country": "Islandia",
        "geology_type": "volcanic_basalt",
        "lat": 65.03,
        "lon": -16.75,
        "is_famous": True,
        "geology_notes": "Caldera volcánica basáltica en las Tierras Altas de Islandia, sitio de entrenamiento de los astronautas del Apolo."
    },
    {
        "name": "Desierto de Mojave",
        "country": "Estados Unidos",
        "geology_type": "hyperarid_regolith",
        "lat": 35.01,
        "lon": -115.47,
        "is_famous": True,
        "geology_notes": "Terrenos aluviales secos y dunas empleados para movilidad y tracción de rovers de NASA JPL."
    },
    {
        "name": "Campo Volcánico Pinacate",
        "country": "México",
        "geology_type": "volcanic_basalt",
        "lat": 31.77,
        "lon": -113.50,
        "is_famous": True,
        "geology_notes": "Campo volcánico con maares gigantes, conos de escoria y basaltos, campo de entrenamiento del Apolo 14."
    },

    # ---------------------------------------------------------
    # 42 Sitios Poco Estudiados (is_famous=False)
    # ---------------------------------------------------------
    {
        "name": "Salar de Uyuni",
        "country": "Bolivia",
        "geology_type": "evaporite_salar",
        "lat": -20.13,
        "lon": -67.63,
        "is_famous": False,
        "geology_notes": "Mayor salar continuo del planeta a 3.650 m; costras de halita y litio análogas a paleolagos marcianos."
    },
    {
        "name": "Puna de Atacama / Volcán Llullaillaco",
        "country": "Argentina/Chile",
        "geology_type": "volcanic_basalt",
        "lat": -24.72,
        "lon": -68.53,
        "is_famous": False,
        "geology_notes": "Altiplano volcánico a 6.700 m con máxima radiación UV terrestre, frío extremo y bajísima presión barométrica."
    },
    {
        "name": "Cuenca de Qaidam",
        "country": "China",
        "geology_type": "evaporite_salar",
        "lat": 37.15,
        "lon": 93.85,
        "is_famous": False,
        "geology_notes": "Depresión hiper-árida a 3.000 m con yardangs eólicos gigantes y sulfatos de magnesio idénticos a Marte."
    },
    {
        "name": "Desierto de Lut",
        "country": "Irán",
        "geology_type": "hyperarid_regolith",
        "lat": 30.60,
        "lon": 58.80,
        "is_famous": False,
        "geology_notes": "Punto de mayor temperatura radiativa superficial del planeta; llanuras de grava oscura eólica sin vegetación."
    },
    {
        "name": "Estructura de Richat",
        "country": "Mauritania",
        "geology_type": "impact_crater",
        "lat": 21.13,
        "lon": -11.40,
        "is_famous": False,
        "geology_notes": "Domo concéntrico multianillo de 40 km visible desde órbita, simulador geomorfológico de cuencas de impacto."
    },
    {
        "name": "Cráter Lonar",
        "country": "India",
        "geology_type": "impact_crater",
        "lat": 19.98,
        "lon": 76.51,
        "is_famous": False,
        "geology_notes": "Único cráter de impacto hiperveloz terrestre formado enteramente sobre manto basáltico (Deccan Traps)."
    },
    {
        "name": "Depresión de Danakil",
        "country": "Etiopía",
        "geology_type": "evaporite_salar",
        "lat": 14.24,
        "lon": 40.30,
        "is_famous": False,
        "geology_notes": "Cuenca tectónica a -125 m bsnm con fumarolas de azufre, manantiales clorurados y salmueras ácidas."
    },
    {
        "name": "Desierto de Tabernas",
        "country": "España",
        "geology_type": "hyperarid_regolith",
        "lat": 37.01,
        "lon": -2.45,
        "is_famous": False,
        "geology_notes": "Badlands semiáridos con cárcavas sedimentarias desnudas, excelentes para visión artificial de rovers."
    },
    {
        "name": "Cráter Pingualuit",
        "country": "Canadá",
        "geology_type": "impact_crater",
        "lat": 61.28,
        "lon": -73.67,
        "is_famous": False,
        "geology_notes": "Cráter meteórico de 3.4 km en la tundra ártica de Nunavik con aguas puras y permafrost criogénico."
    },
    {
        "name": "Cráter Bosumtwi",
        "country": "Ghana",
        "geology_type": "impact_crater",
        "lat": 6.50,
        "lon": -1.42,
        "is_famous": False,
        "geology_notes": "Cráter de impacto de 10.5 km en basamento precámbrico con eyecciones vítreas y tectitas."
    },
    {
        "name": "Cráter Gosses Bluff",
        "country": "Australia",
        "geology_type": "impact_crater",
        "lat": -23.82,
        "lon": 132.31,
        "is_famous": False,
        "geology_notes": "Estructura de impacto altamente erosionada con anillo central levantado en el árido interior australiano."
    },
    {
        "name": "Cráter Nördlinger Ries",
        "country": "Alemania",
        "geology_type": "impact_crater",
        "lat": 48.88,
        "lon": 10.55,
        "is_famous": False,
        "geology_notes": "Cráter de impacto de 24 km donde se descubrieron las brechas suevíticas estudiadas por los astronautas del Apolo."
    },
    {
        "name": "Meseta de Putorana",
        "country": "Rusia",
        "geology_type": "volcanic_basalt",
        "lat": 69.00,
        "lon": 93.00,
        "is_famous": False,
        "geology_notes": "Vastas mesetas escalonadas de basaltos de inundación siberianos con permafrost continuo y cañones profundos."
    },
    {
        "name": "Cráter Batagaika",
        "country": "Rusia",
        "geology_type": "permafrost",
        "lat": 67.58,
        "lon": 134.77,
        "is_famous": False,
        "geology_notes": "Estructura termokárstica colapsada en permafrost de Yakutia; análogo para pérdida de hielo enterrado en Marte."
    },
    {
        "name": "Salar de Makgadikgadi",
        "country": "Botsuana",
        "geology_type": "evaporite_salar",
        "lat": -20.55,
        "lon": 25.75,
        "is_famous": False,
        "geology_notes": "Antiguo lecho lacustre gigante del Kalahari con costras salinas hiper-áridas barridas por fuertes vientos."
    },
    {
        "name": "Chott el Djerid",
        "country": "Túnez",
        "geology_type": "evaporite_salar",
        "lat": 33.70,
        "lon": 8.43,
        "is_famous": False,
        "geology_notes": "Gran lago salino endorreico sahariano con depósitos continuos de yeso y halita deshidratada."
    },
    {
        "name": "Desierto de Badain Jaran",
        "country": "China",
        "geology_type": "hyperarid_regolith",
        "lat": 39.50,
        "lon": 102.30,
        "is_famous": False,
        "geology_notes": "Megadunas eólicas de hasta 500 m de altura en el desierto de Alashan, análogo de dunas transversales marcianas."
    },
    {
        "name": "Desierto del Namib (Sossusvlei)",
        "country": "Namibia",
        "geology_type": "hyperarid_regolith",
        "lat": -24.73,
        "lon": 15.29,
        "is_famous": False,
        "geology_notes": "Desierto hiper-árido ancestral con dunas de arena rojiza rica en óxidos de hierro idénticas al regolito marciano."
    },
    {
        "name": "Campo Volcánico Pali Aike",
        "country": "Chile/Argentina",
        "geology_type": "volcanic_basalt",
        "lat": -52.05,
        "lon": -69.80,
        "is_famous": False,
        "geology_notes": "Campo volcánico basáltico estepario patagónico con tubos de lava, maares y escoria oscura bajo vientos gélidos."
    },
    {
        "name": "Nevado Ojos del Salado",
        "country": "Chile/Argentina",
        "geology_type": "volcanic_basalt",
        "lat": -27.11,
        "lon": -68.54,
        "is_famous": False,
        "geology_notes": "Volcán más alto de la Tierra (6.893 m) con lagunas hipersalinas congeladas en atmósfera de bajísima presión."
    },
    {
        "name": "Cráter Tenoumer",
        "country": "Mauritania",
        "geology_type": "impact_crater",
        "lat": 22.92,
        "lon": -10.41,
        "is_famous": False,
        "geology_notes": "Cráter meteórico circular casi perfecto de 1.9 km en el Sahara occidental con bordes levantados nítidos."
    },
    {
        "name": "Cráter Tswaing",
        "country": "Sudáfrica",
        "geology_type": "impact_crater",
        "lat": -25.41,
        "lon": 28.08,
        "is_famous": False,
        "geology_notes": "Cráter de impacto de 1.1 km con anillo de brechas graníticas y un lago salino hiperevaporítico interior."
    },
    {
        "name": "Ischigualasto / Valle de la Luna",
        "country": "Argentina",
        "geology_type": "hyperarid_regolith",
        "lat": -30.16,
        "lon": -67.84,
        "is_famous": False,
        "geology_notes": "Badlands áridos y geoformas de areniscas y cenizas volcánicas esculpidas por abrasión eólica extrema."
    },
    {
        "name": "Meseta Tibetana Occidental (Ngari)",
        "country": "China",
        "geology_type": "permafrost",
        "lat": 32.50,
        "lon": 80.10,
        "is_famous": False,
        "geology_notes": "Techo del mundo a más de 4.500 m snm con permafrost alpino continuo, radiación solar extrema y aire enrarecido."
    },
    {
        "name": "Montes Tibesti",
        "country": "Chad",
        "geology_type": "volcanic_basalt",
        "lat": 20.80,
        "lon": 17.50,
        "is_famous": False,
        "geology_notes": "Macizo volcánico aislado en el Sahara central con calderas masivas y campos de lava basáltica anhidra."
    },
    {
        "name": "Lago Natrón / Ol Doinyo Lengai",
        "country": "Tanzania",
        "geology_type": "volcanic_basalt",
        "lat": -2.35,
        "lon": 35.93,
        "is_famous": False,
        "geology_notes": "Volcán activo de lavas carbonatíticas frías y lago hipersalino alcalino con costras minerales únicas."
    },
    {
        "name": "Cráter Roter Kamm",
        "country": "Namibia",
        "geology_type": "impact_crater",
        "lat": -27.77,
        "lon": 16.30,
        "is_famous": False,
        "geology_notes": "Cráter de impacto de 2.5 km en arenas rojas del Namib, análogo exacto de cráteres cubiertos por polvo marciano."
    },
    {
        "name": "Cráter Mistastin",
        "country": "Canadá",
        "geology_type": "impact_crater",
        "lat": 55.88,
        "lon": -63.30,
        "is_famous": False,
        "geology_notes": "Estructura de impacto de 28 km en Labrador rica en anortosita lunar y maskelynita producida por choque."
    },
    {
        "name": "Desierto de Sechura",
        "country": "Perú",
        "geology_type": "hyperarid_regolith",
        "lat": -5.80,
        "lon": -80.70,
        "is_famous": False,
        "geology_notes": "Depresión costera hiper-árida con salitrales y dunas eólicas desprovistas de cobertura orgánica."
    },
    {
        "name": "Salar de Arizaro",
        "country": "Argentina",
        "geology_type": "evaporite_salar",
        "lat": -24.58,
        "lon": -67.75,
        "is_famous": False,
        "geology_notes": "Segundo mayor salar andino a 3.460 m snm con el Cono de Arita, rodeado de costras salinas oscuras."
    },
    {
        "name": "Cráter Manicouagan",
        "country": "Canadá",
        "geology_type": "impact_crater",
        "lat": 51.38,
        "lon": -68.70,
        "is_famous": False,
        "geology_notes": "Gigantesco cráter multianillo de 100 km ('Ojo de Quebec') con rocas fundidas por impacto de impacto triásico."
    },
    {
        "name": "Desierto de Karakum",
        "country": "Turkmenistán",
        "geology_type": "hyperarid_regolith",
        "lat": 39.00,
        "lon": 60.00,
        "is_famous": False,
        "geology_notes": "Vastas extensiones arenosas centroasiáticas con campos de barjanes y cráteres colapsados eólicos."
    },
    {
        "name": "Rub al-Jali",
        "country": "Omán/Arabia Saudita",
        "geology_type": "hyperarid_regolith",
        "lat": 20.00,
        "lon": 50.00,
        "is_famous": False,
        "geology_notes": "El mayor mar continuo de arena del mundo; hiper-aridez absoluta y regolito fino transportado por viento."
    },
    {
        "name": "Pastos Grandes",
        "country": "Bolivia",
        "geology_type": "evaporite_salar",
        "lat": -21.63,
        "lon": -67.82,
        "is_famous": False,
        "geology_notes": "Caldera volcánica a 4.400 m snm con manantiales hidrotermales, salmueras de litio y pisolitos de calcita."
    },
    {
        "name": "Cráter Upheaval Dome",
        "country": "Estados Unidos",
        "geology_type": "impact_crater",
        "lat": 38.44,
        "lon": -109.93,
        "is_famous": False,
        "geology_notes": "Estructura de impacto profundamente disecada en areniscas mesozoicas en el Parque Canyonlands de Utah."
    },
    {
        "name": "Campos de Lava Harrat Khaybar",
        "country": "Arabia Saudita",
        "geology_type": "volcanic_basalt",
        "lat": 25.70,
        "lon": 39.95,
        "is_famous": False,
        "geology_notes": "Campos de lava basáltica oscura anhidra con domos de riolita blanca inusuales y tubos de lava volcánica."
    },
    {
        "name": "Meseta de Ennedi",
        "country": "Chad",
        "geology_type": "hyperarid_regolith",
        "lat": 17.15,
        "lon": 21.65,
        "is_famous": False,
        "geology_notes": "Escarpes y pilares de arenisca en el Sahara oriental erosionados intensamente por el viento cargado de arena."
    },
    {
        "name": "Cráter Barringer (Meteor Crater)",
        "country": "Estados Unidos",
        "geology_type": "impact_crater",
        "lat": 35.03,
        "lon": -111.02,
        "is_famous": False,
        "geology_notes": "Cráter de impacto de bólido ferroso de 1.2 km de diámetro en Arizona, modelo canónico de cráteres de impacto simples."
    },
    {
        "name": "Cataviña",
        "country": "México",
        "geology_type": "hyperarid_regolith",
        "lat": 29.73,
        "lon": -114.72,
        "is_famous": False,
        "geology_notes": "Llanura árida de bloques gigantes de granito esferoidal que simulan la rugosidad rocosa del suelo marciano."
    },
    {
        "name": "Lago El'gygytgyn",
        "country": "Rusia",
        "geology_type": "impact_crater",
        "lat": 67.50,
        "lon": 172.08,
        "is_famous": False,
        "geology_notes": "Cráter de impacto en rocas volcánicas félsicas en Chukotka; registro paleoclimático ininterrumpido en permafrost."
    },
    {
        "name": "Volcán Teide / Las Cañadas",
        "country": "España",
        "geology_type": "volcanic_basalt",
        "lat": 28.27,
        "lon": -16.64,
        "is_famous": False,
        "geology_notes": "Caldera volcánica de alta montaña a 3.700 m con coladas de lava basáltica/fonolítica y pruebas de ESA ExoMars."
    },
    {
        "name": "Salar de Coipasa",
        "country": "Bolivia",
        "geology_type": "evaporite_salar",
        "lat": -19.25,
        "lon": -68.15,
        "is_famous": False,
        "geology_notes": "Salar andino a 3.680 m que rodea un lago salado remanente, con extensas costras de sulfato de sodio y potasio."
    }
]


def build_curated_dataset() -> pd.DataFrame:
    """
    Construye el conjunto de datos consultando en vivo NASA POWER y Open-Meteo para cada sitio.
    Guarda los resultados en CSV y JSON.
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    total_sites = len(CATALOG_SITES)
    logger.info(f"Iniciando compilación de {total_sites} análogos planetarios terrestres...")
    
    rows: List[Dict[str, Any]] = []
    seasonality_dict: Dict[str, Any] = {}
    
    for idx, site in enumerate(CATALOG_SITES, start=1):
        name = site["name"]
        lat = site["lat"]
        lon = site["lon"]
        logger.info(f"[{idx}/{total_sites}] Consultando {name} ({lat}, {lon})...")
        
        try:
            analysis = analyze_earth_point(lat, lon, name=name)
        except Exception as e:
            logger.error(f"Error procesando {name}: {e}")
            analysis = {"name": name, "latitude": lat, "longitude": lon, "fetch_status": "error"}
            
        # Incorporar metadatos del catálogo
        analysis["country"] = site["country"]
        analysis["geology_type"] = site["geology_type"]
        analysis["is_famous"] = site["is_famous"]
        analysis["geology_notes"] = site["geology_notes"]
        
        # Extraer serie estacional y separar de la fila tabular
        seasonality = analysis.pop("seasonality", {})
        seasonality_dict[name] = seasonality
        
        rows.append(analysis)
        
        # Respetar límites de cortesía de APIs públicas abiertas
        time.sleep(0.35)
        
    df = pd.DataFrame(rows)
    
    # Reordenar columnas para máxima legibilidad
    front_cols = ["name", "country", "geology_type", "is_famous", "latitude", "longitude", "geology_notes"]
    other_cols = [c for c in df.columns if c not in front_cols]
    df = df[front_cols + other_cols]
    
    df.to_csv(CSV_PATH, index=False, encoding="utf-8")
    logger.info(f"Dataset tabular guardado en: {CSV_PATH} ({len(df)} filas, {len(df.columns)} columnas)")
    
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(seasonality_dict, f, ensure_ascii=False, indent=2)
    logger.info(f"Series mensuales guardadas en: {JSON_PATH}")
    
    return df


def display_top_hidden_gems(df: pd.DataFrame, target_key: str, top_n: int = 5):
    """Calcula y muestra en consola el ranking de Sitios Poco Estudiados para un objetivo planetario."""
    ranked_df = compute_similarity(df, target_key=target_key, preset_or_weights="balanced")
    hidden_gems = ranked_df[ranked_df["is_famous"] == False].head(top_n)
    
    target_name = "Polo Sur Lunar (Artemis)" if "lunar" in target_key else "Marte - Cráter Jezero (Perseverance)"
    print(f"\n{'='*75}")
    print(f"TOP {top_n} SITIOS POCO ESTUDIADOS (is_famous == False) PARA: {target_name.upper()}")
    print(f"{'='*75}")
    
    for rank, (_, row) in enumerate(hidden_gems.iterrows(), start=1):
        print(f"\n#{rank} {row['name']} ({row['country']})")
        print(f"   • Similitud Global: {row['overall_similarity']:.2f}% | Geología: {row['geology_type']}")
        print(f"   • Elevación: {row.get('elevation_m', 'N/D')} m | Pendiente: {row.get('slope_deg', 'N/D')}° | Rugosidad: {row.get('roughness_m', 'N/D')} m")
        print(f"   • T° Min: {row.get('t2m_min_ann', 'N/D')}°C | Oscilación: {row.get('thermal_amplitude_c', 'N/D')}°C | Aridez: {row.get('aridity_index', 'N/D')}")
        print(f"   • Scores dimensionales:")
        print(f"     - Frío: {row.get('sim_cold_extreme', 0):.1f}% | Ciclo Térmico: {row.get('sim_thermal_amplitude', 0):.1f}%")
        print(f"     - Suelo/Aridez: {row.get('sim_aridity_soil', 0):.1f}% | Relieve: {row.get('sim_terrain_topography', 0):.1f}%")
        print(f"     - Viento: {row.get('sim_aeolian_wind', 0):.1f}% | Altitud/Presión/Solar: {row.get('sim_altitude_pressure_solar', 0):.1f}%")
        print(f"   • Justificación científica: {row['geology_notes']}")


if __name__ == "__main__":
    df = build_curated_dataset()
    display_top_hidden_gems(df, target_key="lunar_south_pole", top_n=5)
    display_top_hidden_gems(df, target_key="mars_jezero", top_n=5)
