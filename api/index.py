"""
Vercel Serverless Function entry point for FinSwarm.
Routes all /api/* requests to the FastAPI app in backend/app/main.py.
"""
import sys
import os

# Add project root to sys.path so `backend.app.main` is importable
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.app.main import app  # noqa: F401 — Vercel picks up `app` automatically
