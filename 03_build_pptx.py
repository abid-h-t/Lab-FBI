"""
STEP 3 - Build the PowerPoint deck from the charts in figures/.

Run:  python 03_build_pptx.py      ->  FBI_Homicide_Lab.pptx
"""
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR
from pptx.util import Inches, Pt

FIG = Path("figures")
NAVY, RED, INK, GREY, TINT, WHITE = "1B2A41", "B03A2E", "22262B", "5F6B7A", "EEF1F5", "FFFFFF"
HEAD, BODY, MONO = "Cambria", "Calibri", "Consolas"

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]


def rgb(hex_):
    return RGBColor.from_string(hex_)


def box(slide, x, y, w, h, fill, rounded=False):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE,
        Inches(x), Inches(y), Inches(w), Inches(h))
    if rounded:
        shape.adjustments[0] = 0.06
    shape.fill.solid()
    shape.fill.fore_color.rgb = rgb(fill)
    shape.line.fill.background()
    shape.shadow.inherit = False
    return shape


def text(slide, x, y, w, h, paragraphs, size=16, color=INK, font=BODY, bold=False,
         anchor=MSO_ANCHOR.TOP, space=8):
    """paragraphs: a string, or a list whose items are a string or a list of
    (text, bold) runs. One list item = one paragraph."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    if isinstance(paragraphs, str):
        paragraphs = [paragraphs]
    for i, para in enumerate(paragraphs):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(space)
        runs = [(para, bold)] if isinstance(para, str) else para
        for run_text, run_bold in runs:
            r = p.add_run()
            r.text = run_text
            r.font.size, r.font.bold, r.font.name = Pt(size), run_bold, font
            r.font.color.rgb = rgb(color)
    return tb


def picture(slide, name, x, y, w, h):
    """Place figures/<name>.png inside the box (x, y, w, h), keeping its shape."""
    path = FIG / f"{name}.png"
    pw, ph = Image.open(path).size
    scale = min(w / pw, h / ph)
    iw, ih = pw * scale, ph * scale
    slide.shapes.add_picture(str(path), Inches(x + (w - iw) / 2), Inches(y + (h - ih) / 2),
                             Inches(iw), Inches(ih))


def content_slide(title, kicker, notes=""):
    s = prs.slides.add_slide(BLANK)
    text(s, 0.6, 0.35, 12.1, 0.3, kicker.upper(), size=12, color=RED, bold=True)
    text(s, 0.6, 0.65, 12.1, 0.8, title, size=30, color=NAVY, font=HEAD, bold=True)
    if notes:
        s.notes_slide.notes_text_frame.text = notes
    return s


def chart_caption(slide, x, y, w, label, library):
    text(slide, x, y, w, 0.3, [[(f"{label}  ", True), (library, False)]], size=12, color=GREY)


# ---------------------------------------------------------------- content --
HYPOTHESES = [
    dict(
        n=1, short="The 2020 surge was a firearm surge",
        statement="The rise in homicides around 2020 was driven by firearms: gun homicides grew "
                  "much faster than non-gun homicides, and the firearm share rose in every region.",
        variables="year  x  weapon type  x  region",
        why="If the surge were a general rise in violence, all weapon types would grow together. "
            "Splitting by weapon and by region tests whether it was specific and nationwide.",
        charts=[("h1a_matplotlib_indexed_lines", "Indexed line chart", "matplotlib"),
                ("h1b_seaborn_heatmap", "Heatmap", "seaborn"),
                ("h1c_plotly_region_lines", "Interactive multi-line chart", "plotly")],
        code='''heat = df.pivot_table(index="region", columns="year",
                      values="firearm", aggfunc="mean") * 100

plt.figure(figsize=(11, 3.8))
sns.heatmap(heat, annot=True, fmt=".0f", cmap="Reds",
            cbar_kws={"label": "% committed with a firearm"})
plt.title("Firearm share of homicides by region and year")

long = heat.reset_index().melt(id_vars="region",
           var_name="year", value_name="firearm_pct")
fig = px.line(long, x="year", y="firearm_pct",
              color="region", markers=True)
fig.write_html("figures/h1c_plotly_region_lines.html")''',
        verdict="SUPPORTED",
        findings=[
            [("Guns drove the jump. ", True), ("From 2019 to 2020 firearm homicides rose about 35% "
             "(index 108 to 146) while all other weapons rose about 13% (105 to 118).", False)],
            [("Every region moved. ", True), ("The firearm share rose in all four regions in 2020, "
             "most sharply in the Northeast (65% to 73%).", False)],
            [("It partly reversed. ", True), ("By 2024 the Northeast and West were back near their "
             "2019 shares; the South and Midwest stayed at 76-78%.", False)],
            [("Caveat. ", True), ("The 2021 dip is a reporting gap, not a real fall: many agencies "
             "in CA and NY did not submit that year.", False)],
        ]),
    dict(
        n=2, short="Who kills depends on the victim's sex",
        statement="Women are killed mainly by intimate partners and family, men by acquaintances "
                  "and strangers, and this gap has not narrowed over the decade.",
        variables="victim sex  x  offender relationship  x  year",
        why="A single overall relationship breakdown hides two very different patterns. Adding "
            "time tests whether the difference is stable or changing.",
        charts=[("h2a_seaborn_grouped_bar", "Grouped bar chart", "seaborn"),
                ("h2b_altair_stacked_facets", "Faceted 100% stacked bars", "altair"),
                ("h2c_plotnine_facet_lines", "Small-multiple line charts", "plotnine")],
        code='''known = df.dropna(subset=["victim_sex", "rel_group"])
counts = (known.groupby(["year", "victim_sex", "rel_group"])
               .size().reset_index(name="n"))

chart = alt.Chart(counts).mark_bar().encode(
    x=alt.X("year:O", title="Year"),
    y=alt.Y("n:Q", stack="normalize",
            axis=alt.Axis(format="%"),
            title="Share of homicides"),
    color=alt.Color("rel_group:N", title="Relationship"),
    column=alt.Column("victim_sex:N", title="Victim sex"),
).properties(width=330, height=300)
chart.save("figures/h2b_altair_stacked_facets.html")''',
        verdict="PARTLY SUPPORTED",
        findings=[
            [("The split is real. ", True), ("45% of female victims were killed by an intimate "
             "partner and 19% by family; for male victims it is 6% and 13%.", False)],
            [("Men face outsiders. ", True), ("52% of male victims were killed by an acquaintance "
             "and 29% by a stranger (women: 26% and 9%).", False)],
            [("But the gap narrowed. ", True), ("The intimate-partner share for women fell from "
             "50.5% in 2015 to 44.0% in 2024, while the male share stayed near 6%.", False)],
            [("Caveat. ", True), ("Relationship is unknown in 48% of incidents, so these are "
             "shares of cases where police identified the offender.", False)],
        ]),
    dict(
        n=3, short="Weapon depends on closeness and age",
        statement="Strangers and acquaintances kill with guns, while family homicides and child "
                  "victims involve far more hands or feet, knives and blunt objects.",
        variables="offender relationship  x  weapon  x  victim age band",
        why="Weapon choice reflects planning and access. Close-range domestic violence and "
            "violence against children should look different from street violence.",
        charts=[("h3a_seaborn_heatmap", "Row-normalised heatmap", "seaborn"),
                ("h3b_plotly_sunburst", "Sunburst (two-level hierarchy)", "plotly"),
                ("h3c_bokeh_stacked_bars", "100% stacked horizontal bars", "bokeh")],
        code='''aged["age_band"] = pd.cut(aged["victim_age"],
    bins=[-1, 12, 17, 34, 59, 120],
    labels=["0-12", "13-17", "18-34", "35-59", "60+"]).astype(str)
tab = pd.crosstab(aged["age_band"], aged["weapon_group"],
                  normalize="index") * 100

source = ColumnDataSource({"age_band": list(tab.index),
    **{w: tab[w].tolist() for w in WEAPON_ORDER}})
p = figure(y_range=list(tab.index), width=950, height=420,
           x_axis_label="% of homicides in the age band")
p.hbar_stack(WEAPON_ORDER, y="age_band", height=0.8,
             source=source, color=Category10[6],
             legend_label=WEAPON_ORDER)
save(p)''',
        verdict="SUPPORTED",
        findings=[
            [("Guns fall with closeness. ", True), ("Firearms were used in 79% of stranger "
             "homicides, 68% of acquaintance, 60% of intimate-partner and 44% of family.", False)],
            [("Family violence is hands-on. ", True), ("Hands or feet account for 15% of family "
             "homicides against 4% for strangers; knives 18% against 8%.", False)],
            [("Children are the extreme. ", True), ("For victims aged 0-12 only 20% involve a "
             "firearm and 36% hands or feet; for ages 13-17 firearms reach 88%.", False)],
            [("Nuance. ", True), ("Intimate-partner homicides are still mostly gun deaths; the "
             "difference from strangers is one of degree.", False)],
        ]),
    dict(
        n=4, short="Geography shapes the weapon",
        statement="The firearm share of homicides differs widely between states and is highest "
                  "in the South and lowest in the Northeast.",
        variables="state  x  region  x  weapon type",
        why="Shares, not counts, are compared, so large and small states are on the same scale "
            "and uneven reporting matters less. States under 100 incidents are excluded.",
        charts=[("h4a_plotly_choropleth", "Interactive choropleth map", "plotly"),
                ("h4b_folium_map", "Leaflet web map", "folium"),
                ("h4c_seaborn_box_strip", "Box plot with one dot per state", "seaborn")],
        code='''by_state = df.groupby(["state", "region"]).agg(
    homicides=("firearm", "size"),
    firearm_pct=("firearm", "mean")).reset_index()
by_state["firearm_pct"] *= 100
by_state = by_state[by_state["homicides"] >= 100]

m = folium.Map(location=[39, -97], zoom_start=4)
folium.Choropleth(
    geo_data=borders, data=by_state,
    columns=["state", "firearm_pct"],
    key_on="feature.id", fill_color="YlOrRd",
    legend_name="% of homicides with a firearm",
).add_to(m)
m.save("figures/h4b_folium_map.html")''',
        verdict="PARTLY SUPPORTED",
        findings=[
            [("The South leads as a block. ", True), ("Southern states average a 76% firearm "
             "share, and most sit between 74% and 82%.", False)],
            [("The top states are Midwestern. ", True), ("Illinois (84.0%) and Missouri (83.9%) "
             "rank first; the Midwest spans 46% (South Dakota) to 84%.", False)],
            [("The West is lowest. ", True), ("Western states average 62%, below the Northeast "
             "at 64%; Hawaii is the national minimum at 43%.", False)],
            [("Takeaway. ", True), ("Region explains part of the variance, but the spread inside "
             "regions points to state- and city-level factors.", False)],
        ]),
    dict(
        n=5, short="The age gap depends on the circumstance",
        statement="In arguments and gang killings offender and victim are age peers, but in "
                  "felony-related killings such as robbery the offender is clearly younger.",
        variables="offender age  x  victim age  x  circumstance",
        why="Arguments happen inside social circles of similar age. Felony homicides pair a "
            "young offender with whoever is targeted, so the ages should decouple.",
        charts=[("h5a_matplotlib_hexbin", "Hexbin density panels", "matplotlib"),
                ("h5b_seaborn_violin", "Violin plot", "seaborn"),
                ("h5c_altair_dumbbell", "Dumbbell chart", "altair")],
        code='''fig, axes = plt.subplots(1, 3, figsize=(15, 5),
                         sharex=True, sharey=True)
for ax, group in zip(axes, CIRC_ORDER):
    part = ages[ages["circ_group"] == group]
    hb = ax.hexbin(part["offender_age"], part["victim_age"],
                   gridsize=30, cmap="viridis", mincnt=1,
                   extent=(0, 90, 0, 90))
    ax.plot([0, 90], [0, 90], color="white", ls="--")
    ax.set_title(f"{group}  (n = {len(part):,})")
    ax.set_xlabel("Offender age")
    fig.colorbar(hb, ax=ax, label="incidents")
axes[0].set_ylabel("Victim age")
plt.savefig("figures/h5a_matplotlib_hexbin.png", dpi=150)''',
        verdict="SUPPORTED",
        findings=[
            [("Felony killings decouple ages. ", True), ("Offenders average 29.8 years against "
             "35.9 for victims: a 6.1-year gap (median 3).", False)],
            [("Arguments and gangs are peers. ", True), ("Both show a mean gap of only 2.7 years "
             "and a median of 1; the hexbins hug the same-age line.", False)],
            [("Gang killings are youngest. ", True), ("Mean offender age is 24 and victim age 27, "
             "about a decade below arguments.", False)],
            [("Caveat. ", True), ("Offender age is known for only 68% of incidents, so unsolved "
             "cases are excluded; the effect is real but moderate.", False)],
        ]),
]

# ------------------------------------------------------------------ title --
s = prs.slides.add_slide(BLANK)
box(s, 0, 0, 13.333, 7.5, NAVY)
text(s, 0.9, 1.5, 11.5, 0.4, "CSC664 INFORMATION VISUALIZATION", size=14, color="E8B4AE", bold=True)
text(s, 0.9, 2.0, 11.5, 2.2, ["Exploratory Data Analysis and Hypothesis",
                               "Validation on FBI Homicide Data"],
     size=40, color=WHITE, font=HEAD, bold=True, space=0)
text(s, 0.9, 4.5, 11.5, 0.5, "Lab assignment: five hypotheses, fifteen charts, eight libraries",
     size=20, color="CAD3DF")
text(s, 0.9, 5.9, 11.5, 0.8, ["[Your Name]", "November 9, 2026"], size=18, color=WHITE, space=4)

# ------------------------------------------------------------------ setup --
s = content_slide("Environment and data setup", "Setup",
                  "Data: FBI Crime Data Explorer, SHR master files 2015-2024. "
                  "Everything ran inside the csc_lab_env virtual environment.")
box(s, 0.6, 1.65, 5.9, 2.05, NAVY, rounded=True)
text(s, 0.85, 1.8, 5.4, 1.8, ["python -m venv csc_lab_env",
                               "csc_lab_env\\Scripts\\Activate.ps1",
                               "python -m pip install --upgrade pip",
                               "pip install -r requirements.txt"],
     size=14, color=WHITE, font=MONO, space=6)
text(s, 0.6, 3.9, 5.9, 3.2, [
    [("Source. ", True), ("FBI Crime Data Explorer, Supplementary Homicide Report master files, "
     "2015-2024 (10 fixed-width files).", False)],
    [("After cleaning. ", True), ("161,889 murder and non-negligent manslaughter incidents in "
     "50 states and DC.", False)],
    [("Variables. ", True), ("Year, state, region; victim and offender age, sex, race; weapon; "
     "relationship; circumstance.", False)],
    [("Missing data. ", True), ("Unknown codes were set to NaN and dropped per analysis: "
     "relationship 48%, circumstance 42%, offender age 32%, victim age 1%.", False)],
], size=14, space=7)
picture(s, "00_missing_matrix", 6.9, 1.65, 5.85, 4.9)
chart_caption(s, 6.9, 6.65, 5.85, "Missing-value matrix (white = missing)", "missingno")

# --------------------------------------------------------------- overview --
s = content_slide("Five hypotheses, each tested with three charts", "Overview")
for i, h in enumerate(HYPOTHESES):
    y = 1.75 + i * 1.05
    box(s, 0.6, y, 12.1, 0.9, TINT, rounded=True)
    text(s, 0.85, y, 0.9, 0.9, f"H{h['n']}", size=26, color=RED, font=HEAD, bold=True,
         anchor=MSO_ANCHOR.MIDDLE)
    text(s, 1.8, y, 6.2, 0.9, h["short"], size=18, color=NAVY, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    text(s, 8.2, y, 4.3, 0.9, "  |  ".join(c[2] for c in h["charts"]), size=14, color=GREY,
         anchor=MSO_ANCHOR.MIDDLE)

# -------------------------------------------------------- hypothesis x 5 --
for h in HYPOTHESES:
    tag = f"Hypothesis {h['n']}"
    c1, c2, c3 = h["charts"]

    # slide A: statement + first chart
    s = content_slide(h["short"], f"{tag}  |  statement and rationale", h["statement"])
    box(s, 0.6, 1.65, 4.6, 2.75, TINT, rounded=True)
    text(s, 0.85, 1.65, 4.1, 2.75, h["statement"], size=18, color=NAVY, bold=True,
         anchor=MSO_ANCHOR.MIDDLE)
    text(s, 0.6, 4.65, 4.6, 0.3, "VARIABLES", size=12, color=RED, bold=True)
    text(s, 0.6, 4.95, 4.6, 0.4, h["variables"], size=14, color=INK, bold=True)
    text(s, 0.6, 5.5, 4.6, 0.3, "WHY IT IS NOT TRIVIAL", size=12, color=RED, bold=True)
    text(s, 0.6, 5.8, 4.6, 1.3, h["why"], size=14, color=INK)
    picture(s, c1[0], 5.6, 1.65, 7.15, 4.9)
    chart_caption(s, 5.6, 6.65, 7.15, f"Chart {h['n']}a: {c1[1]}", f"library: {c1[2]}")

    # slide B: charts two and three
    s = content_slide(f"{h['short']}: more evidence", f"{tag}  |  supporting charts")
    picture(s, c2[0], 0.6, 1.65, 5.95, 4.9)
    chart_caption(s, 0.6, 6.65, 5.95, f"Chart {h['n']}b: {c2[1]}", f"library: {c2[2]}")
    picture(s, c3[0], 6.8, 1.65, 5.95, 4.9)
    chart_caption(s, 6.8, 6.65, 5.95, f"Chart {h['n']}c: {c3[1]}", f"library: {c3[2]}")

    # slide C: code + narrative
    s = content_slide(f"{h['short']}: code and findings", f"{tag}  |  code and narrative")
    lines = h["code"].split("\n")
    code_h = 0.5 + 0.19 * len(lines)
    box(s, 0.6, 1.65, 6.6, code_h, NAVY, rounded=True)
    text(s, 0.85, 1.9, 6.1, code_h - 0.4, lines, size=11, color=WHITE, font=MONO, space=0)
    text(s, 0.6, 1.8 + code_h, 6.6, 0.3, "Excerpt from 02_hypotheses.py; the full script is in the "
         "submission zip", size=12, color=GREY)
    good = h["verdict"] == "SUPPORTED"
    box(s, 7.6, 1.65, 3.2 if not good else 2.3, 0.5, "2E7D4F" if good else "B7791F", rounded=True)
    text(s, 7.6, 1.65, 3.2 if not good else 2.3, 0.5, [[("  " + h["verdict"], True)]], size=14,
         color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
    text(s, 7.6, 2.4, 5.15, 4.6, h["findings"], size=14, space=10)

# ------------------------------------------------------------- conclusion --
s = prs.slides.add_slide(BLANK)
box(s, 0, 0, 13.333, 7.5, NAVY)
text(s, 0.6, 0.35, 12.1, 0.3, "CONCLUSION", size=12, color="E8B4AE", bold=True)
text(s, 0.6, 0.65, 12.1, 0.8, "What the data showed, and how far to trust it", size=30,
     color=WHITE, font=HEAD, bold=True)
columns = [
    ("Findings", [
        "3 hypotheses supported, 2 partly supported.",
        "The 2020 surge was a firearm surge in every region.",
        "Victim sex, relationship and victim age strongly shape who kills and with what.",
        "Region matters for weapon choice, but states vary widely inside regions.",
    ]),
    ("Limitations", [
        "Reporting is voluntary: Florida is nearly absent before 2021, and 2021 has gaps.",
        "Relationship is unknown in 48% and offender age in 32% of incidents.",
        "Only the first victim and first offender of each incident were analysed.",
        "Counts are not per-capita rates.",
    ]),
    ("Future work", [
        "Add population data to compute homicide rates.",
        "Use NIBRS incident data for location and time of day.",
        "Test differences formally (chi-square, regression).",
        "Analyse multi-victim and multi-offender incidents.",
    ]),
]
for i, (head, lines) in enumerate(columns):
    x = 0.6 + i * 4.1
    box(s, x, 1.75, 3.9, 4.9, "26384F", rounded=True)
    text(s, x + 0.25, 1.95, 3.4, 0.5, head, size=20, color="E8B4AE", font=HEAD, bold=True)
    text(s, x + 0.25, 2.6, 3.4, 3.9, lines, size=16, color=WHITE, space=14)

prs.save("FBI_Homicide_Lab.pptx")
print(f"Saved FBI_Homicide_Lab.pptx with {len(prs.slides)} slides")
