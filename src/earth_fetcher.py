"""
Earth To Space: New Horizons - Earth Data Fetcher
=================================================
Módulo para consultar y procesar datos climáticos, de suelo y topográficos terrestres
en tiempo real para cualquier coordenada geográfica (lat, lon) utilizando
APIs públicas sin necesidad de claves de API (NASA POWER, Open-Meteo y Nominatim).
"""

import math
import logging
from typing import Dict, Any, Optional, List
import requests
import numpy as np

logger = logging.getLogger("earth_to_space.earth_fetcher")

# Configuración de URLs de APIs abiertas
NASA_POWER_CLIMATOLOGY_URL = "https://power.larc.nasa.gov/api/temporal/climatology/point"
OPEN_METEO_ELEVATION_URL = "https://api.open-meteo.com/v1/elevation"
NOMINATIM_SEARCH_URL = "https://nominatim.openstreetmap.org/search"

# Parámetros climatológicos y de suelo de NASA POWER
CLIMATE_PARAMETERS = [
    "TS",                # Skin Temperature (°C)
    "T2M_MIN",           # Temperature at 2m Minimum (°C)
    "T2M_MAX",           # Temperature at 2m Maximum (°C)
    "PRECTOTCORR",       # Precipitation Corrected (mm/day)
    "RH2M",              # Relative Humidity at 2m (%)
    "WS10M",             # Wind Speed at 10m (m/s)
    "ALLSKY_SFC_SW_DWN", # All Sky Insolation Incident on Horizontal Surface (kW-hr/m^2/day)
    "PS",                # Surface Pressure (kPa)
    "GWETTOP",           # Surface Soil Wetness (0-5 cm) [adimensional 0.0 - 1.0]
    "ALLSKY_SRF_ALB"     # All Sky Surface Albedo [adimensional 0.0 - 1.0]
]

MONTH_KEYS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


def _sanitize_val(val: Any) -> Optional[float]:
    """Sanitiza valores de NASA POWER reemplazando marcadores de valor faltante (-999)."""
    if val is None:
        return None
    try:
        fval = float(val)
        if math.isclose(fval, -999.0, abs_tol=1e-2) or math.isnan(fval):
            return None
        return fval
    except (ValueError, TypeError):
        return None


