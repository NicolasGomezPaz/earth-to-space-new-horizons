"""
Earth To Space: New Horizons - Similarity Engine
================================================
Motor cuantitativo multidimensional para el cálculo de similitud científica entre
sitios terrestres y objetivos de exploración espacial (Luna y Marte).
Calcula 6 dimensiones científicas, aplica ponderaciones por misión, bonificaciones
por afinidad geológica, penalizaciones de coherencia física por objetivo y genera
diagnósticos detallados.

Penalizaciones de coherencia física:
  - lunar_south_pole : sitios húmedos/cálidos (prec > 250 mm o t2m_min > 0°C) → penalización severa.
  - mars_arcadia     : exige terreno plano (slope < 5°, roughness < 25 m); penaliza montañas.
  - mars_jezero      : exige hiper-aridez (aridity > 0.65, prec < 300 mm); penaliza zonas húmedas.
  Cráteres en climas húmedos: penalización ambiental adicional (solo valen por morfología).
"""

import math
from typing import Dict, Any, List, Optional, Union
import numpy as np
import pandas as pd

from src.planetary_profiles import PLANETARY_TARGETS, get_planetary_target

# Presets de ponderaciones según el enfoque de misión científica
MISSION_PRESETS: Dict[str, Dict[str, Any]] = {
    "balanced": {
        "id": "balanced",
        "name": "Balanceado Científico General",
        "description": "Ponderación holística equilibrada entre clima, topografía, suelo y radiación.",
        "weights": {
            "cold_extreme": 0.18,
            "thermal_amplitude": 0.14,
            "aridity_soil": 0.22,
            "terrain_topography": 0.18,
            "aeolian_wind": 0.12,
            "altitude_pressure_solar": 0.16
        }
    },
    "rover_mobility": {
        "id": "rover_mobility",
        "name": "Pruebas de Movilidad de Rover",
        "description": "Prioriza el relieve (pendiente, rugosidad del terreno) y el suelo árido para evaluar tracción y navegación.",
        "weights": {
            "terrain_topography": 0.35,
            "aridity_soil": 0.25,
            "aeolian_wind": 0.15,
            "altitude_pressure_solar": 0.10,
            "cold_extreme": 0.08,
            "thermal_amplitude": 0.07
        }
    },
    "isru_ice_extraction": {
        "id": "isru_ice_extraction",
        "name": "Extracción de Hielo y Recursos In-Situ (ISRU)",
        "description": "Enfocado en frío criogénico, permafrost, hiper-aridez y condiciones extremas de perforación.",
        "weights": {
            "cold_extreme": 0.30,
            "aridity_soil": 0.25,
            "altitude_pressure_solar": 0.18,
            "thermal_amplitude": 0.12,
            "terrain_topography": 0.10,
            "aeolian_wind": 0.05
        }
    },
    "soil_solar_energy": {
        "id": "soil_solar_energy",
        "name": "Suelo/Polvo y Paneles Solares",
        "description": "Optimizado para evaluar acumulación de polvo regolítico, albedo superficial y radiación solar.",
        "weights": {
            "aridity_soil": 0.35,
            "altitude_pressure_solar": 0.25,
            "aeolian_wind": 0.20,
            "thermal_amplitude": 0.10,
            "cold_extreme": 0.05,
            "terrain_topography": 0.05
        }
    }
}


def _safe_float(val: Any, default: Optional[float] = None) -> Optional[float]:
    """Convierte a float seguro manejando None, nan o valores anómalos."""
    if val is None:
        return default
    try:
        f = float(val)
        return default if (math.isnan(f) or math.isclose(f, -999.0, abs_tol=1e-2)) else f
    except (ValueError, TypeError):
        return default


def _calc_dim_cold_extreme(site: Dict[str, Any], target_bm: Dict[str, Any]) -> float:
    """Dimensión 1: Frío extremo (temperatura mínima y media anual)."""
    t_min = _safe_float(site.get("t2m_min_ann"))
    t_mean = _safe_float(site.get("ts_ann"), _safe_float(site.get("t2m_mean_ann")))
    
    tgt_min = target_bm.get("t2m_min_ann", -20.0)
    tgt_mean = target_bm.get("ts_ann", -10.0)
    
    if t_min is None or t_mean is None:
        return 45.0
        
    # Tolerancia asimétrica: ser más frío que el benchmark es bienvenido; ser más cálido se penaliza
    diff_min = t_min - tgt_min
    tol_min = 22.0 if diff_min < 0 else 14.0
    sim_min = math.exp(-0.5 * (abs(diff_min) / tol_min) ** 2)
    
    diff_mean = t_mean - tgt_mean
    tol_mean = 20.0 if diff_mean < 0 else 12.0
    sim_mean = math.exp(-0.5 * (abs(diff_mean) / tol_mean) ** 2)
    
    score = (0.55 * sim_min + 0.45 * sim_mean) * 100.0
    return round(float(np.clip(score, 0.0, 100.0)), 2)


