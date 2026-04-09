import streamlit as st
import json
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# ─── הגדרות ───────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="גדוד חרב שאול",
    page_icon="⚔",
    layout="wide",
    initial_sidebar_state="collapsed"
)

PASSWORDS = {
    "magad":   "magad123",
    "yarden":  "yarden123",
    "gilboa":  "gilboa123",
    "taanach": "taanach123",
    "afula":   "hafoola123",
    "palsam":  "palsam123",
}

COMPANIES = {
    "yarden":  {"name": "ירדן",        "color": "#e24b4a"},
    "gilboa":  {"name": "גלבוע",       "color": "#378add"},
    "taanach": {"name": "תענך",        "color": "#639922"},
    "afula":   {"name": "עפולה",       "color": "#ba7517"},
    "palsam":  {"name": 'פלס"ם אג"ם', "color": "#7f77dd"},
}
COMP_KEYS = list(COMPANIES.keys())

SEV_LABEL = {"low": "נמוך", "mid": "בינוני", "high": "גבוה", "critical": "קריטי"}
SEV_COLOR = {"low": "#7a9170", "mid": "#ba7517", "high": "#e24b4a", "critical": "#a32d2d"}
LOC_LABEL = {"base": "בבסיס", "home": "בבית", "milim": "מגויס", "other": "אחר"}
LOC_COLOR = {"base": "#185fa5", "home": "#854f0b", "milim": "#3b6d11", "other": "#888"}

# ─── Google Sheets connection ──────────────────────────────────────────────────

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def get_gs_client():
    creds_dict = json.loads(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)

def get_sheet(tab_name):
    gc = get_gs_client()
    sh = gc.open(st.secrets["sheet_name"])
    try:
        return sh.worksheet(tab_name)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=tab_name, rows=1000, cols=20)
        return ws

@st.cache_data(ttl=10)
def load_soldiers():
    ws = get_sheet("soldiers")
    records = ws.get_all_records()
    return records

@st.cache_data(ttl=10)
def load_ammo():
    ws = get_sheet("ammo")
    return ws.get_all_records()

@st.cache_data(ttl=10)
def load_events():
    ws = get_sheet("events")
    return ws.get_all_records()

@st.cache_data(ttl=10)
def load_history():
    ws = get_sheet("history")
    return ws.get_all_records()

def clear_cache():
    load_soldiers.clear()
    load_ammo.clear()
    load_events.clear()
    load_history.clear()

def append_row(tab, row):
    ws = get_sheet(tab)
    if ws.row_count == 0 or ws.get_all_values() == []:
        ws.append_row(list(row.keys()))
    ws.append_row(list(row.values()))
    clear_cache()

def overwrite_sheet(tab, df):
    ws = get_sheet(tab)
    ws.clear()
    ws.update([df.columns.tolist()] + df.values.tolist())
    clear_cache()

def add_history(msg):
    user = st.session_state.user
    name = "מג\"ד" if user == "magad" else COMPANIES[user]["name"]
    append_row("history", {
        "ts": datetime.now().strftime("%d/%m %H:%M"),
        "by": name,
        "msg": msg
    })

