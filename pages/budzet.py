import dash
from dash import html, dcc, dash_table, Input, Output, State, callback, set_props
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from database import get_db_connection, get_kategorie_df, get_transakcje_df

dash.register_page(__name__, path='/', name='Budżet Słoikowy')

COLOR_PALETTE = [
    "#0284c7", "#10b981", "#f59e0b", "#8b5cf6", 
    "#ec4899", "#06b6d4", "#84cc16", "#6366f1"
]

MONTHS_NAMES = {
    1: 'Styczeń', 2: 'Luty', 3: 'Marzec', 4: 'Kwiecień',
    5: 'Maj', 6: 'Czerwiec', 7: 'Lipiec', 8: 'Sierpień',
    9: 'Wrzesień', 10: 'Październik', 11: 'Listopad', 12: 'Grudzień'
}

def hex_to_rgba(hex_str, opacity=0.3):
    hex_str = hex_str.lstrip('#')
    r = int(hex_str[0:2], 16)
    g = int(hex_str[2:4], 16)
    b = int(hex_str[4:6], 16)
    return f"rgba({r}, {g}, {b}, {opacity})"

def get_available_years_and_months(trans_df):
    """Pomocnicza funkcja wyciągająca dostępne lata i miesiące z bazy."""
    if trans_df.empty:
        now = datetime.now()
        return [{'label': str(now.year), 'value': now.year}], {now.year: [{'label': MONTHS_NAMES[now.month], 'value': now.month}]}

    df = trans_df.copy()
    df['datetime'] = pd.to_datetime(df['data'])
    df['year'] = df['datetime'].dt.year
    df['month'] = df['datetime'].dt.month

    years = sorted(df['year'].unique().tolist(), reverse=True)
    year_options = [{'label': str(y), 'value': y} for y in years]

    months_by_year = {}
    for y in years:
        m_list = sorted(df[df['year'] == y]['month'].unique().tolist())
        months_by_year[y] = [{'label': MONTHS_NAMES[m], 'value': m} for m in m_list]

    return year_options, months_by_year

layout = html.Div([
    dcc.Location(id="budzet-url-refresh", refresh=True),
    html.H2("📊 Budżet Słoikowy", style={"marginBottom": "20px", "color": "#0f172a"}),
    
    dcc.Tabs(
        id="tabs-budzet",
        value="subtab-podsumowanie",
        className="custom-tabs-container",
        parent_className="custom-tabs-parent",
        children=[
            dcc.Tab(label="📊 Podsumowanie Główne", value="subtab-podsumowanie", className="custom-tab", selected_className="custom-tab--selected"),
            dcc.Tab(label="➕ Dodaj Transakcję", value="subtab-dodaj", className="custom-tab", selected_className="custom-tab--selected"),
            dcc.Tab(label="📜 Rejestr i Edycja", value="subtab-rejestr", className="custom-tab", selected_className="custom-tab--selected"),
            dcc.Tab(label="📥 Analiza Wpływów", value="subtab-wplywy", className="custom-tab", selected_className="custom-tab--selected"),
            dcc.Tab(label="📉 Analiza Wydatków", value="subtab-wykresy", className="custom-tab", selected_className="custom-tab--selected"),
            dcc.Tab(label="⚙️ Podkategorie Słoików", value="subtab-kategorie", className="custom-tab", selected_className="custom-tab--selected"),
        ]
    ),
    
    html.Div(id="tab-budzet-content", style={"marginTop": "20px"})
])

