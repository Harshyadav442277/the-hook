"""THE HOOK visual tokens and Streamlit CSS."""

import streamlit as st


CSS = """
<style>
:root {
  --navy: #0B1F33; --navy2: #183B56; --cream: #F7F4ED;
  --field: #176B4D; --field-soft: #DCEDE6; --hook: #C74755;
  --gold: #D9A928; --slate: #5D6B78; --line: #D9E0E6;
}
.stApp { background: var(--cream); color: var(--navy); }
[data-testid="stHeader"] { background: rgba(247,244,237,.92); }
[data-testid="stSidebarNav"] { display: none; }
.block-container { max-width: 1180px; padding-top: 1.1rem; padding-bottom: 4rem; }
.block-container > [data-testid="stVerticalBlock"] { gap: .7rem; }
.hook-eyebrow { color: var(--hook); font-size: .76rem; font-weight: 800; letter-spacing: .14em; }
.hook-title { color: var(--navy); font-size: clamp(2.35rem,5vw,3.35rem); line-height: .95; font-weight: 850; margin: .18rem 0 .35rem; }
.hook-tagline { color: var(--navy2); font-size: 1.22rem; font-weight: 680; margin-bottom: .3rem; }
.hook-subtitle { color: var(--slate); max-width: 760px; margin-bottom: .15rem; }
.hook-card { background: white; border: 1px solid var(--line); border-radius: 15px; padding: 1.15rem 1.25rem; height: 100%; }
.hook-card.actual { border-top: 5px solid var(--hook); }
.hook-card.recommended { background: var(--field-soft); border-color: #b5d7c9; border-top: 5px solid var(--field); }
.hook-label { color: var(--slate); font-size: .72rem; font-weight: 800; letter-spacing: .1em; text-transform: uppercase; }
.hook-value { color: var(--navy); font-size: 1.75rem; font-weight: 800; line-height: 1.15; margin: .35rem 0; }
.hook-wp { color: var(--navy2); font-size: 1rem; font-weight: 700; }
.hook-delta { color: var(--gold); font-size: 1.28rem; font-weight: 850; text-align: center; margin: 1rem 0 .3rem; }
.situation-grid { display:grid; grid-template-columns:repeat(4,minmax(120px,1fr)); gap:.8rem; }
.situation-item { background:white; border:1px solid var(--line); border-radius:12px; padding:.68rem .9rem; }
.situation-item b { display:block; color:var(--navy); font-size:1.12rem; margin-top:.2rem; }
.base-chip { display:inline-block; margin:.1rem .2rem .1rem 0; padding:.18rem .46rem; border-radius:5px; font-size:.78rem; font-weight:800; background:#E8EDF1; color:var(--navy); }
.base-chip.on { background:var(--gold); color:#17202A; }
.method-step { background:white; border:1px solid var(--line); border-radius:14px; padding:1rem; min-height:135px; }
.method-step .num { color:var(--hook); font-weight:850; }
.muted { color:var(--slate); }
div[data-testid="stMetric"] { background:white; border:1px solid var(--line); border-radius:12px; padding:.8rem 1rem; }
@media (max-width: 760px) { .situation-grid { grid-template-columns:repeat(2,1fr); } }
</style>
"""


def apply_theme() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
