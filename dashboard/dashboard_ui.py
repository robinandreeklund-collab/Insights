"""Insights Dashboard - Sprint 3 Enhanced Dashboard with Interactive Features."""

import dash
from dash import html, dcc, Input, Output, State, callback_context, dash_table
import dash_bootstrap_components as dbc
import signal
import sys
import os
import yaml
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
from datetime import datetime
import base64
import io
import uuid

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.core.account_manager import AccountManager
from modules.core.forecast_engine import get_forecast_summary, get_category_breakdown, load_transactions
from modules.core.import_bank_data import import_csv
from modules.core.categorize_expenses import auto_categorize


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

# Define category and subcategory options
CATEGORIES = {
    'Mat & Dryck': ['Matinköp', 'Restaurang', 'Café'],
    'Transport': ['Bränsle & Parkering', 'Kollektivtrafik', 'Taxi'],
    'Boende': ['Hyra & Räkningar', 'Hemförsäkring', 'El'],
    'Shopping': ['Kläder', 'Elektronik', 'Hem & Trädgård'],
    'Nöje': ['Bio & Teater', 'Sport', 'Hobby'],
    'Övrigt': ['Okategoriserat', 'Transaktioner', 'Avgifter']
}

# Create overview tab content
def create_overview_tab():
    """Create the Economic Overview tab with forecast and category breakdown."""
    return html.Div([
        html.H3("Ekonomisk översikt", className="mt-3 mb-4"),
        
        # Balance and forecast section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Saldo och prognos", className="card-title"),
                        html.Div(id='balance-display', className="mb-3"),
                        dcc.Graph(id='forecast-graph'),
                    ])
                ])
            ], width=12)
        ], className="mb-4"),
        
        # Category breakdown section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Utgiftsfördelning per kategori", className="card-title"),
                        dcc.Graph(id='category-pie-chart'),
                    ])
                ])
            ], width=12)
        ]),
        
        # Interval component for auto-refresh
        dcc.Interval(id='overview-interval', interval=5000, n_intervals=0)
    ], className="p-3")


# Create input tab content with CSV upload
def create_input_tab():
    """Create the Input tab with drag-and-drop CSV upload."""
    return html.Div([
        html.H3("Inmatning", className="mt-3 mb-4"),
        
        dbc.Card([
            dbc.CardBody([
                html.H5("CSV-import", className="card-title mb-3"),
                html.P("Dra och släpp en Nordea CSV-fil här, eller klicka för att välja fil"),
                
                dcc.Upload(
                    id='upload-csv',
                    children=html.Div([
                        html.I(className="bi bi-cloud-upload", style={'fontSize': '48px'}),
                        html.Br(),
                        'Dra och släpp eller klicka för att välja CSV-fil'
                    ]),
                    style={
                        'width': '100%',
                        'height': '200px',
                        'lineHeight': '200px',
                        'borderWidth': '2px',
                        'borderStyle': 'dashed',
                        'borderRadius': '10px',
                        'textAlign': 'center',
                        'backgroundColor': '#f8f9fa'
                    },
                    multiple=False
                ),
                
                html.Div(id='upload-status', className="mt-3")
            ])
        ])
    ], className="p-3")


# Create accounts tab content with transaction browser
def create_accounts_tab():
    """Create the Accounts tab with transaction browser and manual categorization."""
    return html.Div([
        html.H3("Konton", className="mt-3 mb-4"),
        
        # Account selector
        dbc.Row([
            dbc.Col([
                html.Label("Välj konto:", className="fw-bold"),
                dcc.Dropdown(
                    id='account-selector',
                    placeholder="Välj ett konto...",
                    className="mb-3"
                )
            ], width=6)
        ]),
        
        # Transaction browser
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Transaktioner", className="card-title"),
                        html.Div(id='transaction-table-container'),
                        
                        # Pagination controls
                        html.Div([
                            dbc.ButtonGroup([
                                dbc.Button("← Föregående", id='prev-page-btn', size="sm", outline=True, color="primary"),
                                html.Span(id='page-info', className="mx-3 align-self-center"),
                                dbc.Button("Nästa →", id='next-page-btn', size="sm", outline=True, color="primary"),
                            ], className="mt-3")
                        ], className="d-flex justify-content-center")
                    ])
                ])
            ], width=12)
        ], className="mb-4"),
        
        # Manual categorization section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Manuell kategorisering", className="card-title"),
                        html.Div(id='categorization-form')
                    ])
                ])
            ], width=12)
        ]),
        
        # Store for current page
        dcc.Store(id='current-page', data=0),
        dcc.Store(id='selected-transaction-id', data=None),
        
        # Interval for auto-refresh
        dcc.Interval(id='accounts-interval', interval=5000, n_intervals=0)
    ], className="p-3")


