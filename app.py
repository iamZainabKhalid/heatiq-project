"""
HeatIQ — AI Heat Operations Planner
Live Streamlit app that pulls real FortyGuard temperature data,
applies US OSHA's proposed heat-safety thresholds, and recommends
the safest work schedule for outdoor crews.
"""

import os
import pathlib
import requests as http_requests
from datetime import date, timedelta, datetime
from zoneinfo import ZoneInfo  # stdlib — no extra dependency needed

import streamlit as st
from dotenv import load_dotenv

from fortyguard import FortyGuardClient

# ---------------------------------------------------------------
# Setup
# ---------------------------------------------------------------
load_dotenv(pathlib.Path(__file__).parent / ".env")

st.set_page_config(
    page_title="HeatIQ — Heat Operations Command Center",
    page_icon="🌡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------
# Custom styling — clean light dashboard with warm accents
# ---------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Space+Grotesk:wght@600;700;800&display=swap');

.stApp {
    background: linear-gradient(135deg, #F0F4FA 0%, #E8EDF7 50%, #DCE3F0 100%);
    color: #1A2332;
}
* { font-family: 'Inter', sans-serif !important; }

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0B1A2F 0%, #0D2137 40%, #142B44 100%);
    border-right: none;
    box-shadow: 8px 0 32px rgba(0,0,0,0.15);
}
section[data-testid="stSidebar"] * { color: #E8EDF5 !important; }

.sidebar-brand { text-align: center; padding: 16px 0 10px 0; border-bottom: 1px solid rgba(255,255,255,0.08); margin-bottom: 20px; }
.sidebar-brand .logo-icon { font-size: 2.6rem; }
.sidebar-brand .brand-name {
    font-family: 'Space Grotesk', sans-serif; font-size: 1.5rem; font-weight: 800;
    background: linear-gradient(90deg, #FF6B35, #FF8F5E);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.sidebar-brand .brand-sub { font-size: 0.68rem; color: #8899B0 !important; letter-spacing: 0.14em; text-transform: uppercase; }

/* Fix dropdown - select box itself */
section[data-testid="stSidebar"] .stSelectbox > div[data-baseweb="select"] > div {
    background: #FFFFFF !important;
    border-radius: 10px !important;
    border: 1px solid #2C3E66 !important;
    color: #14213D !important;
}

section[data-testid="stSidebar"] .stSelectbox > div[data-baseweb="select"] > div * {
    color: #14213D !important;
    -webkit-text-fill-color: #14213D !important;
}

/* Fix dropdown options - the popover */
div[data-baseweb="popover"] {
    background: #FFFFFF !important;
    border-radius: 10px !important;
    border: 1px solid #E7EAF3 !important;
    box-shadow: 0 8px 32px rgba(0,0,0,0.15) !important;
    max-height: 300px !important;
    overflow-y: auto !important;
}

div[data-baseweb="popover"] * {
    color: #14213D !important;
    -webkit-text-fill-color: #14213D !important;
}

/* Fix individual option items */
div[data-baseweb="popover"] div[role="option"] {
    padding: 12px 16px !important;
    cursor: pointer !important;
    color: #14213D !important;
    -webkit-text-fill-color: #14213D !important;
    background: #FFFFFF !important;
}

div[data-baseweb="popover"] div[role="option"]:hover {
    background: #F0F4FA !important;
}

div[data-baseweb="popover"] div[role="option"][aria-selected="true"] {
    background: #E8EDF7 !important;
    font-weight: 600 !important;
}

div[data-baseweb="popover"] ul[role="listbox"] {
    max-height: 280px !important;
    overflow-y: auto !important;
    padding: 4px 0 !important;
}

/* Fix the select label */
section[data-testid="stSidebar"] .stSelectbox label {
    color: #E8EDF5 !important;
}

/* Hide the broken sidebar-collapse icon (shows as raw text when font fails to load) */
[data-testid="stSidebarCollapseButton"],
[data-testid="collapsedControl"],
button[title="Collapse sidebar"],
button[title="Expand sidebar"] {
    display: none !important;
}

section[data-testid="stSidebar"] input[type="number"] {
    background: #FFFFFF !important; color: #14213D !important; border-radius: 8px !important;
}

button[kind="primary"] {
    background: linear-gradient(135deg, #FF6B35, #E84A1E) !important;
    border: none !important; font-weight: 700 !important; border-radius: 12px !important;
    box-shadow: 0 4px 20px rgba(255,107,53,0.35) !important;
    transition: all 0.25s ease;
}
button[kind="primary"]:hover { transform: translateY(-2px); box-shadow: 0 8px 28px rgba(255,107,53,0.5) !important; }

h1 {
    font-family: 'Space Grotesk', sans-serif !important; font-weight: 800 !important;
    font-size: 2.4rem !important; color: #0B1A2F !important; letter-spacing: -0.02em;
    border-left: 5px solid #FF6B35; padding-left: 16px;
}
h2, h3 { font-weight: 700 !important; color: #0B1A2F !important; }
p, span, label, li { color: #5B6584; }

div[data-testid="stMetric"] {
    background: #FFFFFF; border: 1px solid #E7EAF3; border-top: 4px solid #FF6B35;
    border-radius: 16px; padding: 20px 24px; box-shadow: 0 6px 22px rgba(255,107,53,0.08);
    transition: all 0.25s ease;
}
div[data-testid="stMetric"]:hover { transform: translateY(-4px); box-shadow: 0 10px 28px rgba(255,107,53,0.15); }
div[data-testid="stMetricValue"] { color: #FF6B35 !important; font-weight: 800 !important; }
div[data-testid="stMetricLabel"] { color: #8891AC !important; font-weight: 600 !important; }

.schedule-card {
    background: #FFFFFF; border: 1px solid #E7EAF3; border-radius: 16px;
    padding: 20px 22px; text-align: center; box-shadow: 0 4px 16px rgba(0,0,0,0.04);
    transition: all 0.25s ease;
}
.schedule-card:hover { transform: translateY(-4px); box-shadow: 0 10px 24px rgba(0,0,0,0.08); }
.schedule-card .temp { font-size: 2rem; font-weight: 800; color: #0B1A2F; }
.schedule-card .label { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; color: #6A7B94; font-weight: 600; }
.schedule-card .status-badge { display: inline-block; padding: 4px 14px; border-radius: 100px; font-size: 0.7rem; font-weight: 700; margin-top: 8px; }

.site-card {
    background: #FFFFFF; border: 1px solid #E7EAF3; border-radius: 16px;
    padding: 18px 22px; box-shadow: 0 4px 16px rgba(0,0,0,0.04);
}

div[data-testid="stProgress"] div[role="progressbar"] > div { background: #FF6B35 !important; border-radius: 100px; }
button[data-testid="stDownloadButton"] {
    background: #0B1A2F !important; color: #FFFFFF !important; font-weight: 700 !important;
    border: none !important; border-radius: 12px !important;
}
div[data-testid="stAlert"] { background: #FFFFFF !important; border: 1px solid #E7EAF3 !important; border-radius: 14px !important; }
hr { border-color: #E7EAF3 !important; }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_client():
    return FortyGuardClient()


client = get_client()

# ---------------------------------------------------------------
# Site presets — real US cities with known outdoor-worker heat exposure
# ---------------------------------------------------------------
SITES = {
    "Phoenix, AZ — Industrial Sector": {
        "coords": [[-112.090, 33.440], [-112.060, 33.440], [-112.060, 33.460], [-112.090, 33.460], [-112.090, 33.440]],
        "timezone": "America/Phoenix",
    },
    "Houston, TX — Port District": {
        "coords": [[-95.290, 29.730], [-95.260, 29.730], [-95.260, 29.750], [-95.290, 29.750], [-95.290, 29.730]],
        "timezone": "America/Chicago",
    },
    "Las Vegas, NV — Construction Corridor": {
        "coords": [[-115.160, 36.150], [-115.130, 36.150], [-115.130, 36.170], [-115.160, 36.170], [-115.160, 36.150]],
        "timezone": "America/Los_Angeles",
    },
    "Miami, FL — Port & Logistics": {
        "coords": [[-80.220, 25.760], [-80.190, 25.760], [-80.190, 25.780], [-80.220, 25.780], [-80.220, 25.760]],
        "timezone": "America/New_York",
    },
    "Dallas, TX — Warehouse District": {
        "coords": [[-96.820, 32.760], [-96.790, 32.760], [-96.790, 32.780], [-96.820, 32.780], [-96.820, 32.760]],
        "timezone": "America/Chicago",
    },
    "Atlanta, GA — Distribution Center": {
        "coords": [[-84.420, 33.740], [-84.390, 33.740], [-84.390, 33.760], [-84.420, 33.760], [-84.420, 33.740]],
        "timezone": "America/New_York",
    },
}
CUSTOM_LABEL = "📍 Custom coordinates (enter below)"


def make_aoi(coords):
    return {
        "type": "FeatureCollection",
        "features": [{"type": "Feature", "properties": {}, "geometry": {"type": "Polygon", "coordinates": [coords]}}],
    }


def make_custom_coords(lat, lon, half_width_deg=0.015):
    """Builds a small (~3km) square AOI centered on a user-supplied point."""
    return [
        [lon - half_width_deg, lat - half_width_deg],
        [lon + half_width_deg, lat - half_width_deg],
        [lon + half_width_deg, lat + half_width_deg],
        [lon - half_width_deg, lat + half_width_deg],
        [lon - half_width_deg, lat - half_width_deg],
    ]


# ---------------------------------------------------------------
# Core engine functions
# ---------------------------------------------------------------
def get_heat_index(polygon_aoi, date_str):
    """
    Pulls real humidity + apparent temperature from FortyGuard's
    environmental_parameters endpoint. OSHA's proposed 80°F/90°F
    triggers are based on heat index (temp + humidity), not raw
    air temperature, so this makes the risk grade more accurate.
    """
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
    return {
        "apparent_temp_f": round(apparent_f, 1) if apparent_f is not None else None,
        "humidity_pct": round(humidity, 1) if humidity is not None else None,
    }


def get_osha_risk_grade(hours_above_90f, total_hours):
    percent_exceeded = (hours_above_90f / total_hours) * 100

    if percent_exceeded >= 80:
        grade, message = "CRITICAL", "Extreme, near-constant heat exposure. Immediate schedule change required."
    elif percent_exceeded >= 50:
        grade, message = "HIGH", "Majority of the week exceeds OSHA's proposed High-Heat trigger. Breaks strongly advised."
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


def get_ai_dispatch(risk_data, schedule_data, location):
    """
    Calls an LLM (via OpenRouter — free tier) to generate a human-readable
    safety dispatch grounded in the real FortyGuard/OSHA numbers.
    Falls back to a rule-based recommendation if the AI call fails or no
    API key is set, so the demo never breaks due to network/API issues.
    """
    grade = risk_data["risk_grade"]
    percent = risk_data["percent_time_exceeded"]
    safest_name, safest_data = min(schedule_data.items(), key=lambda x: x[1]["avg_temp_f"])
    still_exceeds = "still exceeds" if safest_data["exceeds_osha"] else "stays within"

    def rule_based_fallback():
        if grade == "CRITICAL":
            action = "Suspend non-essential outdoor work during peak hours and enforce 15-minute breaks every 2 hours, consistent with OSHA's proposed High-Heat Trigger standard."
        elif grade == "HIGH":
            action = "Enforce paid rest breaks (15 min every 2 hours), consistent with OSHA's proposed High-Heat Trigger standard."
        else:
            action = "Continue standard hydration and shade protocols; monitor for changes."
        return (
            f"**{grade} risk** at {location}, exceeding OSHA's proposed 90°F High-Heat threshold for "
            f"**{percent}%** of the past week.\n\n"
            f"**Recommendation:** {action}\n\n"
            f"Of the schedules evaluated, **\"{safest_name}\"** shows the lowest average exposure "
            f"at **{safest_data['avg_temp_f']}°F**. Even so, this {still_exceeds} OSHA limits — "
            f"hydration stations, shaded rest areas, and buddy-system monitoring remain essential "
            f"regardless of schedule.\n\n"
            f"*Note: this tool models outdoor, ground-level conditions. Indoor workers face lower "
            f"but non-zero heat risk from equipment and lack of airflow — separate indoor monitoring is recommended.*"
        )

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return rule_based_fallback()

    prompt = (
        f"Site: {location}\n"
        f"OSHA heat risk grade: {grade}\n"
        f"Percent of past week exceeding OSHA's 90°F High-Heat trigger: {percent}%\n"
        f"Hours above threshold: {risk_data['hours_above_threshold']} of 168\n"
        f"Schedule comparison (avg feels-like temp): {schedule_data}\n"
        f"Safest schedule: {safest_name} at {safest_data['avg_temp_f']}°F ({still_exceeds} OSHA limits)\n\n"
        "As HeatIQ's heat-safety dispatch agent, write a short (4-6 sentence) operational "
        "recommendation for a site supervisor: state the risk level plainly, cite the key "
        "numbers, recommend the safest work window, and give one concrete safety action "
        "aligned with OSHA's proposed High-Heat Trigger standard."
    )

    try:
        response = http_requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "meta-llama/llama-3.1-8b-instruct:free",
                "messages": [
                    {"role": "system", "content": "You are HeatIQ's AI heat-safety dispatch agent for outdoor work crews."},
                    {"role": "user", "content": prompt},
                ],
            },
            timeout=15,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return content if content else rule_based_fallback()
    except Exception:
        return rule_based_fallback()


def generate_printable_report(risk_data, schedule_data, location):
    grade = risk_data["risk_grade"]
    percent = risk_data["percent_time_exceeded"]
    safest_name, safest_data = min(schedule_data.items(), key=lambda x: x[1]["avg_temp_f"])

    grade_colors = {"CRITICAL": ("#B00020", "🔴"), "HIGH": ("#D35400", "🟠"), "MODERATE": ("#B8860B", "🟡"), "LOW": ("#1B7A3D", "🟢")}
    color, emoji = grade_colors.get(grade, ("#B00020", "🔴"))
    grade_text = {
        "CRITICAL": "DANGER — TOO HOT", "HIGH": "HIGH HEAT — TAKE BREAKS",
        "MODERATE": "WARM — BE CAREFUL", "LOW": "OK — NORMAL PRECAUTIONS",
    }.get(grade, "DANGER")

    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>HeatIQ Safety Report</title>
<style>
  body {{ font-family: Arial, Helvetica, sans-serif; max-width: 800px; margin: 0 auto; padding: 40px 30px; color: #1a1a1a; }}
  .banner {{ background: {color}; color: white; text-align: center; padding: 30px 20px; border-radius: 10px; margin-bottom: 24px; }}
  .banner .emoji {{ font-size: 64px; }}
  .banner h1 {{ font-size: 34px; margin: 10px 0 0; }}
  .meta {{ text-align: center; color: #555; font-size: 15px; margin-bottom: 30px; }}
  .rule {{ display: flex; align-items: center; gap: 16px; background: #f4f4f4; border-left: 8px solid {color};
           padding: 16px 20px; border-radius: 6px; font-size: 22px; font-weight: bold; margin-bottom: 14px; }}
  .rule .icon {{ font-size: 36px; }}
  .best-time {{ background: #eef7ee; border: 2px solid #1B7A3D; border-radius: 8px; padding: 18px 20px; text-align: center; font-size: 20px; margin-bottom: 26px; }}
  .footer {{ text-align: center; color: #888; font-size: 12px; margin-top: 30px; }}
</style></head>
<body>
  <div class="banner"><div class="emoji">{emoji}</div><h1>{grade_text}</h1></div>
  <div class="meta"><b>Site:</b> {location} &nbsp;•&nbsp; <b>Heat risk this week:</b> {percent}% of hours over safe limit</div>
  <div class="rule"><span class="icon">💧</span> Drink water every 30 minutes — even if not thirsty</div>
  <div class="rule"><span class="icon">🏠</span> Rest in shade or indoors every 2 hours</div>
  <div class="rule"><span class="icon">⏰</span> Take a 15-minute break every 2 hours</div>
  <div class="rule"><span class="icon">👥</span> Never work alone — check on your partner often</div>
  <div class="rule"><span class="icon">🚨</span> Dizzy, sick, or confused? STOP and tell your supervisor</div>
  <div class="best-time">✅ <b>Safest work window today:</b> {safest_name} ({safest_data['avg_temp_f']}°F average)</div>
  <div class="footer">Generated by HeatIQ using real-time FortyGuard temperature data · OSHA's proposed High-Heat Trigger: 90°F<br>
  Print this page and post it where workers can see it. No phone or internet needed to read it.</div>
</body></html>"""


# ---------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <div class="logo-icon">🌡️</div>
        <div class="brand-name">HeatIQ</div>
        <div class="brand-sub">AI Heat Operations</div>
    </div>
    """, unsafe_allow_html=True)

    site_choice = st.selectbox("📍 Monitored Site", list(SITES.keys()) + [CUSTOM_LABEL])

    custom_lat, custom_lon = None, None
    if site_choice == CUSTOM_LABEL:
        st.caption("Enter any U.S. location (FortyGuard covers the U.S. only).")
        custom_lat = st.number_input("Latitude", value=33.4484, format="%.4f")
        custom_lon = st.number_input("Longitude", value=-112.0740, format="%.4f")

    simple_mode = st.toggle("👷 Simple View", value=False, help="Big text, icons, no technical numbers")
    run = st.button("🚀 Run Live Analysis", type="primary", use_container_width=True)

# ---------------------------------------------------------------
# Header
# ---------------------------------------------------------------
col_title, col_info = st.columns([2, 1])

with col_title:
    st.title("Heat Operations Command Center")
    st.caption("Hyperlocal thermal telemetry, converted into operational decisions. Built on the FortyGuard Temperature API.")

with col_info:
    if site_choice == CUSTOM_LABEL:
        display_name = f"Custom Site ({custom_lat:.3f}, {custom_lon:.3f})"
        tz_name = "UTC"
    else:
        display_name = site_choice
        tz_name = SITES[site_choice]["timezone"]

    local_time = datetime.now(ZoneInfo(tz_name))
    st.markdown(f"""
    <div class="site-card">
        <div style="font-size:0.75rem; color:#8891AC; text-transform:uppercase; letter-spacing:0.05em; font-weight:600;">Local Site Time</div>
        <div style="font-size:1.5rem; font-weight:800; color:#0B1A2F;">{local_time.strftime('%I:%M %p')}</div>
        <div style="font-size:0.85rem; color:#6A7B94;">{local_time.strftime('%A, %b %d')} · {display_name.split(',')[0]}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ---------------------------------------------------------------
# Run analysis
# ---------------------------------------------------------------
if run:
    if site_choice == CUSTOM_LABEL:
        coords = make_custom_coords(custom_lat, custom_lon)
        active_site_name = f"Custom Site ({custom_lat:.3f}, {custom_lon:.3f})"
    else:
        coords = SITES[site_choice]["coords"]
        active_site_name = site_choice

    aoi = make_aoi(coords)
    end_date = date.today().isoformat()
    start_date = (date.today() - timedelta(days=7)).isoformat()

    with st.spinner("Pulling live temperature data from FortyGuard..."):
        exceedance = client.create_heatmap(
            polygon_aoi=aoi, start_date=start_date, end_date=end_date,
            filter_type=4, analytic_type="exceedance", threshold=32.2,
            direction="above", granularity=100,
        )
        ex_stats = exceedance["result"]["stats_data"]
        risk = get_osha_risk_grade(ex_stats["mean"], total_hours=168)

    with st.spinner("Comparing work schedules..."):
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        schedules = compare_schedules(aoi, yesterday)

    with st.spinner("Checking humidity-adjusted heat index..."):
        try:
            heat_index = get_heat_index(aoi, yesterday)
        except Exception:
            heat_index = {"apparent_temp_f": None, "humidity_pct": None}

    st.session_state["results"] = {
        "site_name": active_site_name, "ex_stats": ex_stats, "risk": risk,
        "schedules": schedules, "heat_index": heat_index,
    }

# ---------------------------------------------------------------
# Display results
# ---------------------------------------------------------------
if "results" in st.session_state:
    site_name = st.session_state["results"]["site_name"]
    ex_stats = st.session_state["results"]["ex_stats"]
    risk = st.session_state["results"]["risk"]
    schedules = st.session_state["results"]["schedules"]
    heat_index = st.session_state["results"].get("heat_index", {})

    with st.spinner("Generating AI dispatch..."):
        recommendation = get_ai_dispatch(risk, schedules, site_name)
    report_html = generate_printable_report(risk, schedules, site_name)

    if simple_mode:
        grade_colors = {"CRITICAL": "#B00020", "HIGH": "#D35400", "MODERATE": "#B8860B", "LOW": "#1B7A3D"}
        grade_emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MODERATE": "🟡", "LOW": "🟢"}
        grade_text = {"CRITICAL": "DANGER — TOO HOT", "HIGH": "HIGH HEAT — TAKE BREAKS",
                      "MODERATE": "WARM — BE CAREFUL", "LOW": "OK — NORMAL DAY"}
        c = grade_colors.get(risk["risk_grade"], "#B00020")
        e = grade_emoji.get(risk["risk_grade"], "🔴")
        t = grade_text.get(risk["risk_grade"], "DANGER")

        st.markdown(
            f"""<div style="background:{c}; color:white; text-align:center; padding:40px 20px; border-radius:16px; margin-bottom:20px;">
                <div style="font-size:70px;">{e}</div>
                <div style="font-size:36px; font-weight:800;">{t}</div>
                <div style="font-size:16px; opacity:0.9; margin-top:6px;">{site_name}</div>
            </div>""",
            unsafe_allow_html=True,
        )
        st.markdown("### 💧 Drink water every 30 minutes")
        st.markdown("### 🏠 Rest in shade every 2 hours")
        st.markdown("### ⏰ Take a 15-minute break every 2 hours")
        st.markdown("### 👥 Never work alone — check on your partner")
        st.markdown("### 🚨 Feel dizzy or sick? STOP and tell your supervisor")

        st.download_button(
            "🖨️ Download Printable Safety Poster", data=report_html,
            file_name=f"heatiq_safety_poster_{site_name.split(',')[0].strip()}.html",
            mime="text/html", use_container_width=True,
        )

    else:
        col1, col2 = st.columns([1, 2])
        with col1:
            st.metric("OSHA Exposure Index", f"{risk['percent_time_exceeded']}%", risk["risk_grade"])
            st.progress(min(risk["percent_time_exceeded"] / 100, 1.0))
            st.write(f"**Hours above 90°F:** {risk['hours_above_threshold']} / 168")
            st.write(f"**Zones monitored:** {ex_stats['n_cells']}")
            if heat_index.get("apparent_temp_f") is not None:
                st.write(f"**Heat Index (feels-like):** {heat_index['apparent_temp_f']}°F")
                st.write(f"**Relative Humidity:** {heat_index['humidity_pct']}%")
                st.caption("OSHA's proposed triggers are based on heat index, not raw air temperature.")

        with col2:
            st.subheader("⚠️ AI Dispatch")
            st.markdown(recommendation)

        st.markdown("---")
        st.subheader("Schedule Exposure Comparison")
        sched_cols = st.columns(len(schedules))
        for col, (name, data) in zip(sched_cols, schedules.items()):
            with col:
                status_color = "#B00020" if data["exceeds_osha"] else "#1B7A3D"
                status_text = "⚠️ Exceeds OSHA" if data["exceeds_osha"] else "✅ Within limits"
                st.markdown(f"""
                <div class="schedule-card">
                    <div class="label">{name}</div>
                    <div class="temp">{data['avg_temp_f']}°F</div>
                    <span class="status-badge" style="background:{status_color}20; color:{status_color};">{status_text}</span>
                </div>""", unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("🖨️ Site Safety Poster")
        st.caption("A one-page, icon-based safety poster any worker can read — no smartphone or internet needed once printed.")
        st.download_button(
            "🖨️ Download Printable Safety Poster", data=report_html,
            file_name=f"heatiq_safety_poster_{site_name.split(',')[0].strip()}.html",
            mime="text/html", use_container_width=True,
        )

elif "results" not in st.session_state:
    st.info("👈 Select a site in the sidebar and click **Run Live Analysis** to pull real-time heat data.")

st.markdown("""
<div style="text-align:center; padding:24px 0 8px 0; color:#8891AC; font-size:0.8rem; border-top:1px solid #E7EAF3; margin-top:36px;">
    HeatIQ — AI Heat Operations Planner · Powered by FortyGuard Temperature API · OSHA's proposed High-Heat Trigger: 90°F
</div>
""", unsafe_allow_html=True)