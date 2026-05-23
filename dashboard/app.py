import pathlib
import pandas as pd
import plotly.express as px
import streamlit as st


# ---------------------------------------------------------
# Page config
# ---------------------------------------------------------

st.set_page_config(
    page_title="EF Proficiency Dashboard",
    page_icon="🌍",
    layout="wide"
)


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def section(title: str, description: str | None = None):
    st.divider()
    st.header(title)

    if description:
        st.markdown(description)


@st.cache_data
def load_data():

    project_root = pathlib.Path(__file__).resolve().parent.parent

    data_path = (
        project_root
        / "data"
        / "processed"
        / "merged_analytical.csv"
    )

    return pd.read_csv(data_path)


def apply_standard_layout(fig, height=650):

    fig.update_layout(
        title_x=0.5,
        height=height,
        margin=dict(l=0, r=0, t=60, b=0),
        font=dict(size=12)
    )

    return fig


# ---------------------------------------------------------
# Load dataset
# ---------------------------------------------------------

df = load_data()


# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------

st.sidebar.title("Dashboard controls")

available_years = sorted(
    df.dropna(subset=["gap_pct"])["year"].unique()
)

selected_year = st.sidebar.selectbox(
    "Select year",
    available_years,
    index=len(available_years) - 1
)

filtered_df = (
    df[df["year"] == selected_year]
    .dropna(subset=["gap_pct"])
)


# ---------------------------------------------------------
# Header
# ---------------------------------------------------------

st.title("European EF Proficiency Dashboard")

st.markdown(
    """
This dashboard explores relative English proficiency disparities
across European countries by combining educational exposure
indicators with EF English proficiency measures.

The analysis focuses on the concept of *relative proficiency gap*,
defined as the difference between observed English proficiency
performance and expected outcomes based on learning exposure indicators.

A temporal lag alignment strategy was applied during preprocessing
to better account for delayed effects between educational exposure
and measured proficiency outcomes.

Results should be interpreted cautiously due to differences in
data availability, country coverage, and the exploratory nature
of the analytical framework.
"""
)


# ---------------------------------------------------------
# KPI section
# ---------------------------------------------------------

col1, col2, col3 = st.columns(3)

col1.metric(
    "Countries",
    filtered_df["iso3"].nunique()
)

col2.metric(
    "Average gap",
    f"{filtered_df['gap_pct'].mean():.3f}"
)

col3.metric(
    "Selected year",
    int(selected_year)
)


# ---------------------------------------------------------
# Choropleth
# ---------------------------------------------------------

section(
    "European spatial distribution",
    """
Relative EF proficiency gaps across European countries
for the selected year.
"""
)

fig_map = px.choropleth(
    filtered_df,

    locations="iso3",
    color="gap_pct",

    scope="europe",
    projection="natural earth",

    color_continuous_scale=[
        [0.0, "#B22222"],
        [0.5, "#F5F5F5"],
        [1.0, "#2E8B57"]
    ],

    range_color=[-1, 1],

    hover_name="iso3",

    hover_data={
        "iso3": False,
        "gap_pct": ":.2f",
        "learning_percentile": ":.2f",
        "ef_percentile": ":.2f"
    },

    labels={
        "gap_pct": "Gap"
    }
)

fig_map.update_traces(
    hovertemplate=
    "<b>%{location}</b><br>" +
    "Gap: %{z:.2f}<br>" +
    "<extra></extra>"
)

fig_map.update_geos(
    showcountries=True,
    countrycolor="white",

    showcoastlines=True,
    coastlinecolor="lightgray",

    showland=True,
    landcolor="#F8F8F8",

    showframe=False
)

fig_map.update_layout(
    coloraxis_colorbar_title="Gap"
)

apply_standard_layout(fig_map)

st.plotly_chart(
    fig_map,
    use_container_width=True
)


# ---------------------------------------------------------
# European temporal trend
# ---------------------------------------------------------

