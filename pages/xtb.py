import base64
from datetime import datetime
import io
import dash
from dash import Input, Output, State, callback, dash_table, dcc, html
import openpyxl
import pandas as pd
from database import get_db_connection

dash.register_page(__name__, path='/xtb', name='Inwestycje XTB')


def get_xtb_df():
    conn = get_db_connection()
    try:
        df = pd.read_sql_query(
            'SELECT * FROM inwestycje_xtb ORDER BY data ASC, id ASC', conn
        )
    except Exception:
        df = pd.DataFrame(
            columns=['id', 'data', 'subkonto', 'typ', 'kwota', 'komentarz']
        )
    conn.close()
    return df


def calculate_xirr(cash_flows, dates):
    if len(cash_flows) < 2:
        return 0.0

    d0 = dates[0]
    days = [(d - d0).days for d in dates]

    def xnpv(r):
        if r <= -0.99:
            return 1e12
        return sum(
            cf / ((1.0 + r) ** (day / 365.0)) for cf, day in zip(cash_flows, days)
        )

    low, high = -0.9, 3.0
    for _ in range(80):
        mid = (low + high) / 2.0
        val = xnpv(mid)
        if abs(val) < 1e-5:
            return mid * 100.0
        if xnpv(low) * val < 0:
            high = mid
        else:
            low = mid

    return ((low + high) / 2.0) * 100.0


layout = html.Div([
    html.Div(
        style={
            'display': 'flex',
            'alignItems': 'center',
            'justifyContent': 'space-between',
            'marginBottom': '20px',
        },
        children=[
            html.H2(
                '📈 Portfolio Inwestycyjne XTB',
                style={'margin': 0, 'color': '#0f172a'},
            ),
            dcc.Dropdown(
                id='filtr-subkonto',
                options=[
                    {'label': 'Łącznie (Portfel Ogólny)', 'value': 'ALL'},
                    {'label': 'My Trades (Główne)', 'value': 'My Trades'},
                    {
                        'label': 'Investment Plans (Plany)',
                        'value': 'Investment Plans',
                    },
                ],
                value='ALL',
                clearable=False,
                style={'width': '260px'},
            ),
        ],
    ),
    html.Div(id='xtb-analytics-container'),
    html.Div(
        style={
            'backgroundColor': 'white',
            'padding': '20px',
            'borderRadius': '10px',
            'marginTop': '25px',
            'marginBottom': '25px',
            'boxShadow': '0 2px 8px rgba(0,0,0,0.04)',
        },
        children=[
            html.H3(
                '📁 Wgraj Raport z XTB (.xlsx)',
                style={'marginTop': 0, 'color': '#0f172a', 'fontSize': '16px'},
            ),
            html.P(
                'Przeciągnij plik raportu pobrany z aplikacji XTB.',
                style={'color': '#64748b', 'fontSize': '13px'},
            ),
            dcc.Upload(
                id='upload-xtb-file',
                children=html.Div([
                    'Przeciągnij i upuść raport XTB tutaj lub ',
                    html.A('Wybierz Plik XLSX'),
                ]),
                style={
                    'width': '100%',
                    'height': '80px',
                    'lineHeight': '80px',
                    'borderWidth': '2px',
                    'borderStyle': 'dashed',
                    'borderRadius': '8px',
                    'textAlign': 'center',
                    'backgroundColor': '#f8fafc',
                    'borderColor': '#cbd5e1',
                    'cursor': 'pointer',
                    'fontWeight': 'bold',
                },
                multiple=False,
            ),
            html.Div(
                id='upload-xtb-msg',
                style={
                    'marginTop': '15px',
                    'fontWeight': 'bold',
                    'textAlign': 'center',
                },
            ),
        ],
    ),
    html.Div(
        style={
            'backgroundColor': 'white',
            'padding': '20px',
            'borderRadius': '10px',
            'boxShadow': '0 2px 8px rgba(0,0,0,0.04)',
        },
        children=[
            html.H3(
                'Rejestr Zdarzeń i Wycen XTB',
                style={'marginTop': 0, 'color': '#0f172a', 'fontSize': '18px'},
            ),
            html.Div(id='xtb-table-container'),
        ],
    ),
])


