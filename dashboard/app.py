import os
import streamlit as st
st.set_page_config(page_title="ReForge Workbench", layout="wide")
st.title("ReForge - Repository Migration Workbench")
st.caption("Flask -> FastAPI | Build-time automation with IBM Bob 2.0")
def show_md(path, empty_message):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            st.markdown(f.read())
    else:
        st.info(empty_message) 
left, right = st.columns(2)
with left:
    st.subheader("Migration Contract")
    show_md(
        "reforge/migration_contract.md",
        "Contract not generated yet."
    )
with right:
    st.subheader("Validation Report")
    show_md(
        "reforge/validation_report.md",
        "Validation report not generated yet."
    )
st.divider()
st.subheader("Evidence")
for name in [
    "reforge/baseline.md",
    "reforge/recon.md",
    "reforge/migration_log.md",
    "reforge/human_review.md",
]:
    st.write(name)