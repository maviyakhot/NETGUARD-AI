import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="NetGuard AI",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ NetGuard AI")
st.caption("AI-Based Network Problem Detection & Offline Assistant")

st.info(
    "🔒 OFFLINE MODE ACTIVE — Network telemetry is processed locally. "
    "No data is sent to an external API."
)

# =========================================================
# DATA GENERATOR
# =========================================================

@st.cache_data
def generate_network_data(scenario="Normal Network", n=180):

    rng = np.random.default_rng(42)

    timestamps = pd.date_range(
        "2026-08-31 08:00",
        periods=n,
        freq="min"
    )

    latency = rng.normal(45, 8, n).clip(5)
    packet_loss = rng.normal(1.0, 0.4, n).clip(0)
    bandwidth = rng.normal(55, 8, n).clip(5, 100)
    cpu = rng.normal(45, 10, n).clip(5, 100)
    memory = rng.normal(50, 10, n).clip(5, 100)

    # ---------------------------------------------
    # Simulate different network problems
    # ---------------------------------------------

    if scenario == "🔴 Network Congestion":

        for i in range(110, 145):
            latency[i] += rng.normal(160, 20)
            packet_loss[i] += rng.normal(8, 2)
            bandwidth[i] += rng.normal(30, 5)

    elif scenario == "🟠 CPU Overload":

        for i in range(120, 150):
            cpu[i] += rng.normal(45, 5)
            memory[i] += rng.normal(20, 5)
            latency[i] += rng.normal(40, 10)

    elif scenario == "🟣 Bandwidth Saturation":

        for i in range(115, 150):
            bandwidth[i] += rng.normal(40, 5)
            latency[i] += rng.normal(70, 15)

    elif scenario == "🔴 Packet Loss":

        for i in range(115, 150):
            packet_loss[i] += rng.normal(12, 2)
            latency[i] += rng.normal(90, 20)

    return pd.DataFrame({
        "timestamp": timestamps,
        "latency_ms": latency,
        "packet_loss_pct": packet_loss,
        "bandwidth_util_pct": bandwidth,
        "cpu_usage_pct": cpu,
        "memory_usage_pct": memory
    })


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.header("⚙️ Network Simulation")

scenario = st.sidebar.selectbox(
    "Select network condition",
    [
        "🟢 Normal Network",
        "🔴 Network Congestion",
        "🟠 CPU Overload",
        "🟣 Bandwidth Saturation",
        "🔴 Packet Loss"
    ]
)

st.sidebar.success("Simulation ready")

st.sidebar.markdown("---")

uploaded = st.sidebar.file_uploader(
    "Upload real network CSV",
    type=["csv"]
)

if uploaded:

    df = pd.read_csv(uploaded)

    required = [
        "latency_ms",
        "packet_loss_pct",
        "bandwidth_util_pct",
        "cpu_usage_pct",
        "memory_usage_pct"
    ]

    missing = [
        col for col in required
        if col not in df.columns
    ]

    if missing:
        st.error(
            "CSV missing columns: "
            + ", ".join(missing)
        )
        st.stop()

    if "timestamp" not in df.columns:

        df["timestamp"] = pd.date_range(
            "2026-08-31 08:00",
            periods=len(df),
            freq="min"
        )

else:

    df = generate_network_data(scenario)

# =========================================================
# AI ANOMALY DETECTION
# =========================================================

features = [
    "latency_ms",
    "packet_loss_pct",
    "bandwidth_util_pct",
    "cpu_usage_pct",
    "memory_usage_pct"
]

X = df[features]

X = X.replace(
    [np.inf, -np.inf],
    np.nan
).fillna(0)

scaler = StandardScaler()

X_scaled = scaler.fit_transform(X)

model = IsolationForest(
    n_estimators=150,
    contamination=0.08,
    random_state=42
)

predictions = model.fit_predict(X_scaled)

df["anomaly"] = np.where(
    predictions == -1,
    1,
    0
)

df["anomaly_score"] = (
    -model.decision_function(X_scaled)
)

# =========================================================
# DIAGNOSTIC ENGINE
# =========================================================

