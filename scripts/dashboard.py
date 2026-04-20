"""
Day 13 Observability Dashboard — Streamlit App
Run: streamlit run scripts/dashboard.py
Reads live metrics from FastAPI /metrics endpoint and log history from data/logs.jsonl
"""
from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path

import httpx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
API_BASE = "http://127.0.0.1:8000"
LOG_PATH = Path("data/logs.jsonl")

# SLO thresholds (from config/slo.yaml)
SLO_LATENCY_P95_MS = 3000
SLO_ERROR_RATE_PCT = 2.0
SLO_DAILY_COST_USD = 2.5
SLO_QUALITY_AVG = 0.75

st.set_page_config(
    page_title="Observability Lab Dashboard",
    page_icon="📊",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Sidebar Controls
# ---------------------------------------------------------------------------
st.sidebar.title("Controls")
refresh_rate = st.sidebar.slider("Refresh rate (seconds)", 5, 60, 15)
if st.sidebar.button("Refresh Now"):
    st.rerun()

# Auto-refresh
st.sidebar.markdown("---")
auto_refresh = st.sidebar.checkbox("Auto-refresh", value=True)
if auto_refresh:
    time.sleep(0.1)  # small delay to let page render
    st.markdown(
        f'<meta http-equiv="refresh" content="{refresh_rate}">',
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Fetch Metrics
# ---------------------------------------------------------------------------
@st.cache_data(ttl=5)
def fetch_metrics() -> dict | None:
    try:
        r = httpx.get(f"{API_BASE}/metrics", timeout=5.0)
        return r.json()
    except Exception:
        return None


def load_logs() -> pd.DataFrame:
    if not LOG_PATH.exists():
        return pd.DataFrame()
    records = []
    for line in LOG_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
            records.append(rec)
        except json.JSONDecodeError:
            continue
    if not records:
        return pd.DataFrame()
    df = pd.DataFrame(records)
    if "ts" in df.columns:
        df["ts"] = pd.to_datetime(df["ts"], errors="coerce")
    return df


metrics = fetch_metrics()
logs_df = load_logs()

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown("# 📊 Day 13: Observability Dashboard")

if metrics is None:
    st.error("⚠️ Cannot connect to API. Make sure `uvicorn app.main:app` is running on port 8000.")
    st.stop()

# ---------------------------------------------------------------------------
# Panel row 1: KPI Cards
# ---------------------------------------------------------------------------
total_errors = sum(metrics.get("error_breakdown", {}).values())
error_rate = (total_errors / metrics["traffic"] * 100) if metrics["traffic"] > 0 else 0.0

col1, col2, col3 = st.columns(3)
col1.metric("Total Traffic", f"{metrics['traffic']}", help="Total requests processed")
col2.metric("Error Rate", f"{error_rate:.1f}%", delta=f"{total_errors} failures", delta_color="inverse")
col3.metric("Avg Latency (P50)", f"{metrics['latency_p50']:.0f}ms", help="Median latency")

# ---------------------------------------------------------------------------
# Panel 1: Latency Percentiles (bar chart)
# ---------------------------------------------------------------------------
st.markdown("---")
left_col, right_col = st.columns(2)

with left_col:
    st.subheader("Latency Percentiles")
    latency_data = pd.DataFrame({
        "Percentile": ["P50", "P95", "P99"],
        "Latency (ms)": [metrics["latency_p50"], metrics["latency_p95"], metrics["latency_p99"]],
    })
    fig_lat = px.bar(
        latency_data,
        x="Percentile",
        y="Latency (ms)",
        color="Percentile",
        color_discrete_sequence=["#6c63ff", "#3b82f6", "#8b5cf6"],
        text="Latency (ms)",
    )
    # Add SLO line
    fig_lat.add_hline(
        y=SLO_LATENCY_P95_MS,
        line_dash="dash",
        line_color="#e74c3c",
        annotation_text=f"SLO P95: {SLO_LATENCY_P95_MS}ms",
        annotation_position="top right",
    )
    fig_lat.update_layout(
        showlegend=False,
        yaxis_title="ms",
        height=350,
    )
    fig_lat.update_traces(textposition="outside")
    st.plotly_chart(fig_lat, use_container_width=True)

# ---------------------------------------------------------------------------
# Panel 2: Cost & Token Usage
# ---------------------------------------------------------------------------
with right_col:
    st.subheader("Cost & Token Usage")

    # Build time-series from logs if available
    if not logs_df.empty and "cost_usd" in logs_df.columns and "ts" in logs_df.columns:
        cost_df = logs_df.dropna(subset=["cost_usd", "ts"]).sort_values("ts")
        cost_df["cumulative_cost"] = cost_df["cost_usd"].cumsum()
        fig_cost = px.line(
            cost_df,
            x="ts",
            y="cumulative_cost",
            labels={"ts": "Time", "cumulative_cost": "Cumulative Cost (USD)"},
        )
        fig_cost.add_hline(
            y=SLO_DAILY_COST_USD,
            line_dash="dash",
            line_color="#e74c3c",
            annotation_text=f"SLO: ${SLO_DAILY_COST_USD}/day",
        )
        fig_cost.update_layout(height=350, yaxis_title="USD")
        st.plotly_chart(fig_cost, use_container_width=True)
    else:
        st.metric("Total Cost", f"${metrics['total_cost_usd']:.4f}")
        st.metric("Avg Cost/Request", f"${metrics['avg_cost_usd']:.4f}")

# ---------------------------------------------------------------------------
# Panel 3: Error Rate with Breakdown
# ---------------------------------------------------------------------------
st.markdown("---")
left_col2, right_col2 = st.columns(2)

with left_col2:
    st.subheader("Error Breakdown")
    error_data = metrics.get("error_breakdown", {})
    if error_data:
        fig_err = px.pie(
            names=list(error_data.keys()),
            values=list(error_data.values()),
            color_discrete_sequence=["#e74c3c", "#f39c12", "#e67e22", "#c0392b"],
            hole=0.4,
        )
        fig_err.update_layout(height=350)
        st.plotly_chart(fig_err, use_container_width=True)
    else:
        st.success("✅ No errors detected")

# ---------------------------------------------------------------------------
# Panel 4: Tokens In/Out
# ---------------------------------------------------------------------------
with right_col2:
    st.subheader("Tokens In / Out")
    token_data = pd.DataFrame({
        "Type": ["Input", "Output"],
        "Tokens": [metrics["tokens_in_total"], metrics["tokens_out_total"]],
    })
    fig_tok = px.bar(
        token_data,
        x="Type",
        y="Tokens",
        color="Type",
        color_discrete_sequence=["#3b82f6", "#f39c12"],
        text="Tokens",
    )
    fig_tok.update_layout(showlegend=False, height=350, yaxis_title="Tokens")
    fig_tok.update_traces(textposition="outside")
    st.plotly_chart(fig_tok, use_container_width=True)

# ---------------------------------------------------------------------------
# Panel 5 & 6: Quality Proxy + Traffic over time
# ---------------------------------------------------------------------------
st.markdown("---")
left_col3, right_col3 = st.columns(2)

with left_col3:
    st.subheader("Quality Proxy")
    quality_val = metrics["quality_avg"]
    st.metric("Quality Score (Avg)", f"{quality_val:.2f}", help="Heuristic quality score 0-1")

    # Quality gauge
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=quality_val,
        gauge={
            "axis": {"range": [0, 1]},
            "bar": {"color": "#00d97e" if quality_val >= SLO_QUALITY_AVG else "#e74c3c"},
            "threshold": {
                "line": {"color": "#e74c3c", "width": 3},
                "thickness": 0.8,
                "value": SLO_QUALITY_AVG,
            },
            "steps": [
                {"range": [0, SLO_QUALITY_AVG], "color": "rgba(231,76,60,0.1)"},
                {"range": [SLO_QUALITY_AVG, 1], "color": "rgba(0,217,126,0.1)"},
            ],
        },
        title={"text": f"SLO Target: {SLO_QUALITY_AVG}"},
    ))
    fig_gauge.update_layout(height=280)
    st.plotly_chart(fig_gauge, use_container_width=True)

