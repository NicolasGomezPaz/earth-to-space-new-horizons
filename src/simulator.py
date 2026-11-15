"""
Earth To Space: New Horizons - Engineering Experiment Simulator
===============================================================
Módulo de simulación física de experimentos de ingeniería espacial en análogos terrestres.
Permite comparar métricas de movilidad de rover, presupuesto solar y ventanas óptimas
de campaña entre las condiciones terrestres del sitio análogo y las condiciones reales
del objetivo espacial (Luna o Marte).

Física implementada:
  - Gravedad real: Luna 1.62 m/s² (0.165 G) · Marte 3.72 m/s² (0.38 G) · Tierra 9.81 m/s²
  - Solar Irradiance Marte Jezero  ~3.1 kWh/m²/día (latitud baja, polvo moderado)
  - Solar Irradiance Marte Arcadia ~2.1 kWh/m²/día (latitud media, polvo alto)
  - Solar Irradiance Polo Sur Lunar ~3.8 kWh/m²/día promedio en crestas iluminadas de Shackleton
    (paneles verticales/inclinados, ciclos dia/noche prolongados, 0 en sombra permanente)
"""

import math
from typing import Dict, Any, List, Optional, Tuple

MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
MONTH_LABELS_ES = {
    "JAN": "Ene", "FEB": "Feb", "MAR": "Mar", "APR": "Abr",
    "MAY": "May", "JUN": "Jun", "JUL": "Jul", "AUG": "Ago",
    "SEP": "Sep", "OCT": "Oct", "NOV": "Nov", "DEC": "Dic"
}

# Constantes físicas y planetarias
GRAVITY = {
    "earth":           9.81,   # m/s²
    "lunar_south_pole": 1.62,  # m/s² (0.165 G) — LRO Diviner
    "mars_arcadia":     3.72,  # m/s² (0.38 G)
    "mars_jezero":      3.72,  # m/s² (0.38 G) — MEDA Perseverance
}

# Irradiancia solar de referencia en el objetivo [kWh/m²/día]
SOLAR_REFERENCE = {
    "lunar_south_pole": 3.8,   # Crestas iluminadas de Shackleton (paneles verticales, 1361 W/m² × ángulo rasante × duty cycle)
    "mars_arcadia":     2.1,   # MRO/Mars Odyssey: latitud ~40°N, ángulo bajo, polvo atmosférico alto
    "mars_jezero":      3.1,   # MEDA in-situ: latitud ~18°N, polvo moderado, tau ~0.6
}

# Factor de pérdida por polvo eólico en paneles (reducción por m/s de viento > umbral)
DUST_LOSS_FACTOR_PER_MS = 0.012   # ~1.2% de pérdida adicional por cada m/s sobre 3 m/s de viento

# Rolling resistance coeff. por rugosidad (adimensional, escala empírica de terrenos simulados)
def _rolling_resistance(roughness_m: float) -> float:
    """Estima el coeficiente de resistencia al rodamiento según rugosidad del terreno (std dev elevaciones)."""
    # Regolito fino < 5 m → Cr ~ 0.05; lava/cráter rugoso > 50 m → Cr ~ 0.25
    base = 0.05
    extra = min(0.20, (roughness_m / 60.0) * 0.20)
    return round(base + extra, 4)


