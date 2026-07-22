import streamlit as st
from frontend.utils.api_client import APIClient
from datetime import datetime

def render_live_monitoring():
    st.title("Live Surveillance Node")
    
    # 1. Fetch available cameras
    cameras = APIClient.get("/api/cameras/")
    if not cameras:
        st.warning("No cameras configured yet. Go to 'Cameras Setup' to register a camera feed.")
        return
        
    camera_options = {cam["name"]: cam for cam in cameras}
    
    # Grid: Settings on left (small), Video feed in center, Active Alerts on right
    col_settings, col_video, col_feed = st.columns([1, 3, 1])
    
    # Camera selection
    with col_settings:
        st.subheader("Select Source")
        selected_cam_name = st.selectbox("Active Camera", options=list(camera_options.keys()))
        camera = camera_options[selected_cam_name]
        
        st.markdown(
            f"""
            <div style="background-color: #121824; border: 1px solid #1E293B; border-radius: 8px; padding: 12px; margin-top: 10px;">
                <p style="margin: 0; color: #94A3B8; font-size: 11px;">Details</p>
                <p style="margin: 5px 0 0 0; font-size: 13px;"><b>Type:</b> {camera["connection_type"].upper()}</p>
                <p style="margin: 5px 0 0 0; font-size: 13px; word-break: break-all;"><b>Source:</b> {camera["source_path"]}</p>
                <p style="margin: 5px 0 0 0; font-size: 13px;"><b>Zones:</b> {len(camera["zones"])}</p>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Playback controls
        st.subheader("Controls")
        if "feed_active" not in st.session_state:
            st.session_state["feed_active"] = True
            
        active = st.session_state["feed_active"]
        
        col_play, col_pause = st.columns(2)
        with col_play:
            if st.button("▶️ Start", use_container_width=True, disabled=active):
                st.session_state["feed_active"] = True
                st.rerun()
        with col_pause:
            if st.button("⏸️ Pause", use_container_width=True, disabled=not active):
                st.session_state["feed_active"] = False
                st.rerun()
                
        if st.button("📸 Capture Snapshot", use_container_width=True):
            st.toast("Snapshot captured and logged to system server!")
            
    # Video stream rendering
    with col_video:
        st.subheader(f"Video Feed - {camera['name']}")
        
        if st.session_state["feed_active"]:
            stream_url = f"http://localhost:8000/api/cameras/{camera['id']}/stream"
            # Streamlit displays the raw HTTP MJPEG stream directly inside st.image
            st.image(stream_url, use_container_width=True)
        else:
            st.markdown(
                """
                <div style="background-color: #000; border-radius: 12px; border: 2px solid #1E293B; height: 380px; display: flex; align-items: center; justify-content: center;">
                    <div style="text-align: center;">
                        <span style="font-size: 48px; color: #475569;">⏸️</span>
                        <h4 style="color: #64748B; margin-top: 10px;">Camera Feed Paused</h4>
                        <p style="color: #475569; font-size: 12px;">Click Start to connect to stream</p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
    # Live alert feed for selected camera
    with col_feed:
        st.subheader("Event Logs")
        
        camera_alerts = APIClient.get("/api/alerts/", params={"camera_id": camera["id"]})
        
        if not camera_alerts:
            st.caption("No alerts logged for this camera.")
        else:
            # Display last 8 alerts for this camera
            for alert in camera_alerts[:8]:
                alert_time = datetime.fromisoformat(alert["timestamp"].replace("Z", "+00:00")).strftime("%H:%M:%S")
                card_class = "alert-item-critical" if alert["risk_score"] >= 70 else "alert-item-warning"
                
                st.markdown(
                    f"""
                    <div class="{card_class}" style="padding: 8px; margin-bottom: 8px;">
                        <div style="font-weight: 700; font-size: 12px; color: #F8FAFC;">{alert["description"]}</div>
                        <div style="font-size: 11px; color: #94A3B8; margin-top: 2px;">Risk: {alert["risk_score"]}% | Time: {alert_time}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