@callback(
    Output("tab-budzet-content", "children"),
    Input("tabs-budzet", "value")
)
def render_budzet_subtabs(tab):
    trans_df = get_transakcje_df()
    kategorie_df = get_kategorie_df()
    year_options, months_by_year = get_available_years_and_months(trans_df)
    
    default_year = year_options[0]['value'] if year_options else datetime.now().year
    default_month_opts = months_by_year.get(default_year, [{'label': MONTHS_NAMES[datetime.now().month], 'value': datetime.now().month}])
    default_month = default_month_opts[-1]['value'] if default_month_opts else datetime.now().month

    if tab == "subtab-podsumowanie":
        return html.Div([
            html.Div(style={"display": "flex", "gap": "15px", "alignItems": "center", "marginBottom": "20px", "backgroundColor": "white", "padding": "16px 20px", "borderRadius": "12px", "border": "1px solid #e2e8f0"}, children=[
                html.Span("🗓️ Wybierz Okres:", style={"fontWeight": "800", "color": "#0f172a", "fontSize": "15px"}),
                html.Div(style={"width": "120px"}, children=[
                    dcc.Dropdown(id="filter-year", options=year_options, value=default_year, clearable=False)
                ]),
                html.Div(style={"width": "160px"}, children=[
                    dcc.Dropdown(id="filter-month", options=default_month_opts, value=default_month, clearable=False)
                ]),
            ]),
            html.Div(id="summary-metrics-container")
        ])

    elif tab == "subtab-wplywy":
        return html.Div([
            html.Div(style={"display": "flex", "gap": "15px", "alignItems": "center", "marginBottom": "20px", "backgroundColor": "white", "padding": "16px 20px", "borderRadius": "12px", "border": "1px solid #e2e8f0"}, children=[
                html.Span("🗓️ Wybierz Okres Analizy:", style={"fontWeight": "800", "color": "#0f172a", "fontSize": "15px"}),
                html.Div(style={"width": "120px"}, children=[
                    dcc.Dropdown(id="wplywy-filter-year", options=year_options, value=default_year, clearable=False)
                ]),
                html.Div(style={"width": "160px"}, children=[
                    dcc.Dropdown(id="wplywy-filter-month", options=default_month_opts, value=default_month, clearable=False)
                ]),
            ]),
            html.Div(id="wplywy-analysis-container")
        ])

    elif tab == "subtab-wykresy":
        filter_options = [{'label': '📊 --- WSZYSTKIE WYDATKI ---', 'value': 'ALL'}]
        
        if not kategorie_df.empty:
            unique_sloiki = sorted(kategorie_df['sloik'].unique().tolist())
            for sloik in unique_sloiki:
                filter_options.append({'label': f"📁 SŁOIK: {sloik.upper()}", 'value': f"SLOIK:{sloik}"})
                podkats = sorted(kategorie_df[kategorie_df['sloik'] == sloik]['podkategoria'].unique().tolist())
                for p in podkats:
                    filter_options.append({'label': f"    └── 🔹 {p}", 'value': f"PODKAT:{p}"})

        return html.Div([
            html.Div(style={"display": "flex", "gap": "15px", "alignItems": "center", "marginBottom": "20px", "backgroundColor": "white", "padding": "16px 20px", "borderRadius": "12px", "border": "1px solid #e2e8f0"}, children=[
                html.Span("🗓️ Rok Analizy:", style={"fontWeight": "800", "color": "#0f172a", "fontSize": "15px"}),
                html.Div(style={"width": "120px"}, children=[
                    dcc.Dropdown(id="wydatki-filter-year", options=year_options, value=default_year, clearable=False)
                ]),
            ]),
            
            html.Div(id="wydatki-sankey-container"),
            
            html.Div(style={"marginTop": "25px", "backgroundColor": "white", "padding": "24px", "borderRadius": "16px", "border": "1px solid #e2e8f0"}, children=[
                html.Div(style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "20px"}, children=[
                    html.H3("🎯 Analiza Szczegółowa z Linią Średniej", style={"margin": 0, "color": "#0f172a", "fontWeight": "800"}),
                    html.Div(style={"width": "360px"}, children=[
                        dcc.Dropdown(id="wydatki-filter-item", options=filter_options, value='ALL', clearable=False)
                    ])
                ]),
                html.Div(id="wydatki-detail-chart-container")
            ])
        ])

    elif tab == "subtab-dodaj":
        unique_sloiki = sorted(kategorie_df['sloik'].unique().tolist()) if not kategorie_df.empty else []
        default_sloik = unique_sloiki[0] if unique_sloiki else None
        zrodla = ['GRODNO (pracodawca)', 'Inna praca zarobkowa', 'Uznanie ze sprzedaży']

        return html.Div([
            html.Div(style={"maxWidth": "520px", "margin": "20px auto", "backgroundColor": "white", "padding": "32px", "borderRadius": "16px", "boxShadow": "0 4px 20px rgba(0,0,0,0.04)", "border": "1px solid #e2e8f0"}, children=[
                html.H3("Dodaj Nową Transakcję", style={"marginTop": "0", "marginBottom": "22px", "color": "#0f172a", "fontWeight": "800", "fontSize": "20px"}),
                
                html.Label("Data:"),
                dcc.DatePickerSingle(id="input-data", date=datetime.now().date(), display_format="YYYY-MM-DD", style={"width": "100%", "marginBottom": "16px"}),
                
                html.Label("Typ:"),
                dcc.Dropdown(id="input-typ", options=[{'label': 'Wydatek (-)', 'value': 'WYDATEK'}, {'label': 'Wpływ (+)', 'value': 'WPLYW'}], value='WYDATEK', clearable=False, style={"marginBottom": "16px"}),
                
                html.Div(id="box-zrodlo", children=[
                    html.Label("Źródło wpływu:"),
                    dcc.Dropdown(id="input-zrodlo", options=[{'label': z, 'value': z} for z in zrodla], value=zrodla[0], clearable=False, style={"marginBottom": "16px"})
                ]),

                html.Div(id="box-wydatek", children=[
                    html.Label("Słoik:"),
                    dcc.Dropdown(id="input-sloik", options=[{'label': s, 'value': s} for s in unique_sloiki], value=default_sloik, clearable=False, style={"marginBottom": "16px"}),
                    html.Label("Podkategoria:"),
                    dcc.Dropdown(id="input-podkategoria", options=[], value=None, clearable=False, style={"marginBottom": "16px"})
                ]),
                
                html.Label("Kwota (PLN):", style={"marginTop": "6px"}),
                dcc.Input(id="input-kwota", type="number", placeholder="0.00", step=0.01, style={"width": "100%", "padding": "12px 14px", "marginBottom": "16px", "boxSizing": "border-box", "borderRadius": "10px", "border": "1px solid #cbd5e1"}),
                
                html.Label("Komentarz:"),
                dcc.Input(id="input-komentarz", type="text", placeholder="np. Zakupy...", style={"width": "100%", "padding": "12px 14px", "marginBottom": "24px", "boxSizing": "border-box", "borderRadius": "10px", "border": "1px solid #cbd5e1"}),
                
                html.Button("Zapisz Transakcję", id="btn-zapisz-transakcje", n_clicks=0, style={"width": "100%", "padding": "14px", "backgroundColor": "#10b981", "color": "white", "border": "none", "borderRadius": "10px", "fontWeight": "800", "fontSize": "15px", "cursor": "pointer", "boxShadow": "0 4px 12px rgba(16, 185, 129, 0.25)"}),
                
                html.Div(id="form-output-msg", style={"marginTop": "16px", "fontWeight": "bold", "textAlign": "center"})
            ])
        ])

    elif tab == "subtab-rejestr":
        return html.Div([
            html.Div(style={"backgroundColor": "white", "padding": "24px", "borderRadius": "16px", "boxShadow": "0 4px 20px rgba(0,0,0,0.03)", "border": "1px solid #e2e8f0"}, children=[
                html.Div(style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "20px"}, children=[
                    html.H3("Pełny Rejestr Transakcji", style={"margin": 0, "color": "#0f172a", "fontWeight": "800"}),
                    html.Button("💾 Zapisz Zmiany w Tabeli", id="btn-zapisz-edycje-tabeli", n_clicks=0, style={"padding": "10px 18px", "backgroundColor": "#0284c7", "color": "white", "border": "none", "borderRadius": "8px", "cursor": "pointer", "fontWeight": "700"})
                ]),
                html.Div(id="table-output-msg", style={"marginBottom": "12px", "fontWeight": "bold"}),
                dash_table.DataTable(
                    id="datatable-transakcje",
                    data=trans_df.to_dict('records') if not trans_df.empty else [],
                    columns=[
                        {'name': 'ID', 'id': 'id', 'editable': False},
                        {'name': 'Data', 'id': 'data', 'editable': True},
                        {'name': 'Typ', 'id': 'typ', 'editable': True},
                        {'name': 'Słoik / Źródło', 'id': 'zrodlo_lub_sloik', 'editable': True},
                        {'name': 'Podkategoria', 'id': 'podkategoria', 'editable': True},
                        {'name': 'Kwota (PLN)', 'id': 'kwota', 'editable': True, 'type': 'numeric'},
                        {'name': 'Komentarz', 'id': 'komentarz', 'editable': True},
                    ],
                    editable=True,
                    row_deletable=True,
                    page_size=15,
                    sort_action="native",
                    filter_action="native",
                    style_cell={'textAlign': 'left', 'padding': '12px', 'fontFamily': "'Inter', sans-serif", 'fontSize': '14px'},
                    style_header={'backgroundColor': '#f8fafc', 'fontWeight': '800', 'color': '#475569', 'fontFamily': "'Plus Jakarta Sans', sans-serif"}
                )
            ])
        ])

    elif tab == "subtab-kategorie":
        return html.Div([
            html.Div(style={"maxWidth": "500px", "margin": "20px auto", "backgroundColor": "white", "padding": "30px", "borderRadius": "16px", "boxShadow": "0 4px 20px rgba(0,0,0,0.04)", "border": "1px solid #e2e8f0"}, children=[
                html.H3("Dodaj Podkategorię do Słoika", style={"marginTop": 0, "marginBottom": "20px", "color": "#0f172a", "fontWeight": "800"}),
                html.Label("Wybierz słoik:"),
                dcc.Dropdown(id="dropdown-sloik-dodaj", options=[{'label': s, 'value': s} for s in kategorie_df['sloik'].unique().tolist()] if not kategorie_df.empty else [], clearable=False, style={"marginBottom": "16px"}),
                html.Label("Nazwa nowej podkategorii:"),
                dcc.Input(id="input-nowa-podkat", type="text", placeholder="np. Serwis...", style={"width": "100%", "padding": "12px 14px", "marginBottom": "20px", "boxSizing": "border-box", "borderRadius": "10px", "border": "1px solid #cbd5e1"}),
                html.Button("Dodaj Podkategorię", id="btn-dodaj-kat", n_clicks=0, style={"width": "100%", "padding": "14px", "backgroundColor": "#0284c7", "color": "white", "border": "none", "borderRadius": "10px", "fontWeight": "700", "fontSize": "15px", "cursor": "pointer"}),
                html.Div(id="kat-output-msg", style={"marginTop": "15px", "fontWeight": "bold", "textAlign": "center"})
            ])
        ])