def _calc_dim_thermal_amplitude(site: Dict[str, Any], target_bm: Dict[str, Any]) -> float:
    """Dimensión 2: Estrés por amplitud y ciclo térmico."""
    site_amp = _safe_float(site.get("thermal_amplitude_c"))
    tgt_amp = target_bm.get("thermal_amplitude_c", 30.0)
    
    if site_amp is None:
        return 45.0
        
    diff = abs(site_amp - tgt_amp)
    # Si la amplitud del sitio es alta (>= 25°C), se parece a los ciclos diurnos/estacionales espaciales
    if site_amp >= tgt_amp:
        score = 100.0 - min(10.0, diff * 0.5)
    else:
        score = 100.0 * math.exp(-0.5 * (diff / 10.0) ** 2)
        
    return round(float(np.clip(score, 0.0, 100.0)), 2)


def _calc_dim_aridity_soil(site: Dict[str, Any], target_bm: Dict[str, Any], target_prof: Dict[str, Any]) -> float:
    """Dimensión 3: Aridez, humedad superficial del suelo (GWETTOP) y albedo (ALLSKY_SRF_ALB)."""
    aridity_idx = _safe_float(site.get("aridity_index"), 0.5)
    soil_wet = _safe_float(site.get("soil_wetness_ann"))
    albedo = _safe_float(site.get("surface_albedo_ann"))
    
    tgt_soil = target_prof.get("target_soil_wetness", target_bm.get("soil_wetness_ann", 0.02))
    tgt_albedo = target_prof.get("target_albedo", target_bm.get("surface_albedo_ann", 0.15))
    
    # 1. Componente de aridez climática (0.0 a 1.0 -> 0 a 100)
    score_aridity = min(100.0, max(0.0, aridity_idx * 100.0))
    
    # 2. Componente de humedad de suelo: suelo seco (baja humedad 0-5 cm) es análogo de regolito
    if soil_wet is not None:
        diff_soil = abs(soil_wet - tgt_soil)
        score_soil = 100.0 * math.exp(-0.5 * (diff_soil / 0.12) ** 2)
    else:
        # Si falta suelo, inferir de aridez
        score_soil = score_aridity * 0.9
        
    # 3. Componente de albedo superficial (color y reflectividad del sustrato)
    if albedo is not None:
        diff_albedo = abs(albedo - tgt_albedo)
        score_albedo = 100.0 * math.exp(-0.5 * (diff_albedo / 0.10) ** 2)
    else:
        score_albedo = 65.0
        
    composite = 0.45 * score_aridity + 0.35 * score_soil + 0.20 * score_albedo
    return round(float(np.clip(composite, 0.0, 100.0)), 2)


def _calc_dim_terrain_topography(site: Dict[str, Any], target_bm: Dict[str, Any]) -> float:
    """Dimensión 4: Topografía (pendiente media y rugosidad local)."""
    slope = _safe_float(site.get("slope_deg"))
    roughness = _safe_float(site.get("roughness_m"))
    
    tgt_slope = target_bm.get("slope_deg", 10.0)
    tgt_rough = target_bm.get("roughness_m", 20.0)
    
    if slope is None or roughness is None:
        return 50.0
        
    tol_slope = max(3.0, tgt_slope * 0.45)
    tol_rough = max(5.0, tgt_rough * 0.50)
    
    sim_slope = math.exp(-0.5 * (abs(slope - tgt_slope) / tol_slope) ** 2)
    sim_rough = math.exp(-0.5 * (abs(roughness - tgt_rough) / tol_rough) ** 2)
    
    score = (0.50 * sim_slope + 0.50 * sim_rough) * 100.0
    return round(float(np.clip(score, 0.0, 100.0)), 2)


