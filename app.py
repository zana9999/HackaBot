import streamlit as st
import requests

BASE_URL = "http://127.0.0.1:8000/items"

st.title("Web Scraper Dashboard")

# Add new item
with st.form("add_item"):
    url = st.text_input("URL")
    notify_email = st.text_input("Email")
    submitted = st.form_submit_button("Add Item")
    if submitted:
        response = requests.post(BASE_URL + "/", json={
            "url": url,
            "notify_email": notify_email
        })
        st.write(response.json())

# List items
if st.button("Refresh Items"):
    items = requests.get(BASE_URL + "/").json()
    st.write(items)

# Check changes manually
if st.button("Check Changes"):
    changes = requests.get(BASE_URL + "/check-changes").json()
    st.write(changes)
