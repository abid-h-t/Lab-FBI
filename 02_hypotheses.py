"""
STEP 2 - Test 5 hypotheses, 3 charts each (15 charts, 7 libraries).

Input : data/shr_clean.csv   (made by 01_load_and_clean.py)
Output: figures/h1a_... to figures/h5c_...  (.png for static charts,
        .html for interactive ones) and the numbers behind each chart
        printed in the terminal.

Run:  python 02_hypotheses.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import plotly.express as px
import altair as alt
import folium
import requests
from plotnine import (ggplot, aes, geom_line, geom_point, facet_wrap, labs,
                      theme_minimal, scale_color_manual, scale_x_continuous)
from bokeh.plotting import figure, output_file, save
from bokeh.models import ColumnDataSource
from bokeh.palettes import Category10

FIG = Path("figures")
FIG.mkdir(exist_ok=True)
sns.set_theme(style="whitegrid")

df = pd.read_csv("data/shr_clean.csv")
print(f"Loaded {len(df):,} homicide incidents, years {df.year.min()}-{df.year.max()}")


# ---------- small helpers -------------------------------------------------
def save_mpl(name):
    """Save the current matplotlib / seaborn figure as PNG."""
    plt.tight_layout()
    plt.savefig(FIG / f"{name}.png", dpi=150, bbox_inches="tight")
    plt.close("all")


def save_plotly(fig, name):
    """Interactive HTML always; PNG too if the kaleido package works."""
    fig.write_html(FIG / f"{name}.html")
    try:
        fig.write_image(FIG / f"{name}.png", scale=2)
    except Exception as err:
        print(f"  ({name}.png not written, open the .html and screenshot it: {err})")


def save_altair(chart, name):
    """Interactive HTML always; PNG too if vl-convert-python works."""
    chart.save(str(FIG / f"{name}.html"))
    try:
        chart.save(str(FIG / f"{name}.png"), scale_factor=2)
    except Exception as err:
        print(f"  ({name}.png not written, open the .html and screenshot it: {err})")


def show(title, table):
    print(f"\n--- {title} ---")
    print(table.round(1).to_string())


# ==========================================================================
# H1  The rise in homicides around 2020 was a FIREARM rise: gun homicides
#     grew much faster than non-gun homicides, and the firearm share went
#     up in every region.            (year x weapon x region)
# ==========================================================================
df["weapon_class"] = df["firearm"].map({True: "Firearm", False: "Other weapon"})

# 1a  matplotlib - line chart, counts indexed to the first year (=100)
yearly = df.groupby(["year", "weapon_class"]).size().unstack()
indexed = yearly / yearly.iloc[0] * 100
show("H1a homicides by weapon class, first year = 100", indexed)
fig, ax = plt.subplots(figsize=(9, 5))
ax.plot(indexed.index, indexed["Firearm"], marker="o", lw=2.5, color="#c0392b", label="Firearm")
ax.plot(indexed.index, indexed["Other weapon"], marker="o", lw=2.5, color="#34495e", label="Other weapon")
ax.axhline(100, color="grey", lw=1, ls="--")
ax.set_xticks(indexed.index)
ax.set_xlabel("Year")
ax.set_ylabel(f"Homicides (index, {indexed.index[0]} = 100)")
ax.set_title("H1a  Firearm vs non-firearm homicides over time (matplotlib)")
ax.legend()
save_mpl("h1a_matplotlib_indexed_lines")

# 1b  seaborn - heatmap of firearm share, region x year
heat = df.pivot_table(index="region", columns="year", values="firearm", aggfunc="mean") * 100
show("H1b firearm share (%) by region and year", heat)
plt.figure(figsize=(11, 3.8))
sns.heatmap(heat, annot=True, fmt=".0f", cmap="Reds", cbar_kws={"label": "% committed with a firearm"})
plt.title("H1b  Firearm share of homicides by region and year (seaborn)")
plt.xlabel("Year")
plt.ylabel("")
save_mpl("h1b_seaborn_heatmap")

# 1c  plotly - interactive line chart, one line per region
long = heat.reset_index().melt(id_vars="region", var_name="year", value_name="firearm_pct")
fig = px.line(long, x="year", y="firearm_pct", color="region", markers=True,
              title="H1c  Firearm share of homicides by region (plotly)",
              labels={"firearm_pct": "% committed with a firearm", "year": "Year", "region": "Region"})
save_plotly(fig, "h1c_plotly_region_lines")


# ==========================================================================
# H2  Who kills depends on the victim's sex: women are killed mainly by
#     intimate partners and family, men by acquaintances and strangers, and
#     this gap has NOT narrowed over time.   (victim sex x relationship x year)
# ==========================================================================
known = df.dropna(subset=["victim_sex", "rel_group"])
REL_ORDER = ["Intimate partner", "Family", "Acquaintance", "Stranger"]

# 2a  seaborn - grouped bar chart
tab = pd.crosstab(known["victim_sex"], known["rel_group"], normalize="index") * 100
show("H2a relationship of offender to victim (% within victim sex)", tab[REL_ORDER])
bars = tab.reset_index().melt(id_vars="victim_sex", var_name="rel_group", value_name="pct")
plt.figure(figsize=(9, 5))
sns.barplot(data=bars, x="rel_group", y="pct", hue="victim_sex", order=REL_ORDER,
            palette={"Female": "#8e44ad", "Male": "#2980b9"})
plt.title("H2a  Who was the offender? By victim sex (seaborn)")
plt.xlabel("Offender's relationship to victim")
plt.ylabel("% of homicides with known relationship")
plt.legend(title="Victim sex")
save_mpl("h2a_seaborn_grouped_bar")

# 2b  altair - 100% stacked bars per year, one panel per victim sex
counts = known.groupby(["year", "victim_sex", "rel_group"]).size().reset_index(name="n")
chart = alt.Chart(counts).mark_bar().encode(
    x=alt.X("year:O", title="Year"),
    y=alt.Y("n:Q", stack="normalize", axis=alt.Axis(format="%"), title="Share of homicides"),
    color=alt.Color("rel_group:N", sort=REL_ORDER, title="Relationship"),
    column=alt.Column("victim_sex:N", title="Victim sex"),
    tooltip=["year", "victim_sex", "rel_group", "n"],
).properties(width=330, height=300,
             title="H2b  Relationship mix by year and victim sex (altair)")
save_altair(chart, "h2b_altair_stacked_facets")

# 2c  plotnine - small multiples, one panel per relationship group
totals = counts.groupby(["year", "victim_sex"])["n"].transform("sum")
counts["pct"] = counts["n"] / totals * 100
show("H2c intimate-partner share (%) by year and victim sex",
     counts[counts.rel_group == "Intimate partner"].pivot(index="year", columns="victim_sex", values="pct"))
p = (ggplot(counts, aes("year", "pct", color="victim_sex"))
     + geom_line(size=1.2) + geom_point(size=2)
     + facet_wrap("~rel_group", ncol=2)
     + scale_color_manual(values={"Female": "#8e44ad", "Male": "#2980b9"})
     + scale_x_continuous(breaks=list(range(int(counts.year.min()), int(counts.year.max()) + 1, 3)))
     + labs(title="H2c  Trend of each relationship type by victim sex (plotnine)",
            x="Year", y="% of that sex's homicides", color="Victim sex")
     + theme_minimal())
p.save(FIG / "h2c_plotnine_facet_lines.png", width=10, height=6, dpi=150, verbose=False)


# ==========================================================================
# H3  The weapon depends on how close killer and victim are, and on the
#     victim's age: strangers and acquaintances use guns, family homicides
#     and child victims involve far more hands/feet, knives, blunt objects.
#                              (relationship x weapon x victim age)
# ==========================================================================
WEAPON_ORDER = ["Handgun", "Other firearm", "Knife", "Blunt object", "Hands or feet", "Other"]
rel_known = df.dropna(subset=["rel_group", "weapon_group"])

# 3a  seaborn - heatmap, each row sums to 100%
heat = (pd.crosstab(rel_known["rel_group"], rel_known["weapon_group"], normalize="index") * 100)
heat = heat.loc[REL_ORDER, WEAPON_ORDER]
show("H3a weapon (%) within each relationship group", heat)
plt.figure(figsize=(9, 4))
sns.heatmap(heat, annot=True, fmt=".0f", cmap="YlOrRd", cbar_kws={"label": "% of row"})
plt.title("H3a  Weapon used, by offender-victim relationship (seaborn)")
plt.xlabel("Weapon")
plt.ylabel("")
save_mpl("h3a_seaborn_heatmap")

# 3b  plotly - sunburst: inner ring relationship, outer ring weapon
sun = rel_known.groupby(["rel_group", "weapon_group"]).size().reset_index(name="n")
fig = px.sunburst(sun, path=["rel_group", "weapon_group"], values="n",
                  title="H3b  Relationship (inner) and weapon (outer) (plotly)")
fig.update_traces(textinfo="label+percent parent")
save_plotly(fig, "h3b_plotly_sunburst")

# 3c  bokeh - 100% stacked horizontal bars by victim age band
aged = df.dropna(subset=["victim_age", "weapon_group"]).copy()
aged["age_band"] = pd.cut(aged["victim_age"], bins=[-1, 12, 17, 34, 59, 120],
                          labels=["0-12", "13-17", "18-34", "35-59", "60+"]).astype(str)
tab = (pd.crosstab(aged["age_band"], aged["weapon_group"], normalize="index") * 100)[WEAPON_ORDER]
show("H3c weapon (%) within each victim age band", tab)
bands = list(tab.index)
source = ColumnDataSource({"age_band": bands, **{w: tab[w].tolist() for w in WEAPON_ORDER}})
p = figure(y_range=bands, width=950, height=420, tooltips="$name",
           title="H3c  Weapon mix by victim age band (bokeh)",
           x_axis_label="% of homicides in the age band", y_axis_label="Victim age")
p.hbar_stack(WEAPON_ORDER, y="age_band", height=0.8, source=source,
             color=Category10[len(WEAPON_ORDER)], legend_label=WEAPON_ORDER)
p.add_layout(p.legend[0], "right")
output_file(FIG / "h3c_bokeh_stacked_bars.html", title="H3c")
save(p)


# ==========================================================================
# H4  Geography matters for the weapon: the firearm share of homicides
#     differs widely between states and is highest in the South and lowest
#     in the Northeast / West.              (state x region x weapon)
# ==========================================================================
by_state = df.groupby(["state", "region"]).agg(
    homicides=("firearm", "size"), firearm_pct=("firearm", "mean")).reset_index()
by_state["firearm_pct"] *= 100
by_state = by_state[by_state["homicides"] >= 100]      # too few cases = noisy %
show("H4 firearm share (%) by region (mean of states)",
     by_state.groupby("region")["firearm_pct"].describe()[["count", "mean", "min", "max"]])
show("H4 five highest states", by_state.nlargest(5, "firearm_pct").set_index("state")[["homicides", "firearm_pct"]])
show("H4 five lowest states", by_state.nsmallest(5, "firearm_pct").set_index("state")[["homicides", "firearm_pct"]])

# 4a  plotly - interactive US choropleth map
fig = px.choropleth(by_state, locations="state", locationmode="USA-states", scope="usa",
                    color="firearm_pct", color_continuous_scale="Reds",
                    hover_data=["region", "homicides"],
                    labels={"firearm_pct": "% firearm"},
                    title="H4a  Firearm share of homicides by state (plotly)")
save_plotly(fig, "h4a_plotly_choropleth")

# 4b  folium - zoomable Leaflet map (needs internet once, for state borders)
try:
    borders = requests.get("https://raw.githubusercontent.com/python-visualization/"
                           "folium-example-data/main/us_states.json", timeout=30).json()
    m = folium.Map(location=[39, -97], zoom_start=4, tiles="OpenStreetMap")
    folium.Choropleth(geo_data=borders, data=by_state, columns=["state", "firearm_pct"],
                      key_on="feature.id", fill_color="YlOrRd", fill_opacity=0.8,
                      line_opacity=0.3, nan_fill_color="lightgrey",
                      legend_name="% of homicides committed with a firearm (folium)").add_to(m)
    m.save(str(FIG / "h4b_folium_map.html"))
except Exception as err:
    print(f"  (folium map skipped: {err})")

# 4c  seaborn - box plot + one dot per state, grouped by region
order = by_state.groupby("region")["firearm_pct"].median().sort_values(ascending=False).index
plt.figure(figsize=(9, 5))
sns.boxplot(data=by_state, x="region", y="firearm_pct", order=order, color="#f5cba7", showfliers=False)
sns.stripplot(data=by_state, x="region", y="firearm_pct", order=order, color="#922b21", size=6, jitter=0.15)
plt.title("H4c  State firearm shares grouped by region (seaborn)")
plt.xlabel("")
plt.ylabel("% of homicides committed with a firearm")
save_mpl("h4c_seaborn_box_strip")


# ==========================================================================
# H5  The age relationship between killer and victim depends on the
#     circumstance: in arguments and gang killings they are age peers, but
#     in felony-related killings (robbery etc.) the offender is clearly
#     younger than the victim.   (offender age x victim age x circumstance)
# ==========================================================================
ages = df.dropna(subset=["victim_age", "offender_age", "circ_group"]).copy()
ages["age_gap"] = ages["offender_age"] - ages["victim_age"]
CIRC_ORDER = ["Argument / brawl", "Gang-related", "Felony-related"]
ages = ages[ages["circ_group"].isin(CIRC_ORDER)]
show("H5 ages by circumstance",
     ages.groupby("circ_group")[["victim_age", "offender_age", "age_gap"]].agg(["mean", "median"]).loc[CIRC_ORDER])

# 5a  matplotlib - hexbin density, offender age vs victim age
fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharex=True, sharey=True)
for ax, group in zip(axes, CIRC_ORDER):
    part = ages[ages["circ_group"] == group]
    hb = ax.hexbin(part["offender_age"], part["victim_age"], gridsize=30, cmap="viridis",
                   mincnt=1, extent=(0, 90, 0, 90))
    ax.plot([0, 90], [0, 90], color="white", ls="--", lw=1.5)   # same-age line
    ax.set_title(f"{group}  (n = {len(part):,})")
    ax.set_xlabel("Offender age")
    fig.colorbar(hb, ax=ax, label="incidents")
axes[0].set_ylabel("Victim age")
fig.suptitle("H5a  Offender age vs victim age; dashed line = same age (matplotlib)")
save_mpl("h5a_matplotlib_hexbin")

# 5b  seaborn - violin plot of the age gap
plt.figure(figsize=(9, 5))
sns.violinplot(data=ages, x="circ_group", y="age_gap", order=CIRC_ORDER, color="#aed6f1", inner="quartile")
plt.axhline(0, color="black", lw=1, ls="--")
plt.title("H5b  Age gap (offender age minus victim age) by circumstance (seaborn)")
plt.xlabel("")
plt.ylabel("Years; below 0 = offender younger than victim")
save_mpl("h5b_seaborn_violin")

# 5c  altair - dumbbell chart of the mean ages
means = (ages.groupby("circ_group")[["victim_age", "offender_age"]].mean()
         .rename(columns={"victim_age": "Victim", "offender_age": "Offender"})
         .reset_index().melt(id_vars="circ_group", var_name="role", value_name="mean_age"))
base = alt.Chart(means).encode(
    x=alt.X("mean_age:Q", title="Mean age (years)", scale=alt.Scale(zero=False)),
    y=alt.Y("circ_group:N", sort=CIRC_ORDER, title=None))
chart = (base.mark_line(color="grey", strokeWidth=3).encode(detail="circ_group:N")
         + base.mark_point(filled=True, size=220, opacity=1).encode(
             color=alt.Color("role:N", title=None), tooltip=["circ_group", "role", "mean_age"])
         ).properties(width=600, height=220,
                      title="H5c  Mean victim and offender age by circumstance (altair)")
save_altair(chart, "h5c_altair_dumbbell")

print("\nDone. All charts are in the figures/ folder.")
