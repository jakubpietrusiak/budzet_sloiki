import dash
from dash import html, dcc, Input, Output, State, callback, set_props, ALL
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
from database import get_db_connection

dash.register_page(__name__, path='/cele', name='Cele i Nawyki')

DEFAULT_CATEGORY_STYLES = {
    'Osobowość': {'bg': '#f3e8ff', 'color': '#7e22ce', 'border': '#d8b4fe', 'icon': '👤'},
    'Zdrowie fizyczne': {'bg': '#dcfce7', 'color': '#15803d', 'border': '#86efac', 'icon': '🏋️'},
    'Rozwój osobisty': {'bg': '#e0f2fe', 'color': '#0369a1', 'border': '#7dd3fc', 'icon': '🧠'},
    'Praca': {'bg': '#ffedd5', 'color': '#c2410c', 'border': '#fdba74', 'icon': '💼'}
}

def get_db_categories():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM goals_categories")
    if cursor.fetchone()[0] == 0:
        default_cats = ['Osobowość', 'Zdrowie fizyczne', 'Rozwój osobisty', 'Praca']
        for c in default_cats:
            cursor.execute("INSERT OR IGNORE INTO goals_categories (name) VALUES (?)", (c,))
        conn.commit()
    
    cat_df = pd.read_sql_query("SELECT name FROM goals_categories", conn)
    conn.close()
    return cat_df['name'].tolist() if not cat_df.empty else ['Osobowość', 'Zdrowie fizyczne', 'Rozwój osobisty', 'Praca']

TIME_HORIZONS = [
    {'label': '📅 Dzienne', 'value': 'dzienne'},
    {'label': '🗓️ Tygodniowe', 'value': 'tygodniowe'},
    {'label': '📆 Miesięczne', 'value': 'miesięczne'},
    {'label': '📊 Kwartalne', 'value': 'kwartalne'},
    {'label': '🎯 Roczne', 'value': 'roczne'}
]

PL_DAYS = ['Pon', 'Wt', 'Śr', 'Czw', 'Pt', 'Sob', 'Niedz']

def get_current_week_dates():
    today = datetime.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    return [start_of_week + timedelta(days=i) for i in range(7)]

def is_project_current(start_date_str, horizon):
    """Sprawdza, czy projekt miesięczny/kwartalny/roczny należy do bieżącego okresu."""
    if not start_date_str:
        return True
    try:
        start_dt = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    except Exception:
        return True
        
    today = datetime.now().date()
    
    if horizon == 'miesięczne':
        return start_dt.year == today.year and start_dt.month == today.month
        
    elif horizon == 'kwartalne':
        start_q = (start_dt.month - 1) // 3 + 1
        current_q = (today.month - 1) // 3 + 1
        return start_dt.year == today.year and start_q == current_q
        
    elif horizon == 'roczne':
        return start_dt.year == today.year
        
    return True

def get_fit_hero_card_style(pct):
    score_val = max(1, min(10, round(pct / 10)))
    
    if pct >= 90:
        label = "Znakomicie"
        bg, border, text = "#f0fdf4", "#10b981", "#047857"
    elif pct >= 75:
        label = "Bardzo dobrze"
        bg, border, text = "#f7fee7", "#84cc16", "#4d7c0f"
    elif pct >= 50:
        label = "Stabilnie"
        bg, border, text = "#fefce8", "#facc15", "#ca8a04"
    elif pct >= 25:
        label = "Do poprawy"
        bg, border, text = "#fff7ed", "#f97316", "#c2410c"
    else:
        label = "Wymaga uwagi"
        bg, border, text = "#fef2f2", "#ef4444", "#b91c1c"
        
    return {"bg": bg, "border": border, "text": text, "label": f"Score {score_val}/10 — {label}"}

