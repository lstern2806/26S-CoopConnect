"""Shared API helpers for Streamlit admin pages."""

import os

import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:4000")


def api_request(method: str, url: str, **kwargs) -> requests.Response:
    """Perform HTTP request with consistent timeout; return response or raise."""
    return requests.request(method, url, timeout=10, **kwargs)


def api_error_banner(exc: requests.exceptions.RequestException):
    """Show a user-friendly connection error."""
    st.error(f"Error connecting to the API: {exc}")
    st.caption(f"Ensure the API server is running (default: {API_BASE_URL}).")


def response_error_message(resp: requests.Response) -> str:
    """Return a readable API error, handling JSON and HTML fallback bodies."""
    try:
        payload = resp.json()
        if isinstance(payload, dict):
            return str(payload.get("error") or payload.get("message") or payload)
        return str(payload)
    except ValueError:
        raw_text = (resp.text or "").strip()
        if "<!doctype html" in raw_text.lower():
            return f"HTTP {resp.status_code}: {resp.reason}"
        return raw_text or f"HTTP {resp.status_code}: request failed"
