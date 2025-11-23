import requests
import streamlit as st

import common

c_backend_url = "http://localhost:8080"

def update_analyzes():
    response = requests.get(f"{c_backend_url}/analyzes")
    st.session_state.analyzes = {doc["id"]: common.Analyze(**doc) for doc in response.json()}

def get_result(id):
    response = requests.get(f"{c_backend_url}/result/{id}")
    return common.Result(**response.json())

st.session_state.setdefault("current_page", "Upload")
if st.session_state.setdefault("analyzes", []):
    update_analyzes()


st.sidebar.title("Audio files")

if st.sidebar.button("Upload file"):
    st.session_state.current_page = "Upload"

if st.sidebar.button("Refresh"):
    update_analyzes()

st.sidebar.divider()

for id, analyze in st.session_state.analyzes.items():
    if st.sidebar.button(f"{analyze.title}", key=id):
        st.session_state.current_page = id

if st.session_state.current_page == "Upload":
    uploaded_file = st.file_uploader("Upload audio")
    if uploaded_file and st.button("Start analyze"):
        with st.spinner("Отправка файла..."):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            response = requests.post(f"{c_backend_url}/upload", files=files)

        if response.status_code != 200:
            st.error(response.json()["message"])
        else:
            st.success(response.json()["message"])
            update_analyzes()
else:
    analyze: common.Analyze = st.session_state.analyzes[st.session_state.current_page]
    st.title(analyze.title)
    st.text(f"Status: {analyze.status}")
    if analyze.status == "ready":
        st.divider()
        result = get_result(analyze.result_id)

        st.text(f"Длительность: {result.duration} c.")
        st.text(f"BPM: {result.bpm}")
        st.text(f"Частота дискретизации: {result.sample_rate}")
        
