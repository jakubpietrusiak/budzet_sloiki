import io
import dash
from dash import html, dcc, dash_table, Input, Output, State, callback
import pandas as pd
from datetime import datetime
import plotly.express as px
from database import get_db_connection

dash.register_page(__name__, path='/auto', name='Mercedes W211')

def get_auto_df():
    conn = get_db_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM auto_serwis ORDER BY data DESC, przebieg DESC", conn)
    except Exception:
        df = pd.DataFrame(columns=['id', 'data', 'przebieg', 'typ', 'podkategoria', 'koszt', 'litry', 'cena_l', 'komentarz'])
    conn.close()
    return df

layout = html.Div([
    html.H2("🚗 Garaż: Mercedes-Benz W211", style={"marginBottom": "20px", "color": "#0f172a"}),
    
    dcc.Tabs(id="tabs-auto", value="auto-podsumowanie", children=[
        dcc.Tab(label="📊 Podsumowanie Kosztów", value="auto-podsumowanie"),
        dcc.Tab(label="➕ Dodaj Wpisy / Tankowanie", value="auto-dodaj"),
        dcc.Tab(label="📜 Rejestr Serwisowy", value="auto-rejestr"),
        dcc.Tab(label="📁 Import Fuelio (CSV)", value="auto-import"),
    ]),
    
    html.Div(id="tab-auto-content", style={"marginTop": "20px"})
])

