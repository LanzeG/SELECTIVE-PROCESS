import streamlit as st
from tabs import main
from tabs import app

tab1, tab2 = st.tabs(["Selective", "Data Feed"])

with tab1:
    st.header("SELECTIVE")
    main.main()

with tab2:
    st.header("HEADER")
    app.run()