@callback(
    Output('xtb-analytics-container', 'children'),
    Output('xtb-table-container', 'children'),
    Input('filtr-subkonto', 'value'),
    Input('upload-xtb-msg', 'children'),
)
def update_xtb_view(selected_subkonto, upload_msg):
    df_xtb = get_xtb_df()

    if df_xtb.empty:
        return html.P('Brak danych XTB w bazie.'), html.P('Brak wpisów.')

    df_wyceny = df_xtb[df_xtb['typ'] == 'WYCENA']
    cash_flows = []
    dates = []

    if selected_subkonto == 'ALL':
        df_sub = df_xtb.copy()

        # Wkład całkowity z zewnątrz (WPLYW / Deposit)
        wklady_external = df_xtb[df_xtb['typ'] == 'WPLYW']['kwota'].sum()
        wypolaty_external = df_xtb[df_xtb['typ'] == 'WYPŁATA']['kwota'].sum()
        total_wklad = wklady_external - wypolaty_external

        # Wartość aktualna to suma wycen wszystkich subkont
        ostatnia_wycena = (
            df_wyceny.groupby('subkonto').last()['kwota'].sum()
            if not df_wyceny.empty
            else total_wklad
        )

        # Przepływy do XIRR
        for _, r in df_xtb[df_xtb['typ'] == 'WPLYW'].iterrows():
            try:
                cash_flows.append(-float(r['kwota']))
                dates.append(
                    datetime.strptime(str(r['data'])[:10], '%Y-%m-%d')
                )
            except Exception:
                pass

        if not df_wyceny.empty:
            last_dt_str = str(df_wyceny.iloc[-1]['data'])[:10]
            cash_flows.append(float(ostatnia_wycena))
            dates.append(datetime.strptime(last_dt_str, '%Y-%m-%d'))

    elif selected_subkonto == 'My Trades':
        df_sub = df_xtb[df_xtb['subkonto'] == 'My Trades']

        # Wpłaty z zewnątrz minus transfery oddane do Investment Plans
        wklady_ext = df_sub[df_sub['typ'] == 'WPLYW']['kwota'].sum()
        transfery_out = df_sub[df_sub['typ'] == 'TRANSFER_OUT']['kwota'].sum()
        total_wklad = wklady_ext - transfery_out

        df_w = df_sub[df_sub['typ'] == 'WYCENA']
        ostatnia_wycena = (
            float(df_w.iloc[-1]['kwota']) if not df_w.empty else total_wklad
        )

        for _, r in df_sub.iterrows():
            try:
                if r['typ'] == 'WPLYW':
                    cash_flows.append(-float(r['kwota']))
                    dates.append(
                        datetime.strptime(str(r['data'])[:10], '%Y-%m-%d')
                    )
                elif r['typ'] == 'TRANSFER_OUT':
                    cash_flows.append(float(r['kwota']))
                    dates.append(
                        datetime.strptime(str(r['data'])[:10], '%Y-%m-%d')
                    )
            except Exception:
                pass

        if not df_w.empty:
            cash_flows.append(ostatnia_wycena)
            dates.append(
                datetime.strptime(
                    str(df_w.iloc[-1]['data'])[:10], '%Y-%m-%d'
                )
            )

    else:  # Investment Plans
        df_sub = df_xtb[df_xtb['subkonto'] == 'Investment Plans']

        # Wkład to środki otrzymane z transferów wewnętrznych
        total_wklad = df_sub[df_sub['typ'] == 'TRANSFER_IN']['kwota'].sum()

        df_w = df_sub[df_sub['typ'] == 'WYCENA']
        ostatnia_wycena = (
            float(df_w.iloc[-1]['kwota']) if not df_w.empty else total_wklad
        )

        for _, r in df_sub[df_sub['typ'] == 'TRANSFER_IN'].iterrows():
            try:
                cash_flows.append(-float(r['kwota']))
                dates.append(
                    datetime.strptime(str(r['data'])[:10], '%Y-%m-%d')
                )
            except Exception:
                pass

        if not df_w.empty:
            cash_flows.append(ostatnia_wycena)
            dates.append(
                datetime.strptime(
                    str(df_w.iloc[-1]['data'])[:10], '%Y-%m-%d'
                )
            )

    zysk = ostatnia_wycena - total_wklad
    xirr_val = calculate_xirr(cash_flows, dates)

    analytics_view = html.Div(
        style={'display': 'flex', 'gap': '20px'},
        children=[
            html.Div(
                className='kpi-card blue',
                children=[
                    html.Span(
                        'Sumaryczny Wkład (Netto)',
                        style={
                            'color': '#64748b',
                            'fontSize': '12px',
                            'fontWeight': 'bold',
                        },
                    ),
                    html.H2(
                        f'{total_wklad:,.2f} PLN'.replace(',', ' ').replace(
                            '.', ','
                        ),
                        style={'margin': '5px 0 0 0', 'color': '#0f172a'},
                    ),
                ],
            ),
            html.Div(
                className='kpi-card green',
                children=[
                    html.Span(
                        'Wartość Aktualna Portfela',
                        style={
                            'color': '#64748b',
                            'fontSize': '12px',
                            'fontWeight': 'bold',
                        },
                    ),
                    html.H2(
                        f'{ostatnia_wycena:,.2f} PLN'.replace(',', ' ').replace(
                            '.', ','
                        ),
                        style={'margin': '5px 0 0 0', 'color': '#10b981'},
                    ),
                ],
            ),
            html.Div(
                className=f"kpi-card {'green' if zysk >= 0 else 'red'}",
                children=[
                    html.Span(
                        'Wynik (Zysk/Strata)',
                        style={
                            'color': '#64748b',
                            'fontSize': '12px',
                            'fontWeight': 'bold',
                        },
                    ),
                    html.H2(
                        f'{zysk:,.2f} PLN'.replace(',', ' ').replace('.', ','),
                        style={
                            'margin': '5px 0 0 0',
                            'color': '#10b981' if zysk >= 0 else '#ef4444',
                        },
                    ),
                ],
            ),
            html.Div(
                style={
                    'flex': 1,
                    'backgroundColor': '#0f172a',
                    'color': 'white',
                    'padding': '20px',
                    'borderRadius': '10px',
                },
                children=[
                    html.Span(
                        'Roczna Stopa XIRR',
                        style={
                            'color': '#94a3b8',
                            'fontSize': '12px',
                            'fontWeight': 'bold',
                        },
                    ),
                    html.H2(
                        f'{xirr_val:.2f}%'.replace('.', ','),
                        style={
                            'margin': '5px 0 0 0',
                            'color': '#38bdf8',
                            'fontSize': '22px',
                        },
                    ),
                ],
            ),
        ],
    )

    table_view = dash_table.DataTable(
        data=df_sub.sort_values(by='id', ascending=False).to_dict('records'),
        columns=[
            {'name': 'ID', 'id': 'id'},
            {'name': 'Data', 'id': 'data'},
            {'name': 'Subkonto / Produkt', 'id': 'subkonto'},
            {'name': 'Typ Zdarzenia', 'id': 'typ'},
            {'name': 'Kwota (PLN)', 'id': 'kwota'},
            {'name': 'Komentarz', 'id': 'komentarz'},
        ],
        page_size=10,
        sort_action='native',
        filter_action='native',
        style_cell={'textAlign': 'left', 'padding': '12px'},
        style_header={
            'backgroundColor': '#f8fafc',
            'fontWeight': 'bold',
            'color': '#475569',
        },
    )

    return analytics_view, table_view


