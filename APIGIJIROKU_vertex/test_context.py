import streamlit as st
try:
    st.write(f"Origin: {st.context.headers.get('origin')}")
    st.write(f"Host: {st.context.headers.get('host')}")
except Exception as e:
    st.write(f"Error: {e}")