@callback(
    Output("tab-auto-content", "children"),
    Input("tabs-auto", "value")
)
def render_auto_subtabs(tab):
    df_auto = get_auto_df()
    
    if tab == "auto-podsumowanie":
        if df_auto.empty:
            return html.P("Brak wpisów w historii pojazdu.")
            
        total_koszt = df_auto['koszt'].sum()
        koszt_paliwo = df_auto[df_auto['typ'] == 'TANKOWANIE']['koszt'].sum()
        koszt_serwis = df_auto[df_auto['typ'] == 'SERWIS']['koszt'].sum()
        max_przebieg = df_auto['przebieg'].max() if not df_auto.empty else 0
        
        return html.Div([
            html.Div(style={"display": "flex", "gap": "20px", "marginBottom": "25px"}, children=[
                html.Div(className="kpi-card blue", children=[
                    html.Span("Aktualny Przebieg", style={"color": "#64748b", "fontSize": "12px", "fontWeight": "bold"}),
                    html.H2(f"{max_przebieg:,} km".replace(',', ' '), style={"margin": "5px 0 0 0", "color": "#0f172a"})
                ]),
                html.Div(className="kpi-card red", children=[
                    html.Span("Suma Łącznych Wydatków", style={"color": "#64748b", "fontSize": "12px", "fontWeight": "bold"}),
                    html.H2(f"{total_koszt:,.2f} PLN".replace(',', ' ').replace('.', ','), style={"margin": "5px 0 0 0", "color": "#ef4444"})
                ]),
                html.Div(className="kpi-card green", children=[
                    html.Span("Koszty Paliwa (LPG / PB)", style={"color": "#64748b", "fontSize": "12px", "fontWeight": "bold"}),
                    html.H2(f"{koszt_paliwo:,.2f} PLN".replace(',', ' ').replace('.', ','), style={"margin": "5px 0 0 0", "color": "#10b981"})
                ]),
                html.Div(className="kpi-card blue", children=[
                    html.Span("Koszty Serwisowe i Części", style={"color": "#64748b", "fontSize": "12px", "fontWeight": "bold"}),
                    html.H2(f"{koszt_serwis:,.2f} PLN".replace(',', ' ').replace('.', ','), style={"margin": "5px 0 0 0", "color": "#0284c7"})
                ]),
            ]),
            html.Div(style={"backgroundColor": "white", "padding": "20px", "borderRadius": "10px"}, children=[
                html.H3("Struktura Wydatków na Pojazd", style={"marginTop": 0, "color": "#0f172a"}),
                dcc.Graph(figure=px.pie(df_auto, names='typ', values='koszt', title='Wydatki: Tankowanie vs Serwis'))
            ])
        ])

    elif tab == "auto-dodaj":
        return html.Div([
            html.Div(style={"maxWidth": "500px", "margin": "20px auto", "backgroundColor": "white", "padding": "30px", "borderRadius": "12px", "boxShadow": "0 4px 15px rgba(0,0,0,0.05)"}, children=[
                html.H3("Dodaj Wpis Eksploatacyjny", style={"marginTop": 0, "color": "#0f172a"}),
                html.Label("Data:"),
                dcc.DatePickerSingle(id="auto-input-data", date=datetime.now().date(), display_format="YYYY-MM-DD", style={"width": "100%", "marginBottom": "15px"}),
                html.Label("Aktualny Przebieg (km):"),
                dcc.Input(id="auto-input-przebieg", type="number", placeholder="np. 285000", style={"width": "100%", "padding": "10px", "marginBottom": "15px", "boxSizing": "border-box"}),
                html.Label("Kategoria:"),
                dcc.Dropdown(id="auto-input-typ", options=[{'label': 'Tankowanie', 'value': 'TANKOWANIE'}, {'label': 'Serwis / Naprawa', 'value': 'SERWIS'}, {'label': 'Części / Detailing', 'value': 'CZĘŚCI'}], value='TANKOWANIE', style={"marginBottom": "15px"}),
                html.Label("Koszt Całkowity (PLN):"),
                dcc.Input(id="auto-input-koszt", type="number", placeholder="0.00", step=0.01, style={"width": "100%", "padding": "10px", "marginBottom": "15px", "boxSizing": "border-box"}),
                html.Label("Opis / Wykonane Prace:"),
                dcc.Input(id="auto-input-komentarz", type="text", placeholder="np. Wymiana tarcz i klocków przód...", style={"width": "100%", "padding": "10px", "marginBottom": "20px", "boxSizing": "border-box"}),
                html.Button("Zapisz w Garazu", id="btn-auto-zapisz", n_clicks=0, style={"width": "100%", "padding": "12px", "backgroundColor": "#0284c7", "color": "white", "border": "none", "borderRadius": "6px", "fontWeight": "bold", "cursor": "pointer"}),
                html.Div(id="auto-form-msg", style={"marginTop": "15px", "fontWeight": "bold", "textAlign": "center"})
            ])
        ])

    elif tab == "auto-rejestr":
        return html.Div([
            html.Div(style={"backgroundColor": "white", "padding": "20px", "borderRadius": "10px"}, children=[
                html.H3("Rejestr Napraw i Eksploatacji", style={"marginTop": 0, "color": "#0f172a"}),
                dash_table.DataTable(
                    data=df_auto.to_dict('records') if not df_auto.empty else [],
                    columns=[
                        {'name': 'ID', 'id': 'id'},
                        {'name': 'Data', 'id': 'data'},
                        {'name': 'Przebieg (km)', 'id': 'przebieg'},
                        {'name': 'Typ', 'id': 'typ'},
                        {'name': 'Koszt (PLN)', 'id': 'koszt'},
                        {'name': 'Opis / Komentarz', 'id': 'komentarz'},
                    ],
                    page_size=15,
                    sort_action="native",
                    filter_action="native",
                    style_cell={'textAlign': 'left', 'padding': '12px'},
                    style_header={'backgroundColor': '#f8fafc', 'fontWeight': 'bold', 'color': '#475569'}
                )
            ])
        ])

    elif tab == "auto-import":
        return html.Div([
            html.Div(style={"backgroundColor": "white", "padding": "20px", "borderRadius": "10px"}, children=[
                html.H3("📁 Import z Aplikacji Fuelio (CSV)", style={"marginTop": 0, "color": "#0f172a"}),
                dcc.Upload(
                    id='upload-fuelio-file',
                    children=html.Div(['Przeciągnij plik .csv z Fuelio tutaj lub ', html.A('Wybierz Plik')]),
                    style={'width': '100%', 'height': '80px', 'lineHeight': '80px', 'borderWidth': '2px', 'borderStyle': 'dashed', 'borderRadius': '8px', 'textAlign': 'center', 'backgroundColor': '#f8fafc', 'cursor': 'pointer'}
                ),
                html.Div(id='upload-fuelio-msg', style={"marginTop": "15px", "fontWeight": "bold", "textAlign": "center"})
            ])
        ])

@callback(
    Output("auto-form-msg", "children"),
    Input("btn-auto-zapisz", "n_clicks"),
    State("auto-input-data", "date"),
    State("auto-input-przebieg", "value"),
    State("auto-input-typ", "value"),
    State("auto-input-koszt", "value"),
    State("auto-input-komentarz", "value"),
    prevent_initial_call=True
)
def save_auto_entry(n_clicks, date_val, przebieg, typ, koszt, komentarz):
    if n_clicks > 0 and date_val and koszt:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO auto_serwis (data, przebieg, typ, koszt, komentarz)
            VALUES (?, ?, ?, ?, ?)
        ''', (str(date_val), int(przebieg or 0), typ, float(koszt), komentarz or ''))
        conn.commit()
        conn.close()
        return html.Span(" Zapisano wpis serwisowy!", style={"color": "#10b981"})
    return ""