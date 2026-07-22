import streamlit as st
import requests
from typing import Dict, Any, Optional, List

BASE_URL = "http://localhost:8000"

class APIClient:
    @staticmethod
    def get_headers() -> Dict[str, str]:
        headers = {}
        if "token" in st.session_state and st.session_state["token"]:
            headers["Authorization"] = f"Bearer {st.session_state['token']}"
        return headers

    @classmethod
    def login(cls, email: str, password: str) -> bool:
        """
        Authenticates against backend using form data.
        """
        try:
            response = requests.post(
                f"{BASE_URL}/api/auth/login",
                data={"username": email, "password": password},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                st.session_state["token"] = data["access_token"]
                st.session_state["email"] = email
                st.session_state["authenticated"] = True
                return True
            else:
                return False
        except Exception as e:
            st.error(f"Failed to connect to backend: {e}")
            return False

    @classmethod
    def logout(cls):
        st.session_state["token"] = None
        st.session_state["email"] = None
        st.session_state["authenticated"] = False
        st.rerun()

    @classmethod
    def get(cls, path: str, params: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        try:
            response = requests.get(
                f"{BASE_URL}{path}",
                headers=cls.get_headers(),
                params=params,
                timeout=5
            )
            if response.status_code == 401:
                cls.handle_unauthorized()
                return None
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"GET {path} error: {e}")
            return None

    @classmethod
    def post(cls, path: str, json_data: Dict[str, Any]) -> Optional[Any]:
        try:
            response = requests.post(
                f"{BASE_URL}{path}",
                headers=cls.get_headers(),
                json=json_data,
                timeout=5
            )
            if response.status_code == 401:
                cls.handle_unauthorized()
                return None
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"POST {path} error: {e}")
            return None

    @classmethod
    def put(cls, path: str, json_data: Dict[str, Any]) -> Optional[Any]:
        try:
            response = requests.put(
                f"{BASE_URL}{path}",
                headers=cls.get_headers(),
                json=json_data,
                timeout=5
            )
            if response.status_code == 401:
                cls.handle_unauthorized()
                return None
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"PUT {path} error: {e}")
            return None

    @classmethod
    def delete(cls, path: str) -> bool:
        try:
            response = requests.delete(
                f"{BASE_URL}{path}",
                headers=cls.get_headers(),
                timeout=5
            )
            if response.status_code == 401:
                cls.handle_unauthorized()
                return False
            return response.status_code in [200, 204]
        except Exception as e:
            print(f"DELETE {path} error: {e}")
            return False

    @classmethod
    def handle_unauthorized(cls):
        st.session_state["authenticated"] = False
        st.session_state["token"] = None
        st.session_state["email"] = None
        st.warning("Session expired. Please log in again.")
        st.rerun()
