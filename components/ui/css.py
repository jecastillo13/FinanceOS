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
[data-testid="stSidebar"][aria-expanded="true"] { min-width:340px!important; max-width:340px!important; width:340px!important; }
[data-testid="stSidebar"][aria-expanded="true"] > div:first-child { width:340px!important; min-width:340px!important; }
[data-testid="stSidebar"][aria-expanded="false"] { min-width:0!important; max-width:0!important; width:0!important; border-right:0; }
[data-testid="stSidebar"][aria-expanded="false"] > div:first-child { width:0!important; min-width:0!important; }
[data-testid="stSidebar"] > div:first-child { background:radial-gradient(circle at 10% 0%,#273765 0,transparent 32%),linear-gradient(180deg,#111B34 0%,#0A1020 60%); }
[data-testid="stSidebar"] .block-container { padding:1.3rem 1rem 1.35rem; }
.brand { padding:.8rem .8rem 1rem; }
.brand-row { display:flex; align-items:center; gap:10px; }
.brand-mark { display:inline-flex; align-items:center; justify-content:center; width:56px; height:56px; border-radius:19px; background:linear-gradient(145deg,#9B9CFF,#5B5CEB); font-size:27px; box-shadow:0 12px 24px rgba(79,70,229,.38),inset 0 1px 1px rgba(255,255,255,.32); }
.brand-title { font-family:'Plus Jakarta Sans',sans-serif; font-size:24px; font-weight:800; letter-spacing:-.8px; color:var(--text); }
.brand-subtitle { color:#9AA9C7; font-size:13px; margin-top:3px; }
.sidebar-section { color:#8492B0; font-size:12px; font-weight:800; letter-spacing:1.1px; padding:1.1rem .8rem .65rem; }
[data-testid="stSidebar"] [data-testid="stRadio"] { gap:2px; }
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"] { position:relative; color:#C0CAE0; padding:.92rem 1rem; border-radius:18px; margin:4px 0; min-height:52px; transition:background .18s ease,transform .18s ease,box-shadow .18s ease; }
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"] > div:first-child { display:none!important; }
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"] > div:last-child { margin-left:0!important; }
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"] p { font-size:16px; font-weight:650; letter-spacing:-.1px; }
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"]:hover { background:rgba(137,150,190,.10); color:#F1F5FF; transform:translateX(2px); }
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) { background:linear-gradient(135deg,rgba(129,140,248,.92),rgba(99,102,241,.82)); color:white; box-shadow:0 9px 18px rgba(67,56,202,.28),inset 0 1px 1px rgba(255,255,255,.23); }
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked)::after { content:""; position:absolute; right:13px; top:50%; width:6px; height:6px; transform:translateY(-50%); border-radius:50%; background:white; box-shadow:0 0 10px white; }
.sidebar-insight { margin:1rem .35rem .6rem; padding:1rem; border-radius:18px; background:linear-gradient(145deg,rgba(35,50,84,.88),rgba(20,29,52,.88)); border:1px solid rgba(131,148,190,.22); box-shadow:inset 0 1px rgba(255,255,255,.04); }
.sidebar-insight-label { color:#9AA9C7; font-size:11px; font-weight:700; letter-spacing:.7px; }
.sidebar-insight-text { color:#E8ECFF; font-size:14px; font-weight:700; margin-top:6px; }
.sidebar-footer { color:#61708D; font-size:11px; text-align:center; padding-top:.2rem; }
.app-header { display:flex; align-items:center; justify-content:space-between; gap:1rem; padding:.3rem 0 1.3rem; border-bottom:1px solid rgba(39,52,81,.7); margin-bottom:1.5rem; }
.app-header-title { font-family:'Plus Jakarta Sans',sans-serif; font-size:18px; font-weight:800; letter-spacing:-.5px; color:var(--text); }
.app-header-subtitle { color:var(--muted); font-size:13px; margin-top:3px; }
.app-status { padding:.42rem .75rem; border:1px solid rgba(52,211,153,.25); border-radius:999px; color:#A7F3D0; background:rgba(52,211,153,.08); font-size:12px; font-weight:700; }
.page-hero { display:flex; align-items:center; gap:15px; padding:1.35rem 1.5rem; margin:0 0 1.4rem; border-radius:22px; border:1px solid rgba(133,148,210,.30); background:radial-gradient(circle at 0% 50%,rgba(110,91,255,.20),transparent 35%),linear-gradient(115deg,rgba(36,51,91,.98),rgba(19,27,48,.96)); box-shadow:0 18px 38px rgba(0,0,0,.25),inset 0 1px rgba(255,255,255,.08); }
.page-hero-icon { display:flex; align-items:center; justify-content:center; width:52px; height:52px; flex:0 0 52px; border-radius:17px; font-size:25px; background:linear-gradient(145deg,rgba(129,140,248,.95),rgba(79,70,229,.9)); box-shadow:0 10px 20px rgba(79,70,229,.28),inset 0 1px rgba(255,255,255,.25); }
.page-hero-label { color:#A5B4FC; font-size:10px; font-weight:800; letter-spacing:1.2px; margin-bottom:3px; }
.page-hero-title { font-family:'Plus Jakarta Sans',sans-serif; color:#F7F8FF; font-size:24px; font-weight:800; letter-spacing:-.7px; }
.page-hero-description { color:#AEB9D2; font-size:13px; margin-top:4px; }
h1,h2,h3 { font-family:'Plus Jakarta Sans',sans-serif !important; letter-spacing:-.6px; color:var(--text) !important; }
h1 { font-size:28px !important; margin-bottom:.15rem !important; }
p, label, [data-testid="stCaptionContainer"] { color:var(--muted); }
.metric-card { background:linear-gradient(145deg,rgba(30,41,68,.95),rgba(20,27,46,.95)); border:1px solid var(--border); border-radius:18px; padding:1rem 1.05rem; min-height:118px; box-shadow:0 12px 28px rgba(0,0,0,.14); transition:.18s ease; }
.metric-card:hover { transform:translateY(-2px); border-color:#5866A0; }
.metric-top { display:flex; align-items:center; justify-content:space-between; color:var(--muted); font-size:13px; font-weight:600; }
.metric-icon { width:34px; height:34px; display:flex; align-items:center; justify-content:center; border-radius:11px; background:rgba(129,140,248,.14); font-size:17px; }
.metric-value { color:var(--text); font-family:'Plus Jakarta Sans',sans-serif; font-size:25px; font-weight:800; margin-top:16px; letter-spacing:-1px; }
.metric-help { color:var(--muted); font-size:11px; margin-top:4px; }
.account-card { margin-top:.35rem; padding:1.2rem; border:1px solid rgba(104,124,181,.34); border-radius:20px; background:radial-gradient(circle at 100% 0%,rgba(112,91,255,.20),transparent 42%),linear-gradient(145deg,rgba(35,49,87,.92),rgba(18,27,48,.95)); box-shadow:0 14px 30px rgba(0,0,0,.17),inset 0 1px rgba(255,255,255,.07); }
.account-card-top { display:flex; align-items:center; gap:12px; }
.account-card-brand-stack { display:flex; flex-direction:column; align-items:flex-start; gap:6px; }
.account-card-icon { display:flex; align-items:center; gap:7px; justify-content:flex-start; min-width:82px; height:44px; padding:0 8px; border-radius:14px; font-size:18px; box-shadow:inset 0 1px rgba(255,255,255,.28),0 7px 14px rgba(0,0,0,.16); }
.account-brand-monogram { display:flex; align-items:center; justify-content:center; width:28px; height:28px; border-radius:9px; background:rgba(8,15,31,.34); color:#FFFFFF; font-family:'Plus Jakarta Sans',sans-serif; font-size:15px; font-weight:800; }
.account-brand-word { color:#FFFFFF; font-family:'Plus Jakarta Sans',sans-serif; font-size:10px; font-weight:800; letter-spacing:.35px; white-space:nowrap; }
.account-card-type { color:#AAB8D4; font-size:12px; margin-left:3px; }
.account-card-badge { margin-left:auto; padding:.35rem .55rem; border:1px solid rgba(165,180,252,.35); border-radius:999px; background:rgba(129,140,248,.12); color:#C7D2FE; font-size:11px; font-weight:800; }
.account-card-divider { height:1px; background:linear-gradient(90deg,rgba(139,154,205,.35),transparent); margin:1.1rem 0 .85rem; }
.account-card-label { color:#8E9DBB; font-size:10px; font-weight:800; letter-spacing:.9px; }
.account-card-balance { color:#FFFFFF; font-family:'Plus Jakarta Sans',sans-serif; font-size:24px; font-weight:800; letter-spacing:-.8px; margin-top:6px; }
.account-actions-gap { height:9px; }
.account-card-bottom-gap { height:14px; }
.category-action-gap { height:14px; }
[data-testid="stMetric"] { min-height:108px; padding:1rem 1.05rem; border:1px solid rgba(107,125,182,.30); border-radius:18px; background:linear-gradient(145deg,rgba(35,49,85,.95),rgba(19,27,47,.95)); box-shadow:0 12px 25px rgba(0,0,0,.16),inset 0 1px rgba(255,255,255,.05); }
[data-testid="stMetricLabel"] { color:#AEB9D2!important; font-size:13px!important; font-weight:700!important; }
[data-testid="stMetricValue"] { color:#F7F8FF!important; font-family:'Plus Jakarta Sans',sans-serif!important; font-weight:800!important; }
[data-testid="stExpander"] { background:linear-gradient(105deg,rgba(35,48,82,.66),rgba(17,25,44,.58)); border:1px solid rgba(91,111,170,.36)!important; border-left:3px solid rgba(129,140,248,.75)!important; border-radius:14px!important; overflow:hidden; box-shadow:0 6px 14px rgba(0,0,0,.10); backdrop-filter:blur(10px); margin-bottom:7px; }
[data-testid="stExpander"]:hover { border-color:rgba(150,160,255,.72)!important; background:linear-gradient(105deg,rgba(48,64,108,.82),rgba(24,34,59,.72)); transform:translateX(2px); }
[data-testid="stExpander"] summary { padding:.18rem .15rem; font-size:15px; font-weight:700; color:#EAF0FF!important; }
[data-testid="stExpander"] summary span, [data-testid="stExpander"] summary p { font-size:16px!important; color:#F1F4FF!important; font-weight:700!important; }
[data-testid="stForm"] { background:radial-gradient(circle at 100% 0%,rgba(101,88,230,.14),transparent 36%),rgba(23,33,58,.72); border:1px solid rgba(102,121,177,.35); border-radius:18px; padding:1.25rem 1.35rem; box-shadow:0 14px 30px rgba(0,0,0,.12),inset 0 1px rgba(255,255,255,.05); backdrop-filter:blur(14px); }
[data-testid="stDataFrame"] { border:1px solid var(--border); border-radius:12px; overflow:hidden; }
[data-testid="stAlert"] { border-radius:13px; border:1px solid var(--border); }
hr { border-color:var(--border)!important; margin:1.5rem 0!important; }
[data-testid="stTextInput"] input, [data-testid="stNumberInput"] input, [data-testid="stTextArea"] textarea, [data-baseweb="select"] > div { background:#0F172A!important; color:var(--text)!important; border-color:#33415F!important; border-radius:10px!important; }
[data-testid="stWidgetLabel"] p { color:#B8C5DF!important; font-size:14px!important; font-weight:700!important; }
[data-testid="stTextInput"] input, [data-testid="stNumberInput"] input, [data-testid="stTextArea"] textarea, [data-baseweb="select"] * { font-size:15px!important; }
[data-testid="stTextInput"] input:focus, [data-testid="stNumberInput"] input:focus, [data-testid="stTextArea"] textarea:focus { border-color:var(--primary)!important; box-shadow:0 0 0 2px rgba(129,140,248,.18)!important; }
button[kind="primary"], [data-testid="stFormSubmitButton"] button { min-height:46px!important; background:linear-gradient(135deg,#9A91FF,#605CF4)!important; border:1px solid rgba(190,188,255,.55)!important; border-radius:13px!important; color:#FFFFFF!important; font-size:14px!important; font-weight:800!important; letter-spacing:.1px; box-shadow:0 10px 22px rgba(91,82,242,.34),inset 0 1px rgba(255,255,255,.28)!important; text-shadow:0 1px 2px rgba(0,0,0,.2); }
[data-testid="stFormSubmitButton"] button, [data-testid="stFormSubmitButton"] button * { color:#FFFFFF!important; opacity:1!important; }
[data-testid="stButton"] button { min-height:44px; border-radius:13px!important; border:1px solid #49608E!important; background:linear-gradient(145deg,#2A3B63,#1B2845)!important; color:#F4F6FF!important; font-weight:750!important; box-shadow:inset 0 1px rgba(255,255,255,.08),0 7px 15px rgba(0,0,0,.16); }
[data-testid="stButton"] button[kind="primary"] { background:linear-gradient(135deg,#9A91FF,#605CF4)!important; border-color:rgba(190,188,255,.55)!important; color:#FFFFFF!important; box-shadow:0 10px 22px rgba(91,82,242,.34),inset 0 1px rgba(255,255,255,.28)!important; }
button[kind="secondary"] { border-radius:12px!important; border-color:#415278!important; background:linear-gradient(145deg,#23304D,#18233B)!important; color:#EAF0FF!important; }
[data-testid="stProgress"] > div > div > div { background:linear-gradient(90deg,#818CF8,#34D399)!important; }
div[role="dialog"] { border:1px solid rgba(150,160,255,.48)!important; border-radius:26px!important; background:radial-gradient(circle at 0% 0%,rgba(125,110,255,.24),transparent 38%),linear-gradient(145deg,#1C294A,#10182C)!important; box-shadow:0 30px 80px rgba(0,0,0,.56),inset 0 1px rgba(255,255,255,.10)!important; backdrop-filter:blur(22px); }
div[role="dialog"] [data-testid="stDialogHeader"] { padding-bottom:.55rem; }
div[role="dialog"] h2 { font-size:26px!important; }
@media(max-width:800px) { .block-container { padding:1rem; } .app-status { display:none; } }
</style>
""", unsafe_allow_html=True)
