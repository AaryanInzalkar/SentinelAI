import streamlit as st
import os
from frontend.utils.api_client import APIClient
from datetime import datetime

def render_alerts():
    st.title("Threat Alerts Log")
    
    # 1. Fetch cameras for filtering
    cameras = APIClient.get("/api/cameras/")
    camera_map = {cam["id"]: cam["name"] for cam in cameras} if cameras else {}
    
    col_filters, col_list, col_details = st.columns([1, 2, 2])
    
    with col_filters:
        st.subheader("Filters")
        
        # Camera Filter
        cam_options = ["All Cameras"] + list(camera_map.values())
        sel_cam_name = st.selectbox("Filter by Camera", options=cam_options)
        
        filter_cam_id = None
        if sel_cam_name != "All Cameras":
            filter_cam_id = [cid for cid, name in camera_map.items() if name == sel_cam_name][0]
            
        # Status Filter
        status_options = ["Active Only", "Dismissed Only", "All Alerts"]
        sel_status = st.selectbox("Filter by Status", options=status_options)
        
        filter_dismissed = None
        if sel_status == "Active Only":
            filter_dismissed = False
        elif sel_status == "Dismissed Only":
            filter_dismissed = True
            
        # Query parameters
        params = {}
        if filter_cam_id is not None:
            params["camera_id"] = filter_cam_id
        if filter_dismissed is not None:
            params["is_dismissed"] = filter_dismissed
            
        alerts = APIClient.get("/api/alerts/", params=params)
        
    with col_list:
        st.subheader("Logged Alerts")
        if not alerts:
            st.info("No threat alerts found matching selected filters.")
            selected_alert = None
        else:
            # We will display alerts in a selection list
            alert_items = []
            for alert in alerts:
                time_str = datetime.fromisoformat(alert["timestamp"].replace("Z", "+00:00")).strftime("%m/%d %H:%M:%S")
                cam_name = camera_map.get(alert["camera_id"], f"Cam #{alert['camera_id']}")
                status_label = "Dismissed" if alert["is_dismissed"] else "Active"
                label = f"[{time_str}] {cam_name} | Score: {alert['risk_score']}% ({status_label})"
                alert_items.append((label, alert))
                
            selected_label = st.radio(
                "Select Alert for Incident Details", 
                options=[item[0] for item in alert_items],
                label_visibility="collapsed"
            )
            
            selected_alert = [item[1] for item in alert_items if item[0] == selected_label][0]
            
    with col_details:
        st.subheader("Alert Analysis Details")
        if not selected_alert:
            st.caption("Select an alert from the list to view forensic details.")
        else:
            time_str = datetime.fromisoformat(selected_alert["timestamp"].replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M:%S")
            cam_name = camera_map.get(selected_alert["camera_id"], f"Cam #{selected_alert['camera_id']}")
            
            st.markdown(
                f"""
                <div style="background-color: #121824; border: 1px solid #1E293B; border-radius: 8px; padding: 15px; margin-bottom: 15px;">
                    <h4 style="margin: 0 0 10px 0; color: #F8FAFC;">{selected_alert["description"]}</h4>
                    <p style="margin: 3px 0; font-size: 13px; color: #94A3B8;"><b>Source Camera:</b> {cam_name}</p>
                    <p style="margin: 3px 0; font-size: 13px; color: #94A3B8;"><b>Logged Time:</b> {time_str}</p>
                    <p style="margin: 3px 0; font-size: 13px; color: #94A3B8;"><b>AI Threat Score:</b> <span style="color: #EF4444; font-weight: 700;">{selected_alert["risk_score"]}%</span></p>
                    <p style="margin: 3px 0; font-size: 13px; color: #94A3B8;"><b>Archive Status:</b> {"Dismissed" if selected_alert["is_dismissed"] else "Active Monitoring"}</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
            
            # Explainable AI section
            st.markdown("##### 🧠 Explainable AI Diagnostic")
            st.info(selected_alert["explanation"] or "No behavioral explanation logged.")
            
            # Image snapshot rendering
            if selected_alert.get("image_snapshot_path"):
                filename = os.path.basename(selected_alert["image_snapshot_path"])
                snapshot_url = f"http://localhost:8000/snapshots/{filename}"
                st.markdown("##### 📸 Event Snapshot")
                st.image(snapshot_url, caption=f"Alert Snapshot (ID: #{selected_alert['id']})", use_container_width=True)
                
            # Dismiss button
            if not selected_alert["is_dismissed"]:
                if st.button("📁 Dismiss & Archive Alert", use_container_width=True):
                    success = APIClient.put(f"/api/alerts/{selected_alert['id']}/dismiss", {})
                    if success:
                        st.toast("Alert successfully dismissed and archived.")
                        st.rerun()
                    else:
                        st.error("Failed to dismiss alert.")
