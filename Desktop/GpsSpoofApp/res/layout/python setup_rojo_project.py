import os
import json
import subprocess

# Project name
project_name = "BrainrotStealingGame"

# Step 1: Make folders
folders = [
    "src/server",
    "src/client",
    "src/shared"
]

for folder in folders:
    os.makedirs(folder, exist_ok=True)

# Step 2: Create default.project.json
project_json = {
    "name": project_name,
    "tree": {
        "$className": "DataModel",
        "ServerScriptService": {
            "$path": "src/server"
        },
        "StarterPlayer": {
            "StarterPlayerScripts": {
                "$path": "src/client"
            }
        },
        "ReplicatedStorage": {
            "$path": "src/shared"
        }
    }
}

with open("default.project.json", "w") as f:
    json.dump(project_json, f, indent=4)

# Step 3: Initialize Rojo (if not already done)
try:
    subprocess.run(["rojo", "init"], check=True)
except Exception:
    print("⚠️ Could not run `rojo init`. Make sure Rojo is installed and in PATH.")

print(f"✅ {project_name} Rojo project created successfully!")