section(
    "European temporal evolution",
    """
Average relative EF proficiency gap across Europe
over time.
"""
)

yearly_gap = (
    df.dropna(subset=["gap_pct"])
    .groupby("year", as_index=False)["gap_pct"]
    .mean()
)

fig_trend = px.line(
    yearly_gap,

    x="year",
    y="gap_pct",

    markers=True,

    title="Average European EF proficiency gap over time"
)

fig_trend.update_traces(
    line=dict(
        color="#2E8B57",
        width=3
    )
)

fig_trend.add_hline(
    y=0,
    line_dash="dash",
    line_color="black",
    opacity=0.6
)

fig_trend.update_layout(
    yaxis_title="Average gap",
    xaxis_title="Year"
)

apply_standard_layout(fig_trend, height=420)

st.plotly_chart(
    fig_trend,
    use_container_width=True
)


# ---------------------------------------------------------
# Country comparison
# ---------------------------------------------------------

section(
    "Country performance comparison",
    """
Comparison of the strongest positive and negative
relative EF proficiency gaps across Europe.
"""
)

country_gap = (
    filtered_df.groupby("iso3", as_index=False)["gap_pct"]
    .mean()
    .dropna()
    .sort_values("gap_pct")
)

extremes = pd.concat([
    country_gap.head(8),
    country_gap.tail(8)
])

fig_bar = px.bar(
    extremes,

    x="gap_pct",
    y="iso3",

    orientation="h",

    color="gap_pct",

    color_continuous_scale=[
        [0.0, "#B22222"],
        [0.5, "#F5F5F5"],
        [1.0, "#2E8B57"]
    ],

    range_color=[-1, 1],

    title="Countries with the strongest relative EF proficiency gaps",

    labels={
        "gap_pct": "Relative proficiency gap",
        "iso3": "Country"
    }
)

fig_bar.add_vline(
    x=0,
    line_dash="dash",
    line_color="black",
    opacity=0.7
)

fig_bar.update_layout(
    coloraxis_colorbar_title="Gap"
)

apply_standard_layout(fig_bar, height=500)

st.plotly_chart(
    fig_bar,
    use_container_width=True
)


# ---------------------------------------------------------
# Italy vs Europe
# ---------------------------------------------------------

section(
    "Italy compared with the European average",
    """
Comparison between Italy and the European average
relative EF proficiency gap across time.
"""
)

europe_avg = (
    df.dropna(subset=["gap_pct"])
    .groupby("year", as_index=False)["gap_pct"]
    .mean()
)

italy = (
    df[df["iso3"] == "ITA"]
    .dropna(subset=["gap_pct"])
)

fig_line = px.line()

fig_line.add_scatter(
    x=europe_avg["year"],
    y=europe_avg["gap_pct"],

    mode="lines+markers",

    name="Europe average",

    line=dict(
        color="#2E8B57",
        width=3
    )
)

fig_line.add_scatter(
    x=italy["year"],
    y=italy["gap_pct"],

    mode="lines+markers",

    name="Italy",

    line=dict(
        color="#B22222",
        width=3
    )
)

fig_line.add_hline(
    y=0,
    line_dash="dash",
    line_color="black",
    opacity=0.6
)

fig_line.update_layout(
    title="Italy compared with the European average EF proficiency gap",
    yaxis_title="Gap"
)

apply_standard_layout(fig_line, height=520)

st.plotly_chart(
    fig_line,
    use_container_width=True
)


st.divider()

st.markdown(
    """
### Project repository

Source code, notebooks, preprocessing pipeline and dashboard
implementation are available on GitHub:

https://github.com/lolipop913/Project-Visualisation-EF
"""
)

# ---------------------------------------------------------
# Filtered dataset
# ---------------------------------------------------------

with st.expander("View filtered dataset"):

    st.dataframe(
        filtered_df,
        use_container_width=True
    )