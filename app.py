import glob
import io
import os

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Underemployment Beyond Unemployment", page_icon="📊", layout="wide",
                   initial_sidebar_state="collapsed")

# ------------------------------------------------------------------ constants
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
FULL = ["January", "February", "March", "April", "May", "June", "July", "August",
        "September", "October", "November", "December"]

LEVELS = {  # display name -> column in the CSV
    "No Grade Completed": "No Grade Completed Rate",
    "Basic Education": "Basic Education Rate",
    "Senior High School": "Senior High School Rate",
    "Post Secondary / TVET": "Post-Secondary / TVET Rate",
    "College": "College Rate",
}
NAMES = list(LEVELS.keys())

# One fixed colour per education group, used identically in every chart and card.
LEVEL_COLORS = {
    "No Grade Completed": "#7C3AED",     # violet
    "Basic Education": "#F59E0B",        # amber
    "Senior High School": "#10B981",     # emerald
    "Post Secondary / TVET": "#0EA5E9",  # sky blue
    "College": "#E11D48",                # rose
}
NAVY = "#16324F"      # national line, headers, dark accents
BLUE = "#1D4ED8"      # selection highlight (buttons, selected bars)
INK = "#000000"       # main text
SOFT = "#52627A"      # secondary text
GRID = "#DCE3EC"      # chart gridlines
LINE = "#2A3A50"      # panel borders
MALE, FEMALE = "#2563EB", "#EC4899"
YEAR_PALETTE = ["#8FB3E0", "#3E6FB5", "#16324F"]   # light blue, medium blue, navy (one per year)

# Panel heights (px). Chart heights below are sized to fit inside them.
H_ROW1, H_ROW2, H_ROW3 = 410, 410, 420