def simulate_rover_mobility(
    rover_mass_kg: float,
    slope_deg: float,
    roughness_m: float,
    target_key: str,
    speed_ms: float = 0.2
) -> Dict[str, Any]:
    """
    Simula la movilidad de un rover en Tierra vs el objetivo espacial elegido.

    Calcula fuerzas, potencia mecánica y masa equivalente de prueba en Tierra para
    replicar con fidelidad el comportamiento en baja gravedad.

    Args:
        rover_mass_kg : Masa del rover en kg (referencia diseño).
        slope_deg     : Pendiente del terreno en grados sexagesimales.
        roughness_m   : Rugosidad del terreno (std dev de elevaciones en ~550 m, metros).
        target_key    : 'lunar_south_pole', 'mars_arcadia' o 'mars_jezero'.
        speed_ms      : Velocidad de desplazamiento en m/s (por defecto 0.20 m/s = 12 m/min).

    Returns:
        Diccionario con métricas en Tierra y en el objetivo, plus recomendaciones.
    """
    g_target = GRAVITY.get(target_key, 3.72)
    g_earth  = GRAVITY["earth"]
    theta    = math.radians(max(0.0, min(slope_deg, 85.0)))
    Cr       = _rolling_resistance(roughness_m)

    # --- Fuerzas en Tierra (rover como fue diseñado, masa real) ---
    F_slope_earth  = rover_mass_kg * g_earth * math.sin(theta)          # N
    F_roll_earth   = rover_mass_kg * g_earth * math.cos(theta) * Cr     # N
    F_total_earth  = F_slope_earth + F_roll_earth                        # N
    P_earth        = F_total_earth * speed_ms                            # W

    # --- Fuerzas en el objetivo (mismo rover, gravedad real del planeta) ---
    F_slope_target = rover_mass_kg * g_target * math.sin(theta)
    F_roll_target  = rover_mass_kg * g_target * math.cos(theta) * Cr
    F_total_target = F_slope_target + F_roll_target
    P_target       = F_total_target * speed_ms

    # --- Masa equivalente de prueba en Tierra ---
    # La masa que, sometida a la gravedad terrestre, produce la misma fuerza total que el rover en el objetivo.
    gravity_ratio  = g_target / g_earth
    mass_equiv     = rover_mass_kg * gravity_ratio   # kg — rover reducido para test en Tierra

    # Fracción de peso que hay que colgar/contrarrestar en un arnés de offload
    offload_kg     = rover_mass_kg - mass_equiv       # kg a contrarrestar
    offload_pct    = (1.0 - gravity_ratio) * 100.0   # %

    # Energía por metro de desplazamiento (J/m)
    energy_per_m_earth  = F_total_earth   # J/m (fuerza × distancia)
    energy_per_m_target = F_total_target

    target_name = {
        "lunar_south_pole": "Polo Sur Lunar",
        "mars_arcadia": "Marte · Arcadia Planitia",
        "mars_jezero": "Marte · Cráter Jezero"
    }.get(target_key, target_key)

    return {
        "target_name": target_name,
        "g_target_ms2": g_target,
        "g_ratio": round(gravity_ratio, 4),
        "slope_deg": round(slope_deg, 2),
        "roughness_m": round(roughness_m, 2),
        "rolling_resistance_coeff": Cr,
        "speed_ms": speed_ms,

        # Tierra (rover completo)
        "earth": {
            "force_slope_N": round(F_slope_earth, 2),
            "force_rolling_N": round(F_roll_earth, 2),
            "force_total_N": round(F_total_earth, 2),
            "power_W": round(P_earth, 2),
            "energy_per_m_J": round(energy_per_m_earth, 2),
        },

        # Objetivo espacial (mismo rover)
        "target": {
            "force_slope_N": round(F_slope_target, 2),
            "force_rolling_N": round(F_roll_target, 2),
            "force_total_N": round(F_total_target, 2),
            "power_W": round(P_target, 2),
            "energy_per_m_J": round(energy_per_m_target, 2),
        },

        # Configuración de test en Tierra para replicar misión
        "earth_test": {
            "equivalent_mass_kg": round(mass_equiv, 1),
            "offload_mass_kg": round(offload_kg, 1),
            "offload_pct": round(offload_pct, 1),
            "note": (
                f"Para replicar la tracción real en {target_name}, el banco de pruebas en Tierra debe "
                f"usar un arnés de descarga gravitacional que contrarreste {offload_kg:.1f} kg "
                f"({offload_pct:.1f}% del peso) del rover, dejando una masa efectiva de {mass_equiv:.1f} kg."
            )
        },

        "interpretation": (
            f"En {target_name} (g = {g_target} m/s²), el rover de {rover_mass_kg:.0f} kg "
            f"necesita {P_target:.1f} W para moverse a {speed_ms:.2f} m/s con {slope_deg:.1f}° de pendiente. "
            f"En Tierra, con la misma pendiente, consumiría {P_earth:.1f} W — "
            f"{'un' if P_earth > P_target else 'solo el'} "
            f"{abs(P_earth / max(P_target, 0.01) - 1)*100:.0f}% {'más' if P_earth > P_target else 'menos'}."
        )
    }


