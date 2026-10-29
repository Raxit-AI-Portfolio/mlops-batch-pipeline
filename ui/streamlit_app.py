import os

import requests
import streamlit as st

st.set_page_config(page_title="Iris Predictor", page_icon="🌸")
st.title("Iris species predictor")

api_url = st.sidebar.text_input("API URL", os.getenv("APP_URL", "http://localhost:8000")).rstrip(
    "/"
)

FIELDS = {
    "sepal_length": ("Sepal length (cm)", 5.0),
    "sepal_width": ("Sepal width (cm)", 3.6),
    "petal_length": ("Petal length (cm)", 1.4),
    "petal_width": ("Petal width (cm)", 0.2),
}

with st.form("predict"):
    payload = {
        key: st.number_input(label, 0.0, 10.0, default, step=0.1)
        for key, (label, default) in FIELDS.items()
    }
    submitted = st.form_submit_button("Predict")

if submitted:
    try:
        resp = requests.post(f"{api_url}/predict", json=payload, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        st.success(f"Predicted species: **{result['species']}**")
        st.caption(f"class id {result['species_id']} · model version {result['model_version']}")
    except requests.RequestException as e:
        st.error(f"Request failed: {e}")
