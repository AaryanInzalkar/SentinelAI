import streamlit as st
from frontend.utils.api_client import APIClient

def render_sidebar() -> str:
    """
    Renders sidebar and returns the selected page name.
    """
    with st.sidebar:
        st.markdown(
            """
            <div style="padding: 10px 0; margin-bottom: 20px;">
                <h2 style="margin: 0; color: #2563EB; font-size: 24px; font-weight: 800;">🛡️ SentinelAI</h2>
                <p style="margin: 0; color: #64748B; font-size: 11px;">Intelligent Surveillance Assistant</p>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        # User credentials info
        email = st.session_state.get("email", "operator@sentinel.ai")
        st.markdown(
            f"""
            <div style="background-color: #121824; border: 1px solid #1E293B; border-radius: 8px; padding: 10px; margin-bottom: 25px;">
                <p style="margin: 0; color: #94A3B8; font-size: 10px; text-transform: uppercase;">Operator Node</p>
                <p style="margin: 0; color: #F8FAFC; font-size: 13px; font-weight: 600; overflow: hidden; text-overflow: ellipsis;">{email}</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Navigation Options
        pages = [
            "Dashboard",
            "Live Monitoring",
            "Alerts Log",
            "Incidents Log",
            "Cameras Setup",
            "Zones Manager",
            "Analytics & Reports",
            "Portal Settings"
        ]
        
        selected_page = st.radio(
            "Navigation Menu", 
            options=pages, 
            label_visibility="collapsed"
        )
        
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        
        # Logout button
        if st.button("Disconnect Session", key="sidebar_logout", use_container_width=True):
            APIClient.logout()
            
    return selected_page
