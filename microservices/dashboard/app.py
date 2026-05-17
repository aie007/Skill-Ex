import streamlit as st
import requests
import pandas as pd
import plotly.express as px

print("INFO: Starting AI Career Radar Dashboard...")

API_URL = "http://ml-api-service:8000"

st.set_page_config(page_title="AI Career Radar", layout="wide")
tabs = st.tabs([" Market Trends", "Resume Matcher"])


with tabs[0]:
    st.header("Global Tech Skill Demand")
    res = st.sidebar.selectbox("Resolution", ["D", "W", "M"], index=1)
    
    if st.button("Refresh Trends"):
        print("INFO: Refresh Trends button clicked.")
        with st.spinner("Fetching market data..."):
            print(f"INFO: Sending request to fetch market trends from: {API_URL}/trends?freq={res}")
            response = requests.get(f"{API_URL}/trends?freq={res}")
            if response.status_code == 200:
                data = response.json()
                if data:
                    print("INFO: Successfully fetched market trends.")
                    st.session_state.trend_df = pd.DataFrame(data).set_index('posted_at')
                    # Fetch Momentum
                    print(f"INFO: Sending request to fetch skill momentum from: {API_URL}/momentum")
                    mom_resp = requests.get(f"{API_URL}/momentum")
                    print("INFO: Successfully fetched skill momentum.")
                    st.session_state.momentum = pd.Series(mom_resp.json()).sort_values(ascending=False)
                else:
                    print("WARNING: Trend data endpoint returned empty data.")
                    st.warning("No trend data available in the database yet.")
            else:
                print(f"ERROR: Failed to fetch data from API. Status code: {response.status_code}")
                st.error("Failed to fetch data from API")

    if "trend_df" in st.session_state:
        trend_df = st.session_state.trend_df
        all_skills = trend_df.columns.tolist()
        
        col1, col2 = st.columns([4, 1])
        with col1:
            selected = st.multiselect("Select Skills to Plot", all_skills, default=all_skills[:5])
        with col2:
            if st.button("Clear Cache"):
                print("INFO: Clear Cache button clicked. Clearing trend data cache.")
                del st.session_state.trend_df
                st.rerun()

        if len(selected) > 40:
            st.error("Too many skills selected. Plotting more than 40 skills is disabled to prevent system crash. Please reduce your selection.")
        elif selected:
            try:
                fig = px.line(
                    trend_df[selected], 
                    labels={"value": "Market Share %", "posted_at": "Date"},
                    title="Skill Penetration Over Time"
                )
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error rendering chart: {e}")
        
        st.subheader("Skill Momentum (Fastest Growing)")
        st.dataframe(st.session_state.momentum.head(10).to_frame("Growth Score"))





with tabs[1]:
    st.header("Personalized Job Recommendations")
    uploaded_file = st.file_uploader("Upload Masked Resume (PDF)", type="pdf")
    
    if uploaded_file:
        print(f"INFO: PDF resume file '{uploaded_file.name}' uploaded by user.")
        with st.spinner("Processing via AI API..."):
            files = {"file": uploaded_file}
            print(f"INFO: Sending post request for recommendations to: {API_URL}/recommend")
            response = requests.post(f"{API_URL}/recommend", files=files)
            
            if response.status_code == 200:
                print("INFO: Recommendations returned successfully.")
                data = response.json()
                
                with st.expander("View Masked Resume (PII Redacted)"):
                    st.text(data['masked_resume'])
                
                st.info(f"**Extracted Skills:** {', '.join(data['extracted_skills'])}")
                
                for rec in data['recommendations']:
                    score_pct = int(rec['match_score'] * 100)
                    st.metric(label=f"{rec['title']} @ {rec['company']}", value=f"{score_pct}% Match")
                    if rec['missing_skills']:
                        st.write(f"**Skills to acquire:** {', '.join(rec['missing_skills'])}")
                    else:
                        st.success("Perfect skill match!")
                    st.divider()
            else:
                print(f"ERROR: Recommendation API connection error. Status code: {response.status_code}")
                st.error("API Connection Error")