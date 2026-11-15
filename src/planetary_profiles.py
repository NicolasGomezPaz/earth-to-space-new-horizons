"""
Earth To Space: New Horizons - Planetary Profiles
=================================================
Perfiles planetarios científicos para misiones de exploración de la Luna y Marte.
Contiene metadatos de misiones de la NASA (LRO, MOLA, MEDA / Perseverance) y
las metas de calibración análoga terrestre para el motor cuantitativo de similitud.
"""

from typing import Dict, Any, List, Optional

PLANETARY_TARGETS: Dict[str, Dict[str, Any]] = {
    "lunar_south_pole": {
        "id": "lunar_south_pole",
        "name": "Polo Sur Lunar (Cráter Shackleton / Programa Artemis)",
        "body": "Luna",
        "body_en": "Moon",
        "summary": (
            "Zona de alunizaje prioritaria del programa Artemis. Caracterizada por picos de "
            "iluminación cuasi-continua en los bordes del cráter Shackleton y regiones en sombra "
            "permanente (PSRs) en su interior que albergan trampas frías de hielo de agua."
        ),
        "scientific_mission_reference": "NASA LRO (Lunar Reconnaissance Orbiter) - LOLA & Diviner",
        
        # Metadatos físicos y ambientales reales del cuerpo celeste
        "real_planetary_metrics": {
            "surface_temperature_range_c": [-230.0, -50.0],
            "mean_surface_temp_c": -130.0,
            "surface_gravity_g": 0.165,
            "surface_gravity_ms2": 1.62,
            "atmospheric_pressure_kpa": 1e-11,  # Vacío ultra-alto / exósfera
            "atmospheric_composition": "Exósfera colisionalmente despreciable (He, Ne, H2, Ar)",
            "crater_diameter_km": 21.0,
            "crater_rim_elevation_km": 4.2,     # Profundidad ~4.2 km desde el borde
            "solar_radiation_nature": "Exposición solar continua en picos polares; radiación ionizante directa sin filtro atmosférico",
            "water_ice_presence": "Depósitos masivos de volátiles y hielo de agua en trampas criogénicas permanentes (<40 K)"
        },
        
        # Coordenadas selenográficas del objetivo
        "coordinates": {
            "lat": -89.9,
            "lon": 0.0,
            "system": "Moon 2000"
        },
        
        # Geologías terrestres afines y metas de regolito/suelo
        "target_soil_wetness": 0.00,       # Regolito lunar completamente deshidratado
        "target_albedo": 0.12,             # Albedo medio del regolito anortosítico/basáltico lunar
        "target_geologies": ["impact_crater", "volcanic_basalt", "permafrost"],
        
        # Métricas objetivo escaladas para análogos en la Tierra (benchmarks para el motor de similitud)
        "analog_benchmark": {
            "ts_ann": -25.0,              # Frío polar extremo (mesetas antárticas / árticas)
            "t2m_min_ann": -40.0,
            "t2m_max_ann": 0.0,
            "thermal_amplitude_c": 35.0,  # Gran oscilación térmica
            "prectotcorr_ann": 0.0,       # Precipitación nula (simulación de vacío hiper-árido)
            "rh2m_ann": 5.0,              # Humedad relativa mínima
            "aridity_index": 1.0,         # Máxima aridez alcanzable
            "soil_wetness_ann": 0.00,     # Suelo completamente seco
            "surface_albedo_ann": 0.12,   # Albedo oscuro de regolito
            "elevation_m": 4500.0,        # Gran altitud para minimizar columna atmosférica
            "ps_ann": 58.0,               # Mínima presión atmosférica en Tierra
            "roughness_m": 45.0,          # Alta rugosidad por craterización y regolito suelto
            "slope_deg": 18.0,            # Pendientes pronunciadas (>12°) en bordes de cráter
            "ws10m_ann": 1.5,             # Viento bajo preferido (la Luna carece de dinámica eólica)
            "allsky_sfc_sw_dwn_ann": 6.8  # Fuerte irradiación directa en cumbres
        },
        
        # Ponderaciones base por dimensión
        "dimension_weights": {
            "cold_extreme": 0.20,
            "thermal_amplitude": 0.15,
            "aridity_soil": 0.25,
            "terrain_topography": 0.20,
            "aeolian_wind": 0.05,
            "altitude_pressure_solar": 0.15
        },
        
        # Configuración de visualización en NASA Moon Trek WMTS
        "trek_layer": {
            "layer_id": "LRO_WAC_Mosaic_Global_303ppd_v02",
            "title": "NASA Moon LRO WAC Global Mosaic (303 ppd)",
            "wmts_capabilities_url": "https://trek.nasa.gov/tiles/Moon/EQ/LRO_WAC_Mosaic_Global_303ppd_v02/1.0.0/WMTSCapabilities.xml",
            "tile_url_template": "https://trek.nasa.gov/tiles/Moon/EQ/LRO_WAC_Mosaic_Global_303ppd_v02/1.0.0/default/default028mm/{z}/{y}/{x}.jpg",
            "format": "image/jpeg",
            "tile_matrix_set": "default028mm",
            "default_zoom": 2,
            "center_lat": 0.0,
            "center_lon": 0.0,
            "trek_url": "https://trek.nasa.gov/moon/"
        }
    },
    
    "mars_arcadia": {
        "id": "mars_arcadia",
        "name": "Marte - Arcadia Planitia (Hielo Subsuperficial / Base In-Situ)",
        "body": "Marte",
        "body_en": "Mars",
        "summary": (
            "Extensas llanuras del hemisferio norte marciano identificadas como la región "
            "candidata ideal para la primera base humana permanente y misiones SpaceX Starship. "
            "Alberga grandes láminas de hielo de agua somero enterradas a menos de 1-2 metros del suelo."
        ),
        "scientific_mission_reference": "NASA Mars Reconnaissance Orbiter (SHARAD / HiRISE) & Mars Odyssey (GRS)",
        
        # Metadatos físicos y ambientales reales de Marte
        "real_planetary_metrics": {
            "surface_temperature_range_c": [-120.0, -10.0],
            "mean_surface_temp_c": -63.0,
            "surface_gravity_g": 0.38,
            "surface_gravity_ms2": 3.72,
            "atmospheric_pressure_kpa": 0.60,  # ~6.0 hPa (0.6% de la presión terrestre)
            "atmospheric_composition": "95.3% CO2, 2.6% N2, 1.9% Ar, trazas de vapor de agua y O2",
            "topographic_character": "Llanura sedimentaria-volcánica lisa con baja pendiente y escasos obstáculos",
            "solar_radiation_nature": "Atenuada por polvo atmosférico en suspensión; constante solar ~590 W/m²",
            "water_ice_presence": "Láminas masivas de hielo puro cubiertas por regolito protector (recurso ISRU accesible)"
        },
        
        # Coordenadas areográficas del objetivo
        "coordinates": {
            "lat": 39.3,
            "lon": -171.0,
            "system": "Mars 2000"
        },
        
        # Geologías terrestres afines y metas de regolito/suelo
        "target_soil_wetness": 0.05,       # Suelo frío con permafrost o hielo protegido
        "target_albedo": 0.26,             # Albedo brillante del polvo y arenas oxidadas de Marte
        "target_geologies": ["permafrost", "evaporite_salar", "hyperarid_regolith"],
        
        # Métricas objetivo escaladas para análogos en la Tierra
        "analog_benchmark": {
            "ts_ann": -14.0,              # Frío permafrost / tundra polar
            "t2m_min_ann": -28.0,
            "t2m_max_ann": 8.0,
            "thermal_amplitude_c": 28.0,
            "prectotcorr_ann": 0.15,      # Hiper-árido a desértico frío
            "rh2m_ann": 18.0,
            "aridity_index": 0.90,
            "soil_wetness_ann": 0.05,
            "surface_albedo_ann": 0.26,
            "elevation_m": 3600.0,        # Alta meseta o altiplano
            "ps_ann": 65.0,
            "roughness_m": 4.5,           # Terreno muy regular y plano
            "slope_deg": 2.2,             # Pendiente suave (<4°) ideal para aterrizaje seguro
            "ws10m_ann": 6.8,             # Vientos moderados-altos con transporte de polvo
            "allsky_sfc_sw_dwn_ann": 5.2
        },
        
        "dimension_weights": {
            "cold_extreme": 0.20,
            "thermal_amplitude": 0.10,
            "aridity_soil": 0.25,
            "terrain_topography": 0.20,
            "aeolian_wind": 0.15,
            "altitude_pressure_solar": 0.10
        },
        
        # Configuración de visualización en NASA Mars Trek WMTS
        "trek_layer": {
            "layer_id": "Mars_Viking_MDIM21_ClrMosaic_global_232m",
            "title": "NASA Mars Viking MDIM21 Color Mosaic (232m)",
            "wmts_capabilities_url": "https://trek.nasa.gov/tiles/Mars/EQ/Mars_Viking_MDIM21_ClrMosaic_global_232m/1.0.0/WMTSCapabilities.xml",
            "tile_url_template": "https://trek.nasa.gov/tiles/Mars/EQ/Mars_Viking_MDIM21_ClrMosaic_global_232m/1.0.0/default/default028mm/{z}/{y}/{x}.jpg",
            "format": "image/jpeg",
            "tile_matrix_set": "default028mm",
            "default_zoom": 3,
            "center_lat": 39.3,
            "center_lon": -171.0,
            "trek_url": "https://trek.nasa.gov/mars/"
        }
    },
    
    "mars_jezero": {
        "id": "mars_jezero",
        "name": "Marte - Cráter Jezero (Terreno Deltaico-Volcánico / Rover Perseverance)",
        "body": "Marte",
        "body_en": "Mars",
        "summary": (
            "Sitio de amartizaje del rover Mars 2020 Perseverance. Antiguo lago y delta "
            "fluvial de hace 3.700 millones de años compuesto por arcillas, carbonatos y basaltos, "
            "con escarpes pronunciados, dunas eólicas activas y alta radiación diurna."
        ),
        "scientific_mission_reference": "NASA Mars 2020 Perseverance Rover (MEDA, Mastcam-Z, PIXL, SHERLOC)",
        
        # Metadatos físicos y ambientales reales medidos in-situ por Perseverance MEDA
        "real_planetary_metrics": {
            "surface_temperature_range_c": [-88.0, -12.0],
            "mean_surface_temp_c": -52.0,
            "surface_gravity_g": 0.38,
            "surface_gravity_ms2": 3.72,
            "atmospheric_pressure_kpa": 0.75,  # ~7.5 hPa promedio medido por la estación MEDA
            "atmospheric_composition": "CO2 dominante; ciclos de condensación/sublimación polar estacional",
            "topographic_character": "Cráter de impacto de 45 km de diámetro con delta fluvial escarpado y campos de dunas",
            "solar_radiation_nature": "Intensa radiación UV superficial sin capa de ozono",
            "water_ice_presence": "Sin hielo somero activo; minerales hidratados (arcillas y sulfatos) fósiles"
        },
        
        # Coordenadas areográficas exactas de la estación meteorológica Perseverance MEDA
        "coordinates": {
            "lat": 18.38,
            "lon": 77.58,
            "system": "Mars 2000"
        },
        
        # Geologías terrestres afines y metas de regolito/suelo
        "target_soil_wetness": 0.02,       # Suelo regolítico seco con arcillas deshidratadas
        "target_albedo": 0.13,             # Albedo volcánico oscuro basáltico / deltaico
        "target_geologies": ["volcanic_basalt", "evaporite_salar", "impact_crater"],
        
        # Métricas objetivo escaladas para análogos en la Tierra
        "analog_benchmark": {
            "ts_ann": -8.0,
            "t2m_min_ann": -20.0,
            "t2m_max_ann": 16.0,
            "thermal_amplitude_c": 32.0,  # Gran oscilación térmica diurna/estacional
            "prectotcorr_ann": 0.05,      # Hiper-árido
            "rh2m_ann": 12.0,
            "aridity_index": 0.95,
            "soil_wetness_ann": 0.02,
            "surface_albedo_ann": 0.13,
            "elevation_m": 3200.0,
            "ps_ann": 70.0,
            "roughness_m": 24.0,          # Alta rugosidad por terreno pedregoso y cantos rodados
            "slope_deg": 11.5,            # Pendientes moderadas-altas (6°-15°) en frentes de delta
            "ws10m_ann": 7.8,             # Vientos fuertes y transporte eólico (dust devils)
            "allsky_sfc_sw_dwn_ann": 6.9  # Alta radiación solar despejada
        },
        
        "dimension_weights": {
            "cold_extreme": 0.10,
            "thermal_amplitude": 0.15,
            "aridity_soil": 0.25,
            "terrain_topography": 0.25,
            "aeolian_wind": 0.15,
            "altitude_pressure_solar": 0.10
        },
        
        # Configuración de visualización en NASA Mars Trek WMTS
        "trek_layer": {
            "layer_id": "Mars_Viking_MDIM21_ClrMosaic_global_232m",
            "title": "NASA Mars Viking MDIM21 Color Mosaic (232m)",
            "wmts_capabilities_url": "https://trek.nasa.gov/tiles/Mars/EQ/Mars_Viking_MDIM21_ClrMosaic_global_232m/1.0.0/WMTSCapabilities.xml",
            "tile_url_template": "https://trek.nasa.gov/tiles/Mars/EQ/Mars_Viking_MDIM21_ClrMosaic_global_232m/1.0.0/default/default028mm/{z}/{y}/{x}.jpg",
            "format": "image/jpeg",
            "tile_matrix_set": "default028mm",
            "default_zoom": 4,
            "center_lat": 18.38,
            "center_lon": 77.58,
            "trek_url": "https://trek.nasa.gov/mars/"
        }
    }
}


def get_planetary_target(target_id: str) -> Optional[Dict[str, Any]]:
    """Obtiene el perfil planetario por su identificador clave."""
    return PLANETARY_TARGETS.get(target_id)


def list_planetary_targets() -> List[Dict[str, Any]]:
    """Devuelve la lista completa de perfiles planetarios registrados."""
    return list(PLANETARY_TARGETS.values())
