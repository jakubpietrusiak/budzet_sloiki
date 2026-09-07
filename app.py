import dash
from dash import dcc, html
from database import init_db

# Inicjalizacja baz danych (nie kasuje istniejących danych)
init_db()

# Dołączenie nowoczesnych czcionek Google Fonts w nagłówku aplikacji
external_stylesheets = [
    "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Plus+Jakarta+Sans:wght@600;700;800;900&display=swap"
]

app = dash.Dash(
    __name__,
    use_pages=True,
    suppress_callback_exceptions=True,
    external_stylesheets=external_stylesheets,
)
app.title = "System Menadżera Life & Finance"

app.layout = html.Div(
    style={"display": "flex", "minHeight": "100vh"},
    children=[
        # Dynamiczny Sidebar (Lewy panel nawigacyjny)
        html.Div(
            className="sidebar",
            style={
                "width": "310px",
                "background": "linear-gradient(180deg, #0f172a 0%, #1e293b 100%)",
                "color": "white",
                "padding": "25px 16px",
                "display": "flex",
                "flexDirection": "column",
                "boxShadow": "4px 0 25px rgba(0,0,0,0.15)",
                "boxSizing": "border-box",
            },
            children=[
                # DUŻY NAGŁÓWEK GŁÓWNY
                html.Div(
                    style={
                        "display": "flex",
                        "alignItems": "center",
                        "gap": "14px",
                        "padding": "10px 8px",
                        "marginBottom": "10px",
                    },
                    children=[
                        html.Div(
                            "💎",
                            style={
                                "fontSize": "32px",
                                "background": "rgba(56, 189, 248, 0.15)",
                                "border": "1px solid rgba(56, 189, 248, 0.4)",
                                "borderRadius": "14px",
                                "padding": "8px 12px",
                                "display": "flex",
                                "alignItems": "center",
                                "justifyContent": "center",
                            },
                        ),
                        html.Div([
                            html.H1(
                                "MENADŻER",
                                style={
                                    "margin": "0",
                                    "fontSize": "28px",
                                    "fontWeight": "900",
                                    "letterSpacing": "1.5px",
                                    "color": "#ffffff",
                                    "lineHeight": "1.0",
                                },
                            ),
                            html.Span(
                                "Life & Finance System",
                                style={
                                    "fontSize": "12px",
                                    "color": "#38bdf8",
                                    "fontWeight": "700",
                                    "letterSpacing": "0.8px",
                                    "display": "block",
                                    "marginTop": "4px",
                                },
                            ),
                        ]),
                    ],
                ),
                html.Div(
                    style={
                        "height": "1px",
                        "background": (
                            "linear-gradient(90deg, rgba(255,255,255,0.15)"
                            " 0%, rgba(255,255,255,0.02) 100%)"
                        ),
                        "margin": "15px 0 20px 0",
                    }
                ),
                # WYPEŁNIONE LINKI NAWIGACYJNE
                html.Div(
                    style={
                        "display": "flex",
                        "flexDirection": "column",
                        "gap": "12px",
                        "flex": "1",
                    },
                    children=[
                        dcc.Link(
                            children=[
                                html.Span(
                                    "📊",
                                    style={
                                        "fontSize": "26px",
                                        "marginRight": "14px",
                                    },
                                ),
                                html.Span(
                                    "Wydatki",
                                    style={
                                        "fontSize": "18px",
                                        "fontWeight": "600",
                                    },
                                ),
                            ],
                            href="/",
                            className="nav-link",
                        ),
                        dcc.Link(
                            children=[
                                html.Span(
                                    "📈",
                                    style={
                                        "fontSize": "26px",
                                        "marginRight": "14px",
                                    },
                                ),
                                html.Span(
                                    "Inwestycje XTB",
                                    style={
                                        "fontSize": "18px",
                                        "fontWeight": "600",
                                    },
                                ),
                            ],
                            href="/xtb",
                            className="nav-link",
                        ),
                        dcc.Link(
                            children=[
                                html.Span(
                                    "🚗",
                                    style={
                                        "fontSize": "26px",
                                        "marginRight": "14px",
                                    },
                                ),
                                html.Span(
                                    "Garaż - Mercedes W211",
                                    style={
                                        "fontSize": "18px",
                                        "fontWeight": "600",
                                    },
                                ),
                            ],
                            href="/auto",
                            className="nav-link",
                        ),
                        dcc.Link(
                            children=[
                                html.Span(
                                    "💪",
                                    style={
                                        "fontSize": "26px",
                                        "marginRight": "14px",
                                    },
                                ),
                                html.Span(
                                    "Fit HERO",
                                    style={
                                        "fontSize": "18px",
                                        "fontWeight": "600",
                                    },
                                ),
                            ],
                            href="/fit-hero",
                            className="nav-link",
                        ),
                        dcc.Link(
                            children=[
                                html.Span(
                                    "🎯",
                                    style={
                                        "fontSize": "26px",
                                        "marginRight": "14px",
                                    },
                                ),
                                html.Span(
                                    "Cele i Nawyki",
                                    style={
                                        "fontSize": "18px",
                                        "fontWeight": "600",
                                    },
                                ),
                            ],
                            href="/cele",
                            className="nav-link",
                        ),
                    ],
                ),
            ],
        ),
        # Główne okno wyrenderowanej podstrony
        html.Div(
            className="content-container",
            style={
                "flex": "1",
                "padding": "30px 40px",
                "backgroundColor": "#f8fafc",
                "overflowY": "auto",
            },
            children=[dash.page_container],
        ),
    ],
)

if __name__ == "__main__":
    app.run(debug=True)