def fetch_nasa_power(lat: float, lon: float, timeout: int = 15) -> Dict[str, Any]:
    """
    Consulta la API climatológica de NASA POWER para obtener promedios anuales y series mensuales.
    Incluye fallback automático de comunidad en caso de valores faltantes en GWETTOP o ALLSKY_SRF_ALB.
    
    Args:
        lat: Latitud en grados decimales (-90 a 90).
        lon: Longitud en grados decimales (-180 a 180).
        timeout: Tiempo máximo de espera en segundos.
        
    Returns:
        Diccionario con métricas anuales, suelo, albedo, índice de aridez y series mensuales.
    """
    params = {
        "parameters": ",".join(CLIMATE_PARAMETERS),
        "community": "RE",
        "longitude": round(lon, 4),
        "latitude": round(lat, 4),
        "format": "JSON"
    }
    
    result = {
        "ts_ann": None,
        "t2m_min_ann": None,
        "t2m_max_ann": None,
        "t2m_mean_ann": None,
        "thermal_amplitude_c": None,
        "prectotcorr_ann": None,
        "rh2m_ann": None,
        "ws10m_ann": None,
        "allsky_sfc_sw_dwn_ann": None,
        "ps_ann": None,
        "soil_wetness_ann": None,
        "surface_albedo_ann": None,
        "aridity_index": None,
        "monthly_seasonality": {},
        "status": "error"
    }
    
    try:
        response = requests.get(
            NASA_POWER_CLIMATOLOGY_URL,
            params=params,
            headers={"User-Agent": "EarthToSpace-NewHorizons/1.0"},
            timeout=timeout
        )
        response.raise_for_status()
        data = response.json()
        param_dict = data.get("properties", {}).get("parameter", {})
        
        # Extracción de valores anuales
        ts_ann = _sanitize_val(param_dict.get("TS", {}).get("ANN"))
        t2m_min = _sanitize_val(param_dict.get("T2M_MIN", {}).get("ANN"))
        t2m_max = _sanitize_val(param_dict.get("T2M_MAX", {}).get("ANN"))
        precip = _sanitize_val(param_dict.get("PRECTOTCORR", {}).get("ANN"))
        rh = _sanitize_val(param_dict.get("RH2M", {}).get("ANN"))
        ws = _sanitize_val(param_dict.get("WS10M", {}).get("ANN"))
        solar = _sanitize_val(param_dict.get("ALLSKY_SFC_SW_DWN", {}).get("ANN"))
        ps = _sanitize_val(param_dict.get("PS", {}).get("ANN"))
        soil_wet = _sanitize_val(param_dict.get("GWETTOP", {}).get("ANN"))
        albedo = _sanitize_val(param_dict.get("ALLSKY_SRF_ALB", {}).get("ANN"))
        
        # Fallback para suelo/albedo si RE no los devolvió
        if (soil_wet is None or albedo is None):
            try:
                fb_params = {
                    "parameters": "GWETTOP,ALLSKY_SRF_ALB",
                    "community": "AG",
                    "longitude": round(lon, 4),
                    "latitude": round(lat, 4),
                    "format": "JSON"
                }
                fb_resp = requests.get(
                    NASA_POWER_CLIMATOLOGY_URL,
                    params=fb_params,
                    headers={"User-Agent": "EarthToSpace-NewHorizons/1.0"},
                    timeout=8
                )
                if fb_resp.status_code == 200:
                    fb_data = fb_resp.json().get("properties", {}).get("parameter", {})
                    if soil_wet is None:
                        soil_wet = _sanitize_val(fb_data.get("GWETTOP", {}).get("ANN"))
                    if albedo is None:
                        albedo = _sanitize_val(fb_data.get("ALLSKY_SRF_ALB", {}).get("ANN"))
            except Exception:
                pass  # Mantiene None sin romper
        
        # Amplitud térmica anual promedio
        thermal_amp = None
        if t2m_max is not None and t2m_min is not None:
            thermal_amp = round(t2m_max - t2m_min, 2)
            
        t2m_mean = None
        if t2m_max is not None and t2m_min is not None:
            t2m_mean = round((t2m_max + t2m_min) / 2.0, 2)
        elif ts_ann is not None:
            t2m_mean = ts_ann
            
        # Índice de aridez normalizado (0.0 = muy húmedo, 1.0 = hiper-árido)
        aridity_idx = None
        if rh is not None and precip is not None:
            norm_rh = max(0.0, min(100.0, rh)) / 100.0
            norm_precip = max(0.0, min(8.0, precip)) / 8.0
            moisture_factor = (0.5 * norm_rh) + (0.5 * norm_precip)
            aridity_idx = round(float(np.clip(1.0 - moisture_factor, 0.0, 1.0)), 4)
            
        # Extracción de estacionalidad mensual para graficar
        seasonality = {}
        for p_name in ["TS", "T2M_MIN", "T2M_MAX", "WS10M", "ALLSKY_SFC_SW_DWN", "PRECTOTCORR", "GWETTOP", "ALLSKY_SRF_ALB"]:
            raw_months = param_dict.get(p_name, {})
            cleaned_months = {}
            for m in MONTH_KEYS:
                val = _sanitize_val(raw_months.get(m))
                if val is not None:
                    cleaned_months[m] = round(val, 2)
            if cleaned_months:
                seasonality[p_name] = cleaned_months
                
        result.update({
            "ts_ann": ts_ann,
            "t2m_min_ann": t2m_min,
            "t2m_max_ann": t2m_max,
            "t2m_mean_ann": t2m_mean,
            "thermal_amplitude_c": thermal_amp,
            "prectotcorr_ann": precip,
            "rh2m_ann": rh,
            "ws10m_ann": ws,
            "allsky_sfc_sw_dwn_ann": solar,
            "ps_ann": ps,
            "soil_wetness_ann": soil_wet,
            "surface_albedo_ann": albedo,
            "aridity_index": aridity_idx,
            "monthly_seasonality": seasonality,
            "status": "success"
        })
        
    except requests.RequestException as exc:
        logger.warning(f"Error consultando NASA POWER para ({lat}, {lon}): {exc}")
        result["error_message"] = str(exc)
        
    return result