# 1. KASKADOWE REAGOWANIE FILTRÓW MIESIĘCY NA ZMIANĘ ROKU
@callback(
    Output("filter-month", "options"),
    Output("filter-month", "value"),
    Input("filter-year", "value")
)
def update_summary_month_dropdown(selected_year):
    trans_df = get_transakcje_df()
    _, months_by_year = get_available_years_and_months(trans_df)
    opts = months_by_year.get(selected_year, [])
    val = opts[-1]['value'] if opts else datetime.now().month
    return opts, val

@callback(
    Output("wplywy-filter-month", "options"),
    Output("wplywy-filter-month", "value"),
    Input("wplywy-filter-year", "value")
)
def update_wplywy_month_dropdown(selected_year):
    trans_df = get_transakcje_df()
    _, months_by_year = get_available_years_and_months(trans_df)
    opts = months_by_year.get(selected_year, [])
    val = opts[-1]['value'] if opts else datetime.now().month
    return opts, val

# 2. PRZELICZANIE PODSUMOWANIA GŁÓWNEGO
@callback(
    Output("summary-metrics-container", "children"),
    Input("filter-year", "value"),
    Input("filter-month", "value")
)
def update_summary_view(selected_year, selected_month):
    trans_df = get_transakcje_df()
    kategorie_df = get_kategorie_df()

    if not trans_df.empty:
        trans_df['datetime'] = pd.to_datetime(trans_df['data'])
        trans_df['year'] = trans_df['datetime'].dt.year
        trans_df['month'] = trans_df['datetime'].dt.month
    else:
        trans_df = pd.DataFrame(columns=['data', 'typ', 'zrodlo_lub_sloik', 'podkategoria', 'kwota', 'komentarz', 'datetime', 'year', 'month'])

    df_year = trans_df[trans_df['year'] == selected_year]
    year_wplywy = df_year[df_year['typ'] == 'WPLYW']['kwota'].sum() if not df_year.empty else 0.0
    year_wydatki = df_year[df_year['typ'] == 'WYDATEK']['kwota'].sum() if not df_year.empty else 0.0
    year_saldo = year_wplywy - year_wydatki

    df_month = df_year[df_year['month'] == selected_month]
    month_wplywy = df_month[df_month['typ'] == 'WPLYW']['kwota'].sum() if not df_month.empty else 0.0
    month_wydatki = df_month[df_month['typ'] == 'WYDATEK']['kwota'].sum() if not df_month.empty else 0.0
    month_saldo = month_wplywy - month_wydatki

    unique_sloiki = kategorie_df['sloik'].unique().tolist() if not kategorie_df.empty else []
    sloik_stats = []

    target_date_limit = datetime(selected_year, selected_month if selected_month else 1, 1)

    for sloik in unique_sloiki:
        proc_series = kategorie_df[kategorie_df['sloik'] == sloik]['procent']
        proc = proc_series.iloc[0] if not proc_series.empty else 0.0

        if not trans_df.empty:
            df_past = trans_df[trans_df['datetime'] < target_date_limit]
            past_wplywy = df_past[df_past['typ'] == 'WPLYW']['kwota'].sum()
            past_przypisane = past_wplywy * (proc / 100.0)
            past_wydano = df_past[(df_past['typ'] == 'WYDATEK') & (df_past['zrodlo_lub_sloik'] == sloik)]['kwota'].sum()
            bilans_przeniesiony = past_przypisane - past_wydano
        else:
            bilans_przeniesiony = 0.0

        nalezne_m = month_wplywy * (proc / 100.0)
        wydano_m = df_month[(df_month['typ'] == 'WYDATEK') & (df_month['zrodlo_lub_sloik'] == sloik)]['kwota'].sum() if not df_month.empty else 0.0
        dostepne_m = bilans_przeniesiony + nalezne_m - wydano_m

        sloik_stats.append({
            "Słoik": sloik,
            "Udział %": f"{proc:.1f}%".replace('.', ','),
            "Bilans Przeniesiony": f"{bilans_przeniesiony:,.2f} zł".replace(',', ' ').replace('.', ','),
            "Nowy Budżet (+": f"{nalezne_m:,.2f} zł".replace(',', ' ').replace('.', ','),
            "Wydano (-": f"{wydano_m:,.2f} zł".replace(',', ' ').replace('.', ','),
            "Pozostało / Dostępne": f"{dostepne_m:,.2f} zł".replace(',', ' ').replace('.', ','),
            "_zostalo_val": dostepne_m
        })

    display_df = pd.DataFrame(sloik_stats) if sloik_stats else pd.DataFrame()
    table_data = display_df.drop(columns=['_zostalo_val']).to_dict('records') if not display_df.empty else []
    table_columns = [{"name": i, "id": i} for i in display_df.columns if not i.startswith('_')] if not display_df.empty else []

    conditional_styles = [
        {'if': {'row_index': 'odd'}, 'backgroundColor': '#f8fafc'},
        {'if': {'column_id': 'Słoik'}, 'fontWeight': '700', 'textAlign': 'left', 'color': '#0f172a'},
        {'if': {'column_id': 'Pozostało / Dostępne'}, 'fontWeight': '800'},
    ]

    if not display_df.empty:
        for idx, row in display_df.iterrows():
            if row['_zostalo_val'] < 0:
                conditional_styles.append({
                    'if': {'row_index': idx, 'column_id': 'Pozostało / Dostępne'},
                    'color': '#ef4444',
                    'backgroundColor': '#fef2f2'
                })
            else:
                conditional_styles.append({
                    'if': {'row_index': idx, 'column_id': 'Pozostało / Dostępne'},
                    'color': '#10b981'
                })

    return html.Div([
        html.Div(style={"marginBottom": "20px"}, children=[
            html.H4(f"📈 Rozliczenie Narastająco w Roku {selected_year}", style={"margin": "0 0 10px 0", "color": "#475569", "fontSize": "14px", "fontWeight": "800", "textTransform": "uppercase"}),
            html.Div(style={"display": "flex", "gap": "20px"}, children=[
                html.Div(className="kpi-card green", children=[
                    html.Span(f"Wpływy {selected_year}", style={"color": "#64748b", "fontSize": "13px", "fontWeight": "bold"}),
                    html.H2(f"{year_wplywy:,.2f} zł".replace(',', ' ').replace('.', ','), style={"margin": "5px 0 0 0", "color": "#0f172a"})
                ]),
                html.Div(className="kpi-card red", children=[
                    html.Span(f"Wydatki {selected_year}", style={"color": "#64748b", "fontSize": "13px", "fontWeight": "bold"}),
                    html.H2(f"{year_wydatki:,.2f} zł".replace(',', ' ').replace('.', ','), style={"margin": "5px 0 0 0", "color": "#0f172a"})
                ]),
                html.Div(className="kpi-card blue", children=[
                    html.Span(f"Bilans Roczny {selected_year}", style={"color": "#64748b", "fontSize": "13px", "fontWeight": "bold"}),
                    html.H2(f"{year_saldo:,.2f} zł".replace(',', ' ').replace('.', ','), style={"margin": "5px 0 0 0", "color": "#10b981" if year_saldo >= 0 else "#ef4444"})
                ]),
            ])
        ]),

        html.Div(style={"marginBottom": "25px"}, children=[
            html.H4("📅 Bilans Wybranego Miesiąca", style={"margin": "0 0 10px 0", "color": "#0284c7", "fontSize": "14px", "fontWeight": "800", "textTransform": "uppercase"}),
            html.Div(style={"display": "flex", "gap": "20px"}, children=[
                html.Div(className="kpi-card green", children=[
                    html.Span("Wpływy w Miesiącu", style={"color": "#64748b", "fontSize": "13px", "fontWeight": "bold"}),
                    html.H2(f"{month_wplywy:,.2f} zł".replace(',', ' ').replace('.', ','), style={"margin": "5px 0 0 0", "color": "#0f172a"})
                ]),
                html.Div(className="kpi-card red", children=[
                    html.Span("Wydatki w Miesiącu", style={"color": "#64748b", "fontSize": "13px", "fontWeight": "bold"}),
                    html.H2(f"{month_wydatki:,.2f} zł".replace(',', ' ').replace('.', ','), style={"margin": "5px 0 0 0", "color": "#0f172a"})
                ]),
                html.Div(className="kpi-card blue", children=[
                    html.Span("Saldo Miesięczne", style={"color": "#64748b", "fontSize": "13px", "fontWeight": "bold"}),
                    html.H2(f"{month_saldo:,.2f} zł".replace(',', ' ').replace('.', ','), style={"margin": "5px 0 0 0", "color": "#10b981" if month_saldo >= 0 else "#ef4444"})
                ]),
            ])
        ]),

        html.Div(style={"backgroundColor": "white", "padding": "24px", "borderRadius": "16px", "boxShadow": "0 4px 20px rgba(0,0,0,0.03)", "border": "1px solid #e2e8f0"}, children=[
            html.H3("Stan Słoików w Wybranym Miesiącu (z uwzględnieniem historii)", style={"marginTop": 0, "marginBottom": "18px", "color": "#0f172a", "fontSize": "18px", "fontWeight": "800"}),
            dash_table.DataTable(
                data=table_data,
                columns=table_columns,
                style_cell={
                    'textAlign': 'center',
                    'padding': '14px 16px',
                    'fontFamily': "'Inter', sans-serif",
                    'fontSize': '14px',
                    'color': '#334155',
                    'border': 'none',
                    'borderBottom': '1px solid #f1f5f9'
                },
                style_header={
                    'backgroundColor': '#f8fafc',
                    'fontWeight': '800',
                    'color': '#475569',
                    'fontFamily': "'Plus Jakarta Sans', sans-serif",
                    'textTransform': 'uppercase',
                    'fontSize': '12px',
                    'letterSpacing': '0.5px',
                    'borderBottom': '2px solid #e2e8f0'
                },
                style_data_conditional=conditional_styles
            )
        ])
    ])

