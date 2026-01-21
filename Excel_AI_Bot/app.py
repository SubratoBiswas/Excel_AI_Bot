import os
import streamlit as st
from dotenv import load_dotenv
import pandas as pd

from excel_store import ExcelStore
from llm_agent import generate_sql

load_dotenv()

st.set_page_config(page_title="Excel Analysis Bot", layout="wide")
st.title("📊 Excel Analysis Bot (multi-file)")

if "store" not in st.session_state:
    st.session_state.store = ExcelStore()

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.header("Upload Excel files")
    uploads = st.file_uploader(
        "Upload one or more .xlsx files",
        type=["xlsx", "xls"],
        accept_multiple_files=True
    )

    if uploads:
        for f in uploads:
            st.session_state.store.add_excel_file(f.name, f.read())
        st.success(f"Loaded {len(uploads)} file(s).")

    st.subheader("Loaded tables")
    catalog = st.session_state.store.catalog()
    st.write(f"{len(catalog)} table(s) available.")
    for t, meta in catalog.items():
        st.caption(f"**{t}** — {meta['file']} / {meta['sheet']} — {meta['rows']} rows")

st.divider()

# Chat history
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

question = st.chat_input("Ask a question about your uploaded Excel files…")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        catalog = st.session_state.store.catalog()
        if not catalog:
            st.warning("Upload Excel files first.")
        else:
            plan = generate_sql(question, catalog)
            sql = plan["sql"]
            explanation = plan["explanation"]

            st.markdown("### Answer")
            st.markdown(explanation)

            st.markdown("### SQL used")
            st.code(sql, language="sql")

            try:
                df = st.session_state.store.run_sql(sql)
                st.markdown("### Results")
                st.dataframe(df, use_container_width=True)
            except Exception as e:
                st.error(f"SQL execution failed: {e}")

    st.session_state.messages.append(
        {"role": "assistant", "content": f"{plan['explanation']}\n\nSQL:\n{plan['sql']}"}
    )