def simulate_solar_budget(
    seasonality_site: Dict[str, Any],
    panel_area_m2: float,
    efficiency_pct: float,
    daily_load_wh: float,
    target_key: str,
    wind_ms: float = 4.0
) -> Dict[str, Any]:
    """
    Simula el presupuesto de energía solar mensual en el sitio terrestre y compara
    con la referencia del objetivo espacial.

    Usa los 12 meses reales de ALLSKY_SFC_SW_DWN del sitio (kWh/m²/día) con factor
    de pérdida por polvo eólico y eficiencia del panel.

    Args:
        seasonality_site : Diccionario mensual del sitio (campo 'ALLSKY_SFC_SW_DWN').
        panel_area_m2    : Área total de paneles solares en m².
        efficiency_pct   : Eficiencia de conversión del panel (%).
        daily_load_wh    : Consumo diario objetivo de la misión en Wh/día.
        target_key       : 'lunar_south_pole', 'mars_arcadia' o 'mars_jezero'.
        wind_ms          : Velocidad media anual del viento en m/s (influye en acumulación de polvo).

    Returns:
        Diccionario con balance mensual, mejor mes y análisis comparativo.
    """
    eff = efficiency_pct / 100.0

    # Factor de pérdida por polvo eólico en Tierra: vientos fuertes acumulan más polvo
    dust_loss_earth = 0.0
    if wind_ms > 3.0:
        dust_loss_earth = min(0.20, (wind_ms - 3.0) * DUST_LOSS_FACTOR_PER_MS)
    effective_factor_earth = eff * (1.0 - dust_loss_earth)

    # Referencia solar del objetivo [kWh/m²/día]
    solar_ref_target = SOLAR_REFERENCE.get(target_key, 3.0)

    # Polvo marciano: pérdida adicional fija ~15% (tau=0.6 promedio MEDA)
    # Luna: sin atmósfera, sin polvo eólico — solo factor panel inclinado ~5% pérdida reflexión
    target_dust_loss = {
        "lunar_south_pole": 0.05,
        "mars_arcadia":     0.18,
        "mars_jezero":      0.14,
    }.get(target_key, 0.15)

    effective_factor_target = eff * (1.0 - target_dust_loss)

    # Energía diaria de referencia en el objetivo [Wh/día]
    daily_target_wh = solar_ref_target * panel_area_m2 * effective_factor_target * 1000.0

    # Balance mensual en Tierra
    solar_months = seasonality_site.get("ALLSKY_SFC_SW_DWN", {})
    monthly_earth_wh = {}
    monthly_balance_wh = {}
    best_month_key = None
    best_month_wh = -1e9
    worst_month_key = None
    worst_month_wh = 1e9

    for m in MONTHS:
        solar_kwh = solar_months.get(m, 0.0)
        # Generación diaria Tierra [Wh/día]
        gen_wh = solar_kwh * panel_area_m2 * effective_factor_earth * 1000.0
        balance = gen_wh - daily_load_wh
        monthly_earth_wh[m] = round(gen_wh, 1)
        monthly_balance_wh[m] = round(balance, 1)

        if gen_wh > best_month_wh:
            best_month_wh = gen_wh
            best_month_key = m
        if gen_wh < worst_month_wh:
            worst_month_wh = gen_wh
            worst_month_key = m

    # Mes cuya generación terrestre más se aproxima a la referencia del objetivo
    analog_month_key = min(
        MONTHS,
        key=lambda m: abs(monthly_earth_wh[m] - daily_target_wh)
    )

    target_name = {
        "lunar_south_pole": "Polo Sur Lunar (crestas iluminadas Shackleton)",
        "mars_arcadia":     "Marte · Arcadia Planitia",
        "mars_jezero":      "Marte · Cráter Jezero (MEDA in-situ)",
    }.get(target_key, target_key)

    surplus_months = [m for m in MONTHS if monthly_balance_wh[m] >= 0]
    deficit_months = [m for m in MONTHS if monthly_balance_wh[m] < 0]

    return {
        "target_name": target_name,
        "panel_area_m2": panel_area_m2,
        "efficiency_pct": efficiency_pct,
        "daily_load_wh": daily_load_wh,
        "dust_loss_earth_pct": round(dust_loss_earth * 100, 1),
        "dust_loss_target_pct": round(target_dust_loss * 100, 1),
        "solar_ref_target_kwh_m2_day": solar_ref_target,
        "daily_target_wh": round(daily_target_wh, 1),
        "monthly_earth_wh": monthly_earth_wh,
        "monthly_balance_wh": monthly_balance_wh,
        "best_month": best_month_key,
        "best_month_wh": round(best_month_wh, 1),
        "worst_month": worst_month_key,
        "worst_month_wh": round(worst_month_wh, 1),
        "analog_month": analog_month_key,
        "analog_month_wh": round(monthly_earth_wh[analog_month_key], 1),
        "surplus_months": surplus_months,
        "deficit_months": deficit_months,
        "months_labels": {m: MONTH_LABELS_ES[m] for m in MONTHS},
        "interpretation": (
            f"El sistema de {panel_area_m2} m² × {efficiency_pct}% eficiencia genera en {target_name} "
            f"aproximadamente {daily_target_wh:.0f} Wh/día (con {target_dust_loss*100:.0f}% de pérdida por polvo/ángulo). "
            f"En el sitio terrestre, el mes que mejor replica ese nivel energético es "
            f"**{MONTH_LABELS_ES[analog_month_key]}** ({monthly_earth_wh[analog_month_key]:.0f} Wh/día)."
        )
    }


