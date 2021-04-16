from collections import Counter
import glob
import json
import os

import altair as alt
import pandas as pd
import streamlit as st

st.write("""
# awesome_python_project: Usage report

This is a sample usage report for a (fictional) Python project called `awesome_python_project`.

This report shows some of the information that you get right out of the box with Bugout:

1. What operating systems are your users using?
2. What Python versions are your users using?
3. How frequently are different users using your tool?
4. What are the common errors your users experience when using your tool?
""")

DATA_DIRECTORY = "./sample-data"

raw_data_glob = os.path.join(DATA_DIRECTORY, "*.json")
raw_data_files = glob.glob(raw_data_glob)
raw_data_dfs = []
for raw_data_file in raw_data_files:
    with open(raw_data_file, "r") as ifp:
        response = json.load(ifp)
        raw_data = response.get("results", [])
        raw_data_dfs.append(pd.DataFrame.from_dict(raw_data))
raw_df = pd.concat(raw_data_dfs)
df = raw_df.explode("tags", ignore_index=True)

matches_file = os.path.join(DATA_DIRECTORY, "matches.jsonl")
matches_df = pd.read_json(matches_file, lines=True)
matches_df["capture"] = [tag[capture_start:capture_end] if capture_end > -1 else tag[capture_start:] for tag, capture_start, capture_end in zip(matches_df.tag, matches_df.capture_start, matches_df.capture_end)]

st.write("## Operating systems")

os_counts = matches_df[matches_df.pattern == "os:#"].groupby(matches_df.capture).match.agg("sum").reset_index()

os_chart = alt.Chart(os_counts).mark_bar().encode(x="match", y="capture")
os_values = os_chart.mark_text(align="left", baseline="middle", dx=3).encode(text="match")
st.altair_chart(os_chart + os_values)

st.write("## Python versions")

python_version_counts = matches_df[matches_df.pattern == "python:#<1>.*"].groupby(matches_df.capture).match.agg('sum').reset_index()

python_chart = alt.Chart(python_version_counts).mark_bar().encode(x="match", y="capture")
python_values = python_chart.mark_text(align="left", baseline="middle", dx=3).encode(text="match")
st.altair_chart(python_chart + python_values)

st.write("## Most common errors")

df["exception"] = df.title.str.split(" - ").str[-1]
errors = df[(df.title != "activeloopai/Hub: System information") & (df.title != "Consent change") & (df.tags.str.startswith("session:"))]
exception_names = [value for value, _ in Counter(list(errors["exception"])).most_common()]
selected_error = exception_names[0]
errors_chart = alt.Chart(errors).mark_bar().encode(
    alt.X("count():Q"),
    alt.Y("exception", sort=alt.EncodingSortField(field="entry_url", op="count", order="descending")),
    color=alt.condition(
        alt.datum.exception == selected_error,
        alt.value("orange"),
        alt.value("steelblue"),
    ),
)
st.altair_chart(errors_chart, use_container_width=True)

st.write("## Sessions per client")

clients_df = df[df.tags.str.startswith("client:")]
sessions_df = df[df.tags.str.startswith("session:")]
client_sessions = clients_df.merge(sessions_df, left_on="entry_url", right_on="entry_url", how="inner", suffixes=("_client", "_session"))
client_sessions = client_sessions[["tags_client", "tags_session", "title_client"]]
client_sessions_chart = alt.Chart(client_sessions).mark_bar().encode(alt.X("tags_client:N", axis=None, sort=alt.EncodingSortField(field="tags_session", op="count", order="descending")), alt.Y("count():Q"))
st.altair_chart(client_sessions_chart, use_container_width=True)
