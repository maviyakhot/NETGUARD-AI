import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import psutil
import subprocess
import socket
from datetime import datetime

st.set_page_config(page_title="NetGuard AI", page_icon="🛡️", layout="wide")

# ===================== STYLE =====================
st.markdown("""
<style>
.stApp{background:#070b14}
.block-container{max-width:1450px;padding:1rem 2rem 2rem}
.hero{background:linear-gradient(135deg,#0d1830,#101827);border:1px solid #263957;border-radius:18px;padding:20px 24px;margin-bottom:18px}
.hero-title{font-size:30px;font-weight:800;color:#f4f7fb}
.hero-sub{color:#8d9ab0;font-size:14px}
.live-pill{display:inline-block;padding:7px 12px;border-radius:20px;background:#0b3528;color:#42e6a7;font-weight:700;font-size:13px;border:1px solid #1c7557}
.card{background:linear-gradient(145deg,#10192b,#0c1423);border:1px solid #263957;border-radius:16px;padding:18px;min-height:118px}
.card-title{color:#8d9ab0;font-size:12px;font-weight:600}
.card-value{color:#f6f8fb;font-size:29px;font-weight:800;margin-top:5px}
.card-sub{color:#4fe0a4;font-size:12px;margin-top:4px}
.step{background:#101a2d;border:1px solid #293b5b;border-radius:12px;padding:14px;margin-bottom:10px}
.step-title{font-weight:700;color:#f4f7fb}
.step-desc{font-size:13px;color:#96a3b7;margin-top:4px}
.result{background:#101a2d;border-left:4px solid #42e6a7;border-radius:10px;padding:15px;margin-top:12px}
.small{color:#8d9ab0;font-size:12px}
</style>
""", unsafe_allow_html=True)

# ===================== STATE =====================
if "telemetry" not in st.session_state:
    st.session_state.telemetry = pd.DataFrame(
        columns=["time","latency","packet_loss","bandwidth","cpu","memory"]
    )
if "incidents" not in st.session_state:
    st.session_state.incidents = []
if "troubleshoot_results" not in st.session_state:
    st.session_state.troubleshoot_results = {}

# ===================== SIDEBAR =====================
st.sidebar.markdown("## 🛡️ NetGuard AI")
st.sidebar.caption("Network Operations Center")

mode = st.sidebar.radio("Monitoring Mode", ["🧪 Simulation", "💻 Real System"])
scenario = "🟢 Normal"

if mode == "🧪 Simulation":
    scenario = st.sidebar.selectbox(
        "Network Scenario",
        [
            "🟢 Normal",
            "🟡 High Latency",
            "🔴 Network Congestion",
            "🟠 CPU Overload",
            "🟣 Bandwidth Saturation",
            "🔴 Packet Loss",
        ],
    )

refresh = st.sidebar.slider("Live refresh (seconds)", 1, 5, 1)

# ===================== TELEMETRY =====================
def telemetry():
    rng = np.random.default_rng()
    cpu = psutil.cpu_percent(interval=None)
    memory = psutil.virtual_memory().percent

    if mode == "💻 Real System":
        net = psutil.net_io_counters()
        bandwidth = min(100, ((net.bytes_sent + net.bytes_recv) / 1024 / 1024) % 100)
        return {
            "latency": max(5, rng.normal(40, 5)),
            "packet_loss": max(0, rng.normal(0.5, 0.2)),
            "bandwidth": bandwidth,
            "cpu": cpu,
            "memory": memory,
        }

    latency = rng.normal(45, 6)
    loss = rng.normal(0.8, 0.3)
    bandwidth = rng.normal(50, 7)
    cpu_v = rng.normal(45, 8)

    if scenario == "🟡 High Latency":
        latency += rng.normal(105, 15)
    elif scenario == "🔴 Network Congestion":
        latency += rng.normal(145, 20)
        loss += rng.normal(8, 1.5)
        bandwidth += rng.normal(35, 5)
    elif scenario == "🟠 CPU Overload":
        cpu_v += rng.normal(45, 5)
        latency += rng.normal(35, 8)
    elif scenario == "🟣 Bandwidth Saturation":
        bandwidth += rng.normal(45, 4)
        latency += rng.normal(75, 15)
    elif scenario == "🔴 Packet Loss":
        loss += rng.normal(12, 2)
        latency += rng.normal(80, 15)

    return {
        "latency": max(5, latency),
        "packet_loss": max(0, loss),
        "bandwidth": min(100, max(0, bandwidth)),
        "cpu": min(100, max(0, cpu_v)),
        "memory": memory,
    }