def find_optimal_experiment_window(
    seasonality_site: Dict[str, Any],
    experiment_type: str
) -> Dict[str, Any]:
    """
    Evalúa los 12 meses del sitio para determinar la ventana óptima de campaña
    de ingeniería según el tipo de experimento.

    Args:
        seasonality_site : Datos mensuales del sitio (TS, T2M_MIN, WS10M, ALLSKY_SFC_SW_DWN).
        experiment_type  : Uno de:
                           'cryogenic'     → Pruebas Criogénicas y Baterías
                           'rover_mobility'→ Movilidad Autónoma de Rover
                           'solar_dust'    → Energía Solar y Mitigación de Polvo
                           'eva_human'     → Operaciones Humanas (EVA)

    Returns:
        Diccionario con ranking de meses, mes/trimestre óptimo y justificación.
    """
    ts_m    = seasonality_site.get("TS", {})
    t_min_m = seasonality_site.get("T2M_MIN", {})
    ws_m    = seasonality_site.get("WS10M", {})
    sol_m   = seasonality_site.get("ALLSKY_SFC_SW_DWN", {})

    scores: Dict[str, float] = {}

    for m in MONTHS:
        ts    = ts_m.get(m, 0.0)
        t_min = t_min_m.get(m, 0.0)
        wind  = ws_m.get(m, 3.0)
        solar = sol_m.get(m, 5.0)

        if experiment_type == "cryogenic":
            # Prioriza meses más fríos y secos; penaliza viento alto (mezcla polvo en instrumentos)
            score = (-ts * 1.5) + (-t_min * 2.0) + (-wind * 0.5)

        elif experiment_type == "rover_mobility":
            # Prioriza meses sin extremo de frío ni calor; viento moderado; visibilidad
            temp_penalty = abs(ts - 10.0)   # Óptimo ~10°C para electrónica
            score = (-temp_penalty * 1.0) + (-wind * 0.8) + (solar * 0.3)

        elif experiment_type == "solar_dust":
            # Prioriza máxima irradiancia solar, tolera viento moderado (simula transporte de polvo)
            score = (solar * 2.5) + (-abs(wind - 5.0) * 0.5)

        elif experiment_type == "eva_human":
            # Rango de temperatura habitable para operaciones con traje EVA simulado:
            # Óptimo entre -10°C y +15°C. Penaliza extremos y viento > 7 m/s.
            if ts < -15.0:
                temp_score = ts + 15.0        # negativo cuando ts muy frío
            elif ts > 20.0:
                temp_score = -(ts - 20.0)     # negativo cuando muy caliente
            else:
                temp_score = 15.0 - abs(ts - 5.0)  # máximo cerca de 5°C
            wind_score = -max(0.0, wind - 7.0) * 2.0
            score = temp_score + wind_score + (solar * 0.2)

        else:
            score = solar   # Fallback: máxima irradiancia

        scores[m] = round(score, 3)

    ranked = sorted(MONTHS, key=lambda m: scores[m], reverse=True)
    optimal_month = ranked[0]
    optimal_quarter_months = ranked[:3]

    exp_labels = {
        "cryogenic":      "Pruebas Criogénicas y Baterías",
        "rover_mobility": "Movilidad Autónoma de Rover",
        "solar_dust":     "Energía Solar y Mitigación de Polvo",
        "eva_human":      "Operaciones Humanas (EVA)",
    }

    justifications = {
        "cryogenic": (
            f"El mes óptimo es **{MONTH_LABELS_ES[optimal_month]}**, con la temperatura superficial "
            f"más baja del año ({ts_m.get(optimal_month, 'N/D')} °C media, "
            f"{t_min_m.get(optimal_month, 'N/D')} °C mínima), maximizando el estrés criogénico "
            f"sobre baterías, lubricantes y sellados poliméricos."
        ),
        "rover_mobility": (
            f"El mes óptimo es **{MONTH_LABELS_ES[optimal_month]}** "
            f"(T° media {ts_m.get(optimal_month, 'N/D')} °C, viento {ws_m.get(optimal_month, 'N/D')} m/s), "
            f"que combina condiciones térmicas tolerables para electrónica y visibilidad suficiente."
        ),
        "solar_dust": (
            f"El mes óptimo es **{MONTH_LABELS_ES[optimal_month]}** "
            f"({sol_m.get(optimal_month, 'N/D')} kWh/m²/día, viento {ws_m.get(optimal_month, 'N/D')} m/s), "
            f"con el mayor flujo solar del año para maximizar la generación fotovoltaica "
            f"y estudiar la tasa de acumulación de polvo eólico sobre paneles horizontales."
        ),
        "eva_human": (
            f"El mes óptimo es **{MONTH_LABELS_ES[optimal_month]}** "
            f"(T° media {ts_m.get(optimal_month, 'N/D')} °C, viento {ws_m.get(optimal_month, 'N/D')} m/s), "
            f"que representa el entorno más habitable para un operador con traje EVA análogo "
            f"sin llegar a extremos de hipotermia ni golpe de calor."
        ),
    }

    return {
        "experiment_type": experiment_type,
        "experiment_label": exp_labels.get(experiment_type, experiment_type),
        "scores_by_month": scores,
        "ranked_months": ranked,
        "optimal_month": optimal_month,
        "optimal_month_label": MONTH_LABELS_ES[optimal_month],
        "optimal_quarter": [MONTH_LABELS_ES[m] for m in optimal_quarter_months],
        "worst_month": ranked[-1],
        "worst_month_label": MONTH_LABELS_ES[ranked[-1]],
        "justification": justifications.get(experiment_type, ""),
        "monthly_data_summary": {
            m: {
                "ts": ts_m.get(m, None),
                "t_min": t_min_m.get(m, None),
                "wind": ws_m.get(m, None),
                "solar": sol_m.get(m, None),
                "score": scores[m]
            }
            for m in MONTHS
        }
    }


