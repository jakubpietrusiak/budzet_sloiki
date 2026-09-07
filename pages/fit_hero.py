import dash
from dash import html, dcc, Input, Output, State, callback, set_props, ALL
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
from database import get_db_connection

dash.register_page(__name__, path='/fit-hero', name='Moduł Fit Hero')

USER_HEIGHT_M = 1.86

LOAD_TYPE_OPTIONS = [
    {'label': '⚖️ Masa ciała', 'value': 'Masa ciała'},
    {'label': '🏋️ Ciężar (kg)', 'value': 'Ciężar (kg)'},
    {'label': '🎗️ Guma oporowa', 'value': 'Guma oporowa'}
]

RPE_OPTIONS = [
    {'label': '🟢 Lekko', 'value': 1},
    {'label': '🟡 OK', 'value': 2},
    {'label': '🟠 Ciężko', 'value': 3},
    {'label': '🔴 Max', 'value': 4}
]

FATIGUE_OPTIONS = [
    {'label': '🚀 Nakręcony!', 'value': 1},
    {'label': '⚡ Dobry trening', 'value': 2},
    {'label': '😮‍💨 Zmęczony', 'value': 3},
    {'label': '🥵 Wykończony', 'value': 4}
]

POSTURE_PROFILES = {
    'recomp': {
        'label': '🔄 Rekompozycja (Waga stała / Pas ↓ / Klatka ↑)',
        'w_weight': 0.15, 'w_waist': 0.45, 'w_chest': 0.25, 'w_bf': 0.15
    },
    'cut': {
        'label': '🔥 Redukcja Oponki (Waga ↓↓ / Pas ↓↓ / BF% ↓)',
        'w_weight': 0.35, 'w_waist': 0.40, 'w_chest': 0.05, 'w_bf': 0.20
    },
    'bulk': {
        'label': '🏋️ Czysty Budulec (Waga ↑ / Klatka ↑↑ / Biceps ↑)',
        'w_weight': 0.30, 'w_waist': 0.10, 'w_chest': 0.40, 'w_bf': 0.20
    }
}

HERO_LEVELS_XP = [
    {"lvl": 1, "req_pct": 0, "name": "Start Inicjacji", "desc": "Punkt startowy Twojej transformacji"},
    {"lvl": 2, "req_pct": 5, "name": "Aktywacja Nawyku", "desc": "Pierwsze 5% drogi za Tobą"},
    {"lvl": 3, "req_pct": 10, "name": "Adaptacja Tkankowa", "desc": "Ciało zaczyna reagować na treningi"},
    {"lvl": 4, "req_pct": 15, "name": "Pierwsze Zmiany", "desc": "Zauważalna zmiana w obwodach"},
    {"lvl": 5, "req_pct": 20, "name": "Rytm i Dyscyplina", "desc": "1/5 drogi pokonana stabilnie"},
    {"lvl": 6, "req_pct": 25, "name": "Zarys Nowej Postury", "desc": "25% planu zrealizowane"},
    {"lvl": 7, "req_pct": 30, "name": "Gęstość Mięśniowa", "desc": "Ochrona LBM i zmiana obwodów"},
    {"lvl": 8, "req_pct": 35, "name": "Przełamanie Oporu", "desc": "Przejście przez pierwszą adaptację"},
    {"lvl": 9, "req_pct": 40, "name": "Żelazny Rytm", "desc": "Solidna powtarzalność pomiarowa"},
    {"lvl": 10, "req_pct": 45, "name": "Półmetak Transformacji", "desc": "Prawie połowa celu osiągnięta"},
    {"lvl": 11, "req_pct": 50, "name": "Połowa Drogi za Tobą", "desc": "Dokładnie 50% Twojego celu!"},
    {"lvl": 12, "req_pct": 55, "name": "Poprawa Proporcji", "desc": "V-Taper i obwody wyraźnie zmienione"},
    {"lvl": 13, "req_pct": 60, "name": "Zaawansowana Rzeźba", "desc": "60% pełnej realizacji planu"},
    {"lvl": 14, "req_pct": 65, "name": "Strefa Niskiego Tłuszczu", "desc": "Odbicie w parametrach Xiaomi"},
    {"lvl": 15, "req_pct": 70, "name": "Forma Atletyczna", "desc": "70% drogi — wyraźne detale"},
    {"lvl": 16, "req_pct": 75, "name": "Ostatnia Prosta", "desc": "3/4 celu zrealizowane!"},
    {"lvl": 17, "req_pct": 80, "name": "Elitarna Postura", "desc": "Górne 20% do wykonania"},
    {"lvl": 18, "req_pct": 85, "name": "Plażowy Ready", "desc": "Forma gotowa na wydarzenia"},
    {"lvl": 19, "req_pct": 92, "name": "Przedproże Ideatu", "desc": "Ostatnie szlify parametrów"},
    {"lvl": 20, "req_pct": 100, "name": "👑 Fit HERO Master", "desc": "100% zrealizowania Twojego własnego celu!"}
]