# ===================== DIAGNOSIS =====================
def diagnose(latency, loss, bandwidth, cpu):
    if loss >= 6 and latency >= 120:
        return (
            "🔴 NETWORK CONGESTION",
            "Latency and packet loss are both significantly elevated.",
            "Check bandwidth utilization, traffic sources and routing paths.",
            "CRITICAL",
        )
    if loss >= 6:
        return (
            "🔴 PACKET LOSS",
            "Packet loss is above the expected baseline.",
            "Inspect interface quality, Wi-Fi/cabling and network path.",
            "CRITICAL",
        )
    if bandwidth >= 90:
        return (
            "🟣 BANDWIDTH SATURATION",
            "Network utilization is close to capacity.",
            "Identify high-bandwidth applications and reduce unnecessary traffic.",
            "HIGH",
        )
    if cpu >= 85:
        return (
            "🟠 CPU OVERLOAD",
            "CPU utilization is unusually high.",
            "Identify high-CPU processes and inspect workload.",
            "HIGH",
        )
    if latency >= 120:
        return (
            "🟡 HIGH LATENCY",
            "Network response time is significantly elevated.",
            "Check congestion, routing and upstream connectivity.",
            "MEDIUM",
        )

    return (
        "🟢 NETWORK HEALTHY",
        "Current network metrics are within the expected baseline.",
        "Continue monitoring for changes.",
        "LOW",
    )

# ===================== TROUBLESHOOTING WORKFLOWS =====================
TROUBLESHOOTING = {
    "NETWORK CONGESTION": [
        ("Check bandwidth utilization", "Determine whether the link is approaching capacity."),
        ("Check packet loss", "Packet loss combined with high latency strengthens the congestion diagnosis."),
        ("Identify high-traffic sources", "Look for applications or devices consuming excessive bandwidth."),
        ("Inspect routing path", "Check whether a routing path or upstream link is creating a bottleneck."),
        ("Verify after action", "Re-check latency and packet loss to confirm improvement."),
    ],
    "PACKET LOSS": [
        ("Check network interface", "Verify that the local interface is available."),
        ("Check connection quality", "Inspect cable, Wi-Fi signal or interface quality."),
        ("Check network load", "High utilization can contribute to packet drops."),
        ("Check upstream path", "Inspect the route toward the affected destination."),
        ("Verify after action", "Confirm packet loss decreases after corrective action."),
    ],
    "HIGH LATENCY": [
        ("Check current utilization", "High utilization can increase queueing delay."),
        ("Check packet loss", "Loss and retransmissions can increase latency."),
        ("Check local system load", "High CPU or memory pressure can affect responsiveness."),
        ("Inspect routing path", "A longer or unstable route may increase response time."),
        ("Verify after action", "Re-measure latency after the corrective action."),
    ],
    "CPU OVERLOAD": [
        ("Check CPU utilization", "Confirm that CPU usage remains consistently high."),
        ("Identify heavy processes", "Find processes consuming significant CPU resources."),
        ("Check memory pressure", "Memory pressure can amplify system performance problems."),
        ("Reduce unnecessary workload", "Stop or optimize non-essential resource-heavy tasks."),
        ("Verify after action", "Confirm CPU utilization returns toward baseline."),
    ],
    "BANDWIDTH SATURATION": [
        ("Check link utilization", "Confirm that the network link is near capacity."),
        ("Identify traffic sources", "Find devices or applications generating the most traffic."),
        ("Prioritize important traffic", "Use traffic management or QoS where appropriate."),
        ("Reduce unnecessary traffic", "Pause or limit non-critical transfers."),
        ("Verify after action", "Confirm utilization and latency return toward baseline."),
    ],
    "NETWORK HEALTHY": [
        ("Run baseline check", "Confirm latency and packet loss remain stable."),
        ("Check system load", "Ensure the local system is not under unusual pressure."),
        ("Continue monitoring", "Keep collecting telemetry to detect changes early."),
    ],
}