def diagnose(row):

    latency = row["latency_ms"]
    loss = row["packet_loss_pct"]
    bandwidth = row["bandwidth_util_pct"]
    cpu = row["cpu_usage_pct"]
    memory = row["memory_usage_pct"]

    if loss >= 6 and latency >= 120:

        return (
            "🔴 Network Congestion",
            "High latency and packet loss were detected.",
            "Check bandwidth utilization, routing paths and network congestion.",
            "HIGH"
        )

    if loss >= 6:

        return (
            "🔴 Packet Loss Issue",
            "Packet loss is significantly above the normal baseline.",
            "Check cables, interfaces, Wi-Fi quality and routing.",
            "HIGH"
        )

    if cpu >= 85:

        return (
            "🟠 CPU Overload",
            "CPU utilization is unusually high.",
            "Identify high-CPU processes and inspect the workload.",
            "MEDIUM"
        )

    if bandwidth >= 90:

        return (
            "🟣 Bandwidth Saturation",
            "Network bandwidth is close to its maximum capacity.",
            "Identify heavy traffic sources and consider traffic prioritization.",
            "HIGH"
        )

    if latency >= 120:

        return (
            "🟡 High Latency",
            "Network response time is significantly elevated.",
            "Check congestion, routing and upstream connectivity.",
            "MEDIUM"
        )

    return (
        "🟢 Network Healthy",
        "Network metrics are within the expected baseline.",
        "Continue monitoring the network.",
        "LOW"
    )


# =========================================================
# FIND MOST RECENT ANOMALY
# =========================================================

anomaly_rows = df[df["anomaly"] == 1]

if len(anomaly_rows) > 0:

    latest = anomaly_rows.iloc[-1]

else:

    latest = df.iloc[-1]


diagnosis, evidence, recommendation, severity = diagnose(latest)

# =========================================================
# TOP METRICS
# =========================================================

st.subheader("📊 Network Health Overview")

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric(
    "Telemetry Points",
    len(df)
)

col2.metric(
    "AI Anomalies",
    int(df["anomaly"].sum())
)

col3.metric(
    "Avg Latency",
    f"{df['latency_ms'].mean():.1f} ms"
)

col4.metric(
    "Packet Loss",
    f"{df['packet_loss_pct'].mean():.2f}%"
)

col5.metric(
    "CPU Usage",
    f"{df['cpu_usage_pct'].mean():.1f}%"
)

st.divider()

# =========================================================
# MAIN DASHBOARD
# =========================================================

left, right = st.columns([2, 1])

