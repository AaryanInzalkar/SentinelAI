import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
from frontend.utils.api_client import APIClient

def render_dashboard():
    st.title("Surveillance Dashboard")
    
    # 1. Fetch dashboard stats from FastAPI backend
    stats = APIClient.get("/api/dashboard/stats")
    if not stats:
        stats = {
            "active_cameras": 0,
            "total_alerts_today": 0,
            "unresolved_incidents": 0,
            "system_status": "Offline (Backend Unreachable)"
        }
        
    # Render KPI Cards in a row
    col1, col2, col3, col4 = st.columns(4)
    
    status_class = "metric-status-healthy"
    if "Warning" in stats["system_status"] or "Degraded" in stats["system_status"]:
        status_class = "metric-status-warning"
        
    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">System Health</div>
                <div class="metric-value {status_class}">{stats["system_status"]}</div>
            </div>
            """, 
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Active Cameras</div>
                <div class="metric-value">{stats["active_cameras"]}</div>
            </div>
            """, 
            unsafe_allow_html=True
        )
    with col3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Alerts Today</div>
                <div class="metric-value">{stats["total_alerts_today"]}</div>
            </div>
            """, 
            unsafe_allow_html=True
        )
    with col4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Open Incidents</div>
                <div class="metric-value" style="color: #EF4444;">{stats["unresolved_incidents"]}</div>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 2. Main content area: split into Charts (Left) and Active Alerts (Right)
    left_col, right_col = st.columns([2, 1])
    
    with left_col:
        st.subheader("Threat Analytics & Metrics")
        
        # Generate mock telemetry data for Plotly charts
        days = [datetime.now() - timedelta(days=i) for i in range(6, -1, -1)]
        day_names = [d.strftime("%a") for d in days]
        
        # Mock alerts timeline
        timeline_df = pd.DataFrame({
            "Day": day_names,
            "Critical Threats": [2, 1, 0, 4, 2, 5, stats["unresolved_incidents"]],
            "Minor Warnings": [8, 5, 4, 11, 7, 9, max(0, stats["total_alerts_today"] - stats["unresolved_incidents"])]
        })
        
        # Line chart for Alert frequency
        fig_line = px.line(
            timeline_df, 
            x="Day", 
            y=["Critical Threats", "Minor Warnings"],
            labels={"value": "Alert Count", "variable": "Severity"},
            title="Weekly Threat Frequency Timeline",
            color_discrete_sequence=["#EF4444", "#F59E0B"]
        )
        fig_line.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#94A3B8',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=20, r=20, t=50, b=20)
        )
        fig_line.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#1E293B')
        fig_line.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#1E293B')
        
        st.plotly_chart(fig_line, use_container_width=True)
        
        # Threat distribution pie chart
        dist_df = pd.DataFrame({
            "Severity": ["Critical Risk", "Warning Alert", "Low Risk"],
            "Count": [12, 28, 45]
        })
        fig_pie = px.pie(
            dist_df, 
            values="Count", 
            names="Severity",
            title="Threat Distribution by Risk Classification",
            color_discrete_sequence=["#EF4444", "#F59E0B", "#22C55E"],
            hole=0.4
        )
        fig_pie.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#94A3B8',
            margin=dict(l=20, r=20, t=50, b=20)
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with right_col:
        st.subheader("Live Threats Feed")
        
        # Fetch active alerts from backend
        alerts = APIClient.get("/api/alerts/", params={"is_dismissed": False})
        
        if not alerts:
            st.info("No active threats currently detected. System secure.")
        else:
            # Display last 5 active alerts
            for alert in alerts[:5]:
                alert_time = datetime.fromisoformat(alert["timestamp"].replace("Z", "+00:00")).strftime("%H:%M:%S")
                card_class = "alert-item-critical" if alert["risk_score"] >= 70 else "alert-item-warning"
                
                st.markdown(
                    f"""
                    <div class="{card_class}">
                        <div class="alert-title">⚠️ {alert["description"]}</div>
                        <div style="font-size: 13px; color: #E2E8F0; margin-bottom: 5px;">Risk Score: <b>{alert["risk_score"]}%</b></div>
                        <div class="alert-meta">Time: {alert_time} | ID: #{alert["id"]}</div>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
            
            if len(alerts) > 5:
                st.write(f"And {len(alerts) - 5} more active warnings. View details in Alerts Log.")