def fetch_terrain_metrics(lat: float, lon: float, step_deg: float = 0.005, timeout: int = 15) -> Dict[str, Any]:
    """
    Construye una cuadrícula 3x3 de elevaciones con paso de 0.005° (~550m) y calcula elevación central,
    rugosidad topográfica (desviación estándar) y pendiente en grados mediante el algoritmo de Horn.
    
    Args:
        lat: Latitud central en grados decimales.
        lon: Longitud central en grados decimales.
        step_deg: Paso de la cuadrícula en grados (~0.005° = 550 metros).
        timeout: Tiempo máximo de espera en segundos.
        
    Returns:
        Diccionario con elevation_m, roughness_m, slope_deg y matriz de elevaciones.
    """
    result = {
        "elevation_m": None,
        "roughness_m": None,
        "slope_deg": None,
        "grid_elevations": None,
        "status": "error"
    }
    
    # Cuadrícula 3x3 ordenada:
    # Fila 0 (Norte): lat + step, lons: [lon - step, lon, lon + step]
    # Fila 1 (Centro): lat,       lons: [lon - step, lon, lon + step]
    # Fila 2 (Sur):   lat - step, lons: [lon - step, lon, lon + step]
    lats = [
        lat + step_deg, lat + step_deg, lat + step_deg,
        lat,            lat,            lat,
        lat - step_deg, lat - step_deg, lat - step_deg
    ]
    lons = [
        lon - step_deg, lon,            lon + step_deg,
        lon - step_deg, lon,            lon + step_deg,
        lon - step_deg, lon,            lon + step_deg
    ]
    
    try:
        url = (
            f"{OPEN_METEO_ELEVATION_URL}?"
            f"latitude={','.join(f'{l:.5f}' for l in lats)}&"
            f"longitude={','.join(f'{l:.5f}' for l in lons)}"
        )
        response = requests.get(
            url,
            headers={"User-Agent": "EarthToSpace-NewHorizons/1.0"},
            timeout=timeout
        )
        response.raise_for_status()
        payload = response.json()
        elevations = payload.get("elevation", [])
        
        if len(elevations) == 9 and all(e is not None for e in elevations):
            elevations_arr = np.array(elevations, dtype=float)
            z_grid = elevations_arr.reshape((3, 3))
            
            # 1. Elevación del punto central
            center_elevation = round(float(z_grid[1, 1]), 2)
            
            # 2. Rugosidad topográfica: desviación estándar de las 9 elevaciones del micro-entorno
            roughness_m = round(float(np.std(elevations_arr)), 2)
            
            # 3. Pendiente en grados según el método de Horn (estándar USGS/GDAL)
            lat_rad = math.radians(lat)
            meters_per_deg_lat = 111320.0
            meters_per_deg_lon = 111320.0 * max(0.01, math.cos(lat_rad))
            
            dx = step_deg * meters_per_deg_lon
            dy = step_deg * meters_per_deg_lat
            
            dz_dx = ((z_grid[0, 2] + 2 * z_grid[1, 2] + z_grid[2, 2]) -
                     (z_grid[0, 0] + 2 * z_grid[1, 0] + z_grid[2, 0])) / (8.0 * dx)
                     
            dz_dy = ((z_grid[0, 0] + 2 * z_grid[0, 1] + z_grid[0, 2]) -
                     (z_grid[2, 0] + 2 * z_grid[2, 1] + z_grid[2, 2])) / (8.0 * dy)
                     
            gradient_magnitude = math.hypot(dz_dx, dz_dy)
            slope_deg = round(float(math.degrees(math.atan(gradient_magnitude))), 2)
            
            result.update({
                "elevation_m": center_elevation,
                "roughness_m": roughness_m,
                "slope_deg": slope_deg,
                "grid_elevations": elevations,
                "status": "success"
            })
        else:
            result["error_message"] = f"Respuesta de elevaciones incompleta ({len(elevations)} valores recibidos)"
            
    except requests.RequestException as exc:
        logger.warning(f"Error consultando Open-Meteo Elevation para ({lat}, {lon}): {exc}")
        result["error_message"] = str(exc)
        
    return result