def build_seasonality_from_site_row(site_row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Reconstruye una estructura de estacionalidad mensual mínima desde un sitio evaluado en vivo
    (donde solo se tienen valores anuales, no la serie mensual completa).

    Genera una aproximación sinusoidal hemisférica para temperatura y usa valores constantes
    para viento y solar, de modo que el simulador no quede bloqueado con sitios en vivo.

    Args:
        site_row: Diccionario de métricas anuales del sitio evaluado en vivo.

    Returns:
        Diccionario de estacionalidad mensual sintética, o None si faltan datos básicos.
    """
    ts_ann   = site_row.get("ts_ann")
    t_min    = site_row.get("t2m_min_ann")
    t_max    = site_row.get("t2m_max_ann")
    wind_ann = site_row.get("ws10m_ann", 4.0)
    solar_ann= site_row.get("allsky_sfc_sw_dwn_ann", 5.5)
    lat      = site_row.get("latitude", 0.0)

    if ts_ann is None or t_min is None or t_max is None:
        return None

    amplitude = (t_max - t_min) / 2.0
    mean_t    = (t_max + t_min) / 2.0

    # En el hemisferio sur el verano cae en Dic/Ene/Feb
    phase_offset = 0 if (lat is not None and lat >= 0) else math.pi

    ts_monthly   = {}
    tmin_monthly = {}
    tmax_monthly = {}
    ws_monthly   = {}
    sol_monthly  = {}

    for i, m in enumerate(MONTHS):
        # Ángulo del ciclo estacional (periodo 12 meses)
        angle = (2 * math.pi * i / 12.0) + phase_offset
        t_surface   = mean_t - amplitude * math.cos(angle)
        t_min_m     = t_surface - amplitude * 0.6
        t_max_m     = t_surface + amplitude * 0.4
        solar_m     = solar_ann * (1.0 + 0.25 * math.cos(angle + math.pi))  # inverso a T (más solar en verano NH)

        ts_monthly[m]   = round(t_surface, 2)
        tmin_monthly[m] = round(t_min_m, 2)
        tmax_monthly[m] = round(t_max_m, 2)
        ws_monthly[m]   = round(float(wind_ann), 2)
        sol_monthly[m]  = round(max(0.5, solar_m), 2)

    return {
        "TS": ts_monthly,
        "T2M_MIN": tmin_monthly,
        "T2M_MAX": tmax_monthly,
        "WS10M": ws_monthly,
        "ALLSKY_SFC_SW_DWN": sol_monthly,
        "_synthetic": True  # Bandera para avisar en la UI que son datos sintéticos
    }