# ------------------------------------------------------------------ styling
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Barlow+Condensed:wght@600;700;800&display=swap');
html, body, [class*="css"], .stApp { font-family: 'Inter', sans-serif; }
.stApp, [data-testid="stAppViewContainer"] {
  background: linear-gradient(135deg, #D3E3F6 0%, #E7ECF6 45%, #E8DFF5 100%) !important;
  background-attachment: fixed !important; color: #0F1F33; color-scheme: light; }
[data-testid="stHeader"] { background: transparent !important; height: 0 !important; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding: 1rem 1.5rem 1rem 1.5rem !important; max-width: 100% !important; }
[data-testid="stVerticalBlock"] { gap: .1rem; }

/* header bar */
.top { display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; gap: 18px; background: #FFFFFF;
       border: 2px solid #2A3A50; border-top: 6px solid #16324F; border-radius: 8px; padding: 12px 22px;
       box-shadow: 0 4px 14px rgba(22,50,79,.12); }
.brand { display: flex; align-items: center; gap: 12px; }
.logo { width: 54px; height: 54px; flex: none; background: #16324F; color: #FFFFFF; display: flex; align-items: center;
        justify-content: center; font-family: 'Barlow Condensed', 'Arial Narrow', sans-serif; font-weight: 800; font-size: 1.6rem;
        letter-spacing: .04em; border-radius: 4px; }
.brand .bt { font-size: .78rem; font-weight: 800; letter-spacing: .08em; color: #52627A; text-transform: uppercase; line-height: 1.4; }
.ttl { text-align: center; }
.ttl .h1 { font-family: 'Barlow Condensed', 'Arial Narrow', sans-serif; font-size: 2.1rem; font-weight: 800; letter-spacing: .03em;
           text-transform: uppercase; color: #0F1F33; line-height: 1.05; }
.ttl .h2 { font-size: .9rem; color: #52627A; margin-top: 4px; font-weight: 500; }
.badges { display: flex; gap: 10px; justify-content: flex-end; }
.badge { border: 1.5px solid #2A3A50; border-radius: 4px; padding: 7px 14px; text-align: center; background: #F6F8FB; }
.badge .bl { font-size: .65rem; font-weight: 800; letter-spacing: .1em; color: #52627A; text-transform: uppercase; }
.badge .bv { font-size: .92rem; font-weight: 800; color: #0F1F33; margin-top: 1px; white-space: nowrap; }
.badge.dark { background: #16324F; border-color: #16324F; }
.badge.dark .bl { color: #B9CBDF; }
.badge.dark .bv { color: #FFFFFF; }

/* panels: every chart card and the filter bar get a clear border, white background and soft shadow */
[class*="st-key-panel"] { background: #FFFFFF !important; border: 2px solid #2A3A50 !important; border-radius: 8px !important;
                          box-shadow: 0 4px 14px rgba(22,50,79,.12) !important; }
[class*="st-key-panel"] [data-testid="stVerticalBlock"] { gap: .50rem; }

/* filter labels and controls */
label[data-testid="stWidgetLabel"] p { font-size: .85rem !important; font-weight: 800 !important; letter-spacing: .1em;
                                       text-transform: uppercase; color: #52627A !important; }
/* filter buttons: we build them as keyed st.button widgets so the selected colour is always blue (never Streamlit red) */
[class*="st-key-off_"] button, [class*="st-key-sel_"] button, .st-key-btn_reset button {
  border-radius: 999px !important; min-height: 2.05rem; padding: 2px 10px !important; width: 100%; transition: none; }
[class*="st-key-off_"] button p, [class*="st-key-sel_"] button p, .st-key-btn_reset button p {
  color: inherit !important; font-size: .85rem !important; font-weight: 700 !important; white-space: nowrap; }
[class*="st-key-off_"] button { background: #FFFFFF !important; border: 1.5px solid #9FB0C4 !important; color: #0F1F33 !important; }
[class*="st-key-off_"] button:hover, [class*="st-key-off_"] button:focus, [class*="st-key-off_"] button:active {
  background: #EAF1FF !important; border-color: #1D4ED8 !important; color: #1D4ED8 !important; box-shadow: none !important; }
[class*="st-key-sel_"] button, [class*="st-key-sel_"] button:hover, [class*="st-key-sel_"] button:focus, [class*="st-key-sel_"] button:active {
  background: #1D4ED8 !important; border: 1.5px solid #1D4ED8 !important; color: #FFFFFF !important; box-shadow: none !important; }
.st-key-btn_reset button { background: #FFFFFF !important; border: 2px solid #16324F !important; color: #16324F !important; border-radius: 6px !important; }
.st-key-btn_reset button:hover, .st-key-btn_reset button:focus, .st-key-btn_reset button:active {
  background: #16324F !important; color: #FFFFFF !important; border-color: #16324F !important; box-shadow: none !important; }
.flab { font-size: .90rem; font-weight: 800; letter-spacing: .1em; text-transform: uppercase; color: #52627A;
        line-height: 1.5; padding: 2px 0 15px 0; margin: 0; }
/* title to filter bar */
[class*="st-key-panel_filters"] { margin-top: 1.4rem; }
/* filter bar to KPI cards */
[data-testid="stElementContainer"]:has(.kpis) { margin-top: .4rem; }
/* KPI cards to legend */
[data-testid="stElementContainer"]:has(.legend) { margin-top: 1.4rem; }
/* legend to the first chart row, and between chart rows */
[class*="st-key-panel_rate"], [class*="st-key-panel_gap"], [class*="st-key-panel_year"],
[class*="st-key-panel_pyramid"], [class*="st-key-panel_month"] { margin-top: 1.4rem; }
div[data-baseweb="select"] > div { background: #FFFFFF !important; border: 1.5px solid #9FB0C4 !important; border-radius: 4px !important; }
div[data-baseweb="select"] * { color: #0F1F33 !important; font-weight: 700; font-size: .88rem; }

/* KPI strip */
.kpis { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: .8rem; }
.k { background: #FFFFFF; border: 2px solid #2A3A50; border-left: 9px solid var(--c); border-radius: 8px; padding: .4rem .6rem .4rem 1rem;
     min-width: 0; box-shadow: 0 4px 14px rgba(22,50,79,.12); }
.kl { color: #52627A; font-size: .85rem; font-weight: 800; letter-spacing: .09em; text-transform: uppercase; }
.kmain { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 4px 10px; }
.kv { color: #0F1F33; font-family: 'Barlow Condensed', 'Arial Narrow', sans-serif; font-size: 2.5rem; font-weight: 800; line-height: 1.05; }
.kn { color: #0F1F33; font-size: .92rem; font-weight: 700; margin-top: 1px; }
.kt { color: #000000; font-size: .90rem; font-weight: 500; margin-top: 1px; }
.chip { font-size: .75rem; font-weight: 800; padding: 3px 9px; border-radius: 4px; white-space: nowrap; }
.chip.bad { background: #FBE9E7; color: #A8321F; }
.chip.good { background: #E3F4EA; color: #17653A; }
.chip.flat { background: #E6EDF7; color: #16324F; }

/* shared colour legend */
.legend { display: flex; flex-wrap: wrap; align-items: center; gap: 8px 26px; background: #FFFFFF; border: 2px solid #2A3A50;
          border-radius: 8px; padding: 9px 18px; box-shadow: 0 4px 14px rgba(22,50,79,.12); }
.legend .lt { font-size: .75rem; font-weight: 800; letter-spacing: .1em; text-transform: uppercase; color: #52627A; }
.lg { display: inline-flex; align-items: center; gap: 8px; font-size: .88rem; font-weight: 700; color: #0F1F33; white-space: nowrap; }
.lg i { width: 14px; height: 14px; border-radius: 3px; display: inline-block; }
.lg i.dash { height: 0; width: 26px; background: none; border-radius: 0; border-top: 3px dashed #16324F; }

/* panel headings */
.ph { border-bottom: 2px solid #2A3A50; padding: 4px 0 6px 0; margin-bottom: 2px; min-width: 0; }
.pt { font-family: 'Barlow Condensed', 'Arial Narrow', sans-serif; font-size: 1.7rem; font-weight: 800; letter-spacing: .05em;
      text-transform: uppercase; color: #0F1F33; line-height: 1.15; }
.ps { font-size: .99rem; color: #52627A; margin-top: 2px; font-weight: 500; }
.take { border: 1.5px solid #C2CEDD; border-left: 6px solid #1D4ED8; border-radius: 4px; background: #F3F7FC; padding: 8px 12px;
        font-size: .92rem; line-height: 1.4; color: #0F1F33; }
.take .tl { font-size: .7rem; font-weight: 800; letter-spacing: .12em; color: #52627A; text-transform: uppercase; }

.foot { font-size: .8rem; display: flex; flex-wrap: wrap; justify-content: space-between; gap: 4px 24px; background: #FFFFFF; border: 2px solid #2A3A50;
        border-radius: 8px; padding: 9px 18px; color: #52627A; }
.foot b { color: #0F1F33; letter-spacing: .08em; text-transform: uppercase; font-size: .8rem; }
@media (max-width: 1100px) { .top { grid-template-columns: 1fr; } .ttl { text-align: left; } .badges { justify-content: flex-start; }
  .kpis { grid-template-columns: repeat(2, 1fr); } }
</style>
    """,
    unsafe_allow_html=True,
)


# ------------------------------------------------------------------ data
@st.cache_data
def load(src):
    raw = pd.read_csv(io.BytesIO(src) if isinstance(src, bytes) else src)
    raw["MonthNum"] = raw["Month"].map({m: i + 1 for i, m in enumerate(FULL)})
    raw["Date"] = pd.to_datetime(dict(year=raw["Year"], month=raw["MonthNum"], day=1))
    raw = raw.rename(columns={v: k for k, v in LEVELS.items()})
    raw = raw.rename(columns={"Underemployment Rate Both sexes": "National"})
    return raw.sort_values("Date").reset_index(drop=True)


def find_file():
    here = os.path.dirname(os.path.abspath(__file__))
    csvs = [p for p in glob.glob(os.path.join(here, "*.csv")) if "underemployment" in p.lower()]
    return csvs[0] if csvs else None


src = find_file()
if src is None:
    up = st.file_uploader("Upload the integrated underemployment CSV", type="csv")
    if up is None:
        st.info("Add the integrated underemployment CSV to this folder, or upload it here.")
        st.stop()
    src = up.getvalue()
df = load(src)
ALL_YEARS = sorted(df["Year"].unique().tolist())
BASE_YEAR = ALL_YEARS[0]
PERIOD = f"{ALL_YEARS[0]} – {ALL_YEARS[-1]}"
YEAR_COLORS = {y: YEAR_PALETTE[i % len(YEAR_PALETTE)] for i, y in enumerate(ALL_YEARS)}


def age_label(col):
    s = col.split("_", 1)[1]
    if "and_Over" in s:
        return s.split("_")[0] + " and over"
    a, b = s.replace("_Years_Old", "").split("___")
    return f"{a} to {b}"


SEX_COLS = {sx: [c for c in df.columns if c.startswith(sx + "_") and "Total" not in c] for sx in ("Male", "Female")}
HAS_SEX = all(len(v) > 0 for v in SEX_COLS.values())

# ------------------------------------------------------------------ state + callbacks
st.session_state.setdefault("ver", 0)
st.session_state.setdefault("grp", "All")
st.session_state.setdefault("year_sel", "All")
st.session_state.setdefault("m_from", MONTHS[0])
st.session_state.setdefault("m_to", MONTHS[-1])
st.session_state.setdefault("pyr_mode", "Count")


def reset_filters():
    st.session_state["year_sel"] = "All"
    st.session_state["grp"] = "All"
    st.session_state["m_from"] = MONTHS[0]
    st.session_state["m_to"] = MONTHS[-1]
    st.session_state["ver"] += 1


def _clicked(key, axis):
    try:
        pts = [p.get(axis) for p in st.session_state[key]["selection"]["points"]]
        return pts[0] if pts else None
    except Exception:
        return None


def set_year(v):
    st.session_state["year_sel"] = v
    st.session_state["ver"] += 1


def set_group(v):
    st.session_state["grp"] = v
    st.session_state["ver"] += 1


def set_pyr(v):
    st.session_state["pyr_mode"] = v


def on_group_bar():
    c = _clicked(f"bar_{st.session_state['ver']}", "y")
    st.session_state["grp"] = c if c and c != st.session_state.get("grp") else "All"
    st.session_state["ver"] += 1


def on_gap_bar():
    c = _clicked(f"gap_{st.session_state['ver']}", "x")
    c = str(c) if c is not None else None
    st.session_state["year_sel"] = c if c and c != st.session_state.get("year_sel") else "All"
    st.session_state["ver"] += 1


# ------------------------------------------------------------------ header bar
st.markdown(
    '<div class="top">'
    '<div class="brand"><div class="logo">UE</div><div class="bt">SDG 8<br>Decent Work</div></div>'
    '<div class="ttl"><div class="h1">Underemployment Beyond Unemployment</div>'
    '<div class="h2">Filipino Workers by Education Level &nbsp;·&nbsp; Philippines</div></div>'
    '<div class="badges">'
    f'<div class="badge"><div class="bl">Reporting period</div><div class="bv">{PERIOD}</div></div>'
    '<div class="badge dark"><div class="bl">Data source</div><div class="bv">PSA · Labor Force Survey</div></div>'
    '</div></div>',
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------ filters
with st.container(border=True, key="panel_filters"):
    year_opts = ["All"] + [str(y) for y in ALL_YEARS]
    grp_opts = ["All"] + NAMES
    f1, f2, f3 = st.columns([len(year_opts) * 0.9 + 0.4, 9.4, 3.6], vertical_alignment="bottom")
    with f1:
        st.markdown('<div class="flab">Year</div>', unsafe_allow_html=True)
        for col, v in zip(st.columns(len(year_opts)), year_opts):
            on = st.session_state["year_sel"] == v
            col.button(v, key=f"{'sel' if on else 'off'}_yr_{v}", on_click=set_year, args=(v,), use_container_width=True)
    with f2:
        st.markdown('<div class="flab">Education group</div>', unsafe_allow_html=True)
        widths = [max(len(v), 5) for v in grp_opts]
        for col, v in zip(st.columns(widths), grp_opts):
            on = st.session_state["grp"] == v
            col.button(v, key=f"{'sel' if on else 'off'}_grp_{v}", on_click=set_group, args=(v,), use_container_width=True)
    with f3:
        g1, g2, g3 = st.columns([1, 1, 0.9], vertical_alignment="bottom")
        m_from = g1.selectbox("From month", MONTHS, key="m_from")
        m_to = g2.selectbox("To month", MONTHS, key="m_to")
        g3.button("Reset", key="btn_reset", on_click=reset_filters, use_container_width=True)
year_sel = st.session_state["year_sel"]
grp = st.session_state["grp"]

years = ALL_YEARS if year_sel == "All" else [int(year_sel)]
i0, i1 = sorted((MONTHS.index(m_from) + 1, MONTHS.index(m_to) + 1))
fm = df[df["MonthNum"].between(i0, i1)]                      # months only (used for year comparisons)
f = fm[fm["Year"].isin(years)].sort_values("Date")           # months and years
if f.empty:
    st.warning("No data for this selection.")
    st.stop()
sel_group = None if grp == "All" else grp

# ------------------------------------------------------------------ numbers
avg_all = f[NAMES].mean()
hi_lvl, lo_lvl = avg_all.idxmax(), avg_all.idxmin()
nat = f["National"].mean()
yr_avg = fm.groupby("Year")[NAMES + ["National"]].mean()
nat_base = yr_avg["National"][BASE_YEAR]
# The gap follows the education group that is clicked:
#   no group selected -> highest group minus lowest group
#   a group selected  -> that group minus the national rate (positive = worse than national)
if sel_group is None:
    gap_by_year = yr_avg[NAMES].max(axis=1) - yr_avg[NAMES].min(axis=1)
    gap_now = avg_all.max() - avg_all.min()
    gap_fmt, gap_color = "{:.1f}", NAVY
    gap_kpi_label, gap_kpi_name = "Education gap", "Highest minus lowest group"
    gap_title, gap_what = "Education Gap by Year", "Highest minus lowest group"
else:
    gap_by_year = yr_avg[sel_group] - yr_avg["National"]
    gap_now = avg_all[sel_group] - nat
    gap_fmt, gap_color = "{:+.1f}", LEVEL_COLORS[sel_group]
    gap_kpi_label, gap_kpi_name = "Gap vs national", f"{sel_group} minus national"
    gap_title, gap_what = f"{sel_group}: Gap vs National", "Group minus national"
gap_base = gap_by_year[BASE_YEAR]
show_delta = years != [BASE_YEAR]
stk = f.set_index("Date")[NAMES].stack()
pk_date, pk_grp = stk.idxmax()
pk_val = stk.max()


# ------------------------------------------------------------------ helpers
def chip(delta):
    if abs(delta) < 0.05:
        return '<span class="chip flat">● 0.0 pts</span>'
    cls = "bad" if delta > 0 else "good"
    return f'<span class="chip {cls}">{"▲" if delta > 0 else "▼"} {abs(delta):.1f} pts</span>'


def kpi(label, value, name, chip_html, note, color=NAVY):
    return (f'<div class="k" style="--c:{color}"><div class="kl">{label}</div>'
            f'<div class="kmain"><div class="kv">{value}</div>{chip_html}</div>'
            f'<div class="kn">{name}</div><div class="kt">{note}</div></div>')


def flat(text):
    return f'<span class="chip flat">{text}</span>'


def style(fig, h):
    # No legends inside charts: one shared colour legend sits above the panels, so nothing can overlap.
    fig.update_layout(
        height=h, margin=dict(l=6, r=18, t=10, b=6), showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=INK, size=13),
        hoverlabel=dict(bgcolor="#FFFFFF", font_size=13, bordercolor=LINE, font_color=INK),
    )
    fig.update_xaxes(showgrid=False, linecolor=GRID, ticks="", automargin=True, tickfont=dict(size=13, color="#000000"))
    fig.update_yaxes(gridcolor=GRID, zeroline=False, ticks="", automargin=True, tickfont=dict(size=13, color="#000000"))
    return fig


def show(fig, **kw):
    try:
        return st.plotly_chart(fig, width="stretch", config={"displayModeBar": False}, **kw)
    except TypeError:
        return st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, **kw)


def ph(title, sub="", rule=True):
    border = "" if rule else "border-bottom:none;"
    return (f'<div class="ph" style="{border}"><div class="pt">{title}</div>'
            f'<div class="ps">{sub if sub else "&nbsp;"}</div></div>')


def head(title, sub=""):
    st.markdown(ph(title, sub), unsafe_allow_html=True)


# ------------------------------------------------------------------ KPI strip, then the shared legend as its own element
ratio = avg_all[hi_lvl] / avg_all[lo_lvl]
nat_chip = chip(nat - nat_base) if show_delta else flat("Baseline")
nat_note = f"Change vs {BASE_YEAR}" if show_delta else "Baseline year"
gap_chip = chip(gap_now - gap_base) if show_delta else flat("Baseline")
gap_note = f"Change vs {BASE_YEAR}" if show_delta else "Baseline year"
cards = [
    kpi("National rate", f"{nat:.1f}%", "Philippines, both sexes", nat_chip, nat_note, NAVY),
    kpi("Highest group", f"{avg_all[hi_lvl]:.1f}%", hi_lvl, flat(f"{ratio:.1f} times the lowest"),
        "Highest average rate", LEVEL_COLORS[hi_lvl]),
    kpi("Lowest group", f"{avg_all[lo_lvl]:.1f}%", lo_lvl, flat(f"{abs(nat - avg_all[lo_lvl]):.1f} pts below national"),
        "Lowest average rate", LEVEL_COLORS[lo_lvl]),
    kpi(gap_kpi_label, gap_fmt.format(gap_now) + " pts", gap_kpi_name, gap_chip, gap_note, gap_color),
    kpi("Highest month", f"{pk_val:.1f}%", pk_grp, flat(f"{pk_date:%B %Y}"), "Single month peak", LEVEL_COLORS[pk_grp]),
]
items = "".join(f'<span class="lg"><i style="background:{LEVEL_COLORS[n]}"></i>{n}</span>' for n in NAMES)
legend = (f'<div class="legend"><span class="lt">Education group</span>{items}'
          '<span class="lg"><i class="dash"></i>National or average line</span></div>')
st.markdown(f'<div class="kpis">{"".join(cards)}</div>', unsafe_allow_html=True)
st.markdown(legend, unsafe_allow_html=True)

# ------------------------------------------------------------------ row 1: who is hit hardest, and is the gap growing
c1, c2 = st.columns([1.1, 1])

with c1.container(border=True, height=H_ROW1, key="panel_rate"):
    head("Rate by Education Group", f"Average monthly underemployment rate by education level, compared with the national average of {nat:.1f}%")
    ordered = avg_all.sort_values()
    colors = [LEVEL_COLORS[k] for k in ordered.index]
    opac = [1 if (sel_group is None or k == sel_group) else 0.3 for k in ordered.index]
    outline = [BLUE if k == sel_group else "rgba(0,0,0,0)" for k in ordered.index]
    fig = go.Figure(go.Bar(
        x=ordered.values, y=ordered.index, orientation="h",
        marker=dict(color=colors, opacity=opac, line=dict(color=outline, width=3)),
        text=[f"<b>{v:.1f}%</b>" for v in ordered.values], textposition="outside", cliponaxis=False,
        textfont=dict(size=15, color=INK),
        hovertemplate="<b>%{y}</b><br>Average: %{x:.2f}%<extra></extra>",
    ))
    fig.add_shape(type="line", xref="x", yref="paper", x0=nat, x1=nat, y0=0, y1=1,
                  line=dict(color=NAVY, dash="dash", width=2))
    fig.update_xaxes(visible=False, range=[0, ordered.max() * 1.22])
    fig.update_yaxes(showgrid=False, tickfont=dict(size=14, color="#000000"))
    fig.update_layout(clickmode="event+select", dragmode=False, bargap=0.28)
    show(style(fig, 240), key=f"bar_{st.session_state['ver']}", on_select=on_group_bar, selection_mode=["points"])
    if sel_group is None:
        take = (f"<b>{hi_lvl}</b> workers are underemployed at <b>{avg_all[hi_lvl]:.1f}%</b>, "
                f"<b>{ratio:.1f} times</b> the rate of <b>{lo_lvl}</b> ({avg_all[lo_lvl]:.1f}%).")
    else:
        d = avg_all[sel_group] - nat
        pos = "level with" if abs(d) < 0.05 else f"<b>{abs(d):.1f} pts {'above' if d > 0 else 'below'}</b>"
        take = f"<b>{sel_group}</b> averages <b>{avg_all[sel_group]:.1f}%</b>, {pos} the national rate of {nat:.1f}%."
    st.markdown(f'<div class="take"><div class="tl">Key takeaway</div>{take}</div>', unsafe_allow_html=True)

with c2.container(border=True, height=H_ROW1, key="panel_gap"):
    gmean = gap_by_year.mean()
    signed = sel_group is not None
    head(gap_title, f"{gap_what}, in points | Average {gmean:+.1f}" if signed
         else f"{gap_what}, in points | Average {gmean:.1f}")
    gx = [str(y) for y in gap_by_year.index]
    gopac = [1 if (year_sel == "All" or str(y) == year_sel) else 0.3 for y in gap_by_year.index]
    gline = [BLUE if str(y) == year_sel else "rgba(0,0,0,0)" for y in gap_by_year.index]
    fig = go.Figure(go.Bar(
        x=gx, y=gap_by_year.values,
        marker=dict(color=[YEAR_COLORS[y] for y in gap_by_year.index], opacity=gopac, line=dict(color=gline, width=3)),
        text=[f"<b>{v:+.1f}</b>" if signed else f"<b>{v:.1f}</b>" for v in gap_by_year.values],
        textposition="outside", cliponaxis=False, textfont=dict(size=16, color=INK),
        hovertemplate=("<b>%{x}</b><br>Gap: %{y:+.1f} pts<extra></extra>" if signed
                       else "<b>%{x}</b><br>Gap: %{y:.1f} pts<extra></extra>"),
    ))
    fig.add_shape(type="line", xref="paper", yref="y", x0=0, x1=1, y0=gmean, y1=gmean,
                  line=dict(color=NAVY, dash="dash", width=2))
    fig.update_xaxes(type="category", tickfont=dict(size=15, color="#000000"))
    fig.update_layout(clickmode="event+select", dragmode=False, bargap=0.35)
    style(fig, 285)
    lo_y = min(0.0, gap_by_year.min()) * 1.35
    hi_y = max(0.0, gap_by_year.max()) * 1.25 or 1.0
    fig.update_yaxes(range=[lo_y, hi_y], zeroline=True, zerolinecolor=SOFT, zerolinewidth=1.2)
    show(fig, key=f"gap_{st.session_state['ver']}", on_select=on_gap_bar, selection_mode=["points"])

# ------------------------------------------------------------------ row 2: the calm national line, and who the workers are
c3, c4 = st.columns([1, 1])

with c3.container(border=True, height=H_ROW2, key="panel_year"):
    head("Average Rate by Year", "Annual average underemployment rate by education level, compared with the national rate.")
    fig = go.Figure()
    for lvl in NAMES:
        dim = sel_group is not None and lvl != sel_group
        is_sel = lvl == sel_group
        fig.add_trace(go.Scatter(
            x=yr_avg.index, y=yr_avg[lvl], mode="lines+markers+text" if is_sel else "lines+markers", name=lvl,
            opacity=0.22 if dim else 1,
            line=dict(color=LEVEL_COLORS[lvl], width=5 if is_sel else 3),
            marker=dict(size=11 if is_sel else 9, color=LEVEL_COLORS[lvl], line=dict(color="#FFFFFF", width=1.5)),
            text=[f"<b>{v:.1f}%</b>" for v in yr_avg[lvl]], textposition="top center",
            textfont=dict(size=14, color=INK), hovertemplate="%{y:.1f}%"))
    fig.add_trace(go.Scatter(x=yr_avg.index, y=yr_avg["National"], mode="lines", name="National",
                             line=dict(color=NAVY, dash="dash", width=3), hovertemplate="%{y:.1f}%"))
    if year_sel != "All":
        yv = int(year_sel)
        fig.add_vrect(x0=yv - 0.3, x1=yv + 0.3, fillcolor="rgba(29,78,216,0.12)", line_width=0, layer="below")
    fig.update_xaxes(tickvals=list(yr_avg.index), range=[yr_avg.index.min() - 0.4, yr_avg.index.max() + 0.4],
                     tickfont=dict(size=15, color="#000000"))
    fig.update_yaxes(ticksuffix="%", range=[0, 20], tickmode="linear", tick0=0, dtick=5)
    fig.update_layout(hovermode="x unified")
    (style(fig, 270))
    fig.update_layout(margin=dict(l=6, r=18, t=35, b=6))
    show(fig)

with c4.container(border=True, height=H_ROW2, key="panel_pyramid"):
    if not HAS_SEX:
        head("Underemployed Workers by Age and Sex")
        st.info("No Male and Female columns were found in the dataset.")
    else:
        ta, tb = st.columns([5, 3], vertical_alignment="center")
        ta.markdown(ph("Age and Sex", "Distribution of underemployed workers by age group and sex.", rule=False), unsafe_allow_html=True)
        mode = st.session_state["pyr_mode"]
        for col, v in zip(tb.columns(2), ("Count", "Share")):
            col.button(v, key=f"{'sel' if mode == v else 'off'}_pyr_{v}", on_click=set_pyr, args=(v,), use_container_width=True)
        st.markdown('<div style="border-bottom:2px solid #2A3A50;margin:10px 0 2px 0"></div>', unsafe_allow_html=True)
        pv = pd.DataFrame({
            "Male": [f[c].mean() for c in SEX_COLS["Male"]],
            "Female": [f[c].mean() for c in SEX_COLS["Female"]],
        }, index=[age_label(c) for c in SEX_COLS["Male"]])
        unit = ""
        if mode == "Share":
            pv = pv / pv.sum() * 100
            unit = "%"
        mx = float(pv[["Male", "Female"]].values.max())
        fig = go.Figure()
        for sx, color, sign in (("Male", MALE, -1), ("Female", FEMALE, 1)):
            fig.add_trace(go.Bar(
                y=pv.index, x=sign * pv[sx], orientation="h", name=sx, marker=dict(color=color), customdata=pv[sx],
                text=[f"<b>{v:,.0f}{unit}</b>" for v in pv[sx]], textposition="outside", cliponaxis=False,
                textfont=dict(size=14, color=INK),
                hovertemplate=f"<b>%{{y}}</b><br>{sx}: %{{customdata:,.1f}}{unit}<extra></extra>"))
        ticks = [-mx, 0, mx]
        fig.update_xaxes(range=[-mx * 1.3, mx * 1.3], tickvals=ticks,
                         ticktext=[f"{abs(tv):,.0f}{unit}" for tv in ticks], showgrid=True, gridcolor=GRID)
        # Youngest age group at the bottom, oldest at the top (the natural order of the bars).
        fig.update_yaxes(showgrid=False, tickfont=dict(size=14))
        fig.update_layout(barmode="relative", bargap=0.25)
        style(fig, 285)
        fig.update_layout(margin=dict(l=6, r=18, t=40, b=6))
        for txt, xpos, col in (("Male", 0.25, MALE), ("Female", 0.75, FEMALE)):
            fig.add_annotation(x=xpos, y=1.0, xref="paper", yref="paper", yanchor="bottom", showarrow=False,
                               text=f"<b>{txt}</b>", font=dict(size=16, color=col))
        show(fig)

# ------------------------------------------------------------------ row 3: month by month detail
with st.container(border=True, height=H_ROW3, key="panel_month"):
    head("Monthly Rate by Education Group",
         f"Monthly underemployment rate by education level, {PERIOD if year_sel == 'All' else year_sel}"
         + (" " if (year_sel == "All" and sel_group is None) else ""))
    fig = go.Figure()
    for lvl in NAMES:
        dim = sel_group is not None and lvl != sel_group
        fig.add_trace(go.Scatter(
            x=f["Date"], y=f[lvl], mode="lines", name=lvl, opacity=0.2 if dim else 1,
            line=dict(color=LEVEL_COLORS[lvl], width=4 if lvl == sel_group else 2.6), hovertemplate="%{y:.1f}%"))
    ymin, ymax = None, None
    if year_sel == "All" and sel_group is None:
        # Mark the single highest and lowest month, only when no year or group filter is applied.
        mid = f["Date"].min() + (f["Date"].max() - f["Date"].min()) / 2
        (hi_d, hi_g), hi_v = stk.idxmax(), stk.max()
        (lo_d, lo_g), lo_v = stk.idxmin(), stk.min()
        for d, g, v, kind, side in ((hi_d, hi_g, hi_v, "Highest", "top"), (lo_d, lo_g, lo_v, "Lowest", "bottom")):
            horiz = "left" if d > mid else "right"
            fig.add_trace(go.Scatter(
                x=[d], y=[v], mode="markers+text", showlegend=False,
                marker=dict(size=15, color=LEVEL_COLORS[g], line=dict(color=INK, width=2.5)),
                text=[f"<b>{kind}: {d:%b %Y}<br>{g} {v:.1f}%</b>"], textposition=f"{side} {horiz}", cliponaxis=False,
                textfont=dict(size=14, color=INK), hoverinfo="skip"))
        ymin, ymax = 0.0, hi_v + 4.5
    fig.update_yaxes(ticksuffix="%", nticks=6, rangemode="tozero", range=[0, ymax] if ymax is not None else None)
    fig.update_xaxes(tickformat="%b %Y", nticks=10)
    fig.update_layout(hovermode="x unified")
    style(fig, 280)
    fig.update_layout(margin=dict(l=6, r=18, t=30, b=6))
    show(fig)

# ------------------------------------------------------------------ footer
st.markdown(
    '<div class="foot"><span><b>Definition</b> &nbsp; Underemployment rate = underemployed persons as a percent of employed persons. '
    'Yearly and overall rates are averages of the monthly rates.</span>'
    '<span><b>Source</b> &nbsp; Philippine Statistics Authority, Labor Force Survey (OpenSTAT) &nbsp;·&nbsp; ',
    unsafe_allow_html=True,
)
