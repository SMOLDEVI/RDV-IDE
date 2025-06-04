# src/utils/recent_projects.py
import os
import json

RECENT_PROJECTS_FILE = "recent_projects.json"
MAX_RECENT_PROJECTS = 5

def load_recent_projects():
    if not os.path.exists(RECENT_PROJECTS_FILE):
        return []
    try:
        with open(RECENT_PROJECTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("recent_projects", [])
    except Exception:
        return []

def save_recent_projects(project_paths):
    try:
        with open(RECENT_PROJECTS_FILE, "w", encoding="utf-8") as f:
            json.dump({"recent_projects": project_paths}, f, indent=2)
    except Exception:
        pass

def add_recent_project(path):
    projects = load_recent_projects()
    if path in projects:
        projects.remove(path)
    projects.insert(0, path)
    if len(projects) > MAX_RECENT_PROJECTS:
        projects.pop()
    save_recent_projects(projects)