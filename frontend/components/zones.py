import streamlit as st
from frontend.utils.api_client import APIClient

def render_zones():
    st.title("Restricted Zones Manager")
    
    # 1. Select Camera
    cameras = APIClient.get("/api/cameras/")
    if not cameras:
        st.warning("No cameras configured. Register a camera node first.")
        return
        
    camera_map = {cam["name"]: cam for cam in cameras}
    sel_cam_name = st.selectbox("Select Camera for Zone Editing", options=list(camera_map.keys()))
    camera = camera_map[sel_cam_name]
    
    col_list, col_draw = st.columns([1, 2])
    
    # List active zones on the left
    with col_list:
        st.subheader("Configured Zones")
        
        # Pull latest zones for this camera
        zones = APIClient.get(f"/api/zones/camera/{camera['id']}")
        
        if not zones:
            st.info("No restricted zones defined for this camera.")
        else:
            for zone in zones:
                status_lbl = "RESTRICTED" if zone["is_restricted"] else "SAFE"
                color = "#EF4444" if zone["is_restricted"] else "#22C55E"
                
                with st.container():
                    st.markdown(
                        f"""
                        <div style="background-color: #121824; border: 1px solid #1E293B; border-radius: 8px; padding: 12px; margin-bottom: 10px;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <b style="color: #F8FAFC;">{zone["name"]}</b>
                                <span style="color: {color}; font-size: 10px; font-weight: 700; border: 1px solid {color}44; border-radius: 4px; padding: 1px 5px;">{status_lbl}</span>
                            </div>
                            <p style="margin: 5px 0 0 0; font-size: 11px; color: #64748B; word-break: break-all;">Coords: {zone["polygon_coordinates"]}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    
                    if st.button("🗑️ Delete Zone", key=f"del_zone_{zone['id']}"):
                        success = APIClient.delete(f"/api/zones/{zone['id']}")
                        if success:
                            st.toast(f"Zone '{zone['name']}' deleted.")
                            st.rerun()
                        else:
                            st.error("Failed to delete zone.")
                            
        st.markdown("---")
        if st.button("🔄 Refresh Active Zones List", use_container_width=True):
            st.rerun()

    # Draw canvas on the right
    with col_draw:
        st.subheader("Draw Restricted Poly-Zone")
        st.caption("Click on the video canvas below to draw the polygon points. Connect at least 3 points, enter a name, and submit.")
        
        # Token for backend authentication inside iframe
        token = st.session_state.get("token", "")
        
        # HTML/JS Code for custom drawing tool
        canvas_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    margin: 0;
                    padding: 0;
                    background-color: #080B10;
                    color: #E2E8F0;
                    font-family: sans-serif;
                }}
                .canvas-container {{
                    position: relative;
                    width: 640px;
                    height: 480px;
                    border: 2px solid #1E293B;
                    border-radius: 8px;
                    overflow: hidden;
                    background-color: #000;
                }}
                #bg-img {{
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 640px;
                    height: 480px;
                    pointer-events: none;
                    z-index: 1;
                }}
                #draw-canvas {{
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 640px;
                    height: 480px;
                    z-index: 2;
                    cursor: crosshair;
                }}
                .controls {{
                    margin-top: 15px;
                    display: flex;
                    gap: 10px;
                    align-items: center;
                }}
                input[type="text"] {{
                    background-color: #121824;
                    border: 1px solid #1E293B;
                    color: #F8FAFC;
                    padding: 8px 12px;
                    border-radius: 6px;
                    width: 250px;
                    outline: none;
                }}
                button {{
                    background-color: #2563EB;
                    color: #fff;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: background 0.2s;
                }}
                button:hover {{
                    background-color: #1D4ED8;
                }}
                button.secondary {{
                    background-color: #334155;
                }}
                button.secondary:hover {{
                    background-color: #475569;
                }}
            </style>
        </head>
        <body>
            <div class="canvas-container">
                <img id="bg-img" src="http://localhost:8000/api/cameras/{camera['id']}/snapshot?t={str(hash(sel_cam_name))}" alt="Snapshot" />
                <canvas id="draw-canvas" width="640" height="480"></canvas>
            </div>
            
            <div class="controls">
                <input type="text" id="zone-name" placeholder="Enter Zone Name (e.g. Zone A)" />
                <button id="btn-save">💾 Save Zone</button>
                <button id="btn-clear" class="secondary">🗑️ Clear Canvas</button>
            </div>

            <script>
                const canvas = document.getElementById('draw-canvas');
                const ctx = canvas.getContext('2d');
                const points = [];
                
                canvas.addEventListener('mousedown', function(e) {{
                    const rect = canvas.getBoundingClientRect();
                    const x = Math.round(e.clientX - rect.left);
                    const y = Math.round(e.clientY - rect.top);
                    
                    points.push([x, y]);
                    draw();
                }});
                
                function draw() {{
                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                    
                    if (points.length === 0) return;
                    
                    // Draw dots
                    ctx.fillStyle = '#EF4444';
                    points.forEach(pt => {{
                        ctx.beginPath();
                        ctx.arc(pt[0], pt[1], 5, 0, 2 * Math.PI);
                        ctx.fill();
                    }});
                    
                    // Draw lines
                    ctx.strokeStyle = '#EF4444';
                    ctx.lineWidth = 2;
                    ctx.beginPath();
                    ctx.moveTo(points[0][0], points[0][1]);
                    for (let i = 1; i < points.length; i++) {{
                        ctx.lineTo(points[i][0], points[i][1]);
                    }}
                    
                    if (points.length > 2) {{
                        ctx.lineTo(points[0][0], points[0][1]);
                        ctx.fillStyle = 'rgba(239, 68, 68, 0.2)';
                        ctx.fill();
                    }}
                    ctx.stroke();
                }}
                
                document.getElementById('btn-clear').addEventListener('click', function() {{
                    points.length = 0;
                    draw();
                }});
                
                document.getElementById('btn-save').addEventListener('click', function() {{
                    const name = document.getElementById('zone-name').value.trim();
                    if (!name) {{
                        alert('Please specify a Zone Name first.');
                        return;
                    }}
                    if (points.length < 3) {{
                        alert('Please define at least 3 points for the polygon.');
                        return;
                    }}
                    
                    // Send directly to FastAPI backend
                    fetch('http://localhost:8000/api/zones/camera/{camera['id']}', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                            'Authorization': 'Bearer {token}'
                        }},
                        body: JSON.stringify({{
                            name: name,
                            polygon_coordinates: JSON.stringify(points),
                            is_restricted: true
                        }})
                    }})
                    .then(response => {{
                        if (response.ok) {{
                            alert('Restricted Zone "' + name + '" registered successfully!');
                            points.length = 0;
                            document.getElementById('zone-name').value = '';
                            draw();
                        }} else {{
                            alert('Failed to register restricted zone.');
                        }}
                    }})
                    .catch(err => {{
                        alert('Communication error with backend: ' + err.message);
                    }});
                }});
            </script>
        </body>
        </html>
        """
        st.components.v1.html(canvas_html, height=550)
