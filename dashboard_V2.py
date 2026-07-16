import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px



# ==========================================================
# PAGE CONFIG
# ==========================================================

st.set_page_config(
    page_title="Health-Risk Failure Dashboard",
    layout="wide"
)

st.title("Health-Risk Failure Dashboard")

# ==========================================================
# LOAD DATA
# ==========================================================

@st.cache_data
def load_file(uploaded_file):

    if uploaded_file.name.endswith(".csv"):
        return pd.read_csv(uploaded_file)

    return pd.read_excel(uploaded_file)


uploaded_file = st.sidebar.file_uploader(
    "Upload Dataset",
    type=["csv", "xlsx", "xls"]
)

st.sidebar.caption("Supported formats: CSV, XLSX, XLS")

if uploaded_file is None:
    st.info(
        "Upload a CSV or Excel file from the sidebar to display the dashboard. "
        "If you don't see the sidebar, expand the menu in the top-left corner."
    )
    st.stop()

df = load_file(uploaded_file)

# ==========================================================
# COLUMN SELECTION
# ==========================================================

numeric_cols = [
    c
    for c in df.columns
    if pd.api.types.is_numeric_dtype(df[c])
]

health_col = st.sidebar.selectbox(
    "Health Metric",
    numeric_cols
)

risk_col = st.sidebar.selectbox(
    "Risk Metric",
    [c for c in numeric_cols if c != health_col]
)

failure_col = st.sidebar.selectbox(
    "Failure Event Column",
    df.columns
)


# ==========================================================
# RELAY POPULATION FILTER
# ==========================================================

distribution_col = st.sidebar.selectbox(
    "Distribution Column",
    df.columns,
    index=df.columns.get_loc("distribution")
    if "distribution" in df.columns
    else 0
)

available_distribution_values = (
    df[distribution_col]
    .dropna()
    .astype(str)
    .unique()
    .tolist()
)

distribution_filter = st.sidebar.multiselect(
    "Relay Population",
    available_distribution_values,
    default=available_distribution_values
)

working_df = df[
    df[distribution_col].astype(str).isin(distribution_filter)
].copy()

if working_df.empty:
    st.error(
        "No records available after applying the relay population filter. "
        "Check the selected distribution column and selected values."
    )
    st.stop()



# ==========================================================
# TOP N / TOP %
# ==========================================================

selection_mode = st.sidebar.radio(
    "Selection Mode",
    [
        "Top N Records",
        "Top Percent"
    ]
)

max_records = len(working_df)

if selection_mode == "Top N Records":

    selected_size = st.sidebar.slider(
        "Top N",
        min_value=1,
        max_value=max_records,
        value=min(100, max_records),
        step=1
    )

else:

    selected_percent = st.sidebar.slider(
        "Top Percent",
        min_value=1,
        max_value=100,
        value=10,
        step=1
    )

    selected_size = max(
        1,
        int(max_records * selected_percent / 100)
    )

st.sidebar.markdown(
    f"### Selected Records: {selected_size:,}"
)


# ==========================================================
# QUARTILES
# ==========================================================

health_quartiles = ["Q1", "Q2", "Q3", "Q4"]
risk_quartiles = ["Q1", "Q2", "Q3", "Q4"]



working_df["Health_Q"] = pd.Series(dtype="object", index=working_df.index)

health_mask = working_df[health_col].notna()

if health_mask.sum() >= 4:

    working_df.loc[health_mask, "Health_Q"] = safe_qcut(
        working_df.loc[health_mask, health_col],
        q=4,
        labels=health_quartiles,
    )



working_df["Risk_Q"] = pd.Series(dtype="object", index=working_df.index)

risk_mask = working_df[risk_col].notna()

if risk_mask.sum() >= 4:

    working_df.loc[risk_mask, "Risk_Q"] = safe_qcut(
        working_df.loc[risk_mask, risk_col],
        q=4,
        labels=risk_quartiles,
    )


#quartiles = ["Q1", "Q2", "Q3", "Q4"]





# ==========================================================
# HELPERS
# ==========================================================