# ===================== SAFE DIAGNOSTICS =====================
def ping_check(host="1.1.1.1"):
    try:
        result = subprocess.run(
            ["ping", "-c", "1", "-W", "1", host],
            capture_output=True,
            text=True,
            timeout=3,
        )
        return result.returncode == 0
    except Exception:
        return False

def gateway_check():
    try:
        result = subprocess.run(
            ["ip", "route", "show", "default"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        return result.returncode == 0 and "default" in result.stdout
    except Exception:
        return False

def local_checks(latest=None):
    results = {}

    interfaces = psutil.net_if_stats()
    results["Network interface"] = any(v.isup for v in interfaces.values())

    results["CPU usage"] = psutil.cpu_percent(interval=0.2) < 90
    results["Memory usage"] = psutil.virtual_memory().percent < 90
    results["Default gateway"] = gateway_check()
    results["Internet connectivity"] = ping_check()

    if latest is not None:
        results["Packet loss baseline"] = float(latest["packet_loss"]) < 6
        results["Latency baseline"] = float(latest["latency"]) < 120

    return results

# ===================== HEADER =====================
h1, h2 = st.columns([6, 1])

with h1:
    st.markdown(
        """
        <div class="hero">
            <div class="hero-title">🛡️ NetGuard AI</div>
            <div class="hero-sub">
                AI-Powered Network Operations & Guided Troubleshooting
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with h2:
    st.markdown('<br><span class="live-pill">● LIVE</span>', unsafe_allow_html=True)

nav = st.radio(
    "Navigation",
    [
        "🏠 Dashboard",
        "📡 Telemetry",
        "🤖 AI Assistant",
        "🚨 Incidents",
        "🛠️ Troubleshooting",
        "🧪 Simulator",
        "ℹ️ About",
    ],
    horizontal=True,
    label_visibility="collapsed",
)

# ===================== DASHBOARD / TELEMETRY =====================
if nav in ["🏠 Dashboard", "📡 Telemetry"]:

    @st.fragment(run_every=refresh)
    def live_view():
        data = telemetry()
        now = datetime.now()

        row = pd.DataFrame([{"time": now, **data}])
        st.session_state.telemetry = pd.concat(
            [st.session_state.telemetry, row],
            ignore_index=True,
        ).tail(60)

        diagnosis, evidence, recommendation, severity = diagnose(
            data["latency"],
            data["packet_loss"],
            data["bandwidth"],
            data["cpu"],
        )

        if severity in ["CRITICAL", "HIGH", "MEDIUM"]:
            if (
                not st.session_state.incidents
                or st.session_state.incidents[-1]["problem"] != diagnosis
            ):
                st.session_state.incidents.append(
                    {
                        "time": now.strftime("%H:%M:%S"),
                        "problem": diagnosis,
                        "severity": severity,
                        "latency": data["latency"],
                        "packet_loss": data["packet_loss"],
                    }
                )
                st.session_state.incidents = st.session_state.incidents[-20:]

        score = int(
            max(
                0,
                min(
                    100,
                    100
                    - min(35, data["latency"] / 5)
                    - min(35, data["packet_loss"] * 3)
                    - max(0, (data["cpu"] - 70) * 0.5),
                ),
            )
        )

        cols = st.columns(5)
        cards = [
            ("LATENCY", f"{data['latency']:.0f} ms", "Live measurement"),
            ("PACKET LOSS", f"{data['packet_loss']:.1f}%", "Live measurement"),
            ("BANDWIDTH", f"{data['bandwidth']:.0f}%", "Utilization"),
            ("CPU", f"{data['cpu']:.0f}%", "System usage"),
            ("HEALTH SCORE", f"{score}/100", "AI assessment"),
        ]

        for col, (title, value, sub) in zip(cols, cards):
            with col:
                st.markdown(
                    f"""
                    <div class="card">
                        <div class="card-title">{title}</div>
                        <div class="card-value">{value}</div>
                        <div class="card-sub">{sub}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.write("")
        left, right = st.columns([2.1, 1])

        with left:
            st.markdown(
                '<div class="card-title" style="font-size:19px;color:#f4f7fb">📡 Live Network Telemetry</div>',
                unsafe_allow_html=True,
            )

            df = st.session_state.telemetry

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=df["time"],
                    y=df["latency"],
                    mode="lines",
                    name="Latency (ms)",
                    line=dict(width=3),
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=df["time"],
                    y=df["packet_loss"] * 10,
                    mode="lines",
                    name="Packet Loss ×10",
                    line=dict(width=2),
                )
            )

            fig.update_layout(
                height=380,
                template="plotly_dark",
                paper_bgcolor="#0d1525",
                plot_bgcolor="#0b1220",
                margin=dict(l=10, r=10, t=15, b=10),
                legend=dict(orientation="h"),
            )

            st.plotly_chart(fig, use_container_width=True, key="live_chart")

        with right:
            st.markdown(
                '<div class="card-title" style="font-size:19px;color:#f4f7fb">🤖 AI Diagnosis</div>',
                unsafe_allow_html=True,
            )

            if severity == "CRITICAL":
                st.error(diagnosis)
            elif severity in ["HIGH", "MEDIUM"]:
                st.warning(diagnosis)
            else:
                st.success(diagnosis)

            st.markdown("**Evidence**")
            st.write(evidence)

            st.markdown("**Recommended Action**")
            st.info(recommendation)

        st.markdown(
            '<div class="card-title" style="font-size:19px;color:#f4f7fb">🚨 Live Event Feed</div>',
            unsafe_allow_html=True,
        )

        if st.session_state.incidents:
            for event in reversed(st.session_state.incidents[-5:]):
                st.markdown(
                    f"**{event['time']}** • **{event['problem']}** • "
                    f"{event['latency']:.0f} ms • {event['packet_loss']:.1f}%"
                )
        else:
            st.success(f"{now.strftime('%H:%M:%S')} • Network operating normally")

    live_view()

# ===================== AI ASSISTANT =====================
elif nav == "🤖 AI Assistant":
    st.markdown("## 🤖 Offline AI Assistant")

    question = st.text_input(
        "Ask about the network",
        placeholder="Why is my network unhealthy?",
    )

    if question:
        if len(st.session_state.telemetry):
            latest = st.session_state.telemetry.iloc[-1]
            diagnosis, evidence, recommendation, severity = diagnose(
                latest["latency"],
                latest["packet_loss"],
                latest["bandwidth"],
                latest["cpu"],
            )

            st.success(diagnosis)
            st.write("**Evidence:**", evidence)
            st.info("**Recommended action:** " + recommendation)
        else:
            st.info("Open Dashboard first to collect telemetry.")

# ===================== INCIDENTS =====================
elif nav == "🚨 Incidents":
    st.markdown("## 🚨 Incident Timeline")

    if not st.session_state.incidents:
        st.success("No incidents detected yet.")
    else:
        for event in reversed(st.session_state.incidents):
            st.markdown(
                f"""
                <div class="step">
                    <div class="step-title">
                        {event["problem"]} • {event["severity"]}
                    </div>
                    <div class="step-desc">
                        {event["time"]} •
                        Latency {event["latency"]:.0f} ms •
                        Packet Loss {event["packet_loss"]:.1f}%
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

# ===================== TROUBLESHOOTING =====================
elif nav == "🛠️ Troubleshooting":
    st.markdown("## 🛠️ Guided Troubleshooting")
    st.caption("Detect → Diagnose → Diagnose Locally → Recommend → Verify")

    latest = (
        st.session_state.telemetry.iloc[-1]
        if len(st.session_state.telemetry)
        else None
    )

    if latest is not None:
        diagnosis, evidence, recommendation, severity = diagnose(
            latest["latency"],
            latest["packet_loss"],
            latest["bandwidth"],
            latest["cpu"],
        )
    else:
        diagnosis = "🟢 NETWORK HEALTHY"
        evidence = "No live telemetry collected yet."
        recommendation = "Start the Dashboard first."
        severity = "LOW"

    # Current diagnosis
    st.markdown(f"### Current diagnosis: {diagnosis}")
    st.write(evidence)

    # Current metrics
    if latest is not None:
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Latency", f"{latest['latency']:.0f} ms")
        with m2:
            st.metric("Packet Loss", f"{latest['packet_loss']:.1f}%")
        with m3:
            st.metric("Bandwidth", f"{latest['bandwidth']:.0f}%")
        with m4:
            st.metric("CPU", f"{latest['cpu']:.0f}%")

    # Dynamic workflow
    clean_key = (
        diagnosis.replace("🔴 ", "")
        .replace("🟡 ", "")
        .replace("🟠 ", "")
        .replace("🟣 ", "")
        .replace("🟢 ", "")
    )

    steps = TROUBLESHOOTING.get(
        clean_key,
        TROUBLESHOOTING["NETWORK HEALTHY"],
    )

    st.markdown("### 1️⃣ Recommended troubleshooting path")

    for i, (name, description) in enumerate(steps, start=1):
        st.markdown(
            f"""
            <div class="step">
                <div class="step-title">Step {i}: {name}</div>
                <div class="step-desc">{description}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### 2️⃣ Run safe local diagnostics")

    st.write(
        "These checks are read-only. They inspect the local system and do not change network configuration."
    )

    if st.button("🔍 Run Local Diagnostics", type="primary"):
        with st.spinner("Running safe diagnostics..."):
            st.session_state.troubleshoot_results = local_checks(latest)

    if st.session_state.troubleshoot_results:
        results = st.session_state.troubleshoot_results
        total = len(results)
        passed = sum(1 for value in results.values() if value)

        st.markdown("### 3️⃣ Diagnostic results")

        st.progress(
            passed / total if total else 0,
            text=f"{passed}/{total} checks passed",
        )

        for name, ok in results.items():
            if ok:
                st.success(f"✓ {name}: PASS")
            else:
                st.warning(f"⚠ {name}: NEEDS ATTENTION")

        st.markdown("### 4️⃣ Recommended next action")

        st.markdown(
            f"""
            <div class="result">
                <b>{recommendation}</b>
                <br><br>
                <span class="small">
                    After making a safe corrective change, run the diagnostics
                    again and compare the new telemetry with the previous state.
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("### 5️⃣ Verification")

        if st.button("🔄 Verify Network Again"):
            if latest is not None:
                new_data = telemetry()
                new_diagnosis, new_evidence, new_recommendation, new_severity = diagnose(
                    new_data["latency"],
                    new_data["packet_loss"],
                    new_data["bandwidth"],
                    new_data["cpu"],
                )

                if new_severity == "LOW":
                    st.success("✅ Verification passed: network is currently healthy.")
                else:
                    st.warning(
                        f"⚠️ Issue may still be present: {new_diagnosis}"
                    )

                st.write(new_evidence)

# ===================== SIMULATOR =====================
elif nav == "🧪 Simulator":
    st.markdown("## 🧪 What-If Network Simulator")
    st.caption("Change conditions and instantly see the probable diagnosis.")

    a, b, c, d = st.columns(4)

    with a:
        latency = st.slider("Latency (ms)", 0, 500, 45)

    with b:
        loss = st.slider("Packet Loss (%)", 0.0, 30.0, 1.0)

    with c:
        bandwidth = st.slider("Bandwidth (%)", 0, 100, 50)

    with d:
        cpu = st.slider("CPU (%)", 0, 100, 45)

    diagnosis, evidence, recommendation, severity = diagnose(
        latency, loss, bandwidth, cpu
    )

    st.divider()

    if severity == "CRITICAL":
        st.error(diagnosis)
    elif severity in ["HIGH", "MEDIUM"]:
        st.warning(diagnosis)
    else:
        st.success(diagnosis)

    st.write("**Evidence:**", evidence)
    st.info("**Recommended Action:** " + recommendation)

# ===================== ABOUT =====================
else:
    st.markdown("## ℹ️ About NetGuard AI")

    st.write(
        """
        NetGuard AI is an offline-first network monitoring and troubleshooting
        prototype. It combines live telemetry, explainable diagnosis,
        safe local diagnostics and guided troubleshooting.
        """
    )

    st.markdown("### Core workflow")
    st.success("Monitor → Detect → Diagnose → Troubleshoot → Verify")

    st.markdown("### Technology")
    st.write(
        "Python • Streamlit • Pandas • NumPy • Plotly • psutil"
    )

st.divider()
st.caption("🛡️ NetGuard AI • COSMIX 2026 • Offline Network Intelligence")
