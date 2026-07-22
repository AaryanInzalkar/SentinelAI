import streamlit as st
import os

# 1. Page Configuration (must be first Streamlit command)
st.set_page_config(
    page_title="SentinelAI - Security Assistant",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Inject Custom Enterprise CSS
css_path = os.path.join(os.path.dirname(__file__), "style.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# 3. Session State Initialization
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "token" not in st.session_state:
    st.session_state["token"] = None
if "email" not in st.session_state:
    st.session_state["email"] = None

# 4. Import Component Renders
from frontend.components.login import render_login
from frontend.components.sidebar import render_sidebar
from frontend.components.dashboard import render_dashboard
from frontend.components.live_monitoring import render_live_monitoring
from frontend.components.alerts import render_alerts
from frontend.components.incidents import render_incidents
from frontend.components.cameras import render_cameras
from frontend.components.zones import render_zones
from frontend.components.analytics import render_analytics
from frontend.components.settings import render_settings

# 5. Routing Logic
if not st.session_state["authenticated"]:
    render_login()
else:
    selected_page = render_sidebar()
    
    if selected_page == "Dashboard":
        render_dashboard()
    elif selected_page == "Live Monitoring":
        render_live_monitoring()
    elif selected_page == "Alerts Log":
        render_alerts()
    elif selected_page == "Incidents Log":
        render_incidents()
    elif selected_page == "Cameras Setup":
        render_cameras()
    elif selected_page == "Zones Manager":
        render_zones()
    elif selected_page == "Analytics & Reports":
        render_analytics()
    elif selected_page == "Portal Settings":
        render_settings()