def create_heatmap_data(df_subset, rows, cols,type):

    counts = pd.crosstab(
        df_subset[rows],
        df_subset[cols]
    )

    if type == 'health':

        counts = counts.reindex(
            index=health_quartiles,
            columns=risk_quartiles,
            fill_value=0
        )

    else:

        counts = counts.reindex(
                    index=risk_quartiles,
                    columns=health_quartiles,
                    fill_value=0
                )
    pct = (
        counts /
        counts.values.sum()
        * 100
    )

    return counts, pct



def plot_heatmap(df_pct, title):

    fig = px.imshow(
        df_pct,
        text_auto=".1f",
        color_continuous_scale="Blues",
        aspect="auto"
    )

    fig.update_traces(
        texttemplate="%{z:.1f}%",
        textfont={
                    "size": 16,
                }
    )


    fig.update_layout(
        title=title,
        height=800,
        width=1000,
        font=dict(size=16),
        margin=dict(
            l=50,
            r=50,
            t=80,
            b=50
        )
    )

    
    
    fig.update_xaxes(
        tickfont=dict(size=12)
    )

    fig.update_yaxes(
        tickfont=dict(size=12)
    )

    return fig


def safe_qcut(series, q, labels):
    try:
        return pd.qcut(
            series,
            q=q,
            labels=labels,
            duplicates="drop"
        ).astype("object")
    except Exception:
        unique_values = series.dropna().unique()
        bins = min(q, max(1, len(unique_values)))
        if bins == 1:
            return pd.Series(
                [labels[0]] * len(series),
                index=series.index,
                dtype="object"
            )

        try:
            return pd.cut(
                series,
                bins=bins,
                labels=labels[:bins]
            ).astype("object")
        except Exception:
            return pd.Series(
                [labels[0]] * len(series),
                index=series.index,
                dtype="object"
            )


def calculate_failure_stats(
    subset,
    full_df,
    failure_col
):
    total_failures = (
        full_df[failure_col]
        .notna()
        .sum()
    )

    failures_found = (
        subset[failure_col]
        .notna()
        .sum()
    )

    failures_missed = (
        total_failures -
        failures_found
    )

    # fnr = (
    #     failures_missed /
    #     total_failures *
    #     100
    #     if total_failures > 0
    #     else 0
    # )

    failure_rate = (
        failures_found /
        len(subset)
        * 100
        if len(subset) > 0
        else 0
    )

    return pd.DataFrame({
        "Metric": [
            "Selected Records",
            "Failures Found",
            "Failures Missed",
            "Failure Rate (%)",
            # "False Negative Rate (%)"
        ],
        "Value": [
            len(subset),
            failures_found,
            failures_missed,
            round(failure_rate, 2),
            # round(fnr, 2)
        ]
    })


def quartile_distribution(
    subset,
    quartile_col
):

    if quartile_col == "Health_Q":
        quartiles = health_quartiles
    else:
        quartiles = risk_quartiles

    return (
        subset[quartile_col]
        .value_counts()
        .reindex(quartiles)
        .fillna(0)
        .astype(int)
        .reset_index()
        .rename(
            columns={
                "index": quartile_col,
                quartile_col: "Count"
            }
        )
    )


def failure_breakdown(
    subset,
    quartile_col,
    failure_col
):

    temp = (
        subset
        .groupby(quartile_col)
        .agg(
            Total=(quartile_col, "size"),
            Failures=(
                failure_col,
                lambda x: x.notna().sum()
            )
        )
    )

    temp["Failure %"] = (
        temp["Failures"]
        / temp["Total"]
        * 100
    ).round(2)

    return temp.reset_index()

# ==========================================================
# TOP HEALTH
# ==========================================================

top_health = (
    working_df
    .sort_values(
        health_col,
        ascending=False
    )
    .head(selected_size)
)

health_counts, health_pct = create_heatmap_data(
    top_health,
    "Health_Q",
    "Risk_Q",
    "health"
)

health_stats = calculate_failure_stats(
    top_health,
    working_df,
    failure_col
)

health_dist = quartile_distribution(
    top_health,
    "Risk_Q",
)

health_failure_breakdown = failure_breakdown(
    top_health,
    "Health_Q",
    failure_col
)

# ==========================================================
# TOP RISK
# ==========================================================