def generate_fit_hero_txt_report():
    conn = get_db_connection()
    df_body = pd.read_sql_query("SELECT * FROM fit_body_params ORDER BY entry_date DESC", conn)
    df_goals = pd.read_sql_query("SELECT * FROM fit_target_goals", conn)
    goals = dict(zip(df_goals['param_key'], df_goals['target_val'])) if not df_goals.empty else {}
    
    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    df_sessions = pd.read_sql_query("SELECT * FROM fit_workout_sessions WHERE workout_date >= ? ORDER BY workout_date DESC", conn, params=(thirty_days_ago,))
    df_logs = pd.read_sql_query("SELECT * FROM fit_workout_logs WHERE workout_date >= ? ORDER BY workout_date DESC", conn, params=(thirty_days_ago,))
    conn.close()

    latest_row = df_body.iloc[0] if not df_body.empty else {}
    first_row = df_body.iloc[-1] if not df_body.empty else {}

    rpe_map = {1: "Lekko (1)", 2: "OK (2)", 3: "Ciężko (3)", 4: "Max (4)"}
    fatigue_map = {1: "Nakręcony", 2: "Dobry trening", 3: "Zmęczony", 4: "Wykończony"}

    lines = []
    lines.append("=== FIT HERO: RAPORT ANALITYCZNY DLA TRENERA AI ===")
    lines.append(f"Data wygenerowania: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    lines.append("[ 1. PROFIL I CELE UŻYTKOWNIKA ]")
    lines.append(f"- Wzrost: 186 cm")
    lines.append(f"- Aktualna Waga: {latest_row.get('weight_kg', '--')} kg (Cel: {goals.get('weight_kg', '--')} kg)")
    lines.append(f"- Aktualny Pas: {latest_row.get('waist_cm', '--')} cm (Cel: {goals.get('waist_cm', '--')} cm)")
    lines.append(f"- Aktualna Klatka: {latest_row.get('chest_cm', '--')} cm (Cel: {goals.get('chest_cm', '--')} cm)")
    lines.append(f"- Profil Adaptacji: {str(goals.get('posture_profile', 'recomp')).upper()}\n")

    lines.append("[ 2. DYNAMIKA POMIARÓW (XIAOMI) ]")
    date_a = first_row.get('entry_date', 'Start')
    date_b = latest_row.get('entry_date', 'Aktualnie')
    lines.append(f"- Start ({date_a}): Waga {first_row.get('weight_kg', '--')} kg | Pas {first_row.get('waist_cm', '--')} cm | Klatka {first_row.get('chest_cm', '--')} cm | BF {first_row.get('body_fat_pct', '--')}%")
    lines.append(f"- Aktualnie ({date_b}): Waga {latest_row.get('weight_kg', '--')} kg | Pas {latest_row.get('waist_cm', '--')} cm | Klatka {latest_row.get('chest_cm', '--')} cm | BF {latest_row.get('body_fat_pct', '--')}%\n")

    lines.append("[ 3. HISTORIA SESJI, ĆWICZEŃ I TRUDNOŚCI (OSTATNIE 30 DNI) ]")
    if not df_sessions.empty:
        for _, s in df_sessions.iterrows():
            s_date = s.get('workout_date', '')
            s_plan = s.get('plan_name', '')
            s_comp = s.get('completion_pct', 0)
            s_fat = fatigue_map.get(s.get('fatigue_score'), 'Brak oceny')
            s_notes = s.get('overall_notes', '')
            
            lines.append(f"\n-> Sesja: {s_date} | Plan: {s_plan} | Wykonanie: {s_comp}% | Samopoczucie: {s_fat} | Notatka: {s_notes}")
            
            if not df_logs.empty:
                session_logs = df_logs[df_logs['workout_date'] == s_date]
                if not session_logs.empty:
                    lines.append("   Szczegóły wykonanych ćwiczeń:")
                    for _, ex in session_logs.iterrows():
                        rpe_txt = rpe_map.get(ex.get('rpe_score'), 'Brak RPE')
                        lines.append(f"   * {ex.get('exercise_name')} | Seria {ex.get('set_number')}: {ex.get('reps')} powt. | Ciężar: {ex.get('weight_kg')} kg | Trudność/RPE: {rpe_txt}")
    else:
        lines.append("Brak zarejestrowanych sesji w ostatnich 30 dniach.")
    
    lines.append("\n[ 4. PYTANIE / INSTRUKCJA DLA AI ]")
    lines.append("Jesteś doświadczonym trenerem personalnym i specjalistą ds. rekompozycji sylwetki. Przeanalizuj powyższe dane treningowe (wzrost 186 cm, wykonane serie, powtórzenia, poziomy RPE oraz notatki o trudnościach z poszczególnych ćwiczeń). Zidentyfikuj, które partie lub ćwiczenia generują największy opór/problem, oceń częstotliwość i objętość oraz zaproponuj konkretne, punktowe korekty w planie, aby zmaksymalizować wydajność i progres.")

    return "\n".join(lines)

def init_and_migrate_fit_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('CREATE TABLE IF NOT EXISTS fit_body_params (entry_date TEXT PRIMARY KEY)')
    required_columns = {
        'entry_time': 'TEXT', 'weight_kg': 'REAL', 'body_fat_pct': 'REAL',
        'muscle_mass_kg': 'REAL', 'muscle_pct': 'REAL', 'protein_pct': 'REAL',
        'skeletal_muscle_kg': 'REAL', 'water_pct': 'REAL', 'bmr_kcal': 'REAL',
        'lbm_kg': 'REAL', 'biceps_cm': 'REAL', 'forearm_cm': 'REAL',
        'chest_cm': 'REAL', 'waist_cm': 'REAL', 'hips_cm': 'REAL',
        'thigh_cm': 'REAL', 'calf_cm': 'REAL', 'notes': 'TEXT'
    }
    cursor.execute("PRAGMA table_info(fit_body_params)")
    existing_cols = [row[1] for row in cursor.fetchall()]
    for col_name, col_type in required_columns.items():
        if col_name not in existing_cols:
            cursor.execute(f"ALTER TABLE fit_body_params ADD COLUMN {col_name} {col_type}")
            
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fit_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_name TEXT UNIQUE,
            description TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fit_plan_exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id INTEGER,
            exercise_name TEXT,
            target_sets INTEGER DEFAULT 4,
            target_reps TEXT DEFAULT '8-12',
            load_type TEXT DEFAULT 'Ciężar (kg)',
            load_detail TEXT,
            default_weight_kg REAL DEFAULT 0,
            rest_seconds INTEGER DEFAULT 90,
            FOREIGN KEY(plan_id) REFERENCES fit_plans(id) ON DELETE CASCADE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fit_workout_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workout_date TEXT,
            plan_name TEXT,
            exercise_name TEXT,
            set_number INTEGER,
            weight_kg REAL,
            reps INTEGER,
            rpe_score INTEGER,
            notes TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fit_workout_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workout_date TEXT,
            plan_name TEXT,
            completion_pct REAL,
            fatigue_score INTEGER,
            overall_notes TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fit_target_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            param_key TEXT UNIQUE NOT NULL,
            target_val REAL NOT NULL
        )
    ''')

    conn.commit()
    conn.close()

init_and_migrate_fit_db()

def get_body_params_df():
    conn = get_db_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM fit_body_params ORDER BY entry_date DESC", conn)
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df

def get_plans_list():
    conn = get_db_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM fit_plans", conn)
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df

def get_plan_exercises(plan_id):
    conn = get_db_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM fit_plan_exercises WHERE plan_id = ?", conn, params=(plan_id,))
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df

def get_target_goals_dict():
    conn = get_db_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM fit_target_goals", conn)
        goals = dict(zip(df['param_key'], df['target_val']))
    except Exception:
        goals = {}
    conn.close()
    return goals

layout = html.Div([
    dcc.Location(id="fit-url-refresh", refresh=True),
    dcc.Download(id="download-fit-txt-file"),
    html.H2("💪 Moduł Fit Hero — Karta Pomiarów & Dynamiczna Predykcja", style={"marginBottom": "20px", "color": "#0f172a"}),
    
    dcc.Tabs(
        id="tabs-fit",
        value="fit-pomiary",
        className="custom-tabs-container",
        parent_className="custom-tabs-parent",
        children=[
            dcc.Tab(label="📏 Karta Pomiarów & Analityka", value="fit-pomiary", className="custom-tab", selected_className="custom-tab--selected"),
            dcc.Tab(label="🎯 Dynamiczne Cele & ETA", value="fit-predykcja-eta", className="custom-tab", selected_className="custom-tab--selected"),
            dcc.Tab(label="🏆 Hero XP (20 Lvl)", value="fit-kamienie-milowe", className="custom-tab", selected_className="custom-tab--selected"),
            dcc.Tab(label="📋 Zarządzanie Planami", value="fit-plany-edit", className="custom-tab", selected_className="custom-tab--selected"),
            dcc.Tab(label="🏋️ Trening Live", value="fit-trening-live", className="custom-tab", selected_className="custom-tab--selected"),
            dcc.Tab(label="📈 Wykresy i Postępy", value="fit-historia", className="custom-tab", selected_className="custom-tab--selected"),
        ]
    ),
    
    html.Div(id="tab-fit-content", style={"marginTop": "20px"})
])

def fmt_val(val, unit=""):
    if pd.notnull(val) and val != "":
        try:
            return f"{float(val):.1f} {unit}".replace('.', ',')
        except ValueError:
            pass
    return "--"

def calc_smart_delta(first_val, last_val, unit="", is_positive_good=True):
    if pd.notnull(first_val) and pd.notnull(last_val):
        try:
            diff = float(last_val) - float(first_val)
            if abs(diff) < 0.01:
                return html.Span("0,0 " + unit, style={"color": "#64748b", "fontWeight": "600"})
            sign = "+" if diff > 0 else ""
            text = f"{sign}{diff:.1f} {unit}".replace('.', ',')
            color = "#10b981" if ((diff > 0 and is_positive_good) or (diff < 0 and not is_positive_good)) else "#ef4444"
            return html.Span(text, style={"fontWeight": "800", "color": color})
        except ValueError:
            pass
    return html.Span("--", style={"color": "#94a3b8"})

def get_color_for_score(score):
    colors = {
        1: "#ef4444", 2: "#f97316", 3: "#f59e0b", 4: "#d97706",
        5: "#ca8a04", 6: "#65a30d", 7: "#16a34a", 8: "#15803d",
        9: "#10b981", 10: "#059669"
    }
    return colors.get(score, "#64748b")

@callback(
    Output("tab-fit-content", "children"),
    Input("tabs-fit", "value")
)
def render_fit_subtabs(tab):
    df_body = get_body_params_df()
    
    if not df_body.empty and ('weight_kg' in df_body.columns or 'waist_cm' in df_body.columns):
        df_valid = df_body[
            (df_body.get('weight_kg', pd.Series()).notnull()) | 
            (df_body.get('waist_cm', pd.Series()).notnull())
        ].copy()
    else:
        df_valid = pd.DataFrame()
        
    has_valid_data = not df_valid.empty
    
    if tab == "fit-pomiary":
        bmi_str, whr_str, v_taper_str, ffmi_str = "--", "--", "--", "--"
        bmi_sub, whr_sub, v_taper_sub, ffmi_sub = "Brak danych", "Brak danych", "Brak danych", "Brak danych"
        bmi_score, whr_score, vt_score, ffmi_score = 5, 5, 5, 5
        
        bmi_tip = "BMI (Body Mass Index) — Relacja masy ciała do wzrostu (186 cm)."
        whr_tip = "WHR (Waist-to-Hip Ratio) — Stosunek pasa do bioder."
        vt_tip = "V-Taper — Stosunek klatki piersiowej do pasa."
        ffmi_tip = "FFMI — Indeks beztłuszczowej masy mięśniowej."
        
        if has_valid_data:
            row = df_valid.iloc[0]
            w = row.get('weight_kg')
            waist = row.get('waist_cm')
            chest = row.get('chest_cm')
            hips = row.get('hips_cm')
            bf = row.get('body_fat_pct')
            
            if pd.notnull(w) and w > 0:
                bmi_val = w / (USER_HEIGHT_M ** 2)
                bmi_str = f"{bmi_val:.1f}".replace('.', ',')
                if bmi_val < 18.5: bmi_sub, bmi_score = "Niedowaga", 2
                elif bmi_val <= 24.9: bmi_sub, bmi_score = "Norma", 10
                elif bmi_val <= 27.5: bmi_sub, bmi_score = "Lekka nadwaga", 6
                elif bmi_val <= 29.9: bmi_sub, bmi_score = "Nadwaga", 4
                else: bmi_sub, bmi_score = "Otyłość", 1
                bmi_tip = f"Twój BMI: {bmi_str} ({bmi_sub})"

            if pd.notnull(waist) and pd.notnull(hips) and hips > 0:
                whr_val = waist / hips
                whr_str = f"{whr_val:.2f}".replace('.', ',')
                if whr_val <= 0.85: whr_sub, whr_score = "Optymalny", 10
                elif whr_val <= 0.90: whr_sub, whr_score = "Norma", 8
                elif whr_val <= 0.95: whr_sub, whr_score = "Umiarkowane ryzyko", 5
                else: whr_sub, whr_score = "Typ Brzuszny", 2
                whr_tip = f"Twój WHR: {whr_str} ({whr_sub})"
            elif pd.notnull(waist):
                whr_str = f"{waist:.0f} cm"

            if pd.notnull(chest) and pd.notnull(waist) and waist > 0:
                vt_val = chest / waist
                v_taper_str = f"{vt_val:.2f}".replace('.', ',')
                if vt_val >= 1.25: vt_sub, vt_score = "V-Shape (Świetne)", 10
                elif vt_val >= 1.15: vt_sub, vt_score = "Dobre proporcje", 7
                else: vt_sub, vt_score = "Do poprawy", 3
                vt_tip = f"V-Taper: {v_taper_str}"

            if pd.notnull(w) and pd.notnull(bf) and w > 0:
                lbm = w * (1.0 - (bf / 100.0))
                ffmi_val = lbm / (USER_HEIGHT_M ** 2)
                ffmi_str = f"{ffmi_val:.1f}".replace('.', ',')
                if ffmi_val >= 21.5: ffmi_sub, ffmi_score = "Bardzo dobre", 9
                elif ffmi_val >= 19.5: ffmi_sub, ffmi_score = "Dobre", 7
                else: ffmi_sub, ffmi_score = "Przeciętne", 4
                ffmi_tip = f"FFMI: {ffmi_str}"

        table_rows = []
        if has_valid_data:
            first = df_valid.iloc[-1]
            latest = df_valid.iloc[0]
            params_config = [
                ("Masa Ciała", "weight_kg", "kg", False),
                ("Tkanka Tłuszczowa (BF)", "body_fat_pct", "%", False),
                ("Masa Mięśniowa", "muscle_mass_kg", "kg", True),
                ("Mięśnie Szkieletowe", "skeletal_muscle_kg", "kg", True),
                ("Procent Mięśni", "muscle_pct", "%", True),
                ("Białko", "protein_pct", "%", True),
                ("Nawodnienie", "water_pct", "%", True),
                ("Pas (Pępek)", "waist_cm", "cm", False),
                ("Klatka Piersiowa", "chest_cm", "cm", True),
                ("Biceps / Ramię", "biceps_cm", "cm", True),
                ("Przedramię", "forearm_cm", "cm", True),
                ("Biodra / Oponka", "hips_cm", "cm", False),
                ("Udo", "thigh_cm", "cm", True),
                ("Łydka", "calf_cm", "cm", True),
            ]
            for name, col_id, unit, is_pos_good in params_config:
                val_first = first.get(col_id)
                val_latest = latest.get(col_id)
                if pd.notnull(val_first) or pd.notnull(val_latest):
                    table_rows.append(html.Tr([
                        html.Td(name, style={"padding": "10px 12px", "fontWeight": "700", "color": "#0f172a", "borderBottom": "1px solid #f1f5f9"}),
                        html.Td(fmt_val(val_first, unit), style={"padding": "10px 12px", "textAlign": "center", "color": "#64748b", "borderBottom": "1px solid #f1f5f9"}),
                        html.Td(fmt_val(val_latest, unit), style={"padding": "10px 12px", "textAlign": "center", "fontWeight": "700", "color": "#0284c7", "borderBottom": "1px solid #f1f5f9"}),
                        html.Td(calc_smart_delta(val_first, val_latest, unit, is_positive_good=is_pos_good), style={"padding": "10px 12px", "textAlign": "center", "borderBottom": "1px solid #f1f5f9"}),
                    ]))

        return html.Div([
            html.Div(style={"display": "flex", "gap": "20px", "marginBottom": "25px"}, children=[
                html.Div(className=f"kpi-card score-{bmi_score}", title=bmi_tip, children=[
                    html.Span("Wskaźnik BMI", style={"color": "#64748b", "fontSize": "13px", "fontWeight": "bold"}),
                    html.H2(bmi_str, style={"margin": "4px 0 2px 0", "color": get_color_for_score(bmi_score)}),
                    html.Span(f"Score {bmi_score}/10 — {bmi_sub}", style={"fontSize": "11px", "color": get_color_for_score(bmi_score), "fontWeight": "700"})
                ]),
                html.Div(className=f"kpi-card score-{whr_score}", title=whr_tip, children=[
                    html.Span("Dystrybucja WHR (Pas/Biodra)", style={"color": "#64748b", "fontSize": "13px", "fontWeight": "bold"}),
                    html.H2(whr_str, style={"margin": "4px 0 2px 0", "color": get_color_for_score(whr_score)}),
                    html.Span(f"Score {whr_score}/10 — {whr_sub}", style={"fontSize": "11px", "color": get_color_for_score(whr_score), "fontWeight": "700"})
                ]),
                html.Div(className=f"kpi-card score-{vt_score}", title=vt_tip, children=[
                    html.Span("Proporcja V-Taper (Klatka/Pas)", style={"color": "#64748b", "fontSize": "13px", "fontWeight": "bold"}),
                    html.H2(v_taper_str, style={"margin": "4px 0 2px 0", "color": get_color_for_score(vt_score)}),
                    html.Span(f"Score {vt_score}/10 — {vt_sub}", style={"fontSize": "11px", "color": get_color_for_score(vt_score), "fontWeight": "700"})
                ]),
                html.Div(className=f"kpi-card score-{ffmi_score}", title=ffmi_tip, children=[
                    html.Span("FFMI (Indeks Mięśni)", style={"color": "#64748b", "fontSize": "13px", "fontWeight": "bold"}),
                    html.H2(ffmi_str, style={"margin": "4px 0 2px 0", "color": get_color_for_score(ffmi_score)}),
                    html.Span(f"Score {ffmi_score}/10 — {ffmi_sub}", style={"fontSize": "11px", "color": get_color_for_score(ffmi_score), "fontWeight": "700"})
                ]),
            ]),
            
            html.Div(style={"display": "flex", "gap": "24px", "alignItems": "flex-start"}, children=[
                html.Div(style={"flex": "1.1", "backgroundColor": "white", "padding": "28px", "borderRadius": "16px", "boxShadow": "0 4px 20px rgba(0,0,0,0.04)", "border": "1px solid #e2e8f0"}, children=[
                    html.H3("📋 Karta Pomiarowa Sylwetki", style={"marginTop": 0, "marginBottom": "15px", "color": "#0f172a", "fontWeight": "800", "fontSize": "18px"}),
                    html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "12px", "marginBottom": "15px"}, children=[
                        html.Div([html.Label("Data Pomiaru:"), dcc.DatePickerSingle(id="fit-input-date", date=datetime.now().date(), display_format="YYYY-MM-DD")]),
                        html.Div([html.Label("Godzina Pomiaru:"), dcc.Input(id="fit-input-time", type="text", placeholder="np. 07:15")]),
                    ]),
                    html.Div(style={"backgroundColor": "#f8fafc", "padding": "16px", "borderRadius": "12px", "marginBottom": "20px", "border": "1px solid #e2e8f0"}, children=[
                        html.H4("1. WAGA & SKŁAD CIAŁA (Waga Xiaomi na czczo)", style={"marginTop": 0, "marginBottom": "12px", "color": "#0284c7", "fontSize": "14px", "fontWeight": "800"}),
                        html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "10px"}, children=[
                            html.Div([html.Label("Masa Ciała (kg):"), dcc.Input(id="fit-input-weight", type="number", placeholder="kg", step=0.1)]),
                            html.Div([html.Label("Tkanka Tłuszczowa (%):"), dcc.Input(id="fit-input-bf", type="number", placeholder="%", step=0.1)]),
                            html.Div([html.Label("Masa Mięśniowa (kg):"), dcc.Input(id="fit-input-muscle-kg", type="number", placeholder="kg", step=0.1)]),
                            html.Div([html.Label("Procent Mięśni (%):"), dcc.Input(id="fit-input-muscle-pct", type="number", placeholder="%", step=0.1)]),
                            html.Div([html.Label("Białko Procentowo (%):"), dcc.Input(id="fit-input-protein-pct", type="number", placeholder="%", step=0.1)]),
                            html.Div([html.Label("Mięśnie Szkieletowe (kg):"), dcc.Input(id="fit-input-skeletal-kg", type="number", placeholder="kg", step=0.1)]),
                            html.Div([html.Label("Nawodnienie (%):"), dcc.Input(id="fit-input-water-pct", type="number", placeholder="%", step=0.1)]),
                            html.Div([html.Label("BMR (Metabolizm kcal):"), dcc.Input(id="fit-input-bmr", type="number", placeholder="kcal", step=1)]),
                            html.Div([html.Label("LBM (Bez tłuszczu kg):"), dcc.Input(id="fit-input-lbm", type="number", placeholder="kg", step=0.1)]),
                        ])
                    ]),
                    html.Div(style={"backgroundColor": "#f8fafc", "padding": "16px", "borderRadius": "12px", "marginBottom": "20px", "border": "1px solid #e2e8f0"}, children=[
                        html.H4("2. OBWODY CIAŁA — MIARKA KRAWIECKA", style={"marginTop": 0, "marginBottom": "12px", "color": "#0284c7", "fontSize": "14px", "fontWeight": "800"}),
                        html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "10px"}, children=[
                            html.Div([html.Label("Biceps / Ramię (cm):"), dcc.Input(id="fit-input-biceps", type="number", placeholder="cm", step=0.5)]),
                            html.Div([html.Label("Przedramię (cm):"), dcc.Input(id="fit-input-forearm", type="number", placeholder="cm", step=0.5)]),
                            html.Div([html.Label("Klatka (cm):"), dcc.Input(id="fit-input-chest", type="number", placeholder="cm", step=0.5)]),
                            html.Div([html.Label("Pas - Pępek (cm):"), dcc.Input(id="fit-input-waist", type="number", placeholder="cm", step=0.5)]),
                            html.Div([html.Label("Biodra / Oponka (cm):"), dcc.Input(id="fit-input-hips", type="number", placeholder="cm", step=0.5)]),
                            html.Div([html.Label("Udo (cm):"), dcc.Input(id="fit-input-thigh", type="number", placeholder="cm", step=0.5)]),
                            html.Div([html.Label("Łydka (cm):"), dcc.Input(id="fit-input-calf", type="number", placeholder="cm", step=0.5)]),
                        ])
                    ]),
                    html.Label("Uwagi / Komentarz:"),
                    dcc.Input(id="fit-input-notes", type="text", placeholder="np. Po regeneracji, rano na czczo..."),
                    html.Button("Zapisz Kartę Pomiarów", id="btn-fit-save-body", n_clicks=0, style={"width": "100%", "marginTop": "20px", "padding": "14px", "backgroundColor": "#10b981", "color": "white", "border": "none", "borderRadius": "10px", "fontWeight": "800", "fontSize": "15px", "cursor": "pointer"}),
                    html.Div(id="fit-save-msg", style={"marginTop": "14px", "textAlign": "center", "fontWeight": "bold"})
                ]),
                
                html.Div(style={"flex": "1", "backgroundColor": "white", "padding": "24px", "borderRadius": "16px", "boxShadow": "0 4px 20px rgba(0,0,0,0.03)", "border": "1px solid #e2e8f0"}, children=[
                    html.H3("📊 Analiza Progresu Sylwetkowego", style={"marginTop": 0, "marginBottom": "14px", "color": "#0f172a", "fontWeight": "800", "fontSize": "18px"}),
                    html.Table(style={"width": "100%", "borderCollapse": "collapse"}, children=[
                        html.Thead(html.Tr(style={"backgroundColor": "#f8fafc", "borderBottom": "2px solid #e2e8f0"}, children=[
                            html.Th("PARAMETR", style={"padding": "12px", "textAlign": "left", "fontSize": "11px", "color": "#475569", "fontWeight": "800"}),
                            html.Th("PIERWSZY", style={"padding": "12px", "textAlign": "center", "fontSize": "11px", "color": "#475569", "fontWeight": "800"}),
                            html.Th("OSTATNI", style={"padding": "12px", "textAlign": "center", "fontSize": "11px", "color": "#475569", "fontWeight": "800"}),
                            html.Th("DELTA (PROGRES)", style={"padding": "12px", "textAlign": "center", "fontSize": "11px", "color": "#475569", "fontWeight": "800"}),
                        ])),
                        html.Tbody(table_rows if table_rows else [html.Tr(html.Td("Brak danych pomiarowych do porównania.", colSpan=4, style={"textAlign": "center", "padding": "20px", "color": "#64748b"}))])
                    ])
                ])
            ])
        ])

    elif tab == "fit-predykcja-eta":
        goals = get_target_goals_dict()
        
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        conn = get_db_connection()
        df_sessions = pd.read_sql_query("SELECT * FROM fit_workout_sessions WHERE workout_date >= ?", conn, params=(thirty_days_ago,))
        conn.close()

        actual_workouts = len(df_sessions)
        target_workouts_month = 12
        consistency_ratio = max(0.1, min(1.0, actual_workouts / target_workouts_month)) if target_workouts_month > 0 else 1.0

        latest_row = df_valid.iloc[0] if has_valid_data else {}

        curr_w = latest_row.get('weight_kg')
        curr_waist = latest_row.get('waist_cm')
        curr_chest = latest_row.get('chest_cm')
        curr_bf = latest_row.get('body_fat_pct')

        target_w = goals.get('weight_kg')
        target_waist = goals.get('waist_cm')
        target_chest = goals.get('chest_cm')
        target_bf = goals.get('body_fat_pct')
        selected_profile_key = goals.get('posture_profile', 'recomp')

        weeks_w_real, weeks_waist_real = 0, 0
        eta_w_str, eta_waist_str = "Brak celu", "Brak celu"

        if curr_w and target_w:
            diff_w = abs(curr_w - target_w)
            weeks_w_base = (diff_w / 0.45) * 1.2
            weeks_w_real = weeks_w_base / consistency_ratio if diff_w > 0 else 0
            eta_w_str = (datetime.now() + timedelta(weeks=weeks_w_real)).strftime('%d.%m.%Y')

        if curr_waist and target_waist:
            diff_waist = abs(curr_waist - target_waist)
            weeks_waist_base = (diff_waist / 0.55) * 1.25
            weeks_waist_real = weeks_waist_base / consistency_ratio if diff_waist > 0 else 0
            eta_waist_str = (datetime.now() + timedelta(weeks=weeks_waist_real)).strftime('%d.%m.%Y')

        return html.Div(style={"maxWidth": "1000px", "margin": "0 auto"}, children=[
            html.Div(style={"backgroundColor": "#0f172a", "color": "white", "padding": "24px", "borderRadius": "16px", "marginBottom": "24px"}, children=[
                html.H3("⚙️ Profil Postury & Rekompozycji Sylwetkowej", style={"marginTop": 0, "marginBottom": "8px", "color": "#38bdf8", "fontWeight": "800"}),
                html.P("Wybierz profil adaptacji, aby silnik zoptymalizował wagi obwodów do spalanego tłuszczu i tkanki mięśniowej.", style={"color": "#94a3b8", "fontSize": "13px"}),
                
                dcc.RadioItems(
                    id="edit-posture-profile",
                    options=[{'label': f" {v['label']}", 'value': k} for k, v in POSTURE_PROFILES.items()],
                    value=selected_profile_key,
                    style={"display": "flex", "flexDirection": "column", "gap": "10px", "marginTop": "14px", "fontWeight": "bold", "color": "#f8fafc"}
                )
            ]),

            html.Div(style={"backgroundColor": "white", "padding": "24px", "borderRadius": "16px", "border": "1px solid #e2e8f0", "marginBottom": "24px"}, children=[
                html.H3("📅 Predictor Formy na Wydarzenie / Dzień X", style={"marginTop": 0, "marginBottom": "8px", "color": "#0f172a", "fontWeight": "800"}),
                html.P("Podaj datę ważnego wyjazdu lub wydarzenia, aby przeliczyć przewidywany wygląd sylwetki.", style={"color": "#64748b", "fontSize": "13px"}),
                
                html.Div(style={"display": "flex", "gap": "16px", "alignItems": "center", "marginTop": "16px", "marginBottom": "16px"}, children=[
                    dcc.DatePickerSingle(
                        id="target-event-date",
                        date=(datetime.now() + timedelta(days=60)).date(),
                        display_format="YYYY-MM-DD"
                    ),
                    html.Button("⚡ Oblicz Formę na ten Dzień", id="btn-calc-target-date", n_clicks=0, style={"padding": "10px 20px", "backgroundColor": "#0284c7", "color": "white", "border": "none", "borderRadius": "8px", "fontWeight": "800", "cursor": "pointer"})
                ]),
                html.Div(id="target-date-results-container")
            ]),

            html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr 1fr 1fr", "gap": "15px", "marginBottom": "24px"}, children=[
                html.Div(className="kpi-card blue", children=[
                    html.Span("WAGA CEL", style={"color": "#64748b", "fontSize": "12px", "fontWeight": "bold"}),
                    html.H3(fmt_val(target_w, "kg"), style={"margin": "4px 0", "color": "#0284c7"}),
                    html.Div(f"ETA: {eta_w_str}", style={"fontSize": "12px", "fontWeight": "800", "color": "#0f172a"}),
                    html.Span(f"Obecnie: {fmt_val(curr_w, 'kg')}", style={"fontSize": "11px", "color": "#64748b"})
                ]),
                html.Div(className="kpi-card green", children=[
                    html.Span("PAS CEL", style={"color": "#64748b", "fontSize": "12px", "fontWeight": "bold"}),
                    html.H3(fmt_val(target_waist, "cm"), style={"margin": "4px 0", "color": "#10b981"}),
                    html.Div(f"ETA: {eta_waist_str}", style={"fontSize": "12px", "fontWeight": "800", "color": "#0f172a"}),
                    html.Span(f"Obecnie: {fmt_val(curr_waist, 'cm')}", style={"fontSize": "11px", "color": "#64748b"})
                ]),
                html.Div(className="kpi-card yellow", children=[
                    html.Span("KLATKA CEL", style={"color": "#64748b", "fontSize": "12px", "fontWeight": "bold"}),
                    html.H3(fmt_val(target_chest, "cm"), style={"margin": "4px 0", "color": "#d97706"}),
                    html.Span(f"Obecnie: {fmt_val(curr_chest, 'cm')}", style={"fontSize": "11px", "color": "#64748b"})
                ]),
                html.Div(className="kpi-card purple", children=[
                    html.Span("TŁUSZCZ CEL (BF%)", style={"color": "#64748b", "fontSize": "12px", "fontWeight": "bold"}),
                    html.H3(fmt_val(target_bf, "%"), style={"margin": "4px 0", "color": "#8b5cf6"}),
                    html.Span(f"Obecnie: {fmt_val(curr_bf, '%')}", style={"fontSize": "11px", "color": "#64748b"})
                ]),
            ]),

            html.Div(style={"backgroundColor": "white", "padding": "24px", "borderRadius": "16px", "border": "1px solid #e2e8f0"}, children=[
                html.H4("🎯 Zdefiniuj Swoje Własne Cele Sylwetkowe (Dynamiczne A -> B)", style={"marginTop": 0, "marginBottom": "16px", "color": "#0f172a"}),
                html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr 1fr 1fr", "gap": "12px", "marginBottom": "16px"}, children=[
                    html.Div([html.Label("Cel Waga (kg):"), dcc.Input(id="edit-target-w", type="number", value=target_w, step=0.5)]),
                    html.Div([html.Label("Cel Pas (cm):"), dcc.Input(id="edit-target-waist", type="number", value=target_waist, step=0.5)]),
                    html.Div([html.Label("Cel Klatka (cm):"), dcc.Input(id="edit-target-chest", type="number", value=target_chest, step=0.5)]),
                    html.Div([html.Label("Cel Tłuszcz (%):"), dcc.Input(id="edit-target-bf", type="number", value=target_bf, step=0.5)]),
                ]),
                html.Button("💾 Zapisz Moje Własne Cele", id="btn-save-targets", n_clicks=0, style={"width": "100%", "padding": "12px", "backgroundColor": "#10b981", "color": "white", "border": "none", "borderRadius": "8px", "fontWeight": "bold", "cursor": "pointer"}),
                html.Div(id="save-targets-msg", style={"marginTop": "10px", "textAlign": "center", "fontWeight": "bold"})
            ])
        ])

    elif tab == "fit-kamienie-milowe":
        goals = get_target_goals_dict()
        if not has_valid_data or not goals:
            return html.Div(style={"backgroundColor": "white", "padding": "30px", "borderRadius": "16px"}, children=[
                html.P("Wprowadź pierwszy pomiar w karcie pomiarów i zdefiniuj cele w zakładce 'Dynamiczne Cele & ETA', aby uruchomić silnik Hero XP.", style={"color": "#64748b"})
            ])
        
        first_row = df_valid.iloc[-1]
        latest_row = df_valid.iloc[0]
        selected_profile_key = goals.get('posture_profile', 'recomp')
        prof = POSTURE_PROFILES.get(selected_profile_key, POSTURE_PROFILES['recomp'])

        def calc_param_progress(first_v, curr_v, target_v):
            if first_v is None or curr_v is None or target_v is None:
                return 0.0
            total_dist = abs(first_v - target_v)
            if total_dist < 0.01:
                return 100.0
            made_dist = abs(first_v - curr_v)
            return min(100.0, max(0.0, (made_dist / total_dist) * 100.0))

        prog_w = calc_param_progress(first_row.get('weight_kg'), latest_row.get('weight_kg'), goals.get('weight_kg'))
        prog_waist = calc_param_progress(first_row.get('waist_cm'), latest_row.get('waist_cm'), goals.get('waist_cm'))
        prog_chest = calc_param_progress(first_row.get('chest_cm'), latest_row.get('chest_cm'), goals.get('chest_cm'))
        prog_bf = calc_param_progress(first_row.get('body_fat_pct'), latest_row.get('body_fat_pct'), goals.get('body_fat_pct'))

        total_body_progress_pct = round(
            prog_w * prof['w_weight'] + 
            prog_waist * prof['w_waist'] + 
            prog_chest * prof['w_chest'] + 
            prog_bf * prof['w_bf'], 1
        )

        current_lvl = 1
        for item in HERO_LEVELS_XP:
            if total_body_progress_pct >= item["req_pct"]:
                current_lvl = item["lvl"]

        next_lvl_item = HERO_LEVELS_XP[min(19, current_lvl)]
        needed_pct_next = max(0.0, round(next_lvl_item["req_pct"] - total_body_progress_pct, 1))

        level_cards = []
        for h in HERO_LEVELS_XP:
            is_unlocked = total_body_progress_pct >= h["req_pct"]
            card_style = {
                "padding": "16px", "borderRadius": "12px", "marginBottom": "12px", "display": "flex", "alignItems": "center", "justifyContent": "space-between",
                "backgroundColor": "#f0fdf4" if is_unlocked else "#f8fafc",
                "border": "1px solid #10b981" if is_unlocked else "1px solid #e2e8f0"
            }
            badge_style = {
                "backgroundColor": "#10b981" if is_unlocked else "#cbd5e1",
                "color": "white", "padding": "6px 12px", "borderRadius": "20px", "fontWeight": "bold", "fontSize": "12px"
            }
            
            level_cards.append(
                html.Div(style=card_style, children=[
                    html.Div(children=[
                        html.Div(style={"display": "flex", "alignItems": "center", "gap": "10px"}, children=[
                            html.Span(f"LVL {h['lvl']}", style=badge_style),
                            html.H4(h['name'], style={"margin": 0, "color": "#0f172a" if is_unlocked else "#64748b", "fontWeight": "800"})
                        ]),
                        html.P(h['desc'], style={"margin": "4px 0 0 0", "fontSize": "13px", "color": "#475569" if is_unlocked else "#94a3b8"})
                    ]),
                    html.Div(style={"textAlign": "right"}, children=[
                        html.Span("✅ ODBLOKOWANE" if is_unlocked else f"Wymaga: {h['req_pct']}% Realizacji", style={"fontWeight": "800", "fontSize": "13px", "color": "#10b981" if is_unlocked else "#64748b"})
                    ])
                ])
            )

        return html.Div(style={"maxWidth": "950px", "margin": "0 auto"}, children=[
            html.Div(style={"backgroundColor": "white", "padding": "28px", "borderRadius": "16px", "border": "1px solid #e2e8f0", "marginBottom": "24px"}, children=[
                html.Div(style={"display": "flex", "justifyContent": "space-between", "alignItems": "flex-start"}, children=[
                    html.Div([
                        html.Span("TWÓJ AKTUALNY POZIOM HEROSA (A -> B)", style={"color": "#0284c7", "fontWeight": "800", "fontSize": "12px", "letterSpacing": "1px"}),
                        html.H2(f"Level {current_lvl}: {HERO_LEVELS_XP[current_lvl-1]['name']}", style={"margin": "6px 0 12px 0", "color": "#0f172a", "fontWeight": "900"}),
                    ]),
                    html.Div(style={"backgroundColor": "#0f172a", "color": "#10b981", "padding": "12px 20px", "borderRadius": "12px", "textAlign": "right"}, children=[
                        html.Span("REALIZACJA CELU", style={"fontSize": "10px", "fontWeight": "800", "display": "block", "color": "#94a3b8"}),
                        html.Span(f"{total_body_progress_pct}%", style={"fontSize": "24px", "fontWeight": "900"})
                    ])
                ]),
                
                html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr 1fr 1fr", "gap": "10px", "marginTop": "15px", "marginBottom": "15px"}, children=[
                    html.Div(style={"backgroundColor": "#f8fafc", "padding": "10px", "borderRadius": "8px", "border": "1px solid #e2e8f0"}, children=[
                        html.Span("⚖️ Masa Ciała", style={"fontSize": "11px", "color": "#64748b", "fontWeight": "bold"}),
                        html.Div(f"{round(prog_w, 1)}%", style={"fontWeight": "800", "color": "#0284c7"})
                    ]),
                    html.Div(style={"backgroundColor": "#f8fafc", "padding": "10px", "borderRadius": "8px", "border": "1px solid #e2e8f0"}, children=[
                        html.Span("📏 Obwód Pasa", style={"fontSize": "11px", "color": "#64748b", "fontWeight": "bold"}),
                        html.Div(f"{round(prog_waist, 1)}%", style={"fontWeight": "800", "color": "#10b981"})
                    ]),
                    html.Div(style={"backgroundColor": "#f8fafc", "padding": "10px", "borderRadius": "8px", "border": "1px solid #e2e8f0"}, children=[
                        html.Span("🏋️ Obwód Klatki", style={"fontSize": "11px", "color": "#64748b", "fontWeight": "bold"}),
                        html.Div(f"{round(prog_chest, 1)}%", style={"fontWeight": "800", "color": "#d97706"})
                    ]),
                    html.Div(style={"backgroundColor": "#f8fafc", "padding": "10px", "borderRadius": "8px", "border": "1px solid #e2e8f0"}, children=[
                        html.Span("🔥 Tłuszcz (BF%)", style={"fontSize": "11px", "color": "#64748b", "fontWeight": "bold"}),
                        html.Div(f"{round(prog_bf, 1)}%", style={"fontWeight": "800", "color": "#8b5cf6"})
                    ]),
                ]),

                html.Div(style={"backgroundColor": "#f1f5f9", "padding": "12px", "borderRadius": "8px"}, children=[
                    html.Span(f"Do następnego Poziomu ({next_lvl_item['name']}) brakuje jeszcze: ", style={"fontWeight": "bold"}),
                    html.Span(f"+{needed_pct_next}% postępu!", style={"color": "#0284c7", "fontWeight": "800"})
                ])
            ]),

            html.Div(level_cards)
        ])

    elif tab == "fit-plany-edit":
        df_plans = get_plans_list()
        plans_options = [{'label': r['plan_name'], 'value': r['id']} for _, r in df_plans.iterrows()] if not df_plans.empty else []
        
        return html.Div(style={"maxWidth": "900px", "margin": "0 auto", "backgroundColor": "white", "padding": "32px", "borderRadius": "16px", "border": "1px solid #e2e8f0", "boxShadow": "0 4px 20px rgba(0,0,0,0.03)"}, children=[
            html.Div(style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "24px"}, children=[
                html.H3("📋 Zarządzanie Planami Treningowymi", style={"margin": 0, "color": "#0f172a", "fontWeight": "800"}),
                dcc.RadioItems(
                    id="plan-editor-mode",
                    options=[
                        {'label': ' ✏️ Edytuj Wybrany Plan', 'value': 'edit'},
                        {'label': ' ➕ Stwórz Nowy Plan', 'value': 'new'}
                    ],
                    value='edit',
                    inline=True,
                    style={"fontWeight": "bold", "color": "#0284c7"}
                )
            ]),
            
            html.Div(id="edit-plan-select-container", children=[
                html.Label("Wybierz plan do edycji:"),
                dcc.Dropdown(
                    id="fit-edit-select-plan",
                    options=plans_options,
                    value=plans_options[0]['value'] if plans_options else None,
                    clearable=False,
                    style={"marginBottom": "20px"}
                )
            ]),
            
            html.Div(id="plan-editor-content")
        ])

    elif tab == "fit-trening-live":
        df_plans = get_plans_list()
        plans_options = [{'label': r['plan_name'], 'value': r['id']} for _, r in df_plans.iterrows()] if not df_plans.empty else []
        
        return html.Div(style={"maxWidth": "850px", "margin": "0 auto", "backgroundColor": "white", "padding": "32px", "borderRadius": "16px", "border": "1px solid #e2e8f0", "boxShadow": "0 4px 20px rgba(0,0,0,0.03)"}, children=[
            html.H3("🏋️ Dziennik Treningowy na Żywo (Live Workout)", style={"marginTop": 0, "marginBottom": "16px", "color": "#0f172a", "fontWeight": "800"}),
            html.Label("Wybierz dzisiejszy plan treningowy:"),
            dcc.Dropdown(
                id="fit-select-live-plan",
                options=plans_options,
                value=plans_options[0]['value'] if plans_options else None,
                placeholder="Wybierz plan z listy...",
                clearable=False,
                style={"marginBottom": "24px"}
            ),
            html.Div(id="fit-live-exercises-container")
        ])

    elif tab == "fit-historia":
        if df_valid.empty or len(df_valid) < 2:
            return html.Div(style={"backgroundColor": "white", "padding": "40px", "borderRadius": "16px", "textAlign": "center"}, children=[
                html.P("Wprowadź co najmniej 2 ważne pomiary, aby zobaczyć wykresy postępów.", style={"color": "#64748b"})
            ])
        
        df_plot = df_valid.sort_values(by="entry_date", ascending=True)
        fig_weight = px.line(df_plot, x="entry_date", y=[c for c in ["weight_kg", "muscle_mass_kg", "lbm_kg"] if c in df_plot.columns], title="Masa Ciała i Mięśni (kg)")
        fig_weight.update_layout(font_family="Inter")
        fig_circ = px.line(df_plot, x="entry_date", y=[c for c in ["waist_cm", "biceps_cm", "chest_cm", "hips_cm"] if c in df_plot.columns], title="Obwody Ciała (cm)")
        fig_circ.update_layout(font_family="Inter")

        return html.Div(style={"display": "flex", "flexDirection": "column", "gap": "20px"}, children=[
            html.Div(style={"backgroundColor": "white", "padding": "24px", "borderRadius": "16px", "border": "1px solid #e2e8f0", "display": "flex", "justifyContent": "space-between", "alignItems": "center"}, children=[
                html.Div([
                    html.H3("📄 Raport Analizy Treningowej dla AI (TXT)", style={"margin": 0, "color": "#0f172a", "fontWeight": "800"}),
                    html.P("Pobierz czysty plik tekstowy zawierający wszystkie dane, sesje, ćwiczenia, serie i notatki o trudnościach, idealny do wklejenia dla AI.", style={"margin": "4px 0 0 0", "fontSize": "13px", "color": "#64748b"})
                ]),
                html.Button("📄 Pobierz Raport TXT dla AI", id="btn-download-fit-txt", n_clicks=0, style={
                    "padding": "12px 24px", "backgroundColor": "#0284c7", "color": "white",
                    "border": "none", "borderRadius": "10px", "fontWeight": "800", "fontSize": "14px", "cursor": "pointer",
                    "boxShadow": "0 4px 12px rgba(2, 132, 199, 0.25)"
                })
            ]),

            html.Div(style={"backgroundColor": "white", "padding": "20px", "borderRadius": "16px", "border": "1px solid #e2e8f0"}, children=[dcc.Graph(figure=fig_weight)]),
            html.Div(style={"backgroundColor": "white", "padding": "20px", "borderRadius": "16px", "border": "1px solid #e2e8f0"}, children=[dcc.Graph(figure=fig_circ)]),
        ])

@callback(
    Output("download-fit-txt-file", "data"),
    Input("btn-download-fit-txt", "n_clicks"),
    prevent_initial_call=True
)
def download_txt_report(n_clicks):
    if n_clicks > 0:
        txt_content = generate_fit_hero_txt_report()
        filename = f"Fit_HERO_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
        return dcc.send_string(txt_content, filename)

@callback(
    Output("target-date-results-container", "children"),
    Input("btn-calc-target-date", "n_clicks"),
    State("target-event-date", "date"),
    State("edit-posture-profile", "value"),
    prevent_initial_call=True
)
def calculate_form_for_target_date(n_clicks, selected_date_str, selected_profile_key):
    if not selected_date_str:
        return html.P("Wybierz poprawną datę.", style={"color": "#ef4444"})
    
    target_dt = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    today_dt = datetime.now().date()
    days_left = (target_dt - today_dt).days
    
    if days_left <= 0:
        return html.P("Data wydarzenia musi być w przyszłości!", style={"color": "#ef4444"})

    df_body = get_body_params_df()
    if df_body.empty:
        return html.P("Brak pomiarów w karcie pomiarowej. Uzupełnij dane.", style={"color": "#ef4444"})
    
    latest = df_body.iloc[0]
    first = df_body.iloc[-1]
    goals = get_target_goals_dict()

    curr_w = latest.get('weight_kg') or 85.0
    curr_bf = latest.get('body_fat_pct') or 18.0
    curr_lbm = latest.get('lbm_kg') or (curr_w * (1 - curr_bf/100.0))
    curr_waist = latest.get('waist_cm') or 90.0
    curr_chest = latest.get('chest_cm') or 104.0
    curr_biceps = latest.get('biceps_cm') or 36.0

    conn = get_db_connection()
    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    df_sessions = pd.read_sql_query("SELECT * FROM fit_workout_sessions WHERE workout_date >= ?", conn, params=(thirty_days_ago,))
    conn.close()

    actual_workouts = len(df_sessions)
    consistency_ratio = max(0.1, min(1.0, actual_workouts / 12)) if actual_workouts > 0 else 0.5
    weeks_left = days_left / 7.0

    profile_key = selected_profile_key or goals.get('posture_profile', 'recomp')
    
    if profile_key == 'cut':
        w_rate, waist_rate, chest_rate, bf_rate = 0.50, 0.65, -0.05, 0.35
    elif profile_key == 'bulk':
        w_rate, waist_rate, chest_rate, bf_rate = -0.25, 0.15, 0.30, -0.10
    else:
        w_rate, waist_rate, chest_rate, bf_rate = 0.20, 0.45, 0.20, 0.25

    est_w_delta = (weeks_left * w_rate) * consistency_ratio
    est_waist_delta = (weeks_left * waist_rate) * consistency_ratio
    est_chest_delta = (weeks_left * chest_rate) * consistency_ratio
    est_bf_delta = (weeks_left * bf_rate) * consistency_ratio

    est_w = max(50.0, curr_w - est_w_delta)
    est_waist = max(60.0, curr_waist - est_waist_delta)
    est_chest = max(70.0, curr_chest + est_chest_delta)
    est_bf = max(8.0, curr_bf - est_bf_delta)
    est_lbm = est_w * (1.0 - (est_bf / 100.0))
    est_biceps = curr_biceps + (0.05 * weeks_left * consistency_ratio if profile_key != 'cut' else -0.02 * weeks_left)
    
    est_vt = est_chest / est_waist if est_waist > 0 else 1.15

    def calc_param_prog(first_v, curr_v, target_v):
        if first_v is None or curr_v is None or target_v is None: return 0.0
        tot = abs(first_v - target_v)
        if tot < 0.01: return 100.0
        return min(100.0, max(0.0, (abs(first_v - curr_v) / tot) * 100.0))

    prog_w = calc_param_prog(first.get('weight_kg'), est_w, goals.get('weight_kg'))
    prog_waist = calc_param_prog(first.get('waist_cm'), est_waist, goals.get('waist_cm'))
    prog_chest = calc_param_prog(first.get('chest_cm'), est_chest, goals.get('chest_cm'))
    prog_bf = calc_param_prog(first.get('body_fat_pct'), est_bf, goals.get('body_fat_pct'))

    prof_cfg = POSTURE_PROFILES.get(profile_key, POSTURE_PROFILES['recomp'])
    est_total_prog = round(prog_w * prof_cfg['w_weight'] + prog_waist * prof_cfg['w_waist'] + prog_chest * prof_cfg['w_chest'] + prog_bf * prof_cfg['w_bf'], 1)

    est_lvl = 1
    for item in HERO_LEVELS_XP:
        if est_total_prog >= item["req_pct"]:
            est_lvl = item["lvl"]

    return html.Div(style={"backgroundColor": "#f8fafc", "padding": "24px", "borderRadius": "14px", "border": "1px solid #0284c7", "marginTop": "15px"}, children=[
        html.Div(style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "16px"}, children=[
            html.H4(f"🎯 Prognoza Sylwetki na Dzień: {selected_date_str} (za {days_left} dni / {weeks_left:.1f} tyg.)", style={"margin": 0, "color": "#0f172a", "fontWeight": "800"}),
            html.Span(f"Przewidywany Poziom: LVL {est_lvl} ({est_total_prog}% celu)", style={"backgroundColor": "#0284c7", "color": "white", "padding": "6px 14px", "borderRadius": "20px", "fontWeight": "bold", "fontSize": "12px"})
        ]),
        
        html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr 1fr", "gap": "15px"}, children=[
            html.Div(style={"backgroundColor": "white", "padding": "14px", "borderRadius": "10px", "border": "1px solid #e2e8f0"}, children=[
                html.Span("⚖️ WAGA & SKŁAD CIAŁA", style={"fontSize": "11px", "color": "#0284c7", "fontWeight": "800", "display": "block", "marginBottom": "8px"}),
                html.Div(style={"display": "flex", "justifyContent": "space-between", "marginBottom": "4px"}, children=[
                    html.Span("Masa ciała:", style={"fontSize": "12px", "color": "#64748b"}),
                    html.Span(f"{est_w:.1f} kg ({'-' if est_w_delta>=0 else '+'}{abs(est_w_delta):.1f} kg)", style={"fontWeight": "bold", "fontSize": "13px"})
                ]),
                html.Div(style={"display": "flex", "justifyContent": "space-between", "marginBottom": "4px"}, children=[
                    html.Span("Tłuszcz (BF%):", style={"fontSize": "12px", "color": "#64748b"}),
                    html.Span(f"{est_bf:.1f}% ({'-' if est_bf_delta>=0 else '+'}{abs(est_bf_delta):.1f}%)", style={"fontWeight": "bold", "fontSize": "13px", "color": "#8b5cf6"})
                ]),
                html.Div(style={"display": "flex", "justifyContent": "space-between"}, children=[
                    html.Span("Czysta masa (LBM):", style={"fontSize": "12px", "color": "#64748b"}),
                    html.Span(f"{est_lbm:.1f} kg", style={"fontWeight": "bold", "fontSize": "13px", "color": "#10b981"})
                ]),
            ]),

            html.Div(style={"backgroundColor": "white", "padding": "14px", "borderRadius": "10px", "border": "1px solid #e2e8f0"}, children=[
                html.Span("📏 OBWODY CIAŁA", style={"fontSize": "11px", "color": "#10b981", "fontWeight": "800", "display": "block", "marginBottom": "8px"}),
                html.Div(style={"display": "flex", "justifyContent": "space-between", "marginBottom": "4px"}, children=[
                    html.Span("Pas (Pępek):", style={"fontSize": "12px", "color": "#64748b"}),
                    html.Span(f"{est_waist:.1f} cm ({'-' if est_waist_delta>=0 else '+'}{abs(est_waist_delta):.1f} cm)", style={"fontWeight": "bold", "fontSize": "13px", "color": "#10b981"})
                ]),
                html.Div(style={"display": "flex", "justifyContent": "space-between", "marginBottom": "4px"}, children=[
                    html.Span("Klatka piersiowa:", style={"fontSize": "12px", "color": "#64748b"}),
                    html.Span(f"{est_chest:.1f} cm ({'+' if est_chest_delta>=0 else '-'}{abs(est_chest_delta):.1f} cm)", style={"fontWeight": "bold", "fontSize": "13px"})
                ]),
                html.Div(style={"display": "flex", "justifyContent": "space-between"}, children=[
                    html.Span("Biceps / Ramię:", style={"fontSize": "12px", "color": "#64748b"}),
                    html.Span(f"{est_biceps:.1f} cm", style={"fontWeight": "bold", "fontSize": "13px"})
                ]),
            ]),

            html.Div(style={"backgroundColor": "white", "padding": "14px", "borderRadius": "10px", "border": "1px solid #e2e8f0"}, children=[
                html.Span("📐 PROPORCJE SYLWETKI", style={"fontSize": "11px", "color": "#d97706", "fontWeight": "800", "display": "block", "marginBottom": "8px"}),
                html.Div(style={"display": "flex", "justifyContent": "space-between", "marginBottom": "4px"}, children=[
                    html.Span("Współczynnik V-Taper:", style={"fontSize": "12px", "color": "#64748b"}),
                    html.Span(f"{est_vt:.2f}", style={"fontWeight": "bold", "fontSize": "13px", "color": "#d97706"})
                ]),
                html.Div(style={"display": "flex", "justifyContent": "space-between", "marginBottom": "4px"}, children=[
                    html.Span("Profil adaptacji:", style={"fontSize": "12px", "color": "#64748b"}),
                    html.Span(f"{prof_cfg['label'].split('(')[0]}", style={"fontWeight": "bold", "fontSize": "11px", "color": "#334155"})
                ]),
                html.Div(style={"display": "flex", "justifyContent": "space-between"}, children=[
                    html.Span("Dyscyplina Live:", style={"fontSize": "12px", "color": "#64748b"}),
                    html.Span(f"{round(consistency_ratio*100)}%", style={"fontWeight": "bold", "fontSize": "13px"})
                ]),
            ]),
        ]),
        
        html.P(f" Prognoza wyliczona w oparciu o profil '{prof_cfg['label']}' przy obecnym tempie {actual_workouts} treningów w miesiącu.", style={"marginTop": "14px", "marginBottom": 0, "fontSize": "11px", "color": "#64748b", "textAlign": "center"})
    ])

@callback(
    Output("save-targets-msg", "children"),
    Input("btn-save-targets", "n_clicks"),
    State("edit-target-w", "value"),
    State("edit-target-waist", "value"),
    State("edit-target-chest", "value"),
    State("edit-target-bf", "value"),
    State("edit-posture-profile", "value"),
    prevent_initial_call=True
)
def save_target_goals(n_clicks, w_val, waist_val, chest_val, bf_val, posture_profile):
    if n_clicks > 0:
        conn = get_db_connection()
        cursor = conn.cursor()
        goals_data = [
            ('weight_kg', float(w_val) if w_val else None),
            ('waist_cm', float(waist_val) if waist_val else None),
            ('chest_cm', float(chest_val) if chest_val else None),
            ('body_fat_pct', float(bf_val) if bf_val else None),
            ('posture_profile', str(posture_profile or 'recomp'))
        ]
        for k, v in goals_data:
            if v is not None:
                cursor.execute("INSERT OR REPLACE INTO fit_target_goals (param_key, target_val) VALUES (?, ?)", (k, v))
        conn.commit()
        conn.close()
        set_props("fit-url-refresh", {"href": "/fit-hero"})
        return html.Span(" Zapisano Twoje cele!", style={"color": "#10b981"})
    return ""

@callback(
    Output("edit-plan-select-container", "style"),
    Input("plan-editor-mode", "value")
)
def toggle_select_dropdown(mode):
    return {"display": "block"} if mode == 'edit' else {"display": "none"}

@callback(
    Output("plan-editor-content", "children"),
    Input("plan-editor-mode", "value"),
    Input("fit-edit-select-plan", "value")
)
def render_plan_editor(mode, selected_plan_id):
    if mode == 'edit':
        if not selected_plan_id:
            return html.P("Wybierz plan z rozwijanej listy powyżej, aby go edytować.", style={"color": "#64748b"})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT plan_name FROM fit_plans WHERE id = ?", (selected_plan_id,))
        p_row = cursor.fetchone()
        plan_name = p_row[0] if p_row else ""
        conn.close()
        
        df_ex = get_plan_exercises(selected_plan_id)
        
        ex_inputs = []
        for idx, r in df_ex.iterrows():
            current_load_type = r.get('load_type') or 'Ciężar (kg)'
            ex_inputs.append(
                html.Div(style={"backgroundColor": "#f8fafc", "border": "1px solid #e2e8f0", "padding": "16px", "borderRadius": "12px", "marginBottom": "14px"}, children=[
                    html.Label(f"Ćwiczenie #{idx+1}:", style={"fontWeight": "800", "fontSize": "13px", "color": "#0284c7"}),
                    dcc.Input(id={'type': 'edit-ex-name', 'id': r['id']}, type="text", value=r['exercise_name'], style={"width": "100%", "marginBottom": "8px"}),
                    
                    html.Div(style={"display": "grid", "gridTemplateColumns": "1.2fr 1fr 1fr 1fr", "gap": "10px"}, children=[
                        html.Div([
                            html.Label("Obciążenie:", style={"fontSize": "11px"}),
                            dcc.Dropdown(
                                id={'type': 'edit-ex-loadtype', 'id': r['id']},
                                options=LOAD_TYPE_OPTIONS,
                                value=current_load_type,
                                clearable=False
                            )
                        ]),
                        html.Div([
                            html.Label("Serie:", style={"fontSize": "11px"}),
                            dcc.Input(id={'type': 'edit-ex-sets', 'id': r['id']}, type="number", value=r['target_sets'])
                        ]),
                        html.Div([
                            html.Label("Cel Powtórzeń:", style={"fontSize": "11px"}),
                            dcc.Input(id={'type': 'edit-ex-reps', 'id': r['id']}, type="text", value=r['target_reps'])
                        ]),
                        html.Div([
                            html.Label("Domyślny Ciężar:", style={"fontSize": "11px"}),
                            dcc.Input(id={'type': 'edit-ex-weight', 'id': r['id']}, type="number", value=r.get('default_weight_kg', 0), step=0.5)
                        ]),
                    ])
                ])
            )
            
        return html.Div([
            html.Label("Nazwa Planu:"),
            dcc.Input(id="edit-plan-name-input", type="text", value=plan_name, style={"width": "100%", "marginBottom": "18px"}),
            html.Div(ex_inputs),
            html.Button("💾 Zapisz Zmiany w Planie", id="btn-save-edited-plan", n_clicks=0, style={"width": "100%", "padding": "14px", "backgroundColor": "#0284c7", "color": "white", "border": "none", "borderRadius": "10px", "fontWeight": "800", "fontSize": "15px", "cursor": "pointer"}),
            html.Div(id="edit-plan-save-msg", style={"marginTop": "12px", "textAlign": "center", "fontWeight": "bold"})
        ])
    else:
        return html.Div([
            html.Label("Nazwa Nowego Planu:"),
            dcc.Input(id="new-plan-name-input", type="text", placeholder="np. FBW Hantle B", style={"marginBottom": "16px", "width": "100%"}),
            html.Div(id="new-plan-exercises-list", children=[]),
            html.Button("+ Dodaj Kolejne Ćwiczenie do Planu", id="btn-add-exercise-field", n_clicks=0, style={"width": "100%", "padding": "10px", "backgroundColor": "#e0f2fe", "color": "#0369a1", "border": "1px dashed #0284c7", "borderRadius": "8px", "fontWeight": "700", "marginBottom": "20px", "cursor": "pointer"}),
            html.Button("💾 Stwórz i Zapisz Nowy Plan", id="btn-create-plan-save", n_clicks=0, style={"width": "100%", "padding": "14px", "backgroundColor": "#10b981", "color": "white", "border": "none", "borderRadius": "10px", "fontWeight": "800", "fontSize": "15px", "cursor": "pointer"}),
            html.Div(id="new-plan-save-msg", style={"marginTop": "12px", "textAlign": "center", "fontWeight": "bold"})
        ])

@callback(
    Output("edit-plan-save-msg", "children"),
    Input("btn-save-edited-plan", "n_clicks"),
    State("fit-edit-select-plan", "value"),
    State("edit-plan-name-input", "value"),
    State({'type': 'edit-ex-name', 'id': ALL}, 'value'),
    State({'type': 'edit-ex-loadtype', 'id': ALL}, 'value'),
    State({'type': 'edit-ex-sets', 'id': ALL}, 'value'),
    State({'type': 'edit-ex-reps', 'id': ALL}, 'value'),
    State({'type': 'edit-ex-weight', 'id': ALL}, 'value'),
    State({'type': 'edit-ex-name', 'id': ALL}, 'id'),
    prevent_initial_call=True
)
def save_edited_plan(n_clicks, plan_id, new_plan_name, ex_names, ex_loadtypes, ex_sets, ex_reps, ex_weights, ex_ids):
    if n_clicks > 0 and plan_id:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            if new_plan_name:
                cursor.execute("UPDATE fit_plans SET plan_name = ? WHERE id = ?", (new_plan_name, plan_id))
            
            for i, item in enumerate(ex_ids):
                ex_db_id = item['id']
                cursor.execute('''
                    UPDATE fit_plan_exercises 
                    SET exercise_name = ?, load_type = ?, target_sets = ?, target_reps = ?, default_weight_kg = ?
                    WHERE id = ?
                ''', (ex_names[i], ex_loadtypes[i] or 'Ciężar (kg)', int(ex_sets[i] or 4), str(ex_reps[i] or '8-12'), float(ex_weights[i] or 0), ex_db_id))
                
            conn.commit()
            conn.close()
            set_props("fit-url-refresh", {"href": "/fit-hero"})
            return html.Span(" Zaktualizowano plan!", style={"color": "#10b981"})
        except Exception as e:
            return html.Span(f" Błąd: {str(e)}", style={"color": "#ef4444"})
    return ""

@callback(
    Output("new-plan-exercises-list", "children"),
    Input("btn-add-exercise-field", "n_clicks"),
    State("new-plan-exercises-list", "children"),
    prevent_initial_call=False
)
def add_exercise_input_fields(n_clicks, existing_children):
    if existing_children is None:
        existing_children = []
    idx = len(existing_children) + 1
    new_field = html.Div(style={"backgroundColor": "#f8fafc", "border": "1px solid #e2e8f0", "padding": "16px", "borderRadius": "12px", "marginBottom": "14px"}, children=[
        html.Span(f"Ćwiczenie #{idx}", style={"fontWeight": "800", "fontSize": "13px", "color": "#475569"}),
        dcc.Input(id={'type': 'new-ex-name', 'index': idx}, type="text", placeholder="Nazwa ćwiczenia", style={"width": "100%", "marginTop": "6px", "marginBottom": "8px"}),
        
        html.Div(style={"display": "grid", "gridTemplateColumns": "1.2fr 1fr 1fr 1fr", "gap": "10px"}, children=[
            html.Div([
                html.Label("Obciążenie:", style={"fontSize": "11px"}),
                dcc.Dropdown(
                    id={'type': 'new-ex-loadtype', 'index': idx},
                    options=LOAD_TYPE_OPTIONS,
                    value='Ciężar (kg)',
                    clearable=False
                )
            ]),
            html.Div([
                html.Label("Serie:", style={"fontSize": "11px"}),
                dcc.Input(id={'type': 'new-ex-sets', 'index': idx}, type="number", value=4)
            ]),
            html.Div([
                html.Label("Cel Powtórzeń:", style={"fontSize": "11px"}),
                dcc.Input(id={'type': 'new-ex-reps', 'index': idx}, type="text", value="8-12")
            ]),
            html.Div([
                html.Label("Domyślny Ciężar:", style={"fontSize": "11px"}),
                dcc.Input(id={'type': 'new-ex-weight', 'index': idx}, type="number", placeholder="kg", step=0.5)
            ]),
        ])
    ])
    existing_children.append(new_field)
    return existing_children

@callback(
    Output("new-plan-save-msg", "children"),
    Input("btn-create-plan-save", "n_clicks"),
    State("new-plan-name-input", "value"),
    State({'type': 'new-ex-name', 'index': ALL}, 'value'),
    State({'type': 'new-ex-loadtype', 'index': ALL}, 'value'),
    State({'type': 'new-ex-sets', 'index': ALL}, 'value'),
    State({'type': 'new-ex-reps', 'index': ALL}, 'value'),
    State({'type': 'new-ex-weight', 'index': ALL}, 'value'),
    prevent_initial_call=True
)
def save_new_plan(n_clicks, plan_name, ex_names, ex_loadtypes, ex_sets, ex_reps, ex_weights):
    if n_clicks > 0 and plan_name:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO fit_plans (plan_name) VALUES (?)", (plan_name,))
            plan_id = cursor.lastrowid
            
            for i, name in enumerate(ex_names):
                if name:
                    cursor.execute('''
                        INSERT INTO fit_plan_exercises (plan_id, exercise_name, load_type, target_sets, target_reps, default_weight_kg)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (plan_id, name, ex_loadtypes[i] or 'Ciężar (kg)', int(ex_sets[i] or 4), str(ex_reps[i] or "8-12"), float(ex_weights[i] or 0)))
            
            conn.commit()
            conn.close()
            set_props("fit-url-refresh", {"href": "/fit-hero"})
            return html.Span(" Stworzono nowy plan!", style={"color": "#10b981"})
        except Exception as e:
            return html.Span(f" Błąd: {str(e)}", style={"color": "#ef4444"})
    return ""