def fetch_terrain_grid_7x7(lat: float, lon: float, span_deg: float = 0.025, timeout: int = 15) -> Dict[str, Any]:
    """
    Realiza una sola consulta batch a Open-Meteo Elevation para obtener una cuadrícula 7x7 (49 puntos)
    alrededor de (lat, lon) con un radio de cobertura configurado por span_deg (~2.8 km a la redonda).
    
    Args:
        lat: Latitud central.
        lon: Longitud central.
        span_deg: Extensión angular en grados desde el centro (default 0.025° = ~2.8 km).
        timeout: Tiempo máximo de espera en segundos.
        
    Returns:
        Diccionario con matriz 7x7 de elevaciones (numpy array y lista), ejes x_km, y_km, min, max.
    """
    result: Dict[str, Any] = {
        "grid_7x7": None,
        "x_km": None,
        "y_km": None,
        "elevation_min": None,
        "elevation_max": None,
        "center_elevation": None,
        "status": "error"
    }
    
    # 7 latitudes de Norte (lat + span) a Sur (lat - span)
    # 7 longitudes de Oeste (lon - span) a Este (lon + span)
    lats_1d = np.linspace(lat + span_deg, lat - span_deg, 7)
    lons_1d = np.linspace(lon - span_deg, lon + span_deg, 7)
    
    # Grid 7x7: 49 puntos ordenados
    grid_lats, grid_lons = np.meshgrid(lats_1d, lons_1d, indexing="ij")
    flat_lats = grid_lats.flatten()
    flat_lons = grid_lons.flatten()
    
    lat_rad = math.radians(lat)
    km_per_deg_lat = 111.320
    km_per_deg_lon = 111.320 * max(0.01, math.cos(lat_rad))
    
    # Distancias relativas en km centradas en (0, 0)
    x_km = [round(float((l - lon) * km_per_deg_lon), 2) for l in lons_1d]
    y_km = [round(float((l - lat) * km_per_deg_lat), 2) for l in lats_1d]
    
    try:
        url = (
            f"{OPEN_METEO_ELEVATION_URL}?"
            f"latitude={','.join(f'{l:.4f}' for l in flat_lats)}&"
            f"longitude={','.join(f'{l:.4f}' for l in flat_lons)}"
        )
        resp = requests.get(
            url,
            headers={"User-Agent": "EarthToSpace-NewHorizons/1.0"},
            timeout=timeout
        )
        resp.raise_for_status()
        elevations = resp.json().get("elevation", [])
        
        if len(elevations) == 49 and all(e is not None for e in elevations):
            arr = np.array(elevations, dtype=float).reshape((7, 7))
            result.update({
                "grid_7x7": arr.tolist(),
                "x_km": x_km,
                "y_km": y_km,
                "elevation_min": round(float(np.min(arr)), 1),
                "elevation_max": round(float(np.max(arr)), 1),
                "center_elevation": round(float(arr[3, 3]), 1),
                "status": "success"
            })
        else:
            result["error_message"] = f"Respuesta incompleta ({len(elevations)} puntos)"
    except Exception as exc:
        logger.warning(f"Error consultando elevaciones 7x7 para ({lat}, {lon}): {exc}")
        result["error_message"] = str(exc)
        
    return result


