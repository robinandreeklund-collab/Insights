"""Insights Dashboard - Main Dash application."""

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import signal
import sys
import os
import yaml


def clear_data_on_exit(signum=None, frame=None):
    """Clear transactions and accounts data files on exit."""
    print("\n\nClearing data files before exit...")
    
    yaml_dir = "yaml"
    transactions_file = os.path.join(yaml_dir, "transactions.yaml")
    accounts_file = os.path.join(yaml_dir, "accounts.yaml")
    
    try:
        # Reset transactions.yaml
        if os.path.exists(transactions_file):
            with open(transactions_file, 'w', encoding='utf-8') as f:
                yaml.dump({'transactions': []}, f, default_flow_style=False, allow_unicode=True)
            print(f"✓ Cleared {transactions_file}")
        
        # Reset accounts.yaml
        if os.path.exists(accounts_file):
            with open(accounts_file, 'w', encoding='utf-8') as f:
                yaml.dump({'accounts': []}, f, default_flow_style=False, allow_unicode=True)
            print(f"✓ Cleared {accounts_file}")
        
        print("Data files cleared successfully!")
    except Exception as e:
        print(f"Error clearing data files: {e}")
    
    sys.exit(0)


# Initialize Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True
)

# Define the layout with tabs according to dashboard.yaml
app.layout = dbc.Container([
    html.H1("Insights – Hushållsekonomi Dashboard", className="text-center my-4"),
    
    dcc.Tabs(id="main-tabs", value="overview", children=[
        # Ekonomisk översikt
        dcc.Tab(
            label="Ekonomisk översikt",
            value="overview",
            children=[
                html.Div([
                    html.H3("Ekonomisk översikt", className="mt-3"),
                    html.P("Visar prognos 30 dagar framåt, utgiftsfördelning per kategori och agentgenererade insikter."),
                    html.P("Kopplad till: forecast_engine, categorize_expenses, alerts_and_insights"),
                    html.Div(id="overview-content", className="mt-3")
                ], className="p-3")
            ]
        ),
        
        # Inmatning
        dcc.Tab(
            label="Inmatning",
            value="input",
            children=[
                html.Div([
                    html.H3("Inmatning", className="mt-3"),
                    html.P("Importera CSV, lägg till fakturor och inkomster manuellt, eller läs in PDF-fakturor."),
                    html.P("Kopplad till: import_bank_data, categorize_expenses"),
                    html.Div(id="input-content", className="mt-3")
                ], className="p-3")
            ]
        ),
        
        # Konton
        dcc.Tab(
            label="Konton",
            value="accounts",
            children=[
                html.Div([
                    html.H3("Konton", className="mt-3"),
                    html.P("Skapa och hantera konton, visa kontoutdrag, kategorisera transaktioner och träna AI-modellen."),
                    html.P("Kopplad till: account_manager, categorize_expenses"),
                    html.Div(id="accounts-content", className="mt-3")
                ], className="p-3")
            ]
        ),
        
        # Fakturor
        dcc.Tab(
            label="Fakturor",
            value="bills",
            children=[
                html.Div([
                    html.H3("Fakturor", className="mt-3"),
                    html.P("Visa aktiva och hanterade fakturor, redigera, ta bort och matcha mot transaktioner."),
                    html.Div(id="bills-content", className="mt-3")
                ], className="p-3")
            ]
        ),
        
        # Historik
        dcc.Tab(
            label="Historik",
            value="history",
            children=[
                html.Div([
                    html.H3("Historik", className="mt-3"),
                    html.P("Månadssammanställningar, kategoritrender, saldohistorik och topptransaktioner."),
                    html.Div(id="history-content", className="mt-3")
                ], className="p-3")
            ]
        ),
        
        # Lån
        dcc.Tab(
            label="Lån",
            value="loans",
            children=[
                html.Div([
                    html.H3("Lån", className="mt-3"),
                    html.P("Lägg till lån med ränta och bindningstid, visualisera återbetalning och simulera ränteförändringar."),
                    html.Div(id="loans-content", className="mt-3")
                ], className="p-3")
            ]
        ),
        
        # Frågebaserad analys
        dcc.Tab(
            label="Frågebaserad analys",
            value="agent",
            children=[
                html.Div([
                    html.H3("Frågebaserad analys", className="mt-3"),
                    html.P("Tolkar naturliga frågor och genererar svar, insikter och simuleringar."),
                    html.Div(id="agent-content", className="mt-3")
                ], className="p-3")
            ]
        ),
        
        # Inställningar
        dcc.Tab(
            label="Inställningar",
            value="settings",
            children=[
                html.Div([
                    html.H3("Inställningar", className="mt-3"),
                    html.P("Hanterar användarinställningar, toggles, thresholds och UI-konfiguration."),
                    html.Div(id="settings-content", className="mt-3")
                ], className="p-3")
            ]
        ),
    ])
], fluid=True)


if __name__ == "__main__":
    # Register signal handler for Ctrl-C
    signal.signal(signal.SIGINT, clear_data_on_exit)
    
    print("Starting Insights Dashboard...")
    print("Open your browser at: http://127.0.0.1:8050")
    print("\nPress Ctrl-C to stop the server and clear data files")
    
    try:
        app.run(debug=True, host="0.0.0.0", port=8050)
    except KeyboardInterrupt:
        clear_data_on_exit()