def _calc_dim_aeolian_wind(site: Dict[str, Any], target_bm: Dict[str, Any]) -> float:
    """Dimensión 5: Dinámica eólica y transporte de polvo."""
    wind = _safe_float(site.get("ws10m_ann"))
    tgt_wind = target_bm.get("ws10m_ann", 5.0)
    
    if wind is None:
        return 50.0
        
    diff_wind = abs(wind - tgt_wind)
    score = 100.0 * math.exp(-0.5 * (diff_wind / 3.5) ** 2)
    return round(float(np.clip(score, 0.0, 100.0)), 2)


def _calc_dim_altitude_pressure_solar(site: Dict[str, Any], target_bm: Dict[str, Any]) -> float:
    """Dimensión 6: Altitud, baja presión barométrica y radiación solar."""
    elev = _safe_float(site.get("elevation_m"))
    solar = _safe_float(site.get("allsky_sfc_sw_dwn_ann"))
    ps = _safe_float(site.get("ps_ann"))
    
    tgt_elev = target_bm.get("elevation_m", 3500.0)
    tgt_solar = target_bm.get("allsky_sfc_sw_dwn_ann", 6.5)
    
    if elev is None or solar is None:
        return 50.0
        
    # Altitud elevada reduce la columna atmosférica, siendo mejor análogo de baja presión
    diff_elev = abs(elev - tgt_elev)
    sim_elev = math.exp(-0.5 * (diff_elev / 2000.0) ** 2)
    
    # Presión superficial (si está disponible)
    sim_ps = 1.0
    if ps is not None and "ps_ann" in target_bm:
        tgt_ps = target_bm["ps_ann"]
        diff_ps = abs(ps - tgt_ps)
        sim_ps = math.exp(-0.5 * (diff_ps / 20.0) ** 2)
        
    # Radiación solar incidente
    diff_solar = abs(solar - tgt_solar)
    sim_solar = math.exp(-0.5 * (diff_solar / 2.2) ** 2)
    
    score = (0.45 * sim_elev + 0.25 * sim_ps + 0.30 * sim_solar) * 100.0
    return round(float(np.clip(score, 0.0, 100.0)), 2)


def calculate_dimension_scores(site: Dict[str, Any], target_key: str = "lunar_south_pole") -> Dict[str, float]:
    """
    Calcula las puntuaciones individuales de las 6 dimensiones científicas [0.0 - 100.0].
    
    Args:
        site: Diccionario con las métricas del sitio terrestre.
        target_key: Identificador del perfil planetario objetivo.
        
    Returns:
        Diccionario con los 6 puntajes dimensionales.
    """
    target = get_planetary_target(target_key)
    if not target:
        raise ValueError(f"Perfil planetario desconocido: '{target_key}'")
        
    target_bm = target["analog_benchmark"]
    
    return {
        "cold_extreme": _calc_dim_cold_extreme(site, target_bm),
        "thermal_amplitude": _calc_dim_thermal_amplitude(site, target_bm),
        "aridity_soil": _calc_dim_aridity_soil(site, target_bm, target),
        "terrain_topography": _calc_dim_terrain_topography(site, target_bm),
        "aeolian_wind": _calc_dim_aeolian_wind(site, target_bm),
        "altitude_pressure_solar": _calc_dim_altitude_pressure_solar(site, target_bm)
    }


