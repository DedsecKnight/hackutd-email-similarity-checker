import numpy as np
import pandas as pd
import streamlit as st

from fetch_email import get_all_judge_emails

HIGH_SIMILARITY_THRESHOLD = 0.55

st.set_page_config("HackUTD Judging Request Email Similarity Report", layout="wide")
st.title("HackUTD Judging Request Email Similarity Report")

data_load_state = st.text("Loading data...")
data = get_all_judge_emails()
data_load_state.text("Loading data...done!")

if st.checkbox("Show raw data"):
    st.subheader("Raw data")
    st.write(data)

st.subheader("High Similarity Emails")
for idx, row in data.iterrows():
    if row["similarity_score"] >= HIGH_SIMILARITY_THRESHOLD and row["most_similar_to"] > idx:
        with st.expander(
            f"**{row["subject"]}** and **{data.iloc[row["most_similar_to"]]["subject"]}**"
        ):
            with st.container(border=True):
                if row["most_similar_to"] != -1:
                    st.metric(
                        label="Similarity Score",
                        value="{:.6f}".format(row["similarity_score"]),
                    )
                else:
                    st.metric(label="Similarity Score", value="N/A")
            if row["most_similar_to"] != -1:
                col1, col2 = st.columns(2)
                with col1.container(border=True):
                    st.write(f"**From**: {row["sender"]}")
                    st.write(row["content"])
                with col2.container(border=True):
                    st.write(f"**From**: {data.iloc[row["most_similar_to"]]["sender"]}")
                    st.write(data.iloc[row["most_similar_to"]]["content"])

st.subheader("Emails")
for idx, row in data.iterrows():
    with st.expander(f"{idx}\. **{row["subject"]}**"):
        stats_tab, comparison_tab = st.tabs(["Stats", "Comparison"])
        with stats_tab.container(border=True):
            st.write(f"**Sender**: {row["sender"]}")
        c = stats_tab.container()
        col1, col2 = c.columns(2)
        with col1.container(border=True):
            if row["most_similar_to"] != -1:
                st.metric(
                    label="Highest Similarity Score",
                    value="{:.6f}".format(row["similarity_score"]),
                )
            else:
                st.metric(label="Highest Similarity Score", value="N/A")
            with col2.container(border=True):
                if row["most_similar_to"] != -1:
                    st.metric(label="Most similar to", value=row["most_similar_to"])
                else:
                    st.metric(label="Most similar to", value="N/A")
        with comparison_tab.container(border=True):
            if row["most_similar_to"] != -1:
                st.metric(
                    label="Similarity Score",
                    value="{:.6f}".format(row["similarity_score"]),
                )
            else:
                st.metric(label="Similarity Score", value="N/A")
        if row["most_similar_to"] != -1:
            col1, col2 = comparison_tab.columns(2)
            with col1.container(border=True):
                st.write(f"**From**: {row["sender"]}")
                st.write(row["content"])
            with col2.container(border=True):
                st.write(f"**From**: {data.iloc[row["most_similar_to"]]["sender"]}")
                st.write(data.iloc[row["most_similar_to"]]["content"])
