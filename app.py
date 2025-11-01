import streamlit as st
import requests

BASE_URL = "http://127.0.0.1:8000/hackabot"

st.title("HackaBot Dashboard")

if st.button("Refresh Hackathons"):
    items = requests.get(BASE_URL + "/").json()
    st.write(items)