with left:

    st.subheader("📈 Network Telemetry")

    metric = st.selectbox(
        "Select metric",
        features
    )

    fig = px.line(
        df,
        x="timestamp",
        y=metric,
        title=metric.replace("_", " ").title()
    )

    anomaly_data = df[
        df["anomaly"] == 1
    ]

    fig.add_scatter(
        x=anomaly_data["timestamp"],
        y=anomaly_data[metric],
        mode="markers",
        name="🚨 AI Anomaly"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


with right:

    st.subheader("🤖 AI Diagnosis")

    if severity == "HIGH":

        st.error("🚨 HIGH RISK")

    elif severity == "MEDIUM":

        st.warning("⚠️ MEDIUM RISK")

    else:

        st.success("🟢 SYSTEM STABLE")

    st.markdown(
        f"### {diagnosis}"
    )

    st.write(
        f"**Evidence:** {evidence}"
    )

    st.write(
        f"**Recommended Action:** {recommendation}"
    )

# =========================================================
# NETWORK HEALTH SCORE
# =========================================================

st.divider()

st.subheader("🧠 AI Network Health Score")

anomaly_ratio = df["anomaly"].mean()

health_score = max(
    0,
    int(100 - anomaly_ratio * 250)
)

st.progress(
    health_score / 100
)

st.write(
    f"### {health_score}/100"
)

if health_score >= 80:

    st.success(
        "Network condition is healthy."
    )

elif health_score >= 60:

    st.warning(
        "Network requires attention."
    )

else:

    st.error(
        "Network condition is critical."
    )

# =========================================================
# INCIDENT TABLE
# =========================================================

st.divider()

st.subheader("🚨 Detected Network Incidents")

events = df[
    df["anomaly"] == 1
].copy()

if len(events) > 0:

    events["Problem"] = events.apply(
        lambda row: diagnose(row)[0],
        axis=1
    )

    display_columns = [
        "timestamp",
        "latency_ms",
        "packet_loss_pct",
        "cpu_usage_pct",
        "memory_usage_pct",
        "Problem"
    ]

    st.dataframe(
        events[display_columns].tail(15),
        use_container_width=True
    )

else:

    st.success(
        "No abnormal network events detected."
    )

# =========================================================
# WHAT-IF ANALYSIS
# =========================================================

st.divider()

st.subheader("🧪 What-If Diagnostic Simulator")

st.write(
    "Change network conditions and see how the diagnostic engine responds."
)

c1, c2, c3 = st.columns(3)

with c1:

    test_latency = st.slider(
        "Latency (ms)",
        0,
        500,
        int(latest["latency_ms"])
    )

with c2:

    test_loss = st.slider(
        "Packet Loss (%)",
        0.0,
        30.0,
        float(latest["packet_loss_pct"])
    )

with c3:

    test_cpu = st.slider(
        "CPU Usage (%)",
        0,
        100,
        int(latest["cpu_usage_pct"])
    )

test_row = latest.copy()

test_row["latency_ms"] = test_latency
test_row["packet_loss_pct"] = test_loss
test_row["cpu_usage_pct"] = test_cpu

d, e, a, s = diagnose(test_row)

if s == "HIGH":

    st.error(
        f"🚨 Predicted Problem: {d}"
    )

elif s == "MEDIUM":

    st.warning(
        f"⚠️ Predicted Problem: {d}"
    )

else:

    st.success(
        f"🟢 Predicted Problem: {d}"
    )

st.write(
    f"**Evidence:** {e}"
)

st.write(
    f"**Recommended Action:** {a}"
)
# =========================================================
# OFFLINE NETWORK ASSISTANT
# =========================================================

st.divider()

st.subheader("🤖 Offline Network Assistant")

st.write(
    "Ask the assistant about the current network condition. "
    "Responses are generated locally from the detected telemetry."
)

question = st.text_input(
    "Ask a question",
    placeholder="Why is my network unhealthy?"
)

if question:

    q = question.lower()

    if any(word in q for word in ["why", "problem", "issue", "wrong", "unhealthy"]):

        st.markdown("### 🔎 Network Analysis")

        st.write(
            f"**Current condition:** {diagnosis}"
        )

        st.write(
            f"**What the system observed:** {evidence}"
        )

        st.write(
            f"**Recommended action:** {recommendation}"
        )

        st.caption(
            "This explanation is generated locally from network telemetry "
            "and the diagnostic engine."
        )

    elif any(word in q for word in ["latency", "ping", "delay"]):

        st.write(
            f"Current average latency is "
            f"**{df['latency_ms'].mean():.1f} ms**."
        )

        if df["latency_ms"].mean() > 100:
            st.warning(
                "Latency is elevated and may indicate congestion, "
                "routing problems or an overloaded network path."
            )
        else:
            st.success(
                "Latency is currently within the expected demo range."
            )

    elif any(word in q for word in ["packet", "loss"]):

        st.write(
            f"Current average packet loss is "
            f"**{df['packet_loss_pct'].mean():.2f}%**."
        )

        if df["packet_loss_pct"].mean() > 5:
            st.error(
                "Packet loss is high. Check interfaces, cables, "
                "wireless quality and routing."
            )
        else:
            st.success(
                "Packet loss is currently within the expected demo range."
            )

    elif "cpu" in q:

        st.write(
            f"Current average CPU usage is "
            f"**{df['cpu_usage_pct'].mean():.1f}%**."
        )

        if df["cpu_usage_pct"].mean() > 80:
            st.warning(
                "CPU utilization is high. Inspect resource-heavy "
                "processes and services."
            )
        else:
            st.success(
                "CPU utilization is currently within the expected range."
            )

    elif any(word in q for word in ["recommend", "fix", "solution", "solve"]):

        st.write(
            f"### 🛠️ Recommended Action"
        )

        st.info(recommendation)

    else:

        st.info(
            "Try asking: "
            "'Why is my network unhealthy?', "
            "'What is the latency?', "
            "'Is there packet loss?', or "
            "'How can I fix this?'"
        )
# =========================================================
# AI EXPLANATION
# =========================================================

with st.expander("🔬 How does the AI work?"):

    st.write(
        """
        **Step 1:** Network telemetry is collected locally.

        **Step 2:** The data is standardized before analysis.

        **Step 3:** Isolation Forest performs unsupervised anomaly detection.

        **Step 4:** Detected anomalies are analyzed using network diagnostic rules.

        **Step 5:** The system provides an explainable problem category,
        supporting evidence and troubleshooting recommendations.

        The prototype is designed for offline operation so sensitive
        network telemetry does not need to leave the local system.
        """
    )
