"""
HeatIQ — AI Heat Operations Planner
Live Streamlit app that pulls real FortyGuard temperature data,
applies US OSHA heat-safety thresholds, and recommends the safest
work schedule for outdoor crews.
"""

import os
import pathlib
from datetime import date, timedelta, datetime
import pytz

import streamlit as st
from dotenv import load_dotenv

from fortyguard import FortyGuardClient

# ---------------------------------------------------------------
# Setup
# ---------------------------------------------------------------
load_dotenv(pathlib.Path(__file__).parent / ".env")

st.set_page_config(
    page_title="HeatIQ — Global Heat Operations Center",
    page_icon="🌡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------
# Professional & Attractive Custom Styling with Animations
# ---------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800;900&family=Space+Grotesk:wght@500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

/* ---- Keyframe Animations ---- */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(40px) scale(0.95); }
    to { opacity: 1; transform: translateY(0) scale(1); }
}

@keyframes fadeInDown {
    from { opacity: 0; transform: translateY(-30px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes fadeInLeft {
    from { opacity: 0; transform: translateX(-40px); }
    to { opacity: 1; transform: translateX(0); }
}

@keyframes fadeInRight {
    from { opacity: 0; transform: translateX(40px); }
    to { opacity: 1; transform: translateX(0); }
}

@keyframes pulseGlow {
    0%, 100% { box-shadow: 0 0 20px rgba(255, 107, 53, 0.15); }
    50% { box-shadow: 0 0 50px rgba(255, 107, 53, 0.35); }
}

@keyframes shimmer {
    0% { background-position: -200% center; }
    100% { background-position: 200% center; }
}

@keyframes float {
    0%, 100% { transform: translateY(0px) rotate(0deg); }
    50% { transform: translateY(-8px) rotate(2deg); }
}

@keyframes scaleIn {
    from { opacity: 0; transform: scale(0.8); }
    to { opacity: 1; transform: scale(1); }
}

@keyframes ripple {
    0% { box-shadow: 0 0 0 0 rgba(255, 107, 53, 0.4); }
    100% { box-shadow: 0 0 0 20px rgba(255, 107, 53, 0); }
}

/* ---- Base ---- */
.stApp {
    background: linear-gradient(135deg, #F0F4FA 0%, #E8EDF7 50%, #DCE3F0 100%);
    color: #1A2332;
    animation: fadeInUp 0.8s ease-out;
}

* {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* Hide Streamlit's default keyboard shortcut indicator */
.st-keyboard-shortcut-indicator,
div[data-testid="stKeyboardShortcut"],
button[data-testid="baseButton-header"],
.stApp > header,
[data-testid="stHeader"],
[data-testid="stDecoration"] {
    display: none !important;
}

/* ---- Live Status Bar ---- */
.live-status {
    background: linear-gradient(135deg, #0B1A2F, #1A3A5C);
    border-radius: 16px;
    padding: 12px 24px;
    margin-bottom: 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    animation: fadeInDown 0.6s ease-out;
    box-shadow: 0 4px 20px rgba(11, 26, 47, 0.2);
}

.live-status .dot {
    display: inline-block;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    animation: pulseGlow 1.5s infinite;
}

.live-status .dot.live {
    background: #00E676;
}

.live-status .text {
    color: #FFFFFF;
    font-weight: 600;
    font-size: 0.9rem;
    letter-spacing: 0.02em;
}

.live-status .time {
    color: #A0B8D4;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
}

/* ---- Sidebar ---- */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0B1A2F 0%, #0D2137 40%, #142B44 100%);
    border-right: none;
    box-shadow: 8px 0 32px rgba(0,0,0,0.15);
    animation: fadeInLeft 0.6s ease-out;
}

section[data-testid="stSidebar"] * {
    color: #E8EDF5 !important;
}

.sidebar-brand {
    text-align: center;
    padding: 20px 0 10px 0;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    margin-bottom: 20px;
}

.sidebar-brand .logo-icon {
    font-size: 3rem;
    animation: float 3s ease-in-out infinite;
}

.sidebar-brand .brand-name {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.6rem;
    font-weight: 800;
    background: linear-gradient(90deg, #FF6B35, #FF8F5E);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.sidebar-brand .brand-sub {
    font-size: 0.7rem;
    color: #8899B0 !important;
    letter-spacing: 0.15em;
    text-transform: uppercase;
}

section[data-testid="stSidebar"] .stSelectbox label {
    font-weight: 600 !important;
    color: #A0B8D4 !important;
    font-size: 0.75rem !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 12px !important;
    backdrop-filter: blur(8px);
    transition: all 0.3s ease;
}

section[data-testid="stSidebar"] div[data-baseweb="select"] > div:hover {
    background: rgba(255,255,255,0.1) !important;
    border-color: #FF6B35 !important;
    box-shadow: 0 0 20px rgba(255,107,53,0.1);
}

section[data-testid="stSidebar"] div[data-baseweb="select"] div[role="combobox"] {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
}

section[data-testid="stSidebar"] div[data-baseweb="select"] input {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
}

section[data-testid="stSidebar"] div[data-baseweb="select"] * {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
}

div[data-baseweb="popover"] {
    background: #0B1A2F !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 12px !important;
    backdrop-filter: blur(12px);
}

div[data-baseweb="popover"] * {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
}

div[data-baseweb="popover"] li:hover {
    background: rgba(255,107,53,0.15) !important;
}

section[data-testid="stSidebar"] .stToggle {
    margin-top: 16px;
}

section[data-testid="stSidebar"] .stToggle label {
    font-weight: 500 !important;
    color: #A0B8D4 !important;
    font-size: 0.85rem !important;
}

section[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.06) !important;
    margin: 24px 0;
}

/* Sidebar button with pulse animation */
section[data-testid="stSidebar"] button[kind="primary"] {
    background: linear-gradient(135deg, #FF6B35, #E84A1E) !important;
    border: none !important;
    border-radius: 14px !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    padding: 0.8rem 1rem !important;
    box-shadow: 0 4px 25px rgba(255, 107, 53, 0.4) !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    animation: pulseGlow 2s infinite, ripple 2s infinite;
}

section[data-testid="stSidebar"] button[kind="primary"]:hover {
    transform: translateY(-3px) scale(1.03);
    box-shadow: 0 8px 40px rgba(255, 107, 53, 0.6) !important;
    background: linear-gradient(135deg, #FF7A4A, #D93E14) !important;
    animation-play-state: paused;
}

/* ---- Main Headings ---- */
h1 {
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 800 !important;
    font-size: 2.8rem !important;
    color: #0B1A2F !important;
    letter-spacing: -0.03em;
    background: linear-gradient(135deg, #0B1A2F 0%, #1A3A5C 50%, #2A4A6C 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    padding-bottom: 4px;
    animation: fadeInUp 0.8s ease-out;
}

h1::after {
    content: '';
    display: block;
    width: 80px;
    height: 4px;
    background: linear-gradient(90deg, #FF6B35, #FF8F5E, #FFB088);
    border-radius: 4px;
    margin-top: 10px;
    animation: shimmer 3s infinite linear;
    background-size: 200% auto;
}

h2 {
    font-weight: 700 !important;
    color: #0B1A2F !important;
    animation: fadeInUp 0.9s ease-out;
}

h3 {
    font-weight: 700 !important;
    color: #0B1A2F !important;
    font-size: 1.1rem !important;
    letter-spacing: -0.01em;
}

/* ---- Weather Widget ---- */
.weather-widget {
    background: rgba(255,255,255,0.85);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(255,255,255,0.6);
    border-radius: 20px;
    padding: 20px 24px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.06);
    animation: fadeInUp 0.7s ease-out;
    transition: all 0.3s ease;
}

.weather-widget:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 40px rgba(0,0,0,0.08);
}

.weather-widget .temp-large {
    font-size: 3.5rem;
    font-weight: 800;
    color: #0B1A2F;
    line-height: 1;
}

.weather-widget .temp-large .deg {
    font-size: 2rem;
    color: #FF6B35;
}

.weather-widget .weather-icon {
    font-size: 3.5rem;
    animation: float 4s ease-in-out infinite;
}

.weather-widget .detail-item {
    font-size: 0.85rem;
    color: #6A7B94;
    padding: 4px 0;
}

.weather-widget .detail-item strong {
    color: #0B1A2F;
}

/* ---- Metric Cards ---- */
div[data-testid="stMetric"] {
    background: rgba(255,255,255,0.85);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(255,255,255,0.5);
    border-top: 4px solid #FF6B35;
    border-radius: 20px;
    padding: 22px 26px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.06);
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    animation: fadeInUp 0.7s ease-out;
}

div[data-testid="stMetric"]:hover {
    transform: translateY(-8px) scale(1.02);
    box-shadow: 0 20px 60px rgba(255, 107, 53, 0.12);
    border-color: rgba(255, 107, 53, 0.3);
}

div[data-testid="stMetricValue"] {
    color: #0B1A2F !important;
    font-weight: 800 !important;
    font-size: 2.4rem !important;
    letter-spacing: -0.02em;
}

div[data-testid="stMetricLabel"] {
    color: #6A7B94 !important;
    font-weight: 600 !important;
    font-size: 0.8rem !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

div[data-testid="stMetricDelta"] {
    color: #FF6B35 !important;
    font-weight: 700 !important;
}

/* ---- Progress Bar ---- */
div[data-testid="stProgress"] div[role="progressbar"] > div {
    background: linear-gradient(90deg, #FF6B35, #FF8F5E, #FFB088) !important;
    border-radius: 100px;
    height: 10px !important;
    animation: pulseGlow 2s infinite;
}

div[data-testid="stProgress"] {
    background: #E8EDF5 !important;
    border-radius: 100px;
    height: 10px !important;
}

/* ---- Buttons ---- */
button[kind="primary"] {
    background: linear-gradient(135deg, #FF6B35, #E84A1E) !important;
    border: none !important;
    font-weight: 700 !important;
    border-radius: 14px !important;
    padding: 0.7rem 2rem !important;
    box-shadow: 0 4px 25px rgba(255, 107, 53, 0.3) !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

button[kind="primary"]:hover {
    transform: translateY(-3px) scale(1.03);
    box-shadow: 0 8px 40px rgba(255, 107, 53, 0.5) !important;
}

/* ---- Download Button ---- */
button[data-testid="stDownloadButton"] {
    background: linear-gradient(135deg, #0B1A2F, #1A3A5C) !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 0.7rem 2rem !important;
    transition: all 0.3s ease;
    box-shadow: 0 4px 20px rgba(11, 26, 47, 0.2);
}

button[data-testid="stDownloadButton"]:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 32px rgba(11, 26, 47, 0.3);
    background: linear-gradient(135deg, #1A3A5C, #2A4A6C) !important;
}

/* ---- Schedule Cards ---- */
.schedule-card {
    background: rgba(255,255,255,0.88);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,0.5);
    border-radius: 18px;
    padding: 20px 24px;
    text-align: center;
    box-shadow: 0 4px 20px rgba(0,0,0,0.04);
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    animation: scaleIn 0.7s ease-out;
}

.schedule-card:hover {
    transform: translateY(-6px) scale(1.03);
    box-shadow: 0 12px 48px rgba(0,0,0,0.08);
}

.schedule-card .temp {
    font-size: 2.2rem;
    font-weight: 800;
    color: #0B1A2F;
}

.schedule-card .label {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #6A7B94;
    font-weight: 600;
}

.schedule-card .status-badge {
    display: inline-block;
    padding: 4px 14px;
    border-radius: 100px;
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

/* ---- Risk Banner ---- */
.risk-banner {
    animation: fadeInUp 0.8s ease-out, float 4s ease-in-out infinite;
    border-radius: 20px;
}

/* ---- Info / Alert Boxes ---- */
div[data-testid="stAlert"] {
    background: rgba(255,255,255,0.85) !important;
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,0.4) !important;
    border-radius: 18px !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.04);
    padding: 18px 24px !important;
    animation: fadeInUp 0.8s ease-out;
}

/* ---- Divider ---- */
hr {
    border: none !important;
    height: 2px !important;
    background: linear-gradient(90deg, transparent, rgba(255,107,53,0.15), transparent) !important;
    margin: 32px 0 !important;
    animation: shimmer 4s infinite linear;
    background-size: 200% auto;
}

/* ---- Responsive ---- */
@media (max-width: 768px) {
    h1 { font-size: 2rem !important; }
    div[data-testid="stMetricValue"] { font-size: 1.6rem !important; }
    .weather-widget .temp-large { font-size: 2.5rem; }
    .live-status { flex-direction: column; gap: 8px; text-align: center; }
}
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_client():
    return FortyGuardClient()

client = get_client()

# ---------------------------------------------------------------
# Site presets
# ---------------------------------------------------------------
SITES = {
    "Phoenix, AZ — Industrial Sector": {
        "coords": [
            [-112.090, 33.440], [-112.060, 33.440],
            [-112.060, 33.460], [-112.090, 33.460],
            [-112.090, 33.440],
        ],
        "emoji": "☀️",
        "timezone": "America/Phoenix",
    },
    "Houston, TX — Port District": {
        "coords": [
            [-95.290, 29.730], [-95.260, 29.730],
            [-95.260, 29.750], [-95.290, 29.750],
            [-95.290, 29.730],
        ],
        "emoji": "🌊",
        "timezone": "America/Chicago",
    },
    "Las Vegas, NV — Construction Corridor": {
        "coords": [
            [-115.160, 36.150], [-115.130, 36.150],
            [-115.130, 36.170], [-115.160, 36.170],
            [-115.160, 36.150],
        ],
        "emoji": "🏗️",
        "timezone": "America/Los_Angeles",
    },
    "Miami, FL — Port & Logistics": {
        "coords": [
            [-80.220, 25.760], [-80.190, 25.760],
            [-80.190, 25.780], [-80.220, 25.780],
            [-80.220, 25.760],
        ],
        "emoji": "🌴",
        "timezone": "America/New_York",
    },
}

def make_aoi(coords):
    return {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {},
            "geometry": {"type": "Polygon", "coordinates": [coords]},
        }],
    }

# ---------------------------------------------------------------
# Core engine functions
# ---------------------------------------------------------------
def get_heat_index(polygon_aoi, date_str):
    coords = polygon_aoi["features"][0]["geometry"]["coordinates"][0]
    lons = [c[0] for c in coords]
    lats = [c[1] for c in coords]
    centroid_lon = sum(lons) / len(lons)
    centroid_lat = sum(lats) / len(lats)

    response = client.environmental_parameters(
        latitude=centroid_lat,
        longitude=centroid_lon,
        date_time={"start_date": date_str, "start_time": "14:00", "filter_type": 1},
    )
    result = response.get("result", {})
    apparent_c = result.get("apparent_temperature_celsius") or result.get("apparent_temperature")
    humidity = result.get("relative_humidity") or result.get("humidity")

    apparent_f = (apparent_c * 9 / 5) + 32 if apparent_c is not None else None
    return {"apparent_temp_f": round(apparent_f, 1) if apparent_f else None,
            "humidity_pct": round(humidity, 1) if humidity else None}


def get_osha_risk_grade(hours_above_90f, total_hours):
    percent_exceeded = (hours_above_90f / total_hours) * 100

    if percent_exceeded >= 80:
        grade, message = "CRITICAL", "Extreme, near-constant heat exposure. Immediate schedule change required."
    elif percent_exceeded >= 50:
        grade, message = "HIGH", "Majority of the week exceeds OSHA High-Heat trigger. Mandatory breaks required."
    elif percent_exceeded >= 20:
        grade, message = "MODERATE", "Significant heat exposure periods. Monitor closely and enforce breaks."
    else:
        grade, message = "LOW", "Limited exposure. Standard precautions sufficient."

    return {
        "risk_grade": grade,
        "percent_time_exceeded": round(percent_exceeded, 1),
        "hours_above_threshold": round(hours_above_90f, 1),
        "message": message,
    }


def compare_schedules(polygon_aoi, date_str):
    schedules = {
        "Standard (8AM–5PM)": {"start": "08:00", "end": "17:00"},
        "Early Shift (6AM–3PM)": {"start": "06:00", "end": "15:00"},
        "Split Shift (7AM–11AM)": {"start": "07:00", "end": "11:00"},
        "Night Shift (10PM–6AM)": {"start": "22:00", "end": "06:00"},
    }
    results = {}
    for name, times in schedules.items():
        response = client.create_heatmap(
            polygon_aoi=polygon_aoi,
            start_date=date_str,
            start_time=times["start"],
            end_time=times["end"],
            filter_type=2,
            granularity=100,
        )
        stats = response["result"]["stats_data"]
        temp_stats = stats.get("Temperature_stats") or stats.get("temperature_stats") or {}
        avg_temp_c = temp_stats.get("mean", 0)
        avg_temp_f = (avg_temp_c * 9 / 5) + 32
        results[name] = {"avg_temp_f": round(avg_temp_f, 1), "exceeds_osha": avg_temp_f >= 90}
    return results


def get_recommendation(risk_data, schedule_data, location):
    grade = risk_data["risk_grade"]
    percent = risk_data["percent_time_exceeded"]
    safest_name, safest_data = min(schedule_data.items(), key=lambda x: x[1]["avg_temp_f"])

    if grade == "CRITICAL":
        action = "🛑 SUSPEND all non-essential outdoor work during peak hours. Enforce 15-min breaks every 2 hours."
    elif grade == "HIGH":
        action = "⚠️ Enforce mandatory rest breaks (15 min every 2 hours). Provide hydration stations and shaded areas."
    elif grade == "MODERATE":
        action = "👀 Monitor conditions closely. Ensure hydration and shade protocols are active."
    else:
        action = "✅ Continue standard protocols. Stay vigilant for changing conditions."

    still_exceeds = "⚠️ still exceeds" if safest_data["exceeds_osha"] else "✅ stays within"

    return (
        f"**{grade}** risk at **{location}** — OSHA's 90°F High-Heat threshold exceeded for "
        f"**{percent}%** of the past week.\n\n"
        f"**📋 Recommendation:** {action}\n\n"
        f"**🏆 Safest Schedule:** **{safest_name}** with **{safest_data['avg_temp_f']}°F** average exposure. "
        f"This {still_exceeds} OSHA limits — hydration, shade, and buddy-system monitoring remain essential."
    )


def generate_printable_report(risk_data, schedule_data, location):
    grade = risk_data["risk_grade"]
    percent = risk_data["percent_time_exceeded"]
    safest_name, safest_data = min(schedule_data.items(), key=lambda x: x[1]["avg_temp_f"])

    grade_colors = {
        "CRITICAL": ("#B00020", "🔴"),
        "HIGH": ("#D35400", "🟠"),
        "MODERATE": ("#B8860B", "🟡"),
        "LOW": ("#1B7A3D", "🟢"),
    }
    color, emoji = grade_colors.get(grade, ("#B00020", "🔴"))

    grade_text = {
        "CRITICAL": "DANGER — TOO HOT",
        "HIGH": "HIGH HEAT — TAKE BREAKS",
        "MODERATE": "WARM — BE CAREFUL",
        "LOW": "OK — NORMAL PRECAUTIONS",
    }.get(grade, "DANGER")

    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<title>HeatIQ Safety Report</title>
<style>
  @media print {{ body {{ margin: 0; }} }}
  body {{
    font-family: 'Inter', Arial, sans-serif;
    max-width: 800px; margin: 0 auto; padding: 40px 30px;
    color: #1a1a1a;
    background: #FFFFFF;
  }}
  .banner {{
    background: {color}; color: white; text-align: center;
    padding: 30px 20px; border-radius: 16px; margin-bottom: 24px;
  }}
  .banner .emoji {{ font-size: 64px; }}
  .banner h1 {{ font-size: 34px; margin: 10px 0 0; letter-spacing: 1px; font-weight: 800; }}
  .meta {{ text-align: center; color: #555; font-size: 15px; margin-bottom: 30px; }}
  .rules {{ display: flex; flex-direction: column; gap: 14px; margin-bottom: 30px; }}
  .rule {{
    display: flex; align-items: center; gap: 16px;
    background: #f4f4f4; border-left: 8px solid {color};
    padding: 16px 20px; border-radius: 8px; font-size: 22px; font-weight: bold;
  }}
  .rule .icon {{ font-size: 36px; }}
  .best-time {{
    background: #eef7ee; border: 2px solid #1B7A3D; border-radius: 8px;
    padding: 18px 20px; text-align: center; font-size: 20px; margin-bottom: 26px;
  }}
  .footer {{ text-align: center; color: #888; font-size: 12px; margin-top: 30px; }}
</style></head>
<body>

  <div class="banner">
    <div class="emoji">{emoji}</div>
    <h1>{grade_text}</h1>
  </div>

  <div class="meta">
    <b>Site:</b> {location} &nbsp;•&nbsp; <b>Heat risk this week:</b> {percent}% of hours over safe limit
  </div>

  <div class="rules">
    <div class="rule"><span class="icon">💧</span> Drink water every 30 minutes</div>
    <div class="rule"><span class="icon">🏠</span> Rest in shade every 2 hours</div>
    <div class="rule"><span class="icon">⏰</span> Take a 15-minute break every 2 hours</div>
    <div class="rule"><span class="icon">👥</span> Never work alone — check on your partner</div>
    <div class="rule"><span class="icon">🚨</span> Dizzy, sick, or confused? STOP</div>
  </div>

  <div class="best-time">
    ✅ <b>Safest work window:</b> {safest_name} ({safest_data['avg_temp_f']}°F average)
  </div>

  <div class="footer">
    Generated by HeatIQ · OSHA High-Heat Trigger: 90°F
  </div>

</body></html>"""
    return html

# ---------------------------------------------------------------
# UI — sidebar controls
# ---------------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <div class="logo-icon">🌡️</div>
        <div class="brand-name">HeatIQ</div>
        <div class="brand-sub">AI Heat Operations</div>
    </div>
    """, unsafe_allow_html=True)
    
    site_name = st.selectbox("📍 Monitored Site", list(SITES.keys()))
    simple_mode = st.toggle("👷 Simple View", value=False,
                                  help="Big text, icons, no technical numbers")
    run = st.button("🚀 Run Live Analysis", type="primary", use_container_width=True)

# ---------------------------------------------------------------
# Live Status Bar with Date/Time using pytz
# ---------------------------------------------------------------
# Get timezone for selected site
tz_str = SITES[site_name]["timezone"]
tz = pytz.timezone(tz_str)
current_time_tz = datetime.now(tz)
current_time_str = current_time_tz.strftime("%A, %B %d, %Y • %I:%M %p")

st.markdown(f"""
<div class="live-status">
    <div>
        <span class="dot live"></span>
        <span class="text">🟢 SYSTEM LIVE — Real-time monitoring active</span>
    </div>
    <div>
        <span class="time">📅 {current_time_str} ({tz_str})</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------
# Main Content
# ---------------------------------------------------------------
col_title, col_weather = st.columns([2, 1])

with col_title:
    st.title("Heat Operations Command Center")
    st.caption("⚡ Hyperlocal thermal telemetry • AI-powered operational decisions • Built on FortyGuard Temperature API")

with col_weather:
    site_emoji = SITES[site_name]["emoji"]
    site_time = datetime.now(pytz.timezone(SITES[site_name]["timezone"])).strftime('%I:%M %p')
    site_date = datetime.now(pytz.timezone(SITES[site_name]["timezone"])).strftime('%b %d, %Y')
    
    st.markdown(f"""
    <div class="weather-widget">
        <div style="display:flex; align-items:center; gap:16px;">
            <div class="weather-icon">{site_emoji}</div>
            <div>
                <div class="temp-large">{site_name.split(',')[0]}<span class="deg">°</span></div>
                <div style="color:#6A7B94; font-size:0.85rem; font-weight:500;">
                    {site_name.split('—')[1].strip() if '—' in site_name else ''}
                </div>
            </div>
        </div>
        <div style="display:flex; gap:20px; margin-top:12px; flex-wrap:wrap; border-top:1px solid rgba(0,0,0,0.05); padding-top:12px;">
            <div class="detail-item"><strong>🕐</strong> {site_time}</div>
            <div class="detail-item"><strong>📅</strong> {site_date}</div>
            <div class="detail-item"><strong>📍</strong> {site_name.split(',')[0]}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

if run:
    aoi = make_aoi(SITES[site_name]["coords"])
    end_date = date.today().isoformat()
    start_date = (date.today() - timedelta(days=7)).isoformat()

    with st.spinner("🌡️ Pulling live temperature data from FortyGuard..."):
        exceedance = client.create_heatmap(
            polygon_aoi=aoi,
            start_date=start_date,
            end_date=end_date,
            filter_type=4,
            analytic_type="exceedance",
            threshold=32.2,
            direction="above",
            granularity=100,
        )
        ex_stats = exceedance["result"]["stats_data"]
        risk = get_osha_risk_grade(ex_stats["mean"], total_hours=168)

    with st.spinner("📊 Comparing work schedules..."):
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        schedules = compare_schedules(aoi, yesterday)

    with st.spinner("💧 Checking humidity-adjusted heat index..."):
        try:
            heat_index = get_heat_index(aoi, yesterday)
        except Exception:
            heat_index = {"apparent_temp_f": None, "humidity_pct": None}

    st.session_state["results"] = {
        "site_name": site_name,
        "ex_stats": ex_stats,
        "risk": risk,
        "schedules": schedules,
        "heat_index": heat_index,
    }

if "results" in st.session_state:
    site_name = st.session_state["results"]["site_name"]
    ex_stats = st.session_state["results"]["ex_stats"]
    risk = st.session_state["results"]["risk"]
    schedules = st.session_state["results"]["schedules"]
    heat_index = st.session_state["results"].get("heat_index", {})

    recommendation = get_recommendation(risk, schedules, site_name)
    report_html = generate_printable_report(risk, schedules, site_name)

    if simple_mode:
        grade_colors = {"CRITICAL": "#B00020", "HIGH": "#D35400", "MODERATE": "#B8860B", "LOW": "#1B7A3D"}
        grade_emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MODERATE": "🟡", "LOW": "🟢"}
        grade_text = {
            "CRITICAL": "DANGER — TOO HOT",
            "HIGH": "HIGH HEAT — TAKE BREAKS",
            "MODERATE": "WARM — BE CAREFUL",
            "LOW": "OK — NORMAL DAY",
        }
        c = grade_colors.get(risk["risk_grade"], "#B00020")
        e = grade_emoji.get(risk["risk_grade"], "🔴")
        t = grade_text.get(risk["risk_grade"], "DANGER")

        st.markdown(
            f"""<div class="risk-banner" style="background:{c}; color:white; text-align:center; padding:50px 20px; border-radius:20px; margin-bottom:24px; box-shadow: 0 8px 40px rgba(0,0,0,0.15);">
                <div style="font-size:80px;">{e}</div>
                <div style="font-size:42px; font-weight:800; letter-spacing:1px;">{t}</div>
                <div style="font-size:18px; opacity:0.9; margin-top:8px;">{site_name}</div>
            </div>""",
            unsafe_allow_html=True,
        )
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 💧 Drink water every 30 minutes")
            st.markdown("### 🏠 Rest in shade every 2 hours")
            st.markdown("### ⏰ Take a 15-minute break every 2 hours")
        with col2:
            st.markdown("### 👥 Never work alone — check on your partner")
            st.markdown("### 🚨 Feel dizzy or sick? STOP and tell your supervisor")

        st.download_button(
            "🖨️ Download Printable Safety Poster",
            data=report_html,
            file_name=f"heatiq_safety_poster_{site_name.split(',')[0].strip()}.html",
            mime="text/html",
            use_container_width=True,
        )

    else:
        col1, col2 = st.columns([1, 2])

        with col1:
            st.metric(
                label="OSHA Exposure Index",
                value=f"{risk['percent_time_exceeded']}%",
                delta=risk["risk_grade"],
                delta_color="off"
            )
            st.progress(min(risk["percent_time_exceeded"] / 100, 1.0))
            st.write(f"**⏱️ Hours above 90°F:** {risk['hours_above_threshold']} / 168")
            st.write(f"**📊 Zones monitored:** {ex_stats['n_cells']}")
            if heat_index.get("apparent_temp_f") is not None:
                st.write(f"**🌡️ Heat Index (feels-like):** {heat_index['apparent_temp_f']}°F")
                st.write(f"**💧 Relative Humidity:** {heat_index['humidity_pct']}%")
                st.caption("OSHA triggers are based on heat index (temp + humidity), not raw air temperature.")

        with col2:
            st.subheader("⚠️ AI Dispatch")
            st.markdown(recommendation)

        st.markdown("---")
        st.subheader("📊 Schedule Exposure Comparison")
        sched_cols = st.columns(len(schedules))
        for col, (name, data) in zip(sched_cols, schedules.items()):
            with col:
                status_color = "#B00020" if data["exceeds_osha"] else "#1B7A3D"
                status_text = "⚠️ Exceeds OSHA" if data["exceeds_osha"] else "✅ Within limits"
                st.markdown(f"""
                <div class="schedule-card">
                    <div class="label">{name}</div>
                    <div class="temp">{data['avg_temp_f']}°F</div>
                    <div>
                        <span class="status-badge" style="background:{status_color}20; color:{status_color}; border:1px solid {status_color}40;">
                            {status_text}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("🖨️ Site Safety Poster")
        st.caption("A one-page, icon-based safety poster any worker can read — no smartphone or internet needed once printed.")
        st.download_button(
            "🖨️ Download Printable Safety Poster",
            data=report_html,
            file_name=f"heatiq_safety_poster_{site_name.split(',')[0].strip()}.html",
            mime="text/html",
            use_container_width=True,
        )

elif "results" not in st.session_state:
    st.info("👈 Select a site in the sidebar and click **Run Live Analysis** to pull real-time heat data.")

# ---------------------------------------------------------------
# Footer
# ---------------------------------------------------------------
st.markdown("""
<div style="text-align:center; padding:30px 0 10px 0; color:#8899B0; font-size:0.8rem; border-top:1px solid rgba(0,0,0,0.05); margin-top:40px;">
    🌡️ <strong>HeatIQ</strong> — AI Heat Operations Planner &nbsp;•&nbsp; 
    Powered by FortyGuard Temperature API &nbsp;•&nbsp; 
    OSHA High-Heat Trigger: 90°F
</div>
""", unsafe_allow_html=True)