# 3. GENEROWANIE WIDOKU ANALIZY WPŁYWÓW
@callback(
    Output("wplywy-analysis-container", "children"),
    Input("wplywy-filter-year", "value"),
    Input("wplywy-filter-month", "value")
)
def update_wplywy_analysis(selected_year, selected_month):
    trans_df = get_transakcje_df()
    
    if trans_df.empty:
        return html.P("Brak danych o transakcjach w bazie.", style={"color": "#64748b", "fontSize": "15px"})

    trans_df['datetime'] = pd.to_datetime(trans_df['data'])
    trans_df['year'] = trans_df['datetime'].dt.year
    trans_df['month'] = trans_df['datetime'].dt.month

    df_wplywy = trans_df[trans_df['typ'] == 'WPLYW'].copy()

    if df_wplywy.empty:
        return html.P("Brak transakcji wpływowych w bazie.", style={"color": "#64748b", "fontSize": "15px"})

    df_wplywy_year = df_wplywy[df_wplywy['year'] == selected_year]
    df_wplywy_month = df_wplywy_year[df_wplywy_year['month'] == selected_month]

    sum_m = df_wplywy_month['kwota'].sum() if not df_wplywy_month.empty else 0.0
    sum_y = df_wplywy_year['kwota'].sum() if not df_wplywy_year.empty else 0.0
    
    active_months_count = df_wplywy_year['month'].nunique() if not df_wplywy_year.empty else 1
    avg_m = (sum_y / active_months_count) if active_months_count > 0 else 0.0

    kpi_cards = html.Div(style={"display": "flex", "gap": "20px", "marginBottom": "25px"}, children=[
        html.Div(className="kpi-card green", children=[
            html.Span("Wpływy w Miesiącu", style={"color": "#64748b", "fontSize": "13px", "fontWeight": "bold"}),
            html.H2(f"{sum_m:,.2f} zł".replace(',', ' ').replace('.', ','), style={"margin": "5px 0 0 0", "color": "#0f172a"})
        ]),
        html.Div(className="kpi-card blue", children=[
            html.Span(f"Średni Wpływ / Miesiąc ({selected_year})", style={"color": "#64748b", "fontSize": "13px", "fontWeight": "bold"}),
            html.H2(f"{avg_m:,.2f} zł".replace(',', ' ').replace('.', ','), style={"margin": "5px 0 0 0", "color": "#0f172a"})
        ]),
        html.Div(className="kpi-card green", children=[
            html.Span(f"Suma Wpływów ({selected_year})", style={"color": "#64748b", "fontSize": "13px", "fontWeight": "bold"}),
            html.H2(f"{sum_y:,.2f} zł".replace(',', ' ').replace('.', ','), style={"margin": "5px 0 0 0", "color": "#10b981"})
        ]),
    ])

    if not df_wplywy_month.empty:
        fig_month = px.pie(df_wplywy_month, names='zrodlo_lub_sloik', values='kwota', title=f'Struktura Wpływów w Miesiącu ({selected_month}/{selected_year})', hole=0.45)
        fig_month.update_layout(font_family="Inter", showlegend=True)
    else:
        fig_month = px.pie(title=f'Brak wpływów w miesiącu {selected_month}/{selected_year}')

    if not df_wplywy_year.empty:
        fig_year = px.pie(df_wplywy_year, names='zrodlo_lub_sloik', values='kwota', title=f'Struktura Wpływów w Całym Roku {selected_year}', hole=0.45)
        fig_year.update_layout(font_family="Inter", showlegend=True)
    else:
        fig_year = px.pie(title=f'Brak wpływów w roku {selected_year}')

    donuts_row = html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "20px", "marginBottom": "25px"}, children=[
        html.Div(style={"backgroundColor": "white", "padding": "20px", "borderRadius": "16px", "border": "1px solid #e2e8f0"}, children=[dcc.Graph(figure=fig_month)]),
        html.Div(style={"backgroundColor": "white", "padding": "20px", "borderRadius": "16px", "border": "1px solid #e2e8f0"}, children=[dcc.Graph(figure=fig_year)]),
    ])

    months_short = {1: 'Sty', 2: 'Lut', 3: 'Mar', 4: 'Kwi', 5: 'Maj', 6: 'Cze', 7: 'Lip', 8: 'Sie', 9: 'Wrz', 10: 'Paź', 11: 'Lis', 12: 'Gru'}
    
    if not df_wplywy_year.empty:
        df_grouped = df_wplywy_year.groupby(['month', 'zrodlo_lub_sloik'])['kwota'].sum().reset_index()
        df_grouped['Miesiąc'] = df_grouped['month'].map(months_short)
        
        fig_bar = px.bar(
            df_grouped, 
            x='Miesiąc', 
            y='kwota', 
            color='zrodlo_lub_sloik',
            title=f'Dynamika Wpływów Miesiąc po Miesiącu w Roku {selected_year}',
            labels={'kwota': 'Suma (PLN)', 'zrodlo_lub_sloik': 'Źródło'},
            text_auto='.2f'
        )
        fig_bar.update_layout(font_family="Inter", barmode='stack', xaxis={'categoryorder': 'array', 'categoryarray': list(months_short.values())})
    else:
        fig_bar = px.bar(title=f'Brak danych do wykresu rocznego dla {selected_year}')

    bar_row = html.Div(style={"backgroundColor": "white", "padding": "20px", "borderRadius": "16px", "border": "1px solid #e2e8f0"}, children=[dcc.Graph(figure=fig_bar)])

    return html.Div([kpi_cards, donuts_row, bar_row])

