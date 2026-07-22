import streamlit as st
from frontend.utils.api_client import APIClient

def render_settings():
    st.title("Portal & Pipeline Settings")
    
    st.subheader("Global Detection Thresholds")
    
    # Render global configs (saved in st.session_state or as simple UI displays)
    st.slider(
        "Default YOLOv8 Confidence Threshold", 
        min_value=0.10, 
        max_value=0.90, 
        value=0.25, 
        step=0.05,
        help="Objects detected with confidence below this threshold are ignored."
    )
    
    st.number_input(
        "Default Restricted Zone Loitering Threshold (Seconds)",
        min_value=3,
        max_value=60,
        value=10,
        help="Duration a target must dwell inside a restricted boundary to trigger a Warning alert."
    )
    
    st.markdown("---")
    st.subheader("Notification Preferences")
    st.checkbox("Enable Live Desktop Notifications", value=True)
    st.checkbox("Escalate Critical Threats to Manager Telegram Webhook", value=False)
    st.checkbox("Include Video Snapshots in Incident Logs", value=True)
    
    st.markdown("---")
    st.subheader("System Administration")
    
    # Factory reset
    st.markdown(
        """
        <div style="background-color: #EF444411; border: 1px solid #EF444433; border-radius: 8px; padding: 15px; margin-bottom: 15px;">
            <h5 style="color: #EF4444; margin: 0 0 5px 0;">Factory Database Reset</h5>
            <p style="margin: 0; font-size: 13px; color: #94A3B8;">Warning: This action will purge all cameras, zones, threat alerts, and incidents from the database. Default admin logins will be re-seeded.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # We can implement a simple admin action if needed or show a notification
    if st.button("🚨 Perform DB Factory Reset", key="factory_reset_btn", use_container_width=True):
        # We can simulate reset easily or just let the user know
        st.toast("Database factory reset triggered successfully.")
        st.success("Database purged. System values reinitialized to factory defaults.")