def search_location(query: str, limit: int = 5, timeout: int = 10) -> List[Dict[str, Any]]:
    """
    Busca cualquier lugar del mundo por nombre utilizando OpenStreetMap Nominatim.
    
    Args:
        query: Nombre o descripción del lugar (ej. 'Desierto de Atacama', 'Askja Islandia').
        limit: Número máximo de resultados (default 5).
        timeout: Tiempo máximo de espera en segundos.
        
    Returns:
        Lista de diccionarios con 'display_name', 'lat', 'lon'.
    """
    results: List[Dict[str, Any]] = []
    if not query or not query.strip():
        return results
        
    params = {
        "q": query.strip(),
        "format": "json",
        "limit": limit
    }
    
    try:
        response = requests.get(
            NOMINATIM_SEARCH_URL,
            params=params,
            headers={"User-Agent": "EarthToSpace-NewHorizons/1.0"},
            timeout=timeout
        )
        if response.status_code == 200:
            data = response.json()
            for item in data:
                try:
                    results.append({
                        "display_name": item.get("display_name", ""),
                        "lat": float(item["lat"]),
                        "lon": float(item["lon"])
                    })
                except (KeyError, ValueError, TypeError):
                    continue
    except Exception as exc:
        logger.warning(f"Error en búsqueda de ubicación Nominatim para '{query}': {exc}")
        
    return results


def analyze_earth_point(lat: float, lon: float, name: str = "Custom Site") -> Dict[str, Any]:
    """
    Analiza un punto terrestre combinando métricas climáticas (NASA POWER),
    variables de suelo (humedad y albedo) y topográficas (Open-Meteo).
    
    Args:
        lat: Latitud geográfica (-90 a 90).
        lon: Longitud geográfica (-180 a 180).
        name: Nombre descriptivo o identificador de la ubicación.
        
    Returns:
        Diccionario plano con todas las métricas preparado para análisis y motores de similitud.
    """
    climate = fetch_nasa_power(lat, lon)
    terrain = fetch_terrain_metrics(lat, lon)
    
    # Precipitación anual estimada (mm/año)
    annual_precip = None
    if climate.get("prectotcorr_ann") is not None:
        annual_precip = round(climate["prectotcorr_ann"] * 365.25, 2)
        
    fetch_ok = (climate.get("status") == "success") and (terrain.get("status") == "success")
    
    return {
        "name": name,
        "latitude": round(lat, 5),
        "longitude": round(lon, 5),
        # Variables topográficas
        "elevation_m": terrain.get("elevation_m"),
        "roughness_m": terrain.get("roughness_m"),
        "slope_deg": terrain.get("slope_deg"),
        # Variables térmicas
        "ts_ann": climate.get("ts_ann"),
        "t2m_min_ann": climate.get("t2m_min_ann"),
        "t2m_max_ann": climate.get("t2m_max_ann"),
        "t2m_mean_ann": climate.get("t2m_mean_ann"),
        "thermal_amplitude_c": climate.get("thermal_amplitude_c"),
        # Variables de humedad y precipitación
        "prectotcorr_ann": climate.get("prectotcorr_ann"),
        "annual_precip_mm": annual_precip,
        "rh2m_ann": climate.get("rh2m_ann"),
        "aridity_index": climate.get("aridity_index"),
        # Variables de suelo y albedo
        "soil_wetness_ann": climate.get("soil_wetness_ann"),
        "surface_albedo_ann": climate.get("surface_albedo_ann"),
        # Variables dinámicas y de radiación
        "ws10m_ann": climate.get("ws10m_ann"),
        "allsky_sfc_sw_dwn_ann": climate.get("allsky_sfc_sw_dwn_ann"),
        "ps_ann": climate.get("ps_ann"),
        # Desglose mensual para graficado
        "seasonality": climate.get("monthly_seasonality", {}),
        "fetch_status": "success" if fetch_ok else "partial",
        "climate_status": climate.get("status"),
        "terrain_status": terrain.get("status")
    }