# 4. GENEROWANIE DYNAMICZNEGO WYKRESU SANKEYA DLA ANALYSIS WYDATKÓW
@callback(
    Output("wydatki-sankey-container", "children"),
    Input("wydatki-filter-year", "value")
)
def update_sankey_chart(selected_year):
    trans_df = get_transakcje_df()
    
    if trans_df.empty:
        return html.P("Brak transakcji w bazie.", style={"color": "#64748b"})

    trans_df['datetime'] = pd.to_datetime(trans_df['data'])
    trans_df['year'] = trans_df['datetime'].dt.year
    
    df_wydatki = trans_df[(trans_df['typ'] == 'WYDATEK') & (trans_df['year'] == selected_year)].copy()
    
    if df_wydatki.empty:
        return html.Div(style={"backgroundColor": "white", "padding": "24px", "borderRadius": "16px", "border": "1px solid #e2e8f0"}, children=[
            html.P(f"Brak zarejestrowanych wydatków w roku {selected_year}.", style={"color": "#64748b", "margin": 0})
        ])

    df_wydatki['podkategoria'] = df_wydatki['podkategoria'].fillna('Inne')
    
    grouped = df_wydatki.groupby(['zrodlo_lub_sloik', 'podkategoria'])['kwota'].sum().reset_index()
    
    sloiki = sorted(grouped['zrodlo_lub_sloik'].unique().tolist())
    podkategorie = sorted(grouped['podkategoria'].unique().tolist())
    
    sloik_colors = {s: COLOR_PALETTE[i % len(COLOR_PALETTE)] for i, s in enumerate(sloiki)}
    
    all_labels = sloiki + podkategorie
    label_indices = {label: i for i, label in enumerate(all_labels)}
    
    node_colors = [sloik_colors[label] if label in sloik_colors else "#94a3b8" for label in all_labels]
    
    sources = []
    targets = []
    values = []
    link_colors = []
    
    for _, row in grouped.iterrows():
        s_name = row['zrodlo_lub_sloik']
        sources.append(label_indices[s_name])
        targets.append(label_indices[row['podkategoria']])
        values.append(row['kwota'])
        link_colors.append(hex_to_rgba(sloik_colors[s_name], opacity=0.35))
    
    calculated_height = max(500, 300 + (len(podkategorie) * 22))

    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=18,
            thickness=20,
            line=dict(color="#0f172a", width=0.5),
            label=all_labels,
            color=node_colors
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color=link_colors
        )
    )])
    
    total_wydatki_year = df_wydatki['kwota'].sum()
    
    fig.update_layout(
        title_text=f"📊 Przepływ Wydatków: Słoiki ➔ Podkategorie (Suma: {total_wydatki_year:,.2f} zł w {selected_year} r.)",
        font_family="Inter",
        font_size=12,
        height=calculated_height
    )
    
    return html.Div(style={"backgroundColor": "white", "padding": "20px", "borderRadius": "16px", "border": "1px solid #e2e8f0"}, children=[dcc.Graph(figure=fig)])