def _apply_coherence_penalty(
    row_dict: Dict[str, Any],
    target_key: str,
    base_score: float
) -> float:
    """
    Aplica penalizaciones de coherencia física según el objetivo espacial.

    - lunar_south_pole : penaliza fuertemente sitios cálidos (t2m_min > 0°C) o húmedos (prec > 250 mm).
                         Fuerza peso 0 en viento (en la Luna hay vacío).
    - mars_arcadia     : penaliza terrenos con slope > 10° o roughness > 25 m (no son mesetas).
    - mars_jezero      : penaliza zonas húmedas/lluviosas (aridity < 0.50 o prec > 300 mm).
    Cráteres de impacto en climas húmedos (prec > 350 mm): penalización ambiental adicional (-8 pts).
    """
    penalty = 0.0
    precip = _safe_float(row_dict.get("annual_precip_mm"), 0.0)
    aridity = _safe_float(row_dict.get("aridity_index"), 0.5)
    t2m_min = _safe_float(row_dict.get("t2m_min_ann"), 0.0)
    slope = _safe_float(row_dict.get("slope_deg"), 5.0)
    roughness = _safe_float(row_dict.get("roughness_m"), 10.0)
    geology = row_dict.get("geology_type", "")

    if target_key == "lunar_south_pole":
        # El Polo Sur Lunar exige frío extremo y sequía total
        if t2m_min is not None and t2m_min > 0.0:
            penalty += 18.0 + min(10.0, t2m_min * 0.8)   # Sitio demasiado cálido
        elif t2m_min is not None and t2m_min > -10.0:
            penalty += 8.0
        if precip is not None and precip > 250.0:
            # Penalización progresiva: +10 base + 1 pt por cada 100 mm extra
            penalty += 10.0 + min(15.0, (precip - 250.0) / 100.0 * 5.0)

    elif target_key == "mars_arcadia":
        # Arcadia Planitia es una llanura plana; los volcanes escarpados no sirven
        if slope is not None and slope > 10.0:
            penalty += 10.0 + min(12.0, (slope - 10.0) * 1.5)
        elif slope is not None and slope > 5.0:
            penalty += 5.0
        if roughness is not None and roughness > 25.0:
            penalty += 6.0 + min(8.0, (roughness - 25.0) / 10.0 * 3.0)
        # También penaliza ligeramente la humedad excesiva
        if precip is not None and precip > 350.0:
            penalty += 8.0

    elif target_key == "mars_jezero":
        # Jezero exige hiper-aridez; zonas húmedas son incoherentes ambientalmente
        if aridity is not None and aridity < 0.50:
            penalty += 20.0 + min(10.0, (0.50 - aridity) * 40.0)
        elif aridity is not None and aridity < 0.65:
            penalty += 8.0 + (0.65 - aridity) * 24.0
        if precip is not None and precip > 300.0:
            penalty += 10.0 + min(12.0, (precip - 300.0) / 100.0 * 4.0)

    # Cráteres de impacto en climas húmedos: solo valen por morfología, no por ambiente
    if geology == "impact_crater" and precip is not None and precip > 350.0:
        penalty += 8.0

    return round(float(np.clip(base_score - penalty, 0.0, 100.0)), 2)