@callback(
    Output("fit-live-exercises-container", "children"),
    Input("fit-select-live-plan", "value")
)
def render_live_workout_plan(plan_id):
    if not plan_id:
        return html.P("Wybierz plan treningowy z listy powyżej.", style={"color": "#64748b"})
    
    df_ex = get_plan_exercises(plan_id)
    if df_ex.empty:
        return html.P("Ten plan nie ma jeszcze przypisanych ćwiczeń.", style={"color": "#64748b"})
    
    exercises_ui = []
    for idx, row in df_ex.iterrows():
        ex_id = row['id']
        ex_name = row['exercise_name']
        target_sets = row['target_sets']
        target_reps = row['target_reps']
        load_type = row.get('load_type') or 'Ciężar (kg)'
        default_weight = row.get('default_weight_kg', 0)
        
        if load_type == 'Masa ciała':
            load_info = "⚖️ Masa ciała"
        elif load_type == 'Guma oporowa':
            load_info = f"🎗️ Guma oporowa ({default_weight}kg)" if default_weight > 0 else "🎗️ Guma oporowa"
        else:
            load_info = f"🏋️ Ciężar: {default_weight}kg" if default_weight > 0 else "🏋️ Ciężar (kg)"

        sets_inputs = []
        for s in range(1, target_sets + 1):
            sets_inputs.append(
                html.Div(style={"display": "flex", "gap": "12px", "alignItems": "center", "marginBottom": "10px"}, children=[
                    html.Span(f"Seria {s}:", style={"fontWeight": "700", "fontSize": "14px", "width": "65px", "color": "#334155"}),
                    dcc.Input(
                        id={'type': 'fit-reps-input', 'ex_id': ex_id, 'set': s},
                        type="number",
                        placeholder=f"Powtórzenia (Cel: {target_reps})",
                        step=1,
                        style={"flex": "1", "padding": "10px 14px", "fontSize": "14px", "borderRadius": "8px", "border": "1px solid #cbd5e1"}
                    ),
                    html.Div(style={"display": "flex", "alignItems": "center", "gap": "4px"}, children=[
                        dcc.RadioItems(
                            id={'type': 'fit-rpe-input', 'ex_id': ex_id, 'set': s},
                            options=RPE_OPTIONS,
                            value=None,
                            inline=True,
                            className="rating-bubbles"
                        )
                    ])
                ])
            )
            
        exercises_ui.append(
            html.Div(style={"backgroundColor": "#f8fafc", "border": "1px solid #e2e8f0", "borderRadius": "12px", "padding": "20px", "marginBottom": "20px"}, children=[
                html.Div(style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "14px"}, children=[
                    html.H4(f"🏋️ {ex_name}", style={"margin": 0, "color": "#0284c7", "fontSize": "16px", "fontWeight": "800"}),
                    html.Span(f"{load_info} | Serie: {target_sets} | Cel: {target_reps}", style={"fontSize": "13px", "color": "#475569", "fontWeight": "700", "backgroundColor": "#e2e8f0", "padding": "4px 10px", "borderRadius": "6px"})
                ]),
                html.Div(sets_inputs)
            ])
        )
        
    summary_box = html.Div(style={"backgroundColor": "#f1f5f9", "border": "1px solid #cbd5e1", "borderRadius": "12px", "padding": "20px", "marginBottom": "20px"}, children=[
        html.H4("📊 Samoocena Zmęczenia po Treningu", style={"marginTop": 0, "marginBottom": "12px", "color": "#0f172a"}),
        html.Div(style={"display": "flex", "flexDirection": "column", "gap": "14px"}, children=[
            html.Div(style={"display": "flex", "alignItems": "center", "gap": "12px"}, children=[
                html.Label("Samopoczucie:", style={"fontWeight": "600", "fontSize": "13px", "minWidth": "130px"}),
                dcc.RadioItems(
                    id="fit-session-fatigue",
                    options=FATIGUE_OPTIONS,
                    value=None,
                    inline=True,
                    className="rating-bubbles fatigue-bubbles"
                )
            ]),
            html.Div(style={"display": "flex", "alignItems": "center", "gap": "12px"}, children=[
                html.Label("Komentarz:", style={"fontWeight": "600", "fontSize": "13px", "minWidth": "130px"}),
                dcc.Input(id="fit-session-notes", type="text", placeholder="np. Ogromny zapas siły, pompa, czuć moc...", style={"flex": "1", "padding": "9px 12px"})
            ])
        ])
    ])
    
    exercises_ui.append(summary_box)
    exercises_ui.append(
        html.Div([
            html.Button("💾 Zapisz Wykonany Trening", id="btn-save-live-workout", n_clicks=0, style={"width": "100%", "padding": "16px", "backgroundColor": "#10b981", "color": "white", "border": "none", "borderRadius": "10px", "fontWeight": "800", "fontSize": "16px", "cursor": "pointer", "boxShadow": "0 4px 12px rgba(16, 185, 129, 0.25)"}),
            html.Div(id="live-workout-save-msg", style={"marginTop": "14px", "textAlign": "center", "fontWeight": "bold"})
        ])
    )
    return html.Div(exercises_ui)