layout = html.Div(style={"maxWidth": "1200px", "margin": "0 auto", "paddingBottom": "40px"}, children=[
    dcc.Location(id="goals-url-refresh", refresh=True),
    dcc.Store(id="trigger-goals-reload", data=0),
    
    html.Div(style={"display": "flex", "alignItems": "center", "gap": "12px", "marginBottom": "20px"}, children=[
        html.H2("🎯 Moduł Cele i Nasycenie — Panel Główny", style={"margin": "0", "color": "#0f172a", "fontWeight": "800", "fontSize": "24px"})
    ]),
    
    dcc.Tabs(id="tabs-goals", value="tab-odhaczanie", style={"fontWeight": "bold"}, children=[
        dcc.Tab(label="📋 Odhaczanie Live", value="tab-odhaczanie", style={"padding": "12px"}),
        dcc.Tab(label="📊 Statystyki & Podsumowanie", value="tab-statystyki", style={"padding": "12px"}),
        dcc.Tab(label="➕ Dodaj / Zarządzaj Celami", value="tab-zarzadzanie", style={"padding": "12px"}),
    ]),
    
    html.Div(id="tab-goals-content", style={"marginTop": "20px"})
])

@callback(
    Output("tab-goals-content", "children"),
    Input("tabs-goals", "value"),
    Input("trigger-goals-reload", "data")
)
def render_goals_tab(tab, reload_data):
    conn = get_db_connection()
    categories = get_db_categories()
    
    if tab == "tab-odhaczanie":
        week_dates = get_current_week_dates()
        today_str = datetime.now().strftime('%Y-%m-%d')
        
        header_cols = [html.Div("Cel / Nawyk", style={"fontWeight": "800", "fontSize": "15px", "color": "#1e293b"})]
        for idx, d in enumerate(week_dates):
            d_str = d.strftime('%Y-%m-%d')
            is_today = d_str == today_str
            header_cols.append(
                html.Div(style={
                    "textAlign": "center", 
                    "padding": "6px", 
                    "borderRadius": "8px",
                    "backgroundColor": "#0284c7" if is_today else "transparent",
                    "color": "white" if is_today else "#334155"
                }, children=[
                    html.Div(PL_DAYS[idx], style={"fontWeight": "800", "fontSize": "14px"}),
                    html.Div(d.strftime('%d.%m'), style={"fontSize": "11px", "opacity": "0.9"})
                ])
            )
        header_cols.append(html.Div("Postęp", style={"textAlign": "right", "fontWeight": "800", "fontSize": "15px", "color": "#1e293b"}))
        
        header_row = html.Div(
            style={
                "display": "grid", 
                "gridTemplateColumns": "2.2fr repeat(7, 48px) 1.2fr", 
                "gap": "10px", 
                "alignItems": "center", 
                "padding": "14px 18px", 
                "backgroundColor": "#f1f5f9", 
                "borderRadius": "12px", 
                "marginBottom": "14px",
                "border": "1px solid #cbd5e1"
            }, 
            children=header_cols
        )
        
        df_daily = pd.read_sql_query("SELECT * FROM goals_def WHERE horizon IN ('dzienne', 'tygodniowe') AND is_active = 1", conn)
        df_projects = pd.read_sql_query("SELECT * FROM goals_def WHERE horizon IN ('miesięczne', 'kwartalne', 'roczne') AND is_active = 1", conn)
        
        grid_rows = [header_row]
        for _, row in df_daily.iterrows():
            g_id = row['id']
            title = row['title']
            cat = row['category']
            horizon = row['horizon']
            target_freq = row['target_frequency'] or 1
            start_date_str = row.get('start_date') or '2026-01-01'
            
            cat_style = DEFAULT_CATEGORY_STYLES.get(cat, {'bg': '#f1f5f9', 'color': '#334155', 'border': '#cbd5e1', 'icon': '📌'})
            
            dates_str = [d.strftime('%Y-%m-%d') for d in week_dates]
            logs_df = pd.read_sql_query(f"SELECT log_date, status FROM goals_daily_logs WHERE goal_id = {g_id} AND log_date IN ({','.join(['?']*7)})", conn, params=dates_str)
            logs_dict = dict(zip(logs_df['log_date'], logs_df['status'])) if not logs_df.empty else {}
            
            check_buttons = []
            checked_count = 0
            valid_days_count = 0
            
            for d in week_dates:
                d_str = d.strftime('%Y-%m-%d')
                is_active_day = d_str >= start_date_str and d_str <= today_str
                if is_active_day:
                    valid_days_count += 1
                
                is_checked = logs_dict.get(d_str, 0) == 1
                if is_checked and d_str >= start_date_str: 
                    checked_count += 1
                
                check_buttons.append(
                    html.Button(
                        "✓" if is_checked else "",
                        id={'type': 'btn-toggle-day', 'goal_id': g_id, 'date': d_str},
                        n_clicks=0,
                        style={
                            "width": "48px", "height": "46px", "borderRadius": "10px",
                            "border": "2px solid #10b981" if is_checked else "1px solid #cbd5e1",
                            "backgroundColor": "#10b981" if is_checked else "#ffffff",
                            "color": "white" if is_checked else "transparent",
                            "fontWeight": "900", "fontSize": "18px", "cursor": "pointer",
                            "boxShadow": "0 2px 4px rgba(0,0,0,0.05)" if is_checked else "none"
                        }
                    )
                )
            
            if horizon == 'tygodniowe':
                pct = min(100, round((checked_count / target_freq) * 100)) if target_freq > 0 else 0
            else:
                pct = round((checked_count / valid_days_count) * 100) if valid_days_count > 0 else 0
            
            grid_rows.append(
                html.Div(style={
                    "display": "grid", 
                    "gridTemplateColumns": "2.2fr repeat(7, 48px) 1.2fr", 
                    "gap": "10px", 
                    "alignItems": "center", 
                    "marginBottom": "12px", 
                    "backgroundColor": "white", 
                    "padding": "16px 18px", 
                    "borderRadius": "14px", 
                    "border": f"2px solid {cat_style['border']}",
                    "boxShadow": "0 4px 6px rgba(0,0,0,0.03)"
                }, children=[
                    html.Div([
                        html.Span(f"{cat_style['icon']} {cat}", style={
                            "backgroundColor": cat_style['bg'], 
                            "color": cat_style['color'], 
                            "fontSize": "12px", 
                            "fontWeight": "800", 
                            "padding": "4px 10px", 
                            "borderRadius": "6px",
                            "display": "inline-block",
                            "marginBottom": "6px"
                        }),
                        html.Div(title, style={"fontWeight": "800", "fontSize": "16px", "color": "#0f172a"}),
                        html.Div(f"Cel: {target_freq}x / tydzień" if horizon == 'tygodniowe' else f"Cel: Codziennie", style={"fontSize": "13px", "color": "#475569", "fontWeight": "600"})
                    ]),
                    *check_buttons,
                    html.Div(style={"textAlign": "right"}, children=[
                        html.Span(f"{pct}%", style={"fontWeight": "900", "fontSize": "18px", "color": "#10b981" if pct >= 100 else "#0284c7"}),
                        html.Div(f"{checked_count}/{target_freq}" if horizon == 'tygodniowe' else f"{checked_count}/{valid_days_count} dni", style={"fontSize": "13px", "color": "#475569", "fontWeight": "700"})
                    ])
                ])
            )

        project_cards = []
        for _, row in df_projects.iterrows():
            g_id = row['id']
            title = row['title']
            cat = row['category']
            horizon = row['horizon']
            start_date_str = row.get('start_date')
            
            # DYNAMICZNE FILTROWANIE — POKAZUJEMY TYLKO PROJEKTY Z BIEŻĄCEGO OKRESU
            if not is_project_current(start_date_str, horizon):
                continue

            cat_style = DEFAULT_CATEGORY_STYLES.get(cat, {'bg': '#f1f5f9', 'color': '#334155', 'border': '#cbd5e1', 'icon': '📌'})
            
            prog_df = pd.read_sql_query(f"SELECT progress_pct FROM goals_project_progress WHERE goal_id = {g_id} ORDER BY id DESC LIMIT 1", conn)
            curr_pct = prog_df.iloc[0]['progress_pct'] if not prog_df.empty else 0
            
            project_cards.append(
                html.Div(style={"backgroundColor": "white", "padding": "20px", "borderRadius": "14px", "border": f"2px solid {cat_style['border']}", "marginBottom": "14px", "boxShadow": "0 4px 6px rgba(0,0,0,0.03)"}, children=[
                    html.Div(style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "12px"}, children=[
                        html.Div([
                            html.Span(f"{cat_style['icon']} {cat} • {horizon.capitalize()}", style={"backgroundColor": cat_style['bg'], "color": cat_style['color'], "fontSize": "12px", "fontWeight": "800", "padding": "4px 10px", "borderRadius": "6px", "marginRight": "10px"}),
                            html.Span(title, style={"fontWeight": "800", "fontSize": "17px", "color": "#0f172a"})
                        ]),
                        html.Span(f"{curr_pct}%", style={"fontWeight": "900", "fontSize": "18px", "color": "#0284c7"})
                    ]),
                    dcc.Slider(
                        id={'type': 'slider-project-progress', 'goal_id': g_id},
                        min=0, max=100, step=10, value=curr_pct,
                        marks={i: {"label": f"{i}%", "style": {"fontSize": "13px", "fontWeight": "bold"}} for i in range(0, 101, 20)}
                    )
                ])
            )

        conn.close()
        return html.Div([
            html.H3("🗓️ Tygodniowy Kalendarz Odhaczania (0-1)", style={"color": "#0f172a", "fontSize": "18px", "marginBottom": "16px", "fontWeight": "800"}),
            html.Div(grid_rows),
            html.H3("🎚️ Aktywne Projekty (Bieżący Miesiąc / Kwartał / Rok)", style={"color": "#0f172a", "fontSize": "18px", "marginTop": "32px", "marginBottom": "16px", "fontWeight": "800"}),
            html.Div(project_cards if project_cards else [html.P("Brak aktywnych projektów dla bieżącego okresu.", style={"color": "#64748b", "fontSize": "15px"})])
        ])

    elif tab == "tab-statystyki":
        week_dates = get_current_week_dates()
        today_date = datetime.now().date()
        today_str = today_date.strftime('%Y-%m-%d')
        
        # 1. Cele Dzienne
        df_daily_def = pd.read_sql_query("SELECT * FROM goals_def WHERE horizon = 'dzienne' AND is_active = 1", conn)
        daily_pcts = []
        for _, row in df_daily_def.iterrows():
            g_id = row['id']
            start_date_str = row.get('start_date') or '2026-01-01'
            valid_week_days = [d for d in week_dates if d.strftime('%Y-%m-%d') >= start_date_str and d.strftime('%Y-%m-%d') <= today_str]
            if not valid_week_days:
                continue
            v_strs = [d.strftime('%Y-%m-%d') for d in valid_week_days]
            logs_df = pd.read_sql_query(f"SELECT status FROM goals_daily_logs WHERE goal_id = {g_id} AND log_date IN ({','.join(['?']*len(v_strs))}) AND status = 1", conn, params=v_strs)
            done = len(logs_df)
            daily_pcts.append((done / len(valid_week_days)) * 100)
        score_dzienne = round(sum(daily_pcts) / len(daily_pcts)) if daily_pcts else 0

        # 2. Cele Tygodniowe
        df_weekly_def = pd.read_sql_query("SELECT * FROM goals_def WHERE horizon = 'tygodniowe' AND is_active = 1", conn)
        weekly_pcts = []
        for _, row in df_weekly_def.iterrows():
            g_id = row['id']
            target_freq = row['target_frequency'] or 1
            start_date_str = row.get('start_date') or '2026-01-01'
            valid_week_days = [d for d in week_dates if d.strftime('%Y-%m-%d') >= start_date_str and d.strftime('%Y-%m-%d') <= today_str]
            if not valid_week_days:
                continue
            v_strs = [d.strftime('%Y-%m-%d') for d in valid_week_days]
            logs_df = pd.read_sql_query(f"SELECT status FROM goals_daily_logs WHERE goal_id = {g_id} AND log_date IN ({','.join(['?']*len(v_strs))}) AND status = 1", conn, params=v_strs)
            done = len(logs_df)
            total_possible = len([d for d in week_dates if d.strftime('%Y-%m-%d') <= today_str])
            adjusted_target = max(1, round(target_freq * (len(valid_week_days) / max(1, total_possible))))
            w_pct = min(100, round((done / adjusted_target) * 100))
            weekly_pcts.append(w_pct)
        score_tygodniowe_raw = round(sum(weekly_pcts) / len(weekly_pcts)) if weekly_pcts else 0
        score_tygodniowe = round((score_dzienne * 0.5) + (score_tygodniowe_raw * 0.5))

        # 3. Cele Miesięczne (ZOBOWIĄZANIA HISTORII — BIERZE WSZYSTKIE REKORDY)
        df_m_def = pd.read_sql_query("SELECT * FROM goals_def WHERE horizon = 'miesięczne' AND is_active = 1", conn)
        m_slider_vals = []
        for _, row in df_m_def.iterrows():
            prog_df = pd.read_sql_query(f"SELECT progress_pct FROM goals_project_progress WHERE goal_id = {row['id']} ORDER BY id DESC LIMIT 1", conn)
            m_slider_vals.append(prog_df.iloc[0]['progress_pct'] if not prog_df.empty else 0)
        score_miesieczne_suwaki = round(sum(m_slider_vals) / len(m_slider_vals)) if m_slider_vals else 0
        score_miesieczne = round((score_tygodniowe * 0.5) + (score_miesieczne_suwaki * 0.5))

        # 4. Cele Kwartalne
        df_q_def = pd.read_sql_query("SELECT * FROM goals_def WHERE horizon = 'kwartalne' AND is_active = 1", conn)
        q_slider_vals = []
        for _, row in df_q_def.iterrows():
            prog_df = pd.read_sql_query(f"SELECT progress_pct FROM goals_project_progress WHERE goal_id = {row['id']} ORDER BY id DESC LIMIT 1", conn)
            q_slider_vals.append(prog_df.iloc[0]['progress_pct'] if not prog_df.empty else 0)
        score_kwartalne_suwaki = round(sum(q_slider_vals) / len(q_slider_vals)) if q_slider_vals else 0
        score_kwartalne = round((score_miesieczne * 0.5) + (score_kwartalne_suwaki * 0.5))

        # 5. Cel Roczny
        df_y_def = pd.read_sql_query("SELECT * FROM goals_def WHERE horizon = 'roczne' AND is_active = 1", conn)
        y_slider_vals = []
        for _, row in df_y_def.iterrows():
            prog_df = pd.read_sql_query(f"SELECT progress_pct FROM goals_project_progress WHERE goal_id = {row['id']} ORDER BY id DESC LIMIT 1", conn)
            y_slider_vals.append(prog_df.iloc[0]['progress_pct'] if not prog_df.empty else 0)
        score_roczny_suwaki = round(sum(y_slider_vals) / len(y_slider_vals)) if y_slider_vals else score_kwartalne
        score_roczny = round((score_kwartalne + score_roczny_suwaki) / 2)

        c_dzienne = get_fit_hero_card_style(score_dzienne)
        c_tygodniowe = get_fit_hero_card_style(score_tygodniowe)
        c_miesieczne = get_fit_hero_card_style(score_miesieczne)
        c_kwartalne = get_fit_hero_card_style(score_kwartalne)
        c_roczny = get_fit_hero_card_style(score_roczny)

        # 6. MAPA OSOBOWOŚCI
        cat_scores = []
        for cat in categories:
            all_cat_goals = pd.read_sql_query("SELECT * FROM goals_def WHERE category = ? AND is_active = 1", conn, params=(cat,))
            if all_cat_goals.empty:
                cat_scores.append(0)
                continue
            
            cat_goal_scores = []
            for _, r in all_cat_goals.iterrows():
                h = r['horizon']
                g_id = r['id']
                start_dt = datetime.strptime(r.get('start_date') or '2026-01-01', '%Y-%m-%d').date()
                days_since_start = max(1, (today_date - start_dt).days + 1)
                
                if h == 'dzienne':
                    logs = pd.read_sql_query("SELECT COUNT(*) FROM goals_daily_logs WHERE goal_id = ? AND status = 1", conn, params=(g_id,))
                    done_days = logs.iloc[0,0] if not logs.empty else 0
                    eff = min(100, round((done_days / days_since_start) * 100))
                    cat_goal_scores.append(eff)
                    
                elif h == 'tygodniowe':
                    logs = pd.read_sql_query("SELECT COUNT(*) FROM goals_daily_logs WHERE goal_id = ? AND status = 1", conn, params=(g_id,))
                    done_count = logs.iloc[0,0] if not logs.empty else 0
                    target_f = r['target_frequency'] or 1
                    weeks_passed = max(1, days_since_start / 7.0)
                    expected = target_f * weeks_passed
                    eff = min(100, round((done_count / expected) * 100)) if expected > 0 else 0
                    cat_goal_scores.append(eff)
                    
                elif h in ['miesięczne', 'kwartalne', 'roczne']:
                    p_df = pd.read_sql_query("SELECT progress_pct FROM goals_project_progress WHERE goal_id = ? ORDER BY id DESC LIMIT 1", conn, params=(g_id,))
                    pct = p_df.iloc[0]['progress_pct'] if not p_df.empty else 0
                    cat_goal_scores.append(pct)
            
            cat_scores.append(round(sum(cat_goal_scores) / len(cat_goal_scores)) if cat_goal_scores else 0)

        df_radar = pd.DataFrame({'Category': categories, 'Score': cat_scores})
        fig_radar = px.line_polar(df_radar, r='Score', theta='Category', line_close=True, title="🧠 Mapa Osobowości (Bieżący Balans Życiowy)")
        fig_radar.update_traces(fill='toself')
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(range=[0, 100], dtick=20)),
            font=dict(size=14),
            height=500
        )

        conn.close()
        return html.Div([
            html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr 1fr 1fr 1fr", "gap": "12px", "marginBottom": "20px"}, children=[
                html.Div(style={
                    "backgroundColor": c_dzienne["bg"], "padding": "16px", "borderRadius": "12px", 
                    "border": f"1px solid #e2e8f0", "borderLeft": f"6px solid {c_dzienne['border']}",
                    "boxShadow": "0 2px 4px rgba(0,0,0,0.02)"
                }, children=[
                    html.Div("Dzienne", style={"fontSize": "13px", "color": "#64748b", "fontWeight": "700"}), 
                    html.H2(f"{score_dzienne}%", style={"margin": "6px 0", "color": "#0f172a", "fontSize": "26px", "fontWeight": "800"}),
                    html.Div(c_dzienne["label"], style={"fontSize": "12px", "color": c_dzienne["text"], "fontWeight": "700"})
                ]),
                html.Div(style={
                    "backgroundColor": c_tygodniowe["bg"], "padding": "16px", "borderRadius": "12px", 
                    "border": f"1px solid #e2e8f0", "borderLeft": f"6px solid {c_tygodniowe['border']}",
                    "boxShadow": "0 2px 4px rgba(0,0,0,0.02)"
                }, children=[
                    html.Div("Tygodniowe", style={"fontSize": "13px", "color": "#64748b", "fontWeight": "700"}), 
                    html.H2(f"{score_tygodniowe}%", style={"margin": "6px 0", "color": "#0f172a", "fontSize": "26px", "fontWeight": "800"}),
                    html.Div(c_tygodniowe["label"], style={"fontSize": "12px", "color": c_tygodniowe["text"], "fontWeight": "700"})
                ]),
                html.Div(style={
                    "backgroundColor": c_miesieczne["bg"], "padding": "16px", "borderRadius": "12px", 
                    "border": f"1px solid #e2e8f0", "borderLeft": f"6px solid {c_miesieczne['border']}",
                    "boxShadow": "0 2px 4px rgba(0,0,0,0.02)"
                }, children=[
                    html.Div("Miesięczne", style={"fontSize": "13px", "color": "#64748b", "fontWeight": "700"}), 
                    html.H2(f"{score_miesieczne}%", style={"margin": "6px 0", "color": "#0f172a", "fontSize": "26px", "fontWeight": "800"}),
                    html.Div(c_miesieczne["label"], style={"fontSize": "12px", "color": c_miesieczne["text"], "fontWeight": "700"})
                ]),
                html.Div(style={
                    "backgroundColor": c_kwartalne["bg"], "padding": "16px", "borderRadius": "12px", 
                    "border": f"1px solid #e2e8f0", "borderLeft": f"6px solid {c_kwartalne['border']}",
                    "boxShadow": "0 2px 4px rgba(0,0,0,0.02)"
                }, children=[
                    html.Div("Kwartalne", style={"fontSize": "13px", "color": "#64748b", "fontWeight": "700"}), 
                    html.H2(f"{score_kwartalne}%", style={"margin": "6px 0", "color": "#0f172a", "fontSize": "26px", "fontWeight": "800"}),
                    html.Div(c_kwartalne["label"], style={"fontSize": "12px", "color": c_kwartalne["text"], "fontWeight": "700"})
                ]),
                html.Div(style={
                    "backgroundColor": c_roczny["bg"], "padding": "16px", "borderRadius": "12px", 
                    "border": f"1px solid #e2e8f0", "borderLeft": f"6px solid {c_roczny['border']}",
                    "boxShadow": "0 2px 4px rgba(0,0,0,0.02)"
                }, children=[
                    html.Div("Roczny / Ogólny", style={"fontSize": "13px", "color": "#64748b", "fontWeight": "700"}), 
                    html.H2(f"{score_roczny}%", style={"margin": "6px 0", "color": "#0f172a", "fontSize": "26px", "fontWeight": "800"}),
                    html.Div(c_roczny["label"], style={"fontSize": "12px", "color": c_roczny["text"], "fontWeight": "700"})
                ]),
            ]),
            html.Div(style={"backgroundColor": "white", "padding": "20px", "borderRadius": "14px", "border": "1px solid #e2e8f0"}, children=[dcc.Graph(figure=fig_radar)])
        ])

    elif tab == "tab-zarzadzanie":
        conn.close()
        return html.Div(style={"backgroundColor": "white", "padding": "28px", "borderRadius": "14px", "border": "1px solid #e2e8f0"}, children=[
            html.H3("➕ Dodaj Nowy Cel / Nawyk", style={"marginTop": 0, "color": "#0f172a", "fontSize": "20px", "fontWeight": "800"}),
            html.Div(style={"display": "grid", "gridTemplateColumns": "2fr 1.2fr 1fr", "gap": "15px", "marginBottom": "15px"}, children=[
                html.Div([html.Label("Tytuł:", style={"fontWeight": "700"}), dcc.Input(id="add-goal-title", type="text", placeholder="np. Trening Siłowy / SQL / Medytacja", style={"width": "100%", "padding": "10px", "fontSize": "15px"})]),
                html.Div([html.Label("Kategoria:", style={"fontWeight": "700"}), dcc.Dropdown(id="add-goal-category", options=[{'label': c, 'value': c} for c in categories], value=categories[0] if categories else "Inne")]),
                html.Div([html.Label("Horyzont:", style={"fontWeight": "700"}), dcc.Dropdown(id="add-goal-horizon", options=TIME_HORIZONS, value="dzienne")]),
            ]),
            html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "15px", "marginBottom": "24px"}, children=[
                html.Div([html.Label("Wymagana częstotliwość (tylko tygodniowe):", style={"fontWeight": "700"}), dcc.Input(id="add-goal-freq", type="number", value=1, min=1, max=7, style={"width": "100%", "padding": "10px", "fontSize": "15px"})]),
                html.Div([html.Label("Data Startu:", style={"fontWeight": "700"}), dcc.DatePickerSingle(id="add-goal-date", date=datetime.now().date())]),
            ]),
            html.Button("💾 Zapisz Nowy Cel", id="btn-save-new-goal", n_clicks=0, style={"width": "100%", "padding": "14px", "backgroundColor": "#10b981", "color": "white", "border": "none", "borderRadius": "10px", "fontWeight": "800", "fontSize": "16px", "cursor": "pointer"}),
            html.Div(id="save-goal-msg", style={"marginTop": "12px", "fontWeight": "bold", "textAlign": "center", "fontSize": "15px"}),
            
            html.Hr(style={"margin": "30px 0", "borderColor": "#e2e8f0"}),
            html.H3("📁 Zarządzaj Kategoriami", style={"color": "#0f172a", "fontSize": "18px", "fontWeight": "800"}),
            html.Div(style={"display": "grid", "gridTemplateColumns": "2fr 1fr", "gap": "15px", "alignItems": "flex-end"}, children=[
                html.Div([html.Label("Nowa kategoria:", style={"fontWeight": "700"}), dcc.Input(id="new-category-name", type="text", placeholder="np. Finanse / Rodzina", style={"width": "100%", "padding": "10px", "fontSize": "15px"})]),
                html.Button("➕ Dodaj Kategorię", id="btn-save-new-category", n_clicks=0, style={"padding": "12px", "backgroundColor": "#0284c7", "color": "white", "border": "none", "borderRadius": "10px", "fontWeight": "bold", "cursor": "pointer"})
            ]),
            html.Div(id="save-cat-msg", style={"marginTop": "10px", "fontWeight": "bold", "textAlign": "center"})
        ])

