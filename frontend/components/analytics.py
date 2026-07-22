import streamlit as st
import pandas as pd
import plotly.express as px
from frontend.utils.api_client import APIClient
from datetime import datetime

def render_analytics():
    st.title("Threat Intelligence Reports")
    
    # 1. Fetch data
    alerts = APIClient.get("/api/alerts/")
    cameras = APIClient.get("/api/cameras/")
    camera_map = {cam["id"]: cam["name"] for cam in cameras} if cameras else {}
    
    if not alerts:
        st.info("Insufficient threat telemetry data collected yet to render intelligence reports.")
        return
        
    # Convert to DataFrame
    data = []
    for a in alerts:
        dt = datetime.fromisoformat(a["timestamp"].replace("Z", "+00:00"))
        data.append({
            "Alert ID": a["id"],
            "Camera": camera_map.get(a["camera_id"], f"Cam #{a['camera_id']}"),
            "Risk Score (%)": a["risk_score"],
            "Timestamp": dt,
            "Date": dt.strftime("%Y-%m-%d"),
            "Hour": dt.hour,
            "Description": a["description"],
            "Status": "Dismissed" if a["is_dismissed"] else "Active"
        })
        
    df = pd.DataFrame(data)
    
    # KPI Row
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Telemetry Record Count</div>
                <div class="metric-value">{len(df)}</div>
            </div>
            """, 
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Average Risk Score</div>
                <div class="metric-value">{int(df["Risk Score (%)"].mean())}%</div>
            </div>
            """, 
            unsafe_allow_html=True
        )
    with col3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Most Active Node</div>
                <div class="metric-value" style="font-size: 22px;">{df["Camera"].mode()[0] if not df.empty else "None"}</div>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Plots
    col_left, col_right = st.columns(2)
    
    with col_left:
        # Alerts by Camera
        cam_counts = df["Camera"].value_counts().reset_index()
        cam_counts.columns = ["Camera Node", "Alert Count"]
        
        fig_cam = px.bar(
            cam_counts,
            x="Camera Node",
            y="Alert Count",
            title="Threat Alarms by Camera Node",
            color="Alert Count",
            color_continuous_scale="Viridis"
        )
        fig_cam.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#94A3B8')
        st.plotly_chart(fig_cam, use_container_width=True)
        
    with col_right:
        # Alerts by Hour of Day
        hour_counts = df["Hour"].value_counts().sort_index().reset_index()
        hour_counts.columns = ["Hour of Day", "Alert Count"]
        
        # Fill missing hours
        all_hours = pd.DataFrame({"Hour of Day": list(range(24))})
        hour_counts = pd.merge(all_hours, hour_counts, on="Hour of Day", how="left").fillna(0)
        
        fig_hour = px.area(
            hour_counts,
            x="Hour of Day",
            y="Alert Count",
            title="Alarm Activity Profile by Hour (24-Hour Cycle)",
            color_discrete_sequence=["#06B6D4"]
        )
        fig_hour.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#94A3B8')
        st.plotly_chart(fig_hour, use_container_width=True)
        
    # Telemetry Table & CSV Export
    st.subheader("Raw Security Telemetry Data")
    
    # Format datetimes for viewing
    view_df = df.copy()
    view_df["Timestamp"] = view_df["Timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
    st.dataframe(view_df[["Alert ID", "Timestamp", "Camera", "Risk Score (%)", "Description", "Status"]], use_container_width=True)
    
    # Export button
    csv_bytes = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Export Telemetry Data to CSV",
        data=csv_bytes,
        file_name=f"sentinel_ai_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        use_container_width=True
    )