# 5. GENEROWANIE SZCZEGÓŁOWEGO WYKRESU SŁUPKOWEGO DLA ANALIZY WYDATKÓW
@callback(
    Output("wydatki-detail-chart-container", "children"),
    Input("wydatki-filter-year", "value"),
    Input("wydatki-filter-item", "value")
)
def update_detail_expense_chart(selected_year, selected_item):
    trans_df = get_transakcje_df()
    
    if trans_df.empty:
        return html.P("Brak transakcji.", style={"color": "#64748b"})

    trans_df['datetime'] = pd.to_datetime(trans_df['data'])
    trans_df['year'] = trans_df['datetime'].dt.year
    trans_df['month'] = trans_df['datetime'].dt.month
    
    df_year_all = trans_df[trans_df['year'] == selected_year]
    
    if df_year_all.empty:
        active_months = [1]
    else:
        min_m = df_year_all['month'].min()
        now = datetime.now()
        max_m = now.month if selected_year == now.year else df_year_all['month'].max()
        active_months = list(range(min_m, max_m + 1)) if min_m <= max_m else [min_m]

    df_wydatki = trans_df[(trans_df['typ'] == 'WYDATEK') & (trans_df['year'] == selected_year)].copy()
    df_wydatki['podkategoria'] = df_wydatki['podkategoria'].fillna('Inne')

    if selected_item != 'ALL':
        if selected_item.startswith('SLOIK:'):
            sloik_name = selected_item.replace('SLOIK:', '')
            df_wydatki = df_wydatki[df_wydatki['zrodlo_lub_sloik'] == sloik_name]
            chart_title = f"Miesięczne Wydatki na Słoik: {sloik_name} ({selected_year})"
        elif selected_item.startswith('PODKAT:'):
            podkat_name = selected_item.replace('PODKAT:', '')
            df_wydatki = df_wydatki[df_wydatki['podkategoria'] == podkat_name]
            chart_title = f"Miesięczne Wydatki na Podkategorię: {podkat_name} ({selected_year})"
    else:
        chart_title = f"Łączne Miesięczne Wydatki ({selected_year})"

    months_short = {1: 'Sty', 2: 'Lut', 3: 'Mar', 4: 'Kwi', 5: 'Maj', 6: 'Cze', 7: 'Lip', 8: 'Sie', 9: 'Wrz', 10: 'Paź', 11: 'Lis', 12: 'Gru'}
    
    all_months_df = pd.DataFrame({'month': list(months_short.keys())})
    
    if not df_wydatki.empty:
        monthly_sum = df_wydatki.groupby('month')['kwota'].sum().reset_index()
        merged = pd.merge(all_months_df, monthly_sum, on='month', how='left').fillna(0.0)
    else:
        merged = all_months_df.copy()
        merged['kwota'] = 0.0

    merged['Miesiąc'] = merged['month'].map(months_short)
    
    active_sum = merged[merged['month'].isin(active_months)]['kwota'].sum()
    avg_value = active_sum / len(active_months) if active_months else 0.0

    fig = px.bar(
        merged, 
        x='Miesiąc', 
        y='kwota', 
        title=chart_title,
        labels={'kwota': 'Kwota (PLN)'},
        text_auto='.2f'
    )
    fig.update_traces(marker_color='#0284c7')
    
    fig.add_hline(
        y=avg_value, 
        line_dash="dash", 
        line_color="#ef4444", 
        line_width=2,
        annotation_text=f"Średnia ({len(active_months)} aktywnych mieś.): {avg_value:,.2f} zł", 
        annotation_position="top right"
    )

    fig.update_layout(
        font_family="Inter", 
        xaxis={'categoryorder': 'array', 'categoryarray': list(months_short.values())},
        height=400
    )

    return dcc.Graph(figure=fig)