def compute_similarity(
    site_row_or_df: Union[Dict[str, Any], pd.Series, pd.DataFrame],
    target_key: str = "lunar_south_pole",
    preset_or_weights: Union[str, Dict[str, float]] = "balanced"
) -> Union[Dict[str, Any], pd.DataFrame]:
    """
    Calcula la similitud global cuantitativa y por dimensiones para un sitio individual o un DataFrame.
    Aplica penalizaciones de coherencia física por objetivo para diferenciar claramente los 3 destinos.

    Args:
        site_row_or_df: Diccionario, Serie o DataFrame de pandas con los datos del/los sitio(s).
        target_key: Identificador del objetivo espacial ('lunar_south_pole', 'mars_arcadia', 'mars_jezero').
        preset_or_weights: Nombre de preset ('balanced', 'rover_mobility', etc.) o diccionario de pesos.

    Returns:
        Si recibe DataFrame: devuelve el DataFrame enriquecido con columnas de similitud y ranking.
        Si recibe dict o Series: devuelve un diccionario con overall_similarity y desglose dimensional.
    """
    target = get_planetary_target(target_key)
    if not target:
        raise ValueError(f"Perfil planetario no encontrado: '{target_key}'")

    # En la Luna no hay dinámica eólica: anulamos el peso del viento
    if isinstance(preset_or_weights, str):
        preset = MISSION_PRESETS.get(preset_or_weights, MISSION_PRESETS["balanced"])
        weights = dict(preset["weights"])  # copia para no mutar el preset
    elif isinstance(preset_or_weights, dict):
        weights = dict(preset_or_weights)
    else:
        weights = dict(MISSION_PRESETS["balanced"]["weights"])

    if target_key == "lunar_south_pole":
        # Fuerza peso eólico = 0 y redistribuye a frío y topografía
        aeolian_w = weights.pop("aeolian_wind", 0.12)
        weights["cold_extreme"] = weights.get("cold_extreme", 0.18) + aeolian_w * 0.6
        weights["terrain_topography"] = weights.get("terrain_topography", 0.18) + aeolian_w * 0.4
        weights["aeolian_wind"] = 0.0

    total_w = sum(weights.values()) or 1.0
    norm_weights = {k: v / total_w for k, v in weights.items()}
    target_geologies = target.get("target_geologies", [])

    def _score_single(row_dict: Dict[str, Any]) -> Dict[str, Any]:
        dim_scores = calculate_dimension_scores(row_dict, target_key)

        # Ponderación base de las 6 dimensiones
        weighted_sum = sum(dim_scores[dim] * norm_weights.get(dim, 1/6) for dim in dim_scores)

        # Ajuste por afinidad geológica
        geology = row_dict.get("geology_type")
        geo_bonus = 0.0
        if geology:
            if geology in target_geologies:
                geo_bonus = 4.0
            else:
                geo_bonus = -2.0

        pre_penalty_score = float(np.clip(weighted_sum + geo_bonus, 0.0, 100.0))

        # Penalizaciones de coherencia física por objetivo
        final_score = _apply_coherence_penalty(row_dict, target_key, pre_penalty_score)
        stress_idx = calculate_astrobiology_stress_index(row_dict)

        return {
            "overall_similarity": final_score,
            "dimension_scores": dim_scores,
            "geology_bonus": geo_bonus,
            "astrobiology_stress_index": stress_idx,
            "target_id": target_key
        }

    # Procesamiento si es DataFrame de pandas
    if isinstance(site_row_or_df, pd.DataFrame):
        df = site_row_or_df.copy()
        
        dim_cols = [
            "sim_cold_extreme", "sim_thermal_amplitude", "sim_aridity_soil",
            "sim_terrain_topography", "sim_aeolian_wind", "sim_altitude_pressure_solar"
        ]
        results_list = []
        for _, row in df.iterrows():
            row_dict = row.to_dict()
            res = _score_single(row_dict)
            dims = res["dimension_scores"]
            results_list.append({
                "sim_cold_extreme": dims["cold_extreme"],
                "sim_thermal_amplitude": dims["thermal_amplitude"],
                "sim_aridity_soil": dims["aridity_soil"],
                "sim_terrain_topography": dims["terrain_topography"],
                "sim_aeolian_wind": dims["aeolian_wind"],
                "sim_altitude_pressure_solar": dims["altitude_pressure_solar"],
                "astrobiology_stress_index": res["astrobiology_stress_index"],
                "geology_bonus": res["geology_bonus"],
                "overall_similarity": res["overall_similarity"]
            })
            
        res_df = pd.DataFrame(results_list, index=df.index)
        for col in res_df.columns:
            df[col] = res_df[col]
            
        df["rank"] = df["overall_similarity"].rank(ascending=False, method="min").astype(int)
        df = df.sort_values(by="overall_similarity", ascending=False)
        return df

    # Procesamiento si es pd.Series o Dict
    row_dict = site_row_or_df.to_dict() if isinstance(site_row_or_df, pd.Series) else dict(site_row_or_df)
    return _score_single(row_dict)