top_risk = (
    working_df
    .sort_values(
        risk_col,
        ascending=False
    )
    .head(selected_size)
)

risk_counts, risk_pct = create_heatmap_data(
    top_risk,
    "Risk_Q",
    "Health_Q",
    "risk"
)

risk_stats = calculate_failure_stats(
    top_risk,
    working_df,
    failure_col
)

risk_dist = quartile_distribution(
    top_risk,
    "Health_Q",
)

risk_failure_breakdown = failure_breakdown(
    top_risk,
    "Risk_Q",
    failure_col
)

# ==========================================================
# FAILURE ANALYSIS
# ==========================================================

failure_df = (
    working_df[
        working_df[failure_col].notna()
    ]
    .copy()
)

failure_counts, failure_pct = create_heatmap_data(
    failure_df,
    "Health_Q",
    "Risk_Q",
    "health"
)

failure_df["Combined_Q"] = (
    failure_df["Health_Q"].astype(str)
    + "-"
    + failure_df["Risk_Q"].astype(str)
)

combined_table = (
    failure_df["Combined_Q"]
    .value_counts()
    .reset_index()
)

combined_table.columns = [
    "Quartile Pair",
    "Failure Count"
]

combined_table["% of Failures"] = (
    combined_table["Failure Count"]
    /
    combined_table["Failure Count"].sum()
    * 100
).round(2)

# ==========================================================
# KPI BAR
# ==========================================================

total_failures = (
    working_df[failure_col]
    .notna()
    .sum()
)

health_captured = (
    top_health[failure_col]
    .notna()
    .sum()
)

risk_captured = (
    top_risk[failure_col]
    .notna()
    .sum()
)


k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("Original Relays", f"{len(df):,}")
k2.metric("Filtered Relays", f"{len(working_df):,}")
k3.metric("Failures", f"{total_failures:,}")
k4.metric("Health Captured", f"{health_captured:,}")
k5.metric("Risk Captured", f"{risk_captured:,}")


# ==========================================================
# TABS
# ==========================================================

tab1, tab2, tab3 = st.tabs([
    "Top Health",
    "Top Risk",
    "Failure Analysis"
])

# ==========================================================
# TAB 1
# ==========================================================

with tab1:

    st.subheader(
        f"Top {selected_size:,} Health Records"
    )

    st.plotly_chart(
        plot_heatmap(
            health_pct,
            "Health vs Risk"
        ),
        use_container_width=True
    )

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("### Heatmap Counts")
        st.dataframe(health_counts)

    with c2:
        st.markdown("### Risk Distribution")
        st.dataframe(health_dist)

    c3, c4 = st.columns(2)

    with c3:
        st.markdown("### Failure Statistics")
        st.dataframe(health_stats)

    with c4:
        st.markdown(
            "### Failure Breakdown by Health Quartile"
        )
        st.dataframe(
            health_failure_breakdown
        )

# ==========================================================
# TAB 2
# ==========================================================

with tab2:

    st.subheader(
        f"Top {selected_size:,} Risk Records"
    )

    st.plotly_chart(
        plot_heatmap(
            risk_pct,
            "Risk vs Health"
        ),
        use_container_width=True
    )

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("### Heatmap Counts")
        st.dataframe(risk_counts)

    with c2:
        st.markdown("### Health Distribution")
        st.dataframe(risk_dist)

    c3, c4 = st.columns(2)

    with c3:
        st.markdown("### Failure Statistics")
        st.dataframe(risk_stats)

    with c4:
        st.markdown(
            "### Failure Breakdown by Risk Quartile"
        )
        st.dataframe(
            risk_failure_breakdown
        )

# ==========================================================
# TAB 3
# ==========================================================

with tab3:

    st.subheader(
        "All Failure Records"
    )

    st.plotly_chart(
        plot_heatmap(
            failure_pct,
            "Failure Distribution Across Quartiles"
        ),
        use_container_width=True
    )

    c1, c2 = st.columns(2)

    with c1:
        st.markdown(
            "### Failure Counts by Quartile"
        )
        st.dataframe(
            failure_counts
        )

    with c2:
        st.markdown(
            "### Combined Quartile Analysis"
        )
        st.dataframe(
            combined_table,
            use_container_width=True
        )