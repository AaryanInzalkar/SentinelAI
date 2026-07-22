import streamlit as st
from frontend.utils.api_client import APIClient

def render_cameras():
    st.title("Camera Nodes Administration")
    
    col_list, col_add = st.columns([2, 1])
    
    # 1. Fetch and list cameras
    with col_list:
        st.subheader("Registered Surveillance Devices")
        cameras = APIClient.get("/api/cameras/")
        
        if not cameras:
            st.info("No cameras registered. Use the configuration form on the right to add a device.")
        else:
            for cam in cameras:
                status_color = "#22C55E" if cam["is_active"] else "#64748B"
                status_txt = "ACTIVE" if cam["is_active"] else "DISABLED"
                
                with st.container():
                    st.markdown(
                        f"""
                        <div style="background-color: #121824; border: 1px solid #1E293B; border-radius: 8px; padding: 15px; margin-bottom: 12px;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <h4 style="margin: 0; color: #F8FAFC;">📷 {cam["name"]}</h4>
                                <span style="background-color: {status_color}22; color: {status_color}; font-size: 10px; font-weight: 700; padding: 3px 8px; border-radius: 12px; border: 1px solid {status_color}44;">{status_txt}</span>
                            </div>
                            <p style="margin: 8px 0 0 0; font-size: 12px; color: #94A3B8;"><b>Source Type:</b> {cam["connection_type"].upper()}</p>
                            <p style="margin: 4px 0 0 0; font-size: 12px; color: #94A3B8; word-break: break-all;"><b>Source Address:</b> {cam["source_path"]}</p>
                            <p style="margin: 4px 0 0 0; font-size: 12px; color: #94A3B8;"><b>Detection Confidence Limit:</b> {cam["detection_threshold"]}</p>
                            <p style="margin: 4px 0 0 0; font-size: 12px; color: #94A3B8;"><b>Loitering Warning Limit:</b> {cam["loitering_threshold"]}s</p>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
                    
                    # Delete Camera Button
                    if st.button(f"🗑️ Delete Node '{cam['name']}'", key=f"del_{cam['id']}"):
                        success = APIClient.delete(f"/api/cameras/{cam['id']}")
                        if success:
                            st.toast(f"Camera '{cam['name']}' successfully removed.")
                            st.rerun()
                        else:
                            st.error("Failed to delete camera.")
                            
    # 2. Add camera form
    with col_add:
        st.subheader("Configure New Device")
        
        with st.form("add_camera_form"):
            name = st.text_input("Device Name", placeholder="e.g. Main Entrance Gate")
            connection_type = st.selectbox(
                "Connection Protocol",
                options=["webcam", "file", "ip_camera"]
            )
            source_path = st.text_input(
                "Source Address / ID",
                placeholder="e.g., '0' for webcam, or video file path, or RTSP stream URL"
            )
            
            detect_thresh = st.slider("Object Detection Confidence Threshold", min_value=0.05, max_value=0.95, value=0.25, step=0.05)
            loiter_thresh = st.number_input("Loitering Exceeded Warning Limit (Seconds)", min_value=2, max_value=120, value=10)
            
            submit = st.form_submit_button("Register Camera Node")
            
            if submit:
                if not name or not source_path:
                    st.error("Please fill out all fields.")
                else:
                    payload = {
                        "name": name,
                        "connection_type": connection_type,
                        "source_path": source_path,
                        "is_active": True,
                        "detection_threshold": detect_thresh,
                        "loitering_threshold": loiter_thresh
                    }
                    success = APIClient.post("/api/cameras/", payload)
                    if success:
                        st.toast(f"Successfully registered camera: {name}")
                        st.rerun()
                    else:
                        st.error("Failed to register camera node.")