# 6. STEROWANIE WIDOCZNOŚCIĄ PÓL FORMULARZA
@callback(
    Output("box-zrodlo", "style"),
    Output("box-wydatek", "style"),
    Input("input-typ", "value")
)
def toggle_form_visibility(typ):
    if typ == 'WPLYW':
        return {"display": "block"}, {"display": "none"}
    return {"display": "none"}, {"display": "block"}

# 7. FILTROWANIE PODKATEGORII DLA WYBRANEGO SŁOIKA
@callback(
    Output("input-podkategoria", "options"),
    Output("input-podkategoria", "value"),
    Input("input-sloik", "value")
)
def filter_podkategorie_by_sloik(selected_sloik):
    if not selected_sloik:
        return [], None
    kategorie_df = get_kategorie_df()
    if kategorie_df.empty:
        return [], None
        
    filtered = kategorie_df[kategorie_df['sloik'] == selected_sloik]['podkategoria'].unique().tolist()
    options = [{'label': p, 'value': p} for p in filtered]
    default_val = filtered[0] if filtered else None
    
    return options, default_val

# 8. BEZPIECZNY ZAPIS TRANSAKCJI (BEZ PRZEŁADOWANIA STRONY)
@callback(
    Output("form-output-msg", "children"),
    Output("input-kwota", "value"),
    Output("input-komentarz", "value"),
    Input("btn-zapisz-transakcje", "n_clicks"),
    State("input-data", "date"),
    State("input-typ", "value"),
    State("input-zrodlo", "value"),
    State("input-sloik", "value"),
    State("input-podkategoria", "value"),
    State("input-kwota", "value"),
    State("input-komentarz", "value"),
    prevent_initial_call=True
)
def save_transaction(n_clicks, date_val, typ, zrodlo, sloik, podkat, kwota, komentarz):
    if n_clicks > 0 and date_val and kwota and float(kwota) > 0:
        zrodlo_lub_sloik = zrodlo if typ == 'WPLYW' else sloik
        podkategoria_val = None if typ == 'WPLYW' else podkat

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO transakcje (data, typ, zrodlo_lub_sloik, podkategoria, kwota, komentarz)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (str(date_val), typ, zrodlo_lub_sloik, podkategoria_val, float(kwota), komentarz or ''))
        conn.commit()
        conn.close()
        
        msg = f"✅ Zapisano: {float(kwota):,.2f} zł ({zrodlo_lub_sloik})".replace('.', ',')
        # Zwracamy komunikat oraz czyścimy pola kwota i komentarz
        return html.Span(msg, style={"color": "#10b981", "fontWeight": "bold"}), None, ""
        
    return html.Span("⚠️ Uzupełnij poprawnie kwotę i datę!", style={"color": "#ef4444", "fontWeight": "bold"}), dash.no_update, dash.no_update