@callback(
    Output("trigger-goals-reload", "data"),
    Input({'type': 'btn-toggle-day', 'goal_id': ALL, 'date': ALL}, 'n_clicks'),
    State({'type': 'btn-toggle-day', 'goal_id': ALL, 'date': ALL}, 'id'),
    State("trigger-goals-reload", "data"),
    prevent_initial_call=True
)
def toggle_day_click(n_clicks_list, ids_list, current_trigger):
    ctx = dash.callback_context
    if not ctx.triggered or all(c == 0 for c in n_clicks_list):
        return dash.no_update
        
    trig_id = ctx.triggered[0]['prop_id'].split('.')[0]
    eval_id = eval(trig_id)
    g_id = eval_id['goal_id']
    d_str = eval_id['date']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM goals_daily_logs WHERE goal_id = ? AND log_date = ?", (g_id, d_str))
    row = cursor.fetchone()
    
    if row:
        new_status = 0 if row[0] == 1 else 1
        cursor.execute("UPDATE goals_daily_logs SET status = ? WHERE goal_id = ? AND log_date = ?", (new_status, g_id, d_str))
    else:
        cursor.execute("INSERT INTO goals_daily_logs (goal_id, log_date, status) VALUES (?, ?, 1)", (g_id, d_str))
        
    conn.commit()
    conn.close()
    return current_trigger + 1

