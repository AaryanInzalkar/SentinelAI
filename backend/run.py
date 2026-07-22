import sys
import os
import uvicorn

# Determine the workspace root directory (one level up from run.py)
workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Add it to sys.path for the current process
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

# Set PYTHONPATH environment variable so spawned stat reload subprocesses inherit it
current_python_path = os.environ.get("PYTHONPATH", "")
if current_python_path:
    os.environ["PYTHONPATH"] = f"{workspace_root}{os.pathsep}{current_python_path}"
else:
    os.environ["PYTHONPATH"] = workspace_root

if __name__ == "__main__":
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
