import streamlit as st
import os
from frontend.utils.api_client import APIClient
from datetime import datetime

def render_incidents():
    st.title("Incident Case Management")
    
    # Fetch cameras for naming
    cameras = APIClient.get("/api/cameras/")
    camera_map = {cam["id"]: cam["name"] for cam in cameras} if cameras else {}
    
    col_filters, col_list, col_details = st.columns([1, 2, 2])
    
    with col_filters:
        st.subheader("Filters")
        
        status_filter = st.selectbox(
            "Filter by Case Status",
            options=["All Statuses", "Open", "Closed", "False Alarm"]
        )
        
        params = {}
        if status_filter != "All Statuses":
            params["status_filter"] = status_filter
            
        incidents = APIClient.get("/api/incidents/", params=params)
        
    with col_list:
        st.subheader("Security Cases")
        if not incidents:
            st.info("No security incidents found.")
            selected_incident = None
        else:
            incidents_options = []
            for inc in incidents:
                time_str = datetime.fromisoformat(inc["created_at"].replace("Z", "+00:00")).strftime("%m/%d %H:%M")
                cam_name = camera_map.get(inc["camera_id"], f"Cam #{inc['camera_id']}")
                label = f"[{time_str}] Case #{inc['id']} - {cam_name} ({inc['status']})"
                incidents_options.append((label, inc))
                
            selected_label = st.radio(
                "Select Case",
                options=[item[0] for item in incidents_options],
                label_visibility="collapsed"
            )
            
            selected_incident = [item[1] for item in incidents_options if item[0] == selected_label][0]
            
    with col_details:
        st.subheader("Case Details & Resolution")
        if not selected_incident:
            st.caption("Select a case from the list to manage incident logs.")
        else:
            time_str = datetime.fromisoformat(selected_incident["created_at"].replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M:%S")
            cam_name = camera_map.get(selected_incident["camera_id"], f"Cam #{selected_incident['camera_id']}")
            
            st.markdown(
                f"""
                <div style="background-color: #121824; border: 1px solid #1E293B; border-radius: 8px; padding: 15px; margin-bottom: 15px;">
                    <h4 style="margin: 0 0 10px 0; color: #EF4444;">Case Reference #{selected_incident["id"]}</h4>
                    <p style="margin: 3px 0; font-size: 13px; color: #94A3B8;"><b>Source Camera:</b> {cam_name}</p>
                    <p style="margin: 3px 0; font-size: 13px; color: #94A3B8;"><b>Logged Time:</b> {time_str}</p>
                    <p style="margin: 3px 0; font-size: 13px; color: #94A3B8;"><b>Current Status:</b> <b>{selected_incident["status"]}</b></p>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Show alert info if available
            alert = selected_incident.get("alert")
            if alert:
                st.markdown("##### 🚨 Underlying Threat Alert Trigger")
                st.warning(alert["description"])
                st.info(alert["explanation"])
                
                # Show snapshot
                if alert.get("image_snapshot_path"):
                    filename = os.path.basename(alert["image_snapshot_path"])
                    snapshot_url = f"http://localhost:8000/snapshots/{filename}"
                    st.image(snapshot_url, caption="Incident Event Snapshot", use_container_width=True)
            
            # Edit Case Form
            st.markdown("---")
            st.markdown("##### Update Case File")
            
            with st.form("incident_edit_form"):
                new_status = st.selectbox(
                    "Resolution Status",
                    options=["Open", "Closed", "False Alarm"],
                    index=["Open", "Closed", "False Alarm"].index(selected_incident["status"])
                )
                
                current_notes = selected_incident["notes"] or ""
                new_notes = st.text_area("Case Analysis Notes", value=current_notes, placeholder="Enter response steps, findings, and mitigation details...")
                
                submit = st.form_submit_button("Commit Changes to Case File")
                
                if submit:
                    payload = {"status": new_status, "notes": new_notes}
                    success = APIClient.put(f"/api/incidents/{selected_incident['id']}", payload)
                    if success:
                        st.toast("Case file updated successfully.")
                        st.rerun()
                    else:
                        st.error("Failed to update case file.")