def generate_site_diagnosis(
    site_data: Dict[str, Any],
    target_key: str,
    dim_scores: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Genera un diagnóstico científico exhaustivo del análogo: fortalezas, limitaciones
    específicas e ineludibles (1G, atmósfera, magnetosfera) y ensayos recomendados.
    
    Args:
        site_data: Datos del sitio analizado.
        target_key: Perfil planetario evaluado.
        dim_scores: Puntajes dimensionales precalculados (opcional).
        
    Returns:
        Diccionario con 'strengths', 'limitations' y 'recommended_tests'.
    """
    target = get_planetary_target(target_key)
    if not target:
        raise ValueError(f"Perfil planetario no encontrado: '{target_key}'")
        
    if dim_scores is None:
        dim_scores = calculate_dimension_scores(site_data, target_key)
        
    strengths: List[str] = []
    limitations: List[str] = []
    recommended_tests: List[str] = []
    
    # 1. Evaluación de fortalezas según puntajes dimensionales
    if dim_scores["aridity_soil"] >= 75.0:
        strengths.append(
            f"Excelente hiper-aridez y regolito desecado (Score Suelo/Aridez: {dim_scores['aridity_soil']:.1f}%). "
            f"Humedad superficial mínima ({site_data.get('soil_wetness_ann', 'N/D')}) que emula el sustrato espacial anhidro."
        )
    if dim_scores["cold_extreme"] >= 70.0:
        strengths.append(
            f"Régimen térmico riguroso (Score Frío: {dim_scores['cold_extreme']:.1f}%). "
            f"Mínimas anuales de {site_data.get('t2m_min_ann', 'N/D')}°C aproximan el entorno criogénico de {target['body']}."
        )
    if dim_scores["terrain_topography"] >= 70.0:
        strengths.append(
            f"Topografía altamente representativa (Score Relieve: {dim_scores['terrain_topography']:.1f}%). "
            f"Pendiente ({site_data.get('slope_deg', 'N/D')}°) y rugosidad ({site_data.get('roughness_m', 'N/D')} m) ofrecen desafíos mecánicos realistas."
        )
    if dim_scores["thermal_amplitude"] >= 75.0:
        strengths.append(
            f"Fuerte estrés cíclico térmico ({site_data.get('thermal_amplitude_c', 'N/D')}°C de oscilación), "
            "ideal para pruebas de fatiga térmica en actuadores mecánicos y sellos poliméricos."
        )
    if dim_scores["altitude_pressure_solar"] >= 70.0:
        strengths.append(
            f"Elevada altitud ({site_data.get('elevation_m', 'N/D')} m) con radiación solar intensa ({site_data.get('allsky_sfc_sw_dwn_ann', 'N/D')} kWh/m²/día), "
            "optimizando la exposición UV/solar y minimizando la columna barométrica terrestre."
        )
        
    # Si ninguna dimensión superó 70, destacar la mejor
    if not strengths:
        best_dim = max(dim_scores, key=dim_scores.get)
        strengths.append(f"Su mayor afinidad radica en la dimensión '{best_dim}' ({dim_scores[best_dim]:.1f}% de similitud).")

    # 2. Limitaciones específicas de clima/suelo
    if dim_scores["cold_extreme"] < 50.0:
        limitations.append(
            f"Temperatura media anual ({site_data.get('ts_ann', 'N/D')}°C) considerablemente más cálida que los "
            f"{target['real_planetary_metrics']['mean_surface_temp_c']}°C reales del objetivo espacial."
        )
    if dim_scores["aridity_soil"] < 50.0:
        limitations.append(
            "Niveles de humedad atmosférica y edáfica terrestre superiores a los valores anhidros espaciales."
        )
        
    # 3. Limitaciones físicas universales ineludibles en la Tierra
    body_name = target["body"]
    g_target = target["real_planetary_metrics"]["surface_gravity_g"]
    p_target = target["real_planetary_metrics"]["atmospheric_pressure_kpa"]
    
    limitations.extend([
        f"Gravedad terrestre (1.00 G) vs {g_target:.2f} G en {body_name}: Los rovers y perforadores no experimentan la baja tracción ni la flotabilidad de regolito de baja gravedad.",
        f"Presión y atmósfera terrestre (~101 kPa, N2/O2) vs {p_target} kPa en {body_name}: La disipación convectiva de calor y el rozamiento aerodinámico distorsionan el comportamiento térmico en vacío o CO2 tenue.",
        "Blindaje magnetosférico terrestre: El campo geomagnético y la capa de ozono protegen al sitio terrestre de rayos cósmicos galácticos (GCR) y radiación solar ionizante no atenuada."
    ])

    # 4. Ensayos y protocolos recomendados para esta analogía
    if target_key == "lunar_south_pole":
        recommended_tests = [
            "Ensayos de movilidad en pendientes pronunciadas (>12°) con regolito suelto y simulación de ruedas elásticas Artemis.",
            "Validación de reflectancia óptica y navegación autónoma LiDAR en entornos de alto contraste luz/sombra permanente.",
            "Pruebas de perforación percusiva criogénica para extracción de núcleos de permafrost o hielo volátil.",
            "Ensayo de mitigación de abrasión por polvo regolítico en juntas rotativas y trajes EVA."
        ]
    elif target_key == "mars_arcadia":
        recommended_tests = [
            "Simulación de radar de penetración terrestre (GPR) para detección y mapeo volumétrico de hielo somero.",
            "Pruebas de aterrizaje vertical y sustentación de zapatas en regolito sedimentario plano con baja rugosidad.",
            "Ensayos de sistemas ISRU de extracción de agua a partir de horizontes permafrost someros.",
            "Evaluación de degradación por depósito de polvo eólico sobre paneles solares horizontales."
        ]
    else:  # mars_jezero
        recommended_tests = [
            "Navegación autónoma y evitación de obstáculos (AutoNav) en campos de cantos rodados y escarpes deltaicos.",
            "Calibración de instrumentos espectroscópicos de fluorescencia de rayos X y Raman (análogos a PIXL y SHERLOC).",
            "Muestreo y sellado de testigos de roca ígnea/basáltica y arcillas sedimentarias para retorno de muestras (MSR).",
            "Ensayos de abrasión y transporte eólico de arena sobre carcasas de instrumentación científica expuesta."
        ]
        
    return {
        "strengths": strengths,
        "limitations": limitations,
        "recommended_tests": recommended_tests
    }


def calculate_astrobiology_stress_index(site_data: Dict[str, Any]) -> float:
    """
    Calcula el índice de estrés astrobiológico (0.0 a 100.0) combinando
    radiación solar incidente, índice de aridez y amplitud térmica.
    """
    solar = _safe_float(site_data.get("allsky_sfc_sw_dwn_ann"), 5.0)
    aridity = _safe_float(site_data.get("aridity_index"), 0.5)
    thermal_amp = _safe_float(site_data.get("thermal_amplitude_c"), 20.0)
    
    score_solar = min(100.0, max(0.0, (solar / 7.5) * 100.0))
    score_aridity = min(100.0, max(0.0, aridity * 100.0))
    score_thermal = min(100.0, max(0.0, (thermal_amp / 40.0) * 100.0))
    
    composite = 0.35 * score_solar + 0.40 * score_aridity + 0.25 * score_thermal
    return round(float(np.clip(composite, 0.0, 100.0)), 1)


def explain_score_in_plain_spanish(
    site_data: Dict[str, Any],
    target_key: str,
    dim_scores: Dict[str, float]
) -> str:
    """
    Genera una explicación en español coloquial y riguroso de 2-3 frases
    detallando por qué obtuvo ese % exacto y por qué no llegó al 100%.
    """
    target = get_planetary_target(target_key)
    target_name = target["name"] if target else target_key.replace("_", " ").title()
    body_name = target["body"] if target else "el objetivo"
    
    sorted_dims = sorted(dim_scores.items(), key=lambda x: x[1], reverse=True)
    best_dim, best_score = sorted_dims[0]
    worst_dim, worst_score = sorted_dims[-1]
    
    dim_labels = {
        "cold_extreme": "régimen térmico criogénico",
        "thermal_amplitude": "gran amplitud térmica día/noche",
        "aridity_soil": "hiper-aridez y regolito desecado",
        "terrain_topography": "perfil topográfico de pendiente y rugosidad",
        "aeolian_wind": "dinámica de vientos y polvo",
        "altitude_pressure_solar": "baja presión atmosférica e intensa radiación solar"
    }
    
    t_min = site_data.get("t2m_min_ann", "N/D")
    t_mean = site_data.get("ts_ann", "N/D")
    elev = site_data.get("elevation_m", "N/D")
    aridity = site_data.get("aridity_index", "N/D")
    
    explanation_parts = []
    
    # Frase 1: Motor principal del porcentaje
    explanation_parts.append(
        f"Este análogo sobresale principalmente por su <strong>{dim_labels.get(best_dim, best_dim)}</strong> ({best_score:.1f}% de afinidad), "
        f"donde una aridez de {aridity} y una altitud de {elev} m proporcionan un banco de pruebas representativo para {body_name}."
    )
    
    # Frase 2: Principal factor limitante
    if worst_dim == "cold_extreme":
        tgt_t = target["real_planetary_metrics"]["mean_surface_temp_c"] if target else -60
        explanation_parts.append(
            f"No alcanza una puntuación superior porque sus temperaturas (media de {t_mean}°C y mínima de {t_min}°C) "
            f"son mucho más cálidas que los {tgt_t}°C reales de {target_name}."
        )
    elif worst_dim == "aridity_soil":
        explanation_parts.append(
            "Su principal limitación es la presencia de trazas de humedad en aire y suelo, superando la aridez absoluta del vacío espacial."
        )
    elif worst_dim == "terrain_topography":
        slope = site_data.get("slope_deg", "N/D")
        explanation_parts.append(
            f"El relieve presenta diferencias geométricas: su pendiente de {slope}° no replica con exactitud la topografía objetivo de {target_name}."
        )
    else:
        explanation_parts.append(
            f"La mayor divergencia se encuentra en '{dim_labels.get(worst_dim, worst_dim)}' ({worst_score:.1f}%), marcando el límite con el ambiente espacial."
        )
        
    # Frase 3: Física universal ineludible
    g_target = target["real_planetary_metrics"]["surface_gravity_g"] if target else 0.38
    explanation_parts.append(
        f"Adicionalmente, ningún sitio terrestre puede eliminar la gravedad de 1.00 G (frente a {g_target:.2f} G en {body_name}) ni el escudo magnético protector terrestre."
    )
    
    return " ".join(explanation_parts)


VARIABLE_GLOSSARY: Dict[str, Dict[str, str]] = {
    "albedo": {
        "title": "Albedo Superficial (ALLSKY_SRF_ALB)",
        "unit": "adimensional (0.0 a 1.0)",
        "definition": (
            "Indica qué fracción de la luz solar incidente es reflejada por el suelo. "
            "El basalto volcánico oscuro y el regolito lunar absorben gran parte de la radiación (albedo bajo ~0.12). "
            "En contraste, las arenas oxidadas brillantes y el polvo marciano reflejan más luz (~0.26)."
        )
    },
    "gwettop": {
        "title": "Humedad del Suelo Superficial (GWETTOP)",
        "unit": "adimensional (0.0 a 1.0)",
        "definition": (
            "Humedad volumétrica en los primeros 0 a 5 cm de la capa superficial del suelo. "
            "En la Luna y Marte el regolito es absolutamente anhidro (0.00). "
            "En la Tierra, los desiertos hiper-áridos extremos (como Atacama o Lut) alcanzan valores inferiores a 0.10."
        )
    },
    "ps_kpa": {
        "title": "Presión Atmosférica Superficial (PS)",
        "unit": "kilopascales (kPa)",
        "definition": (
            "Fuerza que ejerce la atmósfera sobre la superficie terrestre (a nivel del mar es ~101.3 kPa). "
            "La Luna posee un vacío casi absoluto (10⁻¹¹ kPa) y Marte una atmósfera extremadamente tenue (~0.6-0.8 kPa). "
            "Los altiplanos y cumbres volcánicas terrestres (>4.500 m) alcanzan entre 45 y 60 kPa, reduciendo la columna de aire."
        )
    },
    "thermal_amplitude": {
        "title": "Amplitud Térmica Anual",
        "unit": "grados Celsius (°C)",
        "definition": (
            "Diferencia entre la temperatura máxima y mínima anual (T2M_MAX - T2M_MIN). "
            "En el espacio, al no haber vapor de agua ni vegetación amortiguadora, los cuerpos celestes sufren cambios térmicos brutales "
            "(>30°C a >150°C), sometiendo a rovers y trajes a severa fatiga térmica por dilatación y contracción."
        )
    },
    "slope_deg": {
        "title": "Pendiente Topográfica (Método de Horn)",
        "unit": "grados sexagesimales (°)",
        "definition": (
            "Inclinación calculada sobre una cuadrícula 3x3 de elevaciones teniendo en cuenta la curvatura terrestre. "
            "Pendientes suaves (<4°) son ideales para aterrizaje seguro (como Arcadia Planitia), mientras que pendientes "
            "pronunciadas (>12°) replican las murallas de cráteres de impacto y escarpes deltaicos."
        )
    },
    "roughness_m": {
        "title": "Rugosidad del Terreno",
        "unit": "metros (m)",
        "definition": (
            "Desviación estándar de las elevaciones en un radio de ~550 m. Cuantifica la presencia de peñascos, "
            "crestas rocosas y micro-barrancos. Esencial para evaluar el riesgo de vuelco y la tracción de ruedas."
        )
    },
    "aridity_index": {
        "title": "Índice de Aridez Cuantitativo",
        "unit": "escala normalizada (0.0 a 1.0)",
        "definition": (
            "Calculado combinando la precipitación media diaria y la humedad relativa a 2 m. "
            "0.0 representa selvas hiper-húmedas, mientras que valores >0.85 indican hiper-aridez extrema análoga a la ausencia de agua libre en Marte y la Luna."
        )
    },
    "astrobiology_stress": {
        "title": "Índice de Estrés Astrobiológico",
        "unit": "escala 0 a 100",
        "definition": (
            "Medida combinada de hostilidad ambiental para la biología terrestre: integra radiación solar/UV incidente, "
            "desecación extrema y choque por oscilaciones térmicas. Cuanto más alto, más estéril y desafiante es el hábitat."
        )
    }
}
