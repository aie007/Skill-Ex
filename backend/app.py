import streamlit as st
from trend_engine.engine import TrendEngine
import plotly.express as px

st.set_page_config(page_title="Job Skill Trend Radar", layout="wide")

# Initialize Engine
engine = TrendEngine("api_ingestion_job/job_market.db")

st.title(" Tech Skill Trend Engine")
st.markdown("---")

try:
    raw_data = engine.fetch_data()

    st.sidebar.header("Settings")
    time_res = st.sidebar.selectbox("Time Resolution", ["D", "W", "M"], index=1)
    top_n = st.sidebar.slider("Show Top N Skills", 5, 20, 10)
    
    trend_data = engine.get_timeseries_trends(raw_data, freq=time_res)
    momentum = engine.calculate_momentum(trend_data)

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Skill Demand Over Time (%)")
        selected_skills = st.multiselect("Filter Skills", trend_data.columns.tolist(), default=trend_data.columns[:5].tolist())
        
        if selected_skills:
            fig = px.line(trend_data[selected_skills], labels={"value": "Market Share %", "posted_at": "Date"})
            st.plotly_chart(fig, width='stretch')

    with col2:
        st.subheader("Skill Momentum")
        st.caption("Growth rate compared to previous period")
        if not momentum.empty:
            st.dataframe(momentum.head(top_n).to_frame("Growth Score"), width='stretch')
        else:
            st.info("Not enough data points for momentum yet.")

except Exception as e:
    st.error(f"Error loading database: {e}")
    st.info("Make sure your SQLite database path is correct and contains the jobs/skills tables.")