with right_col3:
    st.subheader("Traffic Over Time")
    if not logs_df.empty and "ts" in logs_df.columns:
        # Group by minute
        traffic_df = logs_df.dropna(subset=["ts"]).copy()
        traffic_df["minute"] = traffic_df["ts"].dt.floor("min")
        traffic_counts = traffic_df.groupby("minute").size().reset_index(name="requests")
        fig_traffic = px.bar(
            traffic_counts,
            x="minute",
            y="requests",
            labels={"minute": "Time", "requests": "Requests"},
            color_discrete_sequence=["#3b82f6"],
        )
        fig_traffic.update_layout(height=350, yaxis_title="Requests", xaxis_title="Time")
        st.plotly_chart(fig_traffic, use_container_width=True)
    else:
        st.metric("Total Requests", metrics["traffic"])

# ---------------------------------------------------------------------------
# SLO Status Table
# ---------------------------------------------------------------------------
st.markdown("---")
st.subheader("🎯 SLO Status")

slo_rows = [
    {
        "SLI": "Latency P95",
        "Target": f"< {SLO_LATENCY_P95_MS}ms",
        "Window": "28d",
        "Current": f"{metrics['latency_p95']:.0f}ms",
        "Status": "✅ OK" if metrics["latency_p95"] < SLO_LATENCY_P95_MS else "❌ BREACH",
    },
    {
        "SLI": "Error Rate",
        "Target": f"< {SLO_ERROR_RATE_PCT}%",
        "Window": "28d",
        "Current": f"{error_rate:.1f}%",
        "Status": "✅ OK" if error_rate < SLO_ERROR_RATE_PCT else "❌ BREACH",
    },
    {
        "SLI": "Daily Cost",
        "Target": f"< ${SLO_DAILY_COST_USD}",
        "Window": "1d",
        "Current": f"${metrics['total_cost_usd']:.4f}",
        "Status": "✅ OK" if metrics["total_cost_usd"] < SLO_DAILY_COST_USD else "❌ BREACH",
    },
    {
        "SLI": "Quality Avg",
        "Target": f"> {SLO_QUALITY_AVG}",
        "Window": "28d",
        "Current": f"{metrics['quality_avg']:.2f}",
        "Status": "✅ OK" if metrics["quality_avg"] >= SLO_QUALITY_AVG else "❌ BREACH",
    },
]

st.dataframe(pd.DataFrame(slo_rows), use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown("---")
st.caption(f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Auto-refresh: {refresh_rate}s")
