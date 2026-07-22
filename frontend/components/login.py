import streamlit as st
from frontend.utils.api_client import APIClient

def render_login():
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown(
            """
            <div style="background-color: #121824; padding: 40px; border-radius: 16px; border: 1px solid #1E293B; box-shadow: 0 10px 25px rgba(0,0,0,0.5)">
                <h2 style="text-align: center; color: #F8FAFC; margin-bottom: 5px;">SentinelAI Portal</h2>
                <p style="text-align: center; color: #94A3B8; font-size: 14px; margin-bottom: 30px;">Intelligent Surveillance Assistant Login</p>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        # Streamlit forms cannot be placed easily inside HTML, so we render standard inputs inside the columns
        with st.form("login_form"):
            email = st.text_input("Security Email Address", placeholder="e.g. admin@sentinel.ai")
            password = st.text_input("Access Password", type="password", placeholder="••••••••")
            submit = st.form_submit_button("Authenticate Portal")
            
            if submit:
                if not email or not password:
                    st.error("Please provide both email and password.")
                else:
                    success = APIClient.login(email, password)
                    if success:
                        st.success("Access Granted. Loading Dashboard...")
                        st.rerun()
                    else:
                        st.error("Authentication failed. Invalid email or password.")
                        
        st.markdown(
            """
            <div style="text-align: center; margin-top: 20px;">
                <p style="color: #64748B; font-size: 12px;">Authorized Personnel Only. SentinelAI Security System v1.0.0</p>
            </div>
            """,
            unsafe_allow_html=True
        )
