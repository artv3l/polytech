import streamlit as st


st.sidebar.title("Audio files")
if st.sidebar.button("Refresh"):
    pass

uploader = st.file_uploader("Upload audio")