@callback(
    Output("live-workout-save-msg", "children"),
    Output({'type': 'fit-reps-input', 'ex_id': ALL, 'set': ALL}, 'value'),
    Output({'type': 'fit-rpe-input', 'ex_id': ALL, 'set': ALL}, 'value'),
    Output("fit-session-fatigue", "value"),
    Output("fit-session-notes", "value"),
    Input("btn-save-live-workout", "n_clicks"),
    State("fit-select-live-plan", "value"),
    State({'type': 'fit-reps-input', 'ex_id': ALL, 'set': ALL}, 'value'),
    State({'type': 'fit-rpe-input', 'ex_id': ALL, 'set': ALL}, 'value'),
    State({'type': 'fit-reps-input', 'ex_id': ALL, 'set': ALL}, 'id'),
    State("fit-session-fatigue", "value"),
    State("fit-session-notes", "value"),
    prevent_initial_call=True
)
def save_live_workout(n_clicks, plan_id, reps, rpes, ids, fatigue, overall_notes):
    empty_reps = [None] * len(reps)
    empty_rpes = [None] * len(rpes)
    
    if not n_clicks or n_clicks == 0:
        return "", reps, rpes, fatigue, overall_notes
        
    if not plan_id or not ids:
        return html.Span(" Wybierz plan treningowy przed zapisem!", style={"color": "#ef4444"}), reps, rpes, fatigue, overall_notes

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT plan_name FROM fit_plans WHERE id = ?", (plan_id,))
        plan_row = cursor.fetchone()
        plan_name = plan_row[0] if plan_row else "Inny Plan"
        today_str = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        saved_count = 0
        total_possible_sets = len(ids)
        
        for i, input_id in enumerate(ids):
            r = reps[i] if i < len(reps) else None
            rpe = rpes[i] if i < len(rpes) else None
            ex_id = input_id['ex_id']
            set_num = input_id['set']
            
            if r is not None and str(r).strip() != "" and float(r) > 0:
                cursor.execute("SELECT exercise_name, default_weight_kg FROM fit_plan_exercises WHERE id = ?", (ex_id,))
                ex_row = cursor.fetchone()
                ex_name = ex_row[0] if ex_row else "Ćwiczenie"
                weight_val = float(ex_row[1]) if (ex_row and ex_row[1]) else 0.0
                
                cursor.execute('''
                    INSERT INTO fit_workout_logs (workout_date, plan_name, exercise_name, set_number, weight_kg, reps, rpe_score, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (today_str, plan_name, ex_name, set_num, weight_val, int(r), int(rpe) if rpe else None, ''))
                saved_count += 1
                
        if saved_count > 0:
            completion_pct = round((saved_count / total_possible_sets) * 100, 1)
            
            cursor.execute('''
                INSERT INTO fit_workout_sessions (workout_date, plan_name, completion_pct, fatigue_score, overall_notes)
                VALUES (?, ?, ?, ?, ?)
            ''', (today_str, plan_name, completion_pct, fatigue if fatigue else None, overall_notes or ''))
            
            conn.commit()
            conn.close()
            
            msg = html.Span(f" Zapisano trening! Wykonano {completion_pct}% zaplanowanych serii ({saved_count}/{total_possible_sets}). Formularz zresetowany.", style={"color": "#10b981"})
            return msg, empty_reps, empty_rpes, None, ""
        else:
            conn.close()
            return html.Span(" Wpisz liczbę powtórzeń w przynajmniej jednej serii przed zapisem!", style={"color": "#ef4444"}), reps, rpes, fatigue, overall_notes
            
    except Exception as e:
        return html.Span(f" Błąd zapisu w bazie: {str(e)}", style={"color": "#ef4444"}), reps, rpes, fatigue, overall_notes

def clean_num(val):
    if val is None or val == "":
        return None
    try:
        return float(str(val).replace(',', '.'))
    except ValueError:
        return None

@callback(
    Output("fit-save-msg", "children"),
    Input("btn-fit-save-body", "n_clicks"),
    State("fit-input-date", "date"),
    State("fit-input-time", "value"),
    State("fit-input-weight", "value"),
    State("fit-input-bf", "value"),
    State("fit-input-muscle-kg", "value"),
    State("fit-input-muscle-pct", "value"),
    State("fit-input-protein-pct", "value"),
    State("fit-input-skeletal-kg", "value"),
    State("fit-input-water-pct", "value"),
    State("fit-input-bmr", "value"),
    State("fit-input-lbm", "value"),
    State("fit-input-biceps", "value"),
    State("fit-input-forearm", "value"),
    State("fit-input-chest", "value"),
    State("fit-input-waist", "value"),
    State("fit-input-hips", "value"),
    State("fit-input-thigh", "value"),
    State("fit-input-calf", "value"),
    State("fit-input-notes", "value"),
    prevent_initial_call=True
)
def save_body_params(n_clicks, date_val, time_val, weight, bf, muscle_kg, muscle_pct, protein_pct, skeletal_kg, water_pct, bmr, lbm, biceps, forearm, chest, waist, hips, thigh, calf, notes):
    if n_clicks > 0 and date_val:
        w_num = clean_num(weight)
        waist_num = clean_num(waist)
        
        if w_num is None and waist_num is None:
            return html.Span(" Uzupełnij przynajmniej wagę lub obwód pasa!", style={"color": "#ef4444"})

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO fit_body_params 
                (entry_date, entry_time, weight_kg, body_fat_pct, muscle_mass_kg, muscle_pct, protein_pct, skeletal_muscle_kg, water_pct, bmr_kcal, lbm_kg, biceps_cm, forearm_cm, chest_cm, waist_cm, hips_cm, thigh_cm, calf_cm, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                str(date_val), time_val or datetime.now().strftime('%H:%M'),
                w_num, clean_num(bf), clean_num(muscle_kg), clean_num(muscle_pct), clean_num(protein_pct),
                clean_num(skeletal_kg), clean_num(water_pct), clean_num(bmr), clean_num(lbm),
                clean_num(biceps), clean_num(forearm), clean_num(chest), waist_num, clean_num(hips),
                clean_num(thigh), clean_num(calf), notes or ''
            ))
            conn.commit()
            conn.close()
            set_props("fit-url-refresh", {"href": "/fit-hero"})
            return html.Span(" Zapisano!", style={"color": "#10b981"})
        except Exception as e:
            return html.Span(f" Błąd zapisu: {str(e)}", style={"color": "#ef4444"})
    return ""