# Main app layout
app.layout = dbc.Container([
    html.H1("Insights – Hushållsekonomi Dashboard", className="text-center my-4"),
    
    dcc.Tabs(id="main-tabs", value="overview", children=[
        # Ekonomisk översikt
        dcc.Tab(
            label="Ekonomisk översikt",
            value="overview",
            children=create_overview_tab()
        ),
        
        # Inmatning
        dcc.Tab(
            label="Inmatning",
            value="input",
            children=create_input_tab()
        ),
        
        # Konton
        dcc.Tab(
            label="Konton",
            value="accounts",
            children=create_accounts_tab()
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


# Callback: CSV Upload
@app.callback(
    Output('upload-status', 'children'),
    Input('upload-csv', 'contents'),
    State('upload-csv', 'filename'),
    prevent_initial_call=True
)
def handle_csv_upload(contents, filename):
    """Handle CSV file upload and process it."""
    if contents is None:
        return ""
    
    try:
        # Decode the uploaded file
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        
        # Save to temporary file
        temp_file = f"/tmp/{filename}"
        with open(temp_file, 'wb') as f:
            f.write(decoded)
        
        # Import and process the CSV
        account_name, df = import_csv(temp_file)
        
        # Create/update account
        manager = AccountManager()
        latest_balance = df['balance'].iloc[0] if 'balance' in df.columns and len(df) > 0 else 0.0
        manager.create_account(name=account_name, source_file=filename, balance=latest_balance)
        
        # Auto-categorize
        df = auto_categorize(df)
        
        # Save transactions
        transactions = []
        for _, row in df.iterrows():
            transaction = {
                'date': row['date'].strftime('%Y-%m-%d') if pd.notna(row['date']) else '',
                'description': str(row.get('description', '')),
                'amount': float(row.get('amount', 0)),
                'balance': float(row.get('balance', 0)),
                'category': row.get('category', 'Övrigt'),
                'subcategory': row.get('subcategory', 'Okategoriserat'),
                'account': account_name,
                'currency': row.get('currency', 'SEK'),
            }
            transactions.append(transaction)
        
        manager.add_transactions(transactions)
        manager.update_account_balance(account_name, latest_balance)
        
        # Clean up temp file
        os.remove(temp_file)
        
        return dbc.Alert([
            html.I(className="bi bi-check-circle-fill me-2"),
            f"✓ {filename} importerad! {len(transactions)} transaktioner tillagda till konto '{account_name}'"
        ], color="success", className="mt-3")
        
    except Exception as e:
        return dbc.Alert([
            html.I(className="bi bi-exclamation-triangle-fill me-2"),
            f"Fel vid import: {str(e)}"
        ], color="danger", className="mt-3")


# Callback: Update Overview Tab
@app.callback(
    [Output('balance-display', 'children'),
     Output('forecast-graph', 'figure'),
     Output('category-pie-chart', 'figure')],
    Input('overview-interval', 'n_intervals')
)
def update_overview(n):
    """Update the overview tab with current data."""
    manager = AccountManager()
    accounts = manager.get_accounts()
    
    # Calculate total balance
    total_balance = sum(acc.get('balance', 0) for acc in accounts)
    
    # Get forecast
    forecast_summary = get_forecast_summary(total_balance)
    forecast_data = forecast_summary.get('forecast', [])
    
    # Create forecast graph
    if forecast_data:
        forecast_df = pd.DataFrame(forecast_data)
        forecast_fig = go.Figure()
        forecast_fig.add_trace(go.Scatter(
            x=forecast_df['date'],
            y=forecast_df['predicted_balance'],
            mode='lines+markers',
            name='Förväntat saldo',
            line=dict(color='#0d6efd', width=3),
            marker=dict(size=6)
        ))
        forecast_fig.update_layout(
            title='30-dagars prognos',
            xaxis_title='Datum',
            yaxis_title='Saldo (SEK)',
            hovermode='x unified',
            template='plotly_white'
        )
    else:
        forecast_fig = go.Figure()
        forecast_fig.add_annotation(
            text="Ingen data tillgänglig - importera en CSV-fil för att se prognos",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
    
    # Get category breakdown
    transactions = load_transactions()
    category_data = get_category_breakdown(transactions)
    
    # Create pie chart
    if category_data:
        pie_fig = px.pie(
            values=list(category_data.values()),
            names=list(category_data.keys()),
            title='Utgiftsfördelning per kategori'
        )
        pie_fig.update_traces(textposition='inside', textinfo='percent+label')
    else:
        pie_fig = go.Figure()
        pie_fig.add_annotation(
            text="Ingen data tillgänglig - importera en CSV-fil för att se utgiftsfördelning",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
    
    # Balance display
    balance_display = html.Div([
        html.H3(f"{total_balance:,.2f} SEK", className="text-primary"),
        html.P(f"Nuvarande totalt saldo över {len(accounts)} konto(n)", className="text-muted")
    ])
    
    return balance_display, forecast_fig, pie_fig


# Callback: Update Account Selector
@app.callback(
    Output('account-selector', 'options'),
    Input('accounts-interval', 'n_intervals')
)
def update_account_selector(n):
    """Update the account selector dropdown."""
    manager = AccountManager()
    accounts = manager.get_accounts()
    return [{'label': acc['name'], 'value': acc['name']} for acc in accounts]


# Callback: Update Transaction Table
@app.callback(
    [Output('transaction-table-container', 'children'),
     Output('page-info', 'children')],
    [Input('account-selector', 'value'),
     Input('current-page', 'data'),
     Input('accounts-interval', 'n_intervals')]
)
def update_transaction_table(account_name, current_page, n):
    """Update the transaction table for the selected account."""
    if not account_name:
        return html.P("Välj ett konto för att visa transaktioner", className="text-muted"), ""
    
    manager = AccountManager()
    transactions = manager.get_account_transactions(account_name)
    
    if not transactions:
        return html.P("Inga transaktioner funna", className="text-muted"), ""
    
    # Pagination
    per_page = 50
    current_page = current_page or 0
    total_pages = (len(transactions) - 1) // per_page + 1
    start_idx = current_page * per_page
    end_idx = min(start_idx + per_page, len(transactions))
    page_transactions = transactions[start_idx:end_idx]
    
    # Create table
    df = pd.DataFrame(page_transactions)
    table = dash_table.DataTable(
        id='transaction-table',
        columns=[
            {'name': 'Datum', 'id': 'date'},
            {'name': 'Beskrivning', 'id': 'description'},
            {'name': 'Belopp', 'id': 'amount'},
            {'name': 'Saldo', 'id': 'balance'},
            {'name': 'Kategori', 'id': 'category'},
            {'name': 'Underkategori', 'id': 'subcategory'},
        ],
        data=df.to_dict('records'),
        style_cell={'textAlign': 'left', 'padding': '10px'},
        style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
        style_data_conditional=[
            {
                'if': {'filter_query': '{amount} < 0'},
                'color': '#dc3545'
            },
            {
                'if': {'filter_query': '{amount} > 0'},
                'color': '#28a745'
            }
        ],
        row_selectable='single',
        selected_rows=[]
    )
    
    page_info = f"Sida {current_page + 1} av {total_pages} ({len(transactions)} transaktioner)"
    
    return table, page_info


# Callback: Handle Pagination
@app.callback(
    Output('current-page', 'data'),
    [Input('prev-page-btn', 'n_clicks'),
     Input('next-page-btn', 'n_clicks')],
    [State('current-page', 'data'),
     State('account-selector', 'value')]
)
def handle_pagination(prev_clicks, next_clicks, current_page, account_name):
    """Handle pagination button clicks."""
    if not account_name:
        return 0
    
    ctx = callback_context
    if not ctx.triggered:
        return current_page or 0
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    current_page = current_page or 0
    
    manager = AccountManager()
    transactions = manager.get_account_transactions(account_name)
    per_page = 50
    total_pages = (len(transactions) - 1) // per_page + 1
    
    if button_id == 'prev-page-btn' and current_page > 0:
        return current_page - 1
    elif button_id == 'next-page-btn' and current_page < total_pages - 1:
        return current_page + 1
    
    return current_page


# Callback: Show Categorization Form
@app.callback(
    Output('categorization-form', 'children'),
    [Input('transaction-table', 'selected_rows'),
     Input('transaction-table', 'data')]
)
def show_categorization_form(selected_rows, table_data):
    """Show the categorization form when a transaction is selected."""
    if not selected_rows or not table_data:
        return html.P("Välj en transaktion i tabellen ovan för att kategorisera den manuellt", className="text-muted")
    
    selected_tx = table_data[selected_rows[0]]
    
    return html.Div([
        html.H6(f"Kategorisera: {selected_tx['description']}", className="mb-3"),
        dbc.Row([
            dbc.Col([
                html.Label("Kategori:", className="fw-bold"),
                dcc.Dropdown(
                    id='category-dropdown',
                    options=[{'label': cat, 'value': cat} for cat in CATEGORIES.keys()],
                    value=selected_tx.get('category', 'Övrigt'),
                    className="mb-3"
                )
            ], width=6),
            dbc.Col([
                html.Label("Underkategori:", className="fw-bold"),
                dcc.Dropdown(
                    id='subcategory-dropdown',
                    value=selected_tx.get('subcategory', 'Okategoriserat'),
                    className="mb-3"
                )
            ], width=6),
        ]),
        dbc.Button("Spara kategorisering", id='save-category-btn', color="primary", className="mt-2"),
        html.Div(id='category-save-status', className="mt-2")
    ])


# Callback: Update Subcategory Options
@app.callback(
    Output('subcategory-dropdown', 'options'),
    Input('category-dropdown', 'value')
)
def update_subcategory_options(category):
    """Update subcategory options based on selected category."""
    if category and category in CATEGORIES:
        return [{'label': subcat, 'value': subcat} for subcat in CATEGORIES[category]]
    return []


# Callback: Save Manual Categorization
@app.callback(
    Output('category-save-status', 'children'),
    [Input('save-category-btn', 'n_clicks')],
    [State('transaction-table', 'selected_rows'),
     State('transaction-table', 'data'),
     State('category-dropdown', 'value'),
     State('subcategory-dropdown', 'value'),
     State('account-selector', 'value')],
    prevent_initial_call=True
)
def save_manual_categorization(n_clicks, selected_rows, table_data, category, subcategory, account_name):
    """Save manual categorization for selected transaction."""
    if not selected_rows or not table_data or not category or not subcategory:
        return ""
    
    try:
        selected_tx = table_data[selected_rows[0]]
        
        # Load all transactions
        manager = AccountManager()
        data = manager._load_yaml(manager.transactions_file)
        transactions = data.get('transactions', [])
        
        # Find and update the transaction
        for tx in transactions:
            if (tx.get('date') == selected_tx['date'] and 
                tx.get('description') == selected_tx['description'] and
                tx.get('account') == account_name):
                tx['category'] = category
                tx['subcategory'] = subcategory
                tx['categorized_manually'] = True
                
                # Train AI from manual input
                manager.train_ai_from_manual_input(tx)
                break
        
        # Save updated transactions
        manager.save_transactions(data)  # Use public method to save transactions
        
        return dbc.Alert("✓ Kategorisering sparad!", color="success", dismissable=True)
    except Exception as e:
        return dbc.Alert(f"Fel: {str(e)}", color="danger", dismissable=True)


if __name__ == "__main__":
    # Register signal handler for Ctrl-C
    signal.signal(signal.SIGINT, clear_data_on_exit)
    
    print("Starting Insights Dashboard (Sprint 3)...")
    print("Open your browser at: http://127.0.0.1:8050")
    print("\nPress Ctrl-C to stop the server and clear data files")
    
    try:
        app.run(debug=True, host="0.0.0.0", port=8050)
    except KeyboardInterrupt:
        clear_data_on_exit()