# 9. EDYCJA TABELI REJESTRU
@callback(
    Output("table-output-msg", "children"),
    Input("btn-zapisz-edycje-tabeli", "n_clicks"),
    State("datatable-transakcje", "data"),
    prevent_initial_call=True
)
def save_table_edits(n_clicks, table_data):
    if n_clicks > 0 and table_data is not None:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transakcje")
        for row in table_data:
            cursor.execute('''
                INSERT INTO transakcje (id, data, typ, zrodlo_lub_sloik, podkategoria, kwota, komentarz)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (row['id'], row['data'], row['typ'], row['zrodlo_lub_sloik'], row['podkategoria'], float(row['kwota']), row['komentarz']))
        conn.commit()
        conn.close()
        set_props("budzet-url-refresh", {"href": "/"})
        return html.Span(" Zmiany w bazie zostały zapisane!", style={"color": "#10b981"})
    return ""

# 10. DODAWANIE NOWEJ PODKATEGORII
@callback(
    Output("kat-output-msg", "children"),
    Input("btn-dodaj-kat", "n_clicks"),
    State("dropdown-sloik-dodaj", "value"),
    State("input-nowa-podkat", "value"),
    prevent_initial_call=True
)
def add_new_podkategoria(n_clicks, sloik, nowa_podkat):
    if n_clicks > 0 and sloik and nowa_podkat:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT procent FROM kategorie WHERE sloik = ? LIMIT 1", (sloik,))
        row = cursor.fetchone()
        procent_val = row[0] if row else 0.0
        
        cursor.execute('''
            INSERT INTO kategorie (sloik, procent, podkategoria)
            VALUES (?, ?, ?)
        ''', (sloik, procent_val, nowa_podkat.strip()))
        conn.commit()
        conn.close()
        
        set_props("budzet-url-refresh", {"href": "/"})
        return html.Span(" Dodano podkategorię!", style={"color": "#10b981"})
    return html.Span(" Wpisz nazwę podkategorii!", style={"color": "#ef4444"})