# ─── CSS ──────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { direction: rtl; }
    [data-testid="stSidebar"] { display: none; }
    .main .block-container { padding: 1rem 1.5rem 2rem; max-width: 900px; }
    h1, h2, h3 { font-weight: 500; }
    .hdr { background: #5a6e52; color: white; padding: 12px 18px; border-radius: 10px;
           display: flex; align-items: center; gap: 12px; margin-bottom: 1rem; }
    .hdr h1 { margin: 0; font-size: 18px; color: white; }
    .hdr p  { margin: 0; font-size: 12px; opacity: .8; }
    .metric-row { display: flex; gap: 10px; margin-bottom: 1rem; flex-wrap: wrap; }
    .metric-box { background: #eef2ec; border-radius: 10px; padding: 12px 18px;
                  text-align: center; flex: 1; min-width: 80px; }
    .metric-num { font-size: 26px; font-weight: 500; color: #5a6e52; }
    .metric-lbl { font-size: 11px; color: #666; margin-top: 2px; }
    .ev-card { border-right: 4px solid #7a9170; padding: 8px 12px;
               border-radius: 0 8px 8px 0; margin-bottom: 8px; }
    .tag { display: inline-block; border-radius: 10px; padding: 2px 10px;
           font-size: 12px; font-weight: 500; }
    .section-title { font-size: 15px; font-weight: 500; margin-bottom: 8px;
                     padding-bottom: 6px; border-bottom: 1px solid #e0e0e0; }
    .soldier-row { display: flex; align-items: center; gap: 8px; padding: 6px 0;
                   border-bottom: 1px solid #f0f0f0; font-size: 13px; }
    .ammo-bar-bg { background: #d0d8cc; border-radius: 4px; height: 6px; }
    .login-box { max-width: 360px; margin: 60px auto; padding: 30px;
                 border: 1px solid #ddd; border-radius: 14px; background: white; }
</style>
""", unsafe_allow_html=True)

# ─── Session state ─────────────────────────────────────────────────────────────

if "user" not in st.session_state:
    st.session_state.user = None

# ─── Login ─────────────────────────────────────────────────────────────────────

def login_screen():
    st.markdown("""
    <div style='text-align:center;margin-top:40px'>
      <div style='font-size:48px'>⚔</div>
      <h2 style='color:#5a6e52'>גדוד חרב שאול</h2>
      <p style='color:#888'>מערכת שליטה מבצעית — קו ג׳למה</p>
    </div>
    """, unsafe_allow_html=True)

    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            unit_options = {
                "magad":   'מג"ד (מפקד גדוד)',
                "yarden":  "ירדן",
                "gilboa":  "גלבוע",
                "taanach": "תענך",
                "afula":   "עפולה",
                "palsam":  'פלס"ם אג"ם',
            }
            unit = st.selectbox("בחר יחידה", options=list(unit_options.keys()),
                                format_func=lambda x: unit_options[x])
            password = st.text_input("סיסמא", type="password")
            if st.button("כניסה", use_container_width=True, type="primary"):
                if PASSWORDS.get(unit) == password:
                    st.session_state.user = unit
                    st.rerun()
                else:
                    st.error("סיסמא שגויה")

# ─── Helpers ───────────────────────────────────────────────────────────────────

def can_edit(company):
    return st.session_state.user == "magad" or st.session_state.user == company

def colored_tag(text, color):
    return f'<span class="tag" style="background:{color}22;color:{color}">{text}</span>'

def company_dot(key):
    c = COMPANIES[key]["color"]
    return f'<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:{c};margin-left:6px"></span>'

# ─── Dashboard ─────────────────────────────────────────────────────────────────

def tab_dashboard():
    soldiers = load_soldiers()
    events   = load_events()
    ammo     = load_ammo()

    total = len(soldiers)
    base  = sum(1 for s in soldiers if s.get("loc") == "base")
    home  = sum(1 for s in soldiers if s.get("loc") == "home")
    milim = sum(1 for s in soldiers if s.get("loc") == "milim")

    st.markdown(f"""
    <div class="metric-row">
      <div class="metric-box"><div class="metric-num">{total}</div><div class="metric-lbl">סה"כ כ"א</div></div>
      <div class="metric-box"><div class="metric-num" style="color:#3b6d11">{base}</div><div class="metric-lbl">בבסיס</div></div>
      <div class="metric-box"><div class="metric-num" style="color:#854f0b">{home}</div><div class="metric-lbl">בבית</div></div>
      <div class="metric-box"><div class="metric-num" style="color:#185fa5">{milim}</div><div class="metric-lbl">מגויסים</div></div>
      <div class="metric-box"><div class="metric-num" style="color:#a32d2d">{len(events)}</div><div class="metric-lbl">אירועים</div></div>
    </div>
    """, unsafe_allow_html=True)

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown('<div class="section-title">מצב פלוגות</div>', unsafe_allow_html=True)
        for k in COMP_KEYS:
            ss = [s for s in soldiers if s.get("company") == k]
            b  = sum(1 for s in ss if s.get("loc") == "base")
            h  = sum(1 for s in ss if s.get("loc") == "home")
            m  = sum(1 for s in ss if s.get("loc") == "milim")
            c  = COMPANIES[k]["color"]
            st.markdown(f"""
            <div class="soldier-row">
              {company_dot(k)}
              <span style="flex:1;font-weight:500">{COMPANIES[k]['name']}</span>
              <span style="color:#3b6d11;font-size:12px">{b} בסיס</span>&nbsp;
              <span style="color:#854f0b;font-size:12px">{h} בית</span>&nbsp;
              {'<span style="color:#185fa5;font-size:12px">'+str(m)+' מגויס</span>' if m else ''}
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<div class="section-title" style="margin-top:1rem">אירועים אחרונים</div>', unsafe_allow_html=True)
        shown = sorted(events, key=lambda e: e.get("ts",""), reverse=True)[:3]
        if shown:
            for e in shown:
                sc = SEV_COLOR.get(e.get("sev","low"), "#7a9170")
                comp_name = COMPANIES.get(e.get("company",""), {}).get("name", e.get("company",""))
                st.markdown(f"""
                <div class="ev-card" style="border-color:{sc};background:{sc}11">
                  <div style="font-size:11px;color:#888">{e.get('ts','')} — {comp_name}</div>
                  <div style="font-size:13px;font-weight:500;margin-top:2px">{e.get('title','')}</div>
                  {colored_tag(SEV_LABEL.get(e.get('sev','low'),''), sc)}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("אין אירועים")

    with col_right:
        st.markdown('<div class="section-title">מצב תחמושת</div>', unsafe_allow_html=True)
        by_type = {}
        for r in ammo:
            t = r.get("type","")
            if t not in by_type:
                by_type[t] = {"signed": 0, "used": 0}
            by_type[t]["signed"] += int(r.get("signed", 0) or 0)
            by_type[t]["used"]   += int(r.get("used", 0) or 0)
        for t, d in by_type.items():
            pct = round((d["signed"] - d["used"]) / d["signed"] * 100) if d["signed"] else 100
            fill = "#639922" if pct > 70 else "#ba7517" if pct > 40 else "#e24b4a"
            st.markdown(f"""
            <div style="margin-bottom:10px">
              <div style="display:flex;justify-content:space-between;font-size:13px">
                <span>{t}</span><span style="color:{fill};font-weight:500">{pct}% יתרה</span>
              </div>
              <div class="ammo-bar-bg"><div style="height:6px;border-radius:4px;background:{fill};width:{pct}%"></div></div>
            </div>
            """, unsafe_allow_html=True)

# ─── Manpower ──────────────────────────────────────────────────────────────────

def tab_manpower():
    user = st.session_state.user
    soldiers = load_soldiers()

    comp_filter_options = ["all"] + COMP_KEYS if user == "magad" else [user]
    comp_filter_labels  = {"all": "כולל"} | {k: COMPANIES[k]["name"] for k in COMP_KEYS}
    comp_filter = st.radio("פלוגה", comp_filter_options,
                           format_func=lambda x: comp_filter_labels.get(x, x),
                           horizontal=True)

    filtered = soldiers if comp_filter == "all" else [s for s in soldiers if s.get("company") == comp_filter]
    total = len(filtered)
    base  = sum(1 for s in filtered if s.get("loc") == "base")
    home  = sum(1 for s in filtered if s.get("loc") == "home")
    milim = sum(1 for s in filtered if s.get("loc") == "milim")

    st.markdown(f"""
    <div class="metric-row">
      <div class="metric-box"><div class="metric-num">{total}</div><div class="metric-lbl">סה"כ</div></div>
      <div class="metric-box"><div class="metric-num" style="color:#3b6d11">{base}</div><div class="metric-lbl">בבסיס</div></div>
      <div class="metric-box"><div class="metric-num" style="color:#854f0b">{home}</div><div class="metric-lbl">בבית</div></div>
      <div class="metric-box"><div class="metric-num" style="color:#185fa5">{milim}</div><div class="metric-lbl">מגויסים</div></div>
    </div>
    """, unsafe_allow_html=True)

    if can_edit(comp_filter) or comp_filter == "all":
        with st.expander("➕ הוסף / עדכן חייל", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                mp_name = st.text_input("שם מלא")
                mp_pid  = st.text_input("מספר אישי (אופציונלי)")
            with col2:
                comp_keys_edit = COMP_KEYS if user == "magad" else [user]
                mp_comp = st.selectbox("פלוגה", comp_keys_edit,
                                       format_func=lambda x: COMPANIES[x]["name"])
                mp_loc  = st.selectbox("מיקום", ["base","home","milim","other"],
                                       format_func=lambda x: LOC_LABEL[x])
            mp_other = ""
            if mp_loc == "other":
                mp_other = st.text_input("פרט מיקום")
            if st.button("שמור חייל", type="primary"):
                if mp_name:
                    append_row("soldiers", {
                        "ts": datetime.now().strftime("%d/%m %H:%M"),
                        "name": mp_name, "pid": mp_pid,
                        "company": mp_comp, "loc": mp_loc, "other": mp_other
                    })
                    add_history(f'הוסיף "{mp_name}" ({COMPANIES[mp_comp]["name"]}) — {LOC_LABEL[mp_loc]}')
                    st.success("חייל נוסף!")
                    st.rerun()
                else:
                    st.warning("נא להזין שם")

    st.markdown('<div class="section-title">רשימת חיילים</div>', unsafe_allow_html=True)

    if filtered:
        df = pd.DataFrame(filtered)
        df["פלוגה"]   = df["company"].map(lambda x: COMPANIES.get(x, {}).get("name", x))
        df["מיקום"]   = df.apply(lambda r: r["other"] if r["loc"] == "other" else LOC_LABEL.get(r["loc"], r["loc"]), axis=1)
        df["מספר"]    = df.get("pid", "")
        display_df    = df[["name","מספר","פלוגה","מיקום"]].rename(columns={"name":"שם"})
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        csv = display_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("יצוא CSV", csv, "כוח_אדם.csv", "text/csv")
    else:
        st.caption("אין חיילים ברשימה")

# ─── Ammo ──────────────────────────────────────────────────────────────────────

def tab_ammo():
    user = st.session_state.user
    ammo = load_ammo()

    comp_filter_options = ["all"] + COMP_KEYS if user == "magad" else [user]
    comp_filter_labels  = {"all": "כולל"} | {k: COMPANIES[k]["name"] for k in COMP_KEYS}
    comp_filter = st.radio("פלוגה", comp_filter_options,
                           format_func=lambda x: comp_filter_labels.get(x, x),
                           horizontal=True)

    filtered = ammo if comp_filter == "all" else [r for r in ammo if r.get("company") == comp_filter]
    by_type = {}
    for r in filtered:
        t = r.get("type","")
        if t not in by_type:
            by_type[t] = {"signed": 0, "used": 0}
        by_type[t]["signed"] += int(r.get("signed", 0) or 0)
        by_type[t]["used"]   += int(r.get("used", 0) or 0)

    if by_type:
        rows = []
        for t, d in by_type.items():
            rem = d["signed"] - d["used"]
            pct = round(rem / d["signed"] * 100) if d["signed"] else 100
            rows.append({"סוג": t, "חתמו": d["signed"], "השתמשו": d["used"], "יתרה": rem, "% יתרה": pct})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.caption("אין נתונים")

    if can_edit(comp_filter) or comp_filter == "all":
        with st.expander("➕ עדכון תחמושת", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                comp_keys_edit = COMP_KEYS if user == "magad" else [user]
                a_comp   = st.selectbox("פלוגה", comp_keys_edit,
                                        format_func=lambda x: COMPANIES[x]["name"], key="a_comp")
                a_type   = st.selectbox("סוג תחמושת",
                                        ["כדורי 5.56","כדורי 7.62","רימונים","מטענים",'נפ"צ',"אחר"])
            with col2:
                a_signed = st.number_input("כמות שחתמו", min_value=0, step=1)
                a_used   = st.number_input("כמות שהשתמשו", min_value=0, step=1)
            a_note = st.text_input("הערות (אופציונלי)")
            if st.button("שמור תחמושת", type="primary"):
                if a_signed > 0:
                    append_row("ammo", {
                        "ts": datetime.now().strftime("%d/%m %H:%M"),
                        "company": a_comp, "type": a_type,
                        "signed": a_signed, "used": a_used, "note": a_note
                    })
                    add_history(f'עדכן "{a_type}" ל{COMPANIES[a_comp]["name"]}: חתמו {a_signed}, השתמשו {a_used}')
                    st.success("תחמושת עודכנה!")
                    st.rerun()
                else:
                    st.warning("נא להזין כמות")

# ─── Events ────────────────────────────────────────────────────────────────────

def tab_events():
    user   = st.session_state.user
    events = load_events()

    if can_edit("all") or True:
        with st.expander("➕ דיווח אירוע חריג", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                comp_keys_edit = COMP_KEYS if user == "magad" else [user]
                ev_comp = st.selectbox("פלוגה", comp_keys_edit,
                                       format_func=lambda x: COMPANIES[x]["name"], key="ev_comp")
                ev_sev  = st.selectbox("חומרה", ["low","mid","high","critical"],
                                       format_func=lambda x: SEV_LABEL[x])
            with col2:
                ev_title = st.text_input("כותרת האירוע")
            ev_desc = st.text_area("פרטים", height=80)
            if st.button("שלח דיווח", type="primary"):
                if ev_title:
                    append_row("events", {
                        "ts": datetime.now().strftime("%d/%m %H:%M"),
                        "company": ev_comp, "sev": ev_sev,
                        "title": ev_title, "desc": ev_desc, "by": user
                    })
                    add_history(f'דיווח אירוע "{ev_title}" — {COMPANIES[ev_comp]["name"]}')
                    st.success("אירוע דווח!")
                    st.rerun()
                else:
                    st.warning("נא להזין כותרת")

    comp_filter_options = ["all"] + COMP_KEYS if user == "magad" else [user]
    comp_filter_labels  = {"all": "כולל"} | {k: COMPANIES[k]["name"] for k in COMP_KEYS}
    comp_filter = st.radio("סנן לפי פלוגה", comp_filter_options,
                           format_func=lambda x: comp_filter_labels.get(x, x),
                           horizontal=True)

    filtered = events if comp_filter == "all" else [e for e in events if e.get("company") == comp_filter]
    filtered = sorted(filtered, key=lambda e: e.get("ts",""), reverse=True)

    if filtered:
        for e in filtered:
            sc   = SEV_COLOR.get(e.get("sev","low"), "#7a9170")
            comp_name = COMPANIES.get(e.get("company",""), {}).get("name", e.get("company",""))
            st.markdown(f"""
            <div class="ev-card" style="border-color:{sc};background:{sc}11">
              <div style="display:flex;justify-content:space-between;font-size:11px;color:#888">
                <span>{e.get('ts','')} — {comp_name}</span>
                {colored_tag(SEV_LABEL.get(e.get('sev','low'),''), sc)}
              </div>
              <div style="font-size:14px;font-weight:500;margin-top:4px">{e.get('title','')}</div>
              {f'<div style="font-size:12px;color:#666;margin-top:3px">{e.get("desc","")}</div>' if e.get('desc') else ''}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.caption("אין אירועים")

# ─── History ───────────────────────────────────────────────────────────────────

def tab_history():
    hist = load_history()
    hist = sorted(hist, key=lambda h: h.get("ts",""), reverse=True)
    if hist:
        for h in hist:
            st.markdown(f"""
            <div style="display:flex;gap:10px;padding:6px 0;border-bottom:1px solid #f0f0f0;font-size:13px">
              <span style="color:#888;white-space:nowrap">{h.get('ts','')}</span>
              <span><strong>{h.get('by','')}</strong>: {h.get('msg','')}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.caption("אין שינויים עדיין")

# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    if not st.session_state.user:
        login_screen()
        return

    user = st.session_state.user
    role_label = 'מג"ד — צפייה מלאה' if user == "magad" else f'פלוגה {COMPANIES[user]["name"]}'

    st.markdown(f"""
    <div class="hdr">
      <span style="font-size:28px">⚔</span>
      <div style="flex:1">
        <h1>גדוד חרב שאול</h1>
        <p>קו ג׳למה — {role_label}</p>
      </div>
    </div>
    """, unsafe_allow_html=True)

    tabs = ["דשבורד", "כוח אדם", "תחמושת", "אירועים", "היסטוריה"]
    if user != "magad":
        tabs = ["כוח אדם", "תחמושת", "אירועים", "היסטוריה"]

    selected = st.tabs(tabs)

    if user == "magad":
        with selected[0]: tab_dashboard()
        with selected[1]: tab_manpower()
        with selected[2]: tab_ammo()
        with selected[3]: tab_events()
        with selected[4]: tab_history()
    else:
        with selected[0]: tab_manpower()
        with selected[1]: tab_ammo()
        with selected[2]: tab_events()
        with selected[3]: tab_history()

    st.markdown("---")
    if st.button("יציאה"):
        st.session_state.user = None
        st.rerun()

main()
