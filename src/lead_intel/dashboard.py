import streamlit as st

from lead_intel.engine import demo_engine

st.set_page_config(page_title="Customer 360", layout="wide")
engine = demo_engine()
st.title("Customer 360 Lead Intelligence")
st.caption("Synthetic, consent-aware lead prioritization")
funnel = engine.funnel()
cols = st.columns(4)
for col, (stage, value) in zip(cols, funnel["stages"].items()):
    col.metric(stage.title(), value)
st.subheader("Funnel conversion")
st.bar_chart(funnel["conversion_rates"])
key = st.selectbox("Resolved identity", list(engine.profiles()))
threshold = st.slider("MQL threshold", 0.0, 1.0, 0.65)
result = engine.score(key, threshold)
st.metric("Lead probability", f"{result['probability']:.1%}", result["route"])
st.bar_chart(result["contributions"])
st.json(result)

