"""
Earth To Space: New Horizons - Environmental Analysis Module (EN / ES)
======================================================================
Módulo independiente y bilingüe para evaluar dinámica hídrica, erosión eólica,
balance radiativo-albedo y sensibilidad ambiental / protección planetaria (COSPAR)
usando los datos reales de NASA POWER y Copernicus DEM.
"""

from typing import Dict, Any
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
MONTH_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONTH_ES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


def _txt(en: str, es: str, lang: str) -> str:
    return en if lang == "en" else es


def _classify_environmental_sensitivity(site: Dict[str, Any], lang: str) -> Dict[str, str]:
    geo = site.get("geology_type", "")
    aridity = float(site.get("aridity_index") or 0.5)
    t_min = float(site.get("t2m_min_ann") or 0.0)
    wind = float(site.get("ws10m_ann") or 3.0)

    if geo == "permafrost" or t_min < -10.0:
        return {
            "level": _txt("HIGH — Cryogenic Permafrost Sensitivity", "ALTA — Sensibilidad Criogénica / Permafrost", lang),
            "note": _txt(
                "Frozen ground and ice-rich horizons are vulnerable to thermal disturbance from base camps and drilling rigs. Strict thermal insulation and zero-spill containment required.",
                "Los horizontes congelados y ricos en hielo son vulnerables a perturbaciones térmicas por campamentos y taladros. Requiere aislamiento térmico estricto y contención cero derrames.",
                lang
            )
        }
    if geo == "evaporite_salar":
        return {
            "level": _txt("HIGH — Fragile Evaporite Crust & Extremophile Habitat", "ALTA — Costra Salinas Frágil y Hábitat Extremófilo", lang),
            "note": _txt(
                "High-altitude salt flats host unique microbial mats and endolithic biosignatures. Wheeled rover tests must follow Leave-No-Trace corridors and COSPAR bioburden controls.",
                "Los salares de altura albergan tapetes microbianos únicos y biofirmas endolíticas. Las pruebas con rovers deben seguir corredores de mínimo impacto y control biológico COSPAR.",
                lang
            )
        }
    if aridity >= 0.80:
        return {
            "level": _txt("MODERATE-HIGH — Hyper-Arid Desert Soil & Dust Mobilization", "MEDIA-ALTA — Suelo Hiperárido y Movilización de Polvo", lang),
            "note": _txt(
                "Fragile desert pavements recover slowly from vehicle tracks; wind speeds above 4 m/s increase fine-particulate aerosol suspension during rover operations.",
                "Los pavimentos desérticos frágiles tardan décadas en recuperarse de las huellas; vientos >4 m/s elevan la suspensión de polvo fino durante las operaciones.",
                lang
            )
        }
    return {
        "level": _txt("MODERATE — Standard Field Analog Stewardship", "MEDIA — Manejo Estándar de Campo", lang),
        "note": _txt(
            f"Wind regime ({wind:.1f} m/s) and local geology require routine dust-suppression and waste-management protocols during multi-week instrumentation campaigns.",
            f"El régimen de viento ({wind:.1f} m/s) y la geología local requieren protocolos estándar de control de polvo y gestión de residuos durante campañas de instrumentación.",
            lang
        )
    }


