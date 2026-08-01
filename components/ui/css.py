import streamlit as st


def load_css():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap');
:root { --bg:#0B1020; --surface:#141B2E; --surface2:#1A233A; --border:#273451; --text:#F5F7FF; --muted:#99A7C2; --primary:#818CF8; --success:#34D399; }
html, body, [class*="css"] { font-family:'DM Sans', sans-serif; }
[data-testid="stAppViewContainer"] { background:radial-gradient(circle at 75% -10%, #202c56 0, transparent 30%),var(--bg); color:var(--text); }
[data-testid="stHeader"] { display:none; }
[data-testid="stAppViewContainer"] .main { padding-top:0; }
.block-container { max-width:1500px; padding:1.5rem 2.25rem 3rem; }
[data-testid="stSidebar"] { background:#0A1020; border-right:1px solid rgba(100,116,139,.22); }
[data-testid="stSidebar"] > div:first-child { background:radial-gradient(circle at 10% 0%,#273765 0,transparent 32%),linear-gradient(180deg,#111B34 0%,#0A1020 60%); }
[data-testid="stSidebar"] .block-container { padding:1rem .75rem 1.15rem; }
.brand { padding:.7rem .65rem .75rem; }
.brand-row { display:flex; align-items:center; gap:10px; }
.brand-mark { display:inline-flex; align-items:center; justify-content:center; width:44px; height:44px; border-radius:15px; background:linear-gradient(145deg,#9B9CFF,#5B5CEB); font-size:21px; box-shadow:0 12px 24px rgba(79,70,229,.38),inset 0 1px 1px rgba(255,255,255,.32); }
.brand-title { font-family:'Plus Jakarta Sans',sans-serif; font-size:19px; font-weight:800; letter-spacing:-.8px; color:var(--text); }
.brand-subtitle { color:#9AA9C7; font-size:11px; margin-top:2px; }
.sidebar-section { color:#70809F; font-size:10px; font-weight:800; letter-spacing:1.1px; padding:.7rem .7rem .45rem; }
[data-testid="stSidebar"] [data-testid="stRadio"] { gap:2px; }
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"] { position:relative; color:#AEB9D2; padding:.67rem .72rem; border-radius:14px; margin:2px 0; min-height:40px; transition:background .18s ease,transform .18s ease,box-shadow .18s ease; }
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"] > div:first-child { display:none!important; }
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"] > div:last-child { margin-left:0!important; }
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"] p { font-size:13px; font-weight:600; letter-spacing:-.1px; }
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"]:hover { background:rgba(137,150,190,.10); color:#F1F5FF; transform:translateX(2px); }
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) { background:linear-gradient(135deg,rgba(129,140,248,.92),rgba(99,102,241,.82)); color:white; box-shadow:0 9px 18px rgba(67,56,202,.28),inset 0 1px 1px rgba(255,255,255,.23); }
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked)::after { content:""; position:absolute; right:13px; top:50%; width:6px; height:6px; transform:translateY(-50%); border-radius:50%; background:white; box-shadow:0 0 10px white; }
.sidebar-insight { margin:.9rem .35rem .5rem; padding:.85rem .9rem; border-radius:16px; background:linear-gradient(145deg,rgba(35,50,84,.88),rgba(20,29,52,.88)); border:1px solid rgba(131,148,190,.22); box-shadow:inset 0 1px rgba(255,255,255,.04); }
.sidebar-insight-label { color:#9AA9C7; font-size:10px; font-weight:700; letter-spacing:.7px; }
.sidebar-insight-text { color:#E8ECFF; font-size:12px; font-weight:700; margin-top:5px; }
.sidebar-footer { color:#61708D; font-size:10px; text-align:center; padding-top:.2rem; }
.app-header { display:flex; align-items:center; justify-content:space-between; gap:1rem; padding:.3rem 0 1.3rem; border-bottom:1px solid rgba(39,52,81,.7); margin-bottom:1.5rem; }
.app-header-title { font-family:'Plus Jakarta Sans',sans-serif; font-size:18px; font-weight:800; letter-spacing:-.5px; color:var(--text); }
.app-header-subtitle { color:var(--muted); font-size:13px; margin-top:3px; }
.app-status { padding:.42rem .75rem; border:1px solid rgba(52,211,153,.25); border-radius:999px; color:#A7F3D0; background:rgba(52,211,153,.08); font-size:12px; font-weight:700; }
h1,h2,h3 { font-family:'Plus Jakarta Sans',sans-serif !important; letter-spacing:-.6px; color:var(--text) !important; }
h1 { font-size:28px !important; margin-bottom:.15rem !important; }
p, label, [data-testid="stCaptionContainer"] { color:var(--muted); }
.metric-card { background:linear-gradient(145deg,rgba(30,41,68,.95),rgba(20,27,46,.95)); border:1px solid var(--border); border-radius:18px; padding:1rem 1.05rem; min-height:118px; box-shadow:0 12px 28px rgba(0,0,0,.14); transition:.18s ease; }
.metric-card:hover { transform:translateY(-2px); border-color:#5866A0; }
.metric-top { display:flex; align-items:center; justify-content:space-between; color:var(--muted); font-size:13px; font-weight:600; }
.metric-icon { width:34px; height:34px; display:flex; align-items:center; justify-content:center; border-radius:11px; background:rgba(129,140,248,.14); font-size:17px; }
.metric-value { color:var(--text); font-family:'Plus Jakarta Sans',sans-serif; font-size:25px; font-weight:800; margin-top:16px; letter-spacing:-1px; }
.metric-help { color:var(--muted); font-size:11px; margin-top:4px; }
[data-testid="stExpander"] { background:rgba(20,27,46,.8); border:1px solid var(--border)!important; border-radius:14px!important; overflow:hidden; }
[data-testid="stForm"] { background:rgba(20,27,46,.68); border:1px solid var(--border); border-radius:16px; padding:1rem 1.1rem; }
[data-testid="stDataFrame"] { border:1px solid var(--border); border-radius:12px; overflow:hidden; }
[data-testid="stAlert"] { border-radius:13px; border:1px solid var(--border); }
hr { border-color:var(--border)!important; margin:1.5rem 0!important; }
[data-testid="stTextInput"] input, [data-testid="stNumberInput"] input, [data-testid="stTextArea"] textarea, [data-baseweb="select"] > div { background:#0F172A!important; color:var(--text)!important; border-color:#33415F!important; border-radius:10px!important; }
[data-testid="stTextInput"] input:focus, [data-testid="stNumberInput"] input:focus, [data-testid="stTextArea"] textarea:focus { border-color:var(--primary)!important; box-shadow:0 0 0 2px rgba(129,140,248,.18)!important; }
button[kind="primary"], [data-testid="stFormSubmitButton"] button { background:linear-gradient(135deg,#818CF8,#6366F1)!important; border:0!important; border-radius:10px!important; color:white!important; font-weight:700!important; }
button[kind="secondary"] { border-radius:10px!important; border-color:#3A4969!important; background:#18223A!important; color:#DCE3F7!important; }
[data-testid="stProgress"] > div > div > div { background:linear-gradient(90deg,#818CF8,#34D399)!important; }
@media(max-width:800px) { .block-container { padding:1rem; } .app-status { display:none; } }
</style>
""", unsafe_allow_html=True)
