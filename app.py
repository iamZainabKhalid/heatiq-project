"""
HeatIQ — AI Heat Operations Planner
Live Streamlit app that pulls real FortyGuard temperature data,
applies US OSHA heat-safety thresholds, and recommends the safest
work schedule for outdoor crews.
"""

import os
import pathlib
from datetime import date, timedelta

import streamlit as st
from dotenv import load_dotenv

from fortyguard import FortyGuardClient

# ---------------------------------------------------------------
# Setup
# ---------------------------------------------------------------
load_dotenv(pathlib.Path(__file__).parent / ".env")

st.set_page_config(
    page_title="HeatIQ — Phoenix Heat Operations Center",
    page_icon="🌡️",
    layout="wide",
)

# ---------------------------------------------------------------
# Custom styling — clean light dashboard, navy sidebar, card-based
# ---------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Poppins:wght@600;700&display=swap');

.stApp {
    background: linear-gradient(180deg, #F9FAFC, #E8ECF7);
    color: #1B2340;
}

* { font-family: 'Inter', sans-serif !important; }

section[data-testid="stSidebar"] {
    background: #14213D;
    border-right: none;
    box-shadow: 4px 0 14px rgba(20,33,61,0.2);
}
section[data-testid="stSidebar"] * { color: #E8ECF7 !important; }
section[data-testid="stSidebar"] h1 {
    font-family: 'Poppins', sans-serif !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
    border-left: 5px solid #F0651E;
    padding-left: 14px;
}

/* Sidebar dropdown */
section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
    background: #FFFFFF !important;
    border-radius: 10px !important;
    border: 1px solid #2C3E66 !important;
    transition: all 0.3s ease;
}
section[data-testid="stSidebar"] div[data-baseweb="select"] > div:hover {
    box-shadow: 0 0 10px rgba(255,255,255,0.3);
}
section[data-testid="stSidebar"] div[data-baseweb="select"] * {
    color: black !important;
    -webkit-text-fill-color: black !important;
    fill: black !important;
}
div[data-baseweb="popover"] * { color: #14213D !important; }
div[data-baseweb="popover"] { background: #FFFFFF !important; }

/* Main headings */
h1 {
    font-family: 'Poppins', sans-serif !important;
    font-weight: 700 !important;
    font-size: 2.2rem !important;
    color: #14213D !important;
    letter-spacing: -0.02em;
    border-left: 5px solid #F0651E;
    padding-left: 16px;
}
h2, h3 { font-weight: 700 !important; color: #14213D !important; }
p, span, label, li { color: #5B6584; }

/* Metric cards — white, rounded, soft shadow, warm accent, hover lift */
div[data-testid="stMetric"] {
    background: #FFFFFF;
    border: 1px solid #E7EAF3;
    border-top: 3px solid #F0651E;
    border-radius: 14px;
    padding: 18px 22px;
    box-shadow: 0 4px 16px rgba(240,101,30,0.08);
    transition: all 0.25s ease-in-out;
}
div[data-testid="stMetric"]:hover {
    transform: translateY(-3px);
    box-shadow: 0 6px 20px rgba(240,101,30,0.15);
}
div[data-testid="stMetricValue"] { color: #F0651E !important; font-weight: 800 !important; }
div[data-testid="stMetricLabel"] { color: #8891AC !important; font-weight: 600 !important; }
div[data-testid="stMetricDelta"] { color: #F0651E !important; }

/* Primary button — warm heat gradient with hover lift */
button[kind="primary"] {
    background: linear-gradient(90deg, #F0651E, #E8492E) !important;
    border: none !important;
    font-weight: 700 !important;
    border-radius: 10px !important;
    box-shadow: 0 4px 14px rgba(240,101,30,0.35);
    transition: all 0.25s ease-in-out;
}
button[kind="primary"]:hover {
    transform: scale(1.03);
    background: linear-gradient(90deg, #D9560F, #D93E24) !important;
}

/* Progress bar with glow pulse */
div[data-testid="stProgress"] div[role="progressbar"] > div {
    background: #E8492E !important;
    border-radius: 6px;
    animation: progressGlow 2s infinite alternate;
}
@keyframes progressGlow {
    from { box-shadow: 0 0 6px rgba(232,73,46,0.4); }
    to { box-shadow: 0 0 12px rgba(232,73,46,0.8); }
}

/* Download button */
button[data-testid="stDownloadButton"] {
    background: #14213D !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 10px !important;
}

/* Info / alert box */
div[data-testid="stAlert"] {
    background: #FFFFFF !important;
    border: 1px solid #E7EAF3 !important;
    border-radius: 14px !important;
    box-shadow: 0 2px 10px rgba(20,33,61,0.05);
}

hr { border-color: #E7EAF3 !important; }
[data-testid="stCaptionContainer"] { color: #8891AC !important; }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_client():
    return FortyGuardClient()

client = get_client()

# ---------------------------------------------------------------
# Site presets — real US cities with known extreme-heat exposure
# ---------------------------------------------------------------
SITES = {
    "Phoenix, AZ — Industrial Sector": {
        "coords": [
            [-112.090, 33.440], [-112.060, 33.440],
            [-112.060, 33.460], [-112.090, 33.460],
            [-112.090, 33.440],
        ]
    },
    "Houston, TX — Port District": {
        "coords": [
            [-95.290, 29.730], [-95.260, 29.730],
            [-95.260, 29.750], [-95.290, 29.750],
            [-95.290, 29.730],
        ]
    },
    "Las Vegas, NV — Construction Corridor": {
        "coords": [
            [-115.160, 36.150], [-115.130, 36.150],
            [-115.130, 36.170], [-115.160, 36.170],
            [-115.160, 36.150],
        ]
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
# Core engine functions (same logic proven in the notebook)
# ---------------------------------------------------------------
def get_heat_index(polygon_aoi, date_str):
    """
    Pulls real humidity + apparent temperature from FortyGuard's
    environmental_parameters endpoint at the site's centroid.
    OSHA's actual 80°F/90°F triggers are based on heat index
    (temperature + humidity combined), not raw air temperature —
    this makes the risk grade closer to the real regulatory metric.
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
        action = "Suspend all non-essential outdoor work during peak hours and enforce 15-minute breaks every 2 hours, consistent with OSHA's proposed High-Heat Trigger standard."
    elif grade == "HIGH":
        action = "Enforce paid rest breaks (15 min every 2 hours), consistent with OSHA's proposed High-Heat Trigger standard."
    else:
        action = "Continue standard hydration and shade protocols; monitor for changes."

    still_exceeds = "still exceeds" if safest_data["exceeds_osha"] else "stays within"

    return (
        f"**{grade} risk** at {location}, exceeding OSHA's proposed 90°F High-Heat threshold for "
        f"**{percent}%** of the past week.\n\n"
        f"**Recommendation:** {action}\n\n"
        f"Of the schedules evaluated, **\"{safest_name}\"** shows the lowest average exposure "
        f"at **{safest_data['avg_temp_f']}°F**. Even so, this {still_exceeds} OSHA limits — "
        f"hydration stations, shaded rest areas, and buddy-system monitoring remain essential "
        f"regardless of schedule."
    )


def generate_printable_report(risk_data, schedule_data, location):
    """
    Builds a single, self-contained HTML file: big icons, minimal text,
    high color contrast. Works fully offline once downloaded — no internet,
    no smartphone, no login needed. Meant to be printed and posted on-site
    for workers of any literacy level or age.
    """
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
    font-family: Arial, Helvetica, sans-serif;
    max-width: 800px; margin: 0 auto; padding: 40px 30px;
    color: #1a1a1a;
  }}
  .banner {{
    background: {color}; color: white; text-align: center;
    padding: 30px 20px; border-radius: 10px; margin-bottom: 24px;
  }}
  .banner .emoji {{ font-size: 64px; }}
  .banner h1 {{ font-size: 34px; margin: 10px 0 0; letter-spacing: 1px; }}
  .meta {{ text-align: center; color: #555; font-size: 15px; margin-bottom: 30px; }}
  .rules {{ display: flex; flex-direction: column; gap: 14px; margin-bottom: 30px; }}
  .rule {{
    display: flex; align-items: center; gap: 16px;
    background: #f4f4f4; border-left: 8px solid {color};
    padding: 16px 20px; border-radius: 6px; font-size: 22px; font-weight: bold;
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
    <div class="rule"><span class="icon">💧</span> Drink water every 30 minutes — even if not thirsty</div>
    <div class="rule"><span class="icon">🏠</span> Rest in shade or indoors every 2 hours</div>
    <div class="rule"><span class="icon">⏰</span> Take a 15-minute break every 2 hours — recommended under OSHA's proposed heat rule</div>
    <div class="rule"><span class="icon">👥</span> Never work alone — check on your partner often</div>
    <div class="rule"><span class="icon">🚨</span> Dizzy, sick, or confused? STOP and tell your supervisor immediately</div>
  </div>

  <div class="best-time">
    ✅ <b>Safest work window today:</b> {safest_name} ({safest_data['avg_temp_f']}°F average)
  </div>

  <div class="footer">
    Generated by HeatIQ using real-time FortyGuard temperature data · OSHA's proposed High-Heat Trigger: 90°F<br>
    Print this page and post it where workers can see it. No phone or internet needed to read it.
  </div>

</body></html>"""
    return html

# ---------------------------------------------------------------
# UI — sidebar controls
# ---------------------------------------------------------------
st.sidebar.title("HeatIQ Controls")
site_name = st.sidebar.selectbox("Monitored site", list(SITES.keys()))
simple_mode = st.sidebar.toggle("👷 Simple View (for workers)", value=False,
                                  help="Big text, icons, no technical numbers — for any age or literacy level")
run = st.sidebar.button("Run Live Analysis", type="primary", use_container_width=True)

st.title("HeatIQ — Heat Operations Command Center")
st.caption("Hyperlocal thermal telemetry, converted into operational decisions. Not just where it's hot — what to do about it. Built on the FortyGuard Temperature API.")

if run:
    aoi = make_aoi(SITES[site_name]["coords"])
    end_date = date.today().isoformat()
    start_date = (date.today() - timedelta(days=7)).isoformat()

    with st.spinner("Pulling live temperature data from FortyGuard..."):
        exceedance = client.create_heatmap(
            polygon_aoi=aoi,
            start_date=start_date,
            end_date=end_date,
            filter_type=4,
            analytic_type="exceedance",
            threshold=32.2,          # 90°F in Celsius = OSHA High-Heat Trigger
            direction="above",
            granularity=100,
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

    # Save results so toggling Simple View later doesn't re-trigger API calls
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

    # ---- Simple Mode: big icons, minimal text, any age/literacy level ----
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
            f"""<div style="background:{c}; color:white; text-align:center; padding:40px 20px; border-radius:14px; margin-bottom:20px;">
                <div style="font-size:70px;">{e}</div>
                <div style="font-size:36px; font-weight:800; letter-spacing:1px;">{t}</div>
            </div>""",
            unsafe_allow_html=True,
        )
        st.markdown("### 💧 Drink water every 30 minutes")
        st.markdown("### 🏠 Rest in shade every 2 hours")
        st.markdown("### ⏰ Take a 15-minute break every 2 hours")
        st.markdown("### 👥 Never work alone — check on your partner")
        st.markdown("### 🚨 Feel dizzy or sick? STOP and tell your supervisor")

        st.download_button(
            "🖨️ Download Printable Safety Poster",
            data=report_html,
            file_name=f"heatiq_safety_poster_{site_name.split(',')[0].strip()}.html",
            mime="text/html",
            use_container_width=True,
        )

    # ---- Detailed Mode: full technical dashboard ----
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
                st.caption("OSHA's 80°F/90°F triggers are based on heat index, not raw air temperature — this accounts for humidity too.")

        with col2:
            st.subheader("⚠️ AI Dispatch")
            st.markdown(recommendation)

        st.subheader("Schedule Exposure Comparison")
        sched_cols = st.columns(len(schedules))
        for col, (name, data) in zip(sched_cols, schedules.items()):
            with col:
                st.metric(name, f"{data['avg_temp_f']}°F")
                st.write("⚠️ Exceeds OSHA" if data["exceeds_osha"] else "✅ Within limits")

        st.divider()
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
    st.info("Select a site in the sidebar and click **Run Live Analysis** to pull real-time heat data.")