@callback(
    Output('upload-xtb-msg', 'children'),
    Input('upload-xtb-file', 'contents'),
    State('upload-xtb-file', 'filename'),
    prevent_initial_call=True,
)
def upload_xtb_excel(contents, filename):
    if contents is not None:
        try:
            content_type, content_string = contents.split(',')
            decoded = base64.b64decode(content_string)
            xls = pd.ExcelFile(io.BytesIO(decoded))

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM inwestycje_xtb')

            added_records = 0

            # 1. PARSOWANIE HISTORII OPERACJI GOTÓWKOWYCH (Cash Operations)
            if 'Cash Operations' in xls.sheet_names:
                df_cash_raw = pd.read_excel(
                    xls, sheet_name='Cash Operations', header=None
                )

                header_idx = None
                for idx, row in df_cash_raw.iterrows():
                    row_vals = [
                        str(v).strip().lower()
                        for v in row.values
                        if pd.notnull(v)
                    ]
                    if 'type' in row_vals and 'amount' in row_vals:
                        header_idx = idx
                        break

                if header_idx is not None:
                    df_cash = pd.read_excel(
                        xls, sheet_name='Cash Operations', skiprows=header_idx
                    )
                    df_cash.columns = [
                        str(c).strip().lower() for c in df_cash.columns
                    ]

                    for _, row in df_cash.iterrows():
                        typ_val = str(row.get('type', '')).strip()
                        kwota_val = row.get('amount', 0)
                        dt_val = row.get('time', '')
                        sub_val = str(row.get('product', 'My Trades')).strip()
                        kom_val = str(row.get('comment', ''))

                        if pd.isnull(dt_val) or str(dt_val).strip() == '':
                            continue

                        dt = str(dt_val)[:10]

                        try:
                            kwota = float(kwota_val)
                        except (ValueError, TypeError):
                            continue

                        typ_upper = typ_val.upper()
                        if (
                            'DEPOSIT' in typ_upper
                            or 'WPŁATA' in typ_upper
                            or 'PAYU' in typ_upper
                            or 'BLIK' in typ_upper
                        ):
                            typ = 'WPLYW'
                        elif 'WITHDRAWAL' in typ_upper or 'WYPŁATA' in typ_upper:
                            typ = 'WYPŁATA'
                        elif 'SUBACCOUNT TRANSFER' in typ_upper:
                            typ = (
                                'TRANSFER_IN'
                                if kwota > 0
                                else 'TRANSFER_OUT'
                            )
                        else:
                            typ = typ_val

                        cursor.execute(
                            '''
                            INSERT INTO inwestycje_xtb (data, subkonto, typ, kwota, komentarz)
                            VALUES (?, ?, ?, ?, ?)
                        ''',
                            (dt, sub_val, typ, abs(kwota), kom_val or typ_val),
                        )
                        added_records += 1

            # 2. PARSOWANIE WYCENY PORTFELA (Open Positions)
            if 'Open Positions' in xls.sheet_names:
                df_open_raw = pd.read_excel(
                    xls, sheet_name='Open Positions', header=None
                )
                today_str = datetime.now().strftime('%Y-%m-%d')

                for _, row in df_open_raw.iterrows():
                    row_str = [
                        str(v).strip() for v in row.values if pd.notnull(v)
                    ]
                    if len(row_str) >= 3 and row_str[1] == 'Value':
                        subkonto_name = row_str[0]
                        try:
                            val_kwota = float(row_str[2])
                            cursor.execute(
                                '''
                                INSERT INTO inwestycje_xtb (data, subkonto, typ, kwota, komentarz)
                                VALUES (?, ?, 'WYCENA', ?, 'Wycena aktualna portfela')
                            ''',
                                (today_str, subkonto_name, val_kwota),
                            )
                            added_records += 1
                        except (ValueError, TypeError):
                            pass

            conn.commit()
            conn.close()

            if added_records > 0:
                return html.Span(
                    f' Success! Zaimportowano {added_records} operacji i wycen'
                    f' z pliku {filename}.',
                    style={'color': '#10b981'},
                )
            else:
                return html.Span(
                    f'⚠️ Nie udało się wyciągnąć danych z pliku {filename}.',
                    style={'color': '#f59e0b'},
                )

        except Exception as e:
            return html.Span(
                f' Błąd parsowania pliku XTB: {str(e)}',
                style={'color': '#ef4444'},
            )

    return ''