@callback(
    Input({'type': 'slider-project-progress', 'goal_id': ALL}, 'value'),
    State({'type': 'slider-project-progress', 'goal_id': ALL}, 'id'),
    prevent_initial_call=True
)
def update_slider_progress(values, ids):
    ctx = dash.callback_context
    if not ctx.triggered:
        return
    trig_id = eval(ctx.triggered[0]['prop_id'].split('.')[0])
    g_id = trig_id['goal_id']
    val = ctx.triggered[0]['value']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO goals_project_progress (goal_id, progress_pct, updated_at) VALUES (?, ?, ?)", (g_id, val, datetime.now().strftime('%Y-%m-%d')))
    conn.commit()
    conn.close()

@callback(
    Output("save-goal-msg", "children"),
    Input("btn-save-new-goal", "n_clicks"),
    State("add-goal-title", "value"),
    State("add-goal-category", "value"),
    State("add-goal-horizon", "value"),
    State("add-goal-freq", "value"),
    State("add-goal-date", "date"),
    prevent_initial_call=True
)
def save_new_goal_def(n_clicks, title, category, horizon, freq, start_date):
    if n_clicks > 0 and title:
        w_type = 'frequency' if horizon == 'tygodniowe' else ('binary' if horizon == 'dzienne' else 'slider')
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO goals_def (title, category, horizon, weight_type, target_frequency, start_date, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        ''', (title, category, horizon, w_type, freq or 1, str(start_date)))
        conn.commit()
        conn.close()
        set_props("goals-url-refresh", {"href": "/cele"})
        return html.Span(" Stworzono nowy cel!", style={"color": "#10b981", "fontSize": "16px"})
    return ""

@callback(
    Output("save-cat-msg", "children"),
    Input("btn-save-new-category", "n_clicks"),
    State("new-category-name", "value"),
    prevent_initial_call=True
)
def save_new_category(n_clicks, cat_name):
    if n_clicks > 0 and cat_name:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO goals_categories (name) VALUES (?)", (cat_name.strip(),))
            conn.commit()
            conn.close()
            set_props("goals-url-refresh", {"href": "/cele"})
            return html.Span(" Dodano nową kategorię!", style={"color": "#10b981"})
        except Exception:
            return html.Span(" Taka kategoria już istnieje lub wystąpił błąd.", style={"color": "#ef4444"})
    return ""