def render_environmental_tab(
    scored_df: pd.DataFrame,
    seasonality_base: Dict[str, Any],
    selected_site_name: str,
    lang: str = "en"
) -> None:
    """Renderiza la pestaña completa de Análisis Ambiental en el idioma activo."""
    st.markdown(_txt(
        "#### 🌿 Environmental Analysis & Planetary Protection Assessment",
        "#### 🌿 Análisis Ambiental y Evaluación de Protección Planetaria",
        lang
    ))
    st.caption(_txt(
        "Evaluates water balance, soil moisture dynamics, aeolian dust erosion risk, surface albedo energy exchange, and field sustainability protocols using NASA POWER telemetry.",
        "Evalúa el balance hídrico, dinámica de humedad del suelo, riesgo de erosión eólica, intercambio radiativo por albedo y sostenibilidad en campo con telemetría NASA POWER.",
        lang
    ))

    sites = scored_df["name"].tolist()
    default_idx = sites.index(selected_site_name) if selected_site_name in sites else 0
    env_site_name = st.selectbox(
        _txt("📍 Select site for environmental diagnostics:", "📍 Selecciona el sitio para diagnóstico ambiental:", lang),
        options=sites,
        index=default_idx,
        key="env_tab_site_selector"
    )
    site = scored_df[scored_df["name"] == env_site_name].iloc[0].to_dict()

    precip_yr = float(site.get("annual_precip_mm") or 0.0)
    rh = float(site.get("rh2m_ann") or 0.0)
    soil_w = float(site.get("soil_wetness_ann") or 0.0)
    wind = float(site.get("ws10m_ann") or 0.0)
    albedo = float(site.get("surface_albedo_ann") or 0.2)
    solar = float(site.get("allsky_sfc_sw_dwn_ann") or 0.0)
    ps_kpa = float(site.get("ps_ann") or 101.3)

    # Clasificación rápida de riesgo eólico y radiación absorbida
    dust_risk = (
        _txt("High", "Alto", lang) if wind >= 5.5
        else (_txt("Moderate", "Moderado", lang) if wind >= 3.0 else _txt("Low", "Bajo", lang))
    )
    absorbed_solar = round(solar * (1.0 - albedo), 2)

    # --- 1. KPIs AMBIENTALES ---
    with st.container(border=True):
        e1, e2, e3, e4 = st.columns(4)
        e1.metric(
            _txt("Annual Precipitation", "Precipitación Anual", lang),
            f"{precip_yr:.1f} mm/yr",
            _txt(f"Rel. Humidity: {rh:.1f}%", f"Humedad Rel.: {rh:.1f}%", lang)
        )
        e2.metric(
            _txt("Topsoil Moisture (0–5 cm)", "Humedad Suelo (0–5 cm)", lang),
            f"{soil_w:.2f}",
            _txt("Anhydrous (<0.10)" if soil_w < 0.1 else "Semi-moist", "Anhidro (<0.10)" if soil_w < 0.1 else "Semihúmedo", lang)
        )
        e3.metric(
            _txt("Aeolian Dust / Erosion Risk", "Riesgo Eólico / Polvo", lang),
            dust_risk,
            f"{wind:.2f} m/s @ 10m"
        )
        e4.metric(
            _txt("Net Absorbed Solar Flux", "Flujo Solar Neto Absorbido", lang),
            f"{absorbed_solar} kWh/m²/d",
            f"Albedo: {albedo:.2f} · {ps_kpa:.1f} kPa"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # --- 2. DINÁMICA AMBIENTAL MENSUAL (12 MESES) ---
    col_env_l, col_env_r = st.columns([0.55, 0.45])
    site_seas = seasonality_base.get(env_site_name) or site.get("seasonality") or {}

    with col_env_l:
        with st.container(border=True):
            st.markdown(_txt(
                "**💧 Monthly Water, Soil Wetness & Wind Dynamics (12 Months)**",
                "**💧 Dinámica Mensual de Agua, Humedad de Suelo y Viento (12 Meses)**",
                lang
            ))
            if site_seas and ("PRECTOTCORR" in site_seas or "WS10M" in site_seas):
                m_labels = MONTH_EN if lang == "en" else MONTH_ES
                precip_m = [float(site_seas.get("PRECTOTCORR", {}).get(m, 0.0)) * 30.4 for m in MONTHS]
                soil_m = [float(site_seas.get("GWETTOP", {}).get(m, soil_w)) for m in MONTHS]
                wind_m = [float(site_seas.get("WS10M", {}).get(m, wind)) for m in MONTHS]

                fig_env = go.Figure()
                fig_env.add_trace(go.Bar(
                    x=m_labels, y=precip_m,
                    name=_txt("Monthly Precip. (mm)", "Precipitación Mensual (mm)", lang),
                    marker_color="#38BDF8", opacity=0.75
                ))
                fig_env.add_trace(go.Scatter(
                    x=m_labels, y=wind_m, mode="lines+markers",
                    name=_txt("Wind Speed (m/s)", "Viento (m/s)", lang),
                    line=dict(color="#F59E0B", width=2.5), yaxis="y2"
                ))
                fig_env.add_trace(go.Scatter(
                    x=m_labels, y=[s * 100 for s in soil_m], mode="lines",
                    name=_txt("Soil Wetness (%)", "Humedad Suelo (%)", lang),
                    line=dict(color="#10B981", width=2, dash="dot"), yaxis="y2"
                ))
                fig_env.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(15, 28, 54, 0.4)",
                    height=330,
                    margin=dict(l=10, r=20, t=20, b=10),
                    legend=dict(orientation="h", y=-0.18),
                    yaxis=dict(title=_txt("Precipitation (mm/mo)", "Precipitación (mm/mes)", lang)),
                    yaxis2=dict(title=_txt("Wind (m/s) & Soil (%)", "Viento (m/s) y Suelo (%)", lang), overlaying="y", side="right")
                )
                st.plotly_chart(fig_env, width="stretch")
            else:
                st.info(_txt(
                    "Full 12-month environmental series is available for the 50 catalog sites. Live points show annual averages above.",
                    "La serie mensual completa de 12 meses está disponible para los 50 sitios del catálogo. Arriba ves los promedios anuales.",
                    lang
                ))

    with col_env_r:
        with st.container(border=True):
            st.markdown(_txt(
                "**🛡️ Field Environmental Stewardship & COSPAR Guidelines**",
                "**🛡️ Impacto Ambiental en Campo y Guías COSPAR**",
                lang
            ))
            sens = _classify_environmental_sensitivity(site, lang)
            st.warning(f"**{sens['level']}**")
            st.markdown(sens["note"])
            st.markdown("---")
            st.markdown(_txt("**Key Environmental Indicators:**", "**Indicadores Ambientales Clave:**", lang))
            st.markdown(f"• **{_txt('Aridity Index', 'Índice de Aridez', lang)}:** `{site.get('aridity_index', 'N/D')}`")
            st.markdown(f"• **{_txt('Thermal Stress Swing', 'Oscilación Térmica', lang)}:** `{site.get('thermal_amplitude_c', 'N/D')} °C`")
            st.markdown(f"• **{_txt('Astrobiology Hostility', 'Hostilidad Astrobiológica', lang)}:** `{site.get('astrobiology_stress_index', 0):.1f} / 100`")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- 3. MAPEO AMBIENTAL COMPARATIVO DEL CATÁLOGO ---
    with st.container(border=True):
        st.markdown(_txt(
            "##### 🌍 Global Catalog Environmental Matrix: Aridity vs. Wind Erosion Potential",
            "##### 🌍 Matriz Ambiental del Catálogo: Aridez vs. Potencial de Erosión Eólica",
            lang
        ))
        plot_df = scored_df.dropna(subset=["aridity_index", "ws10m_ann", "allsky_sfc_sw_dwn_ann"]).copy()
        fig_mat = px.scatter(
            plot_df,
            x="aridity_index",
            y="ws10m_ann",
            size="allsky_sfc_sw_dwn_ann",
            color="surface_albedo_ann",
            hover_name="name",
            color_continuous_scale="Cividis",
            labels={
                "aridity_index": _txt("Aridity Index (0–1)", "Índice de Aridez (0–1)", lang),
                "ws10m_ann": _txt("Mean Wind Speed (m/s)", "Velocidad Media Viento (m/s)", lang),
                "surface_albedo_ann": _txt("Albedo", "Albedo", lang),
                "allsky_sfc_sw_dwn_ann": _txt("Solar Flux (kWh/m²/d)", "Flujo Solar (kWh/m²/d)", lang),
            }
        )
        fig_mat.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(15, 28, 54, 0.4)",
            height=360,
            margin=dict(l=10, r=10, t=20, b=10)
        )
        st.plotly_chart(fig_mat, width="stretch")
