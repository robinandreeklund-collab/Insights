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
from modules.core.bill_manager import BillManager
from modules.core.loan_manager import LoanManager
from modules.core.parse_pdf_bills import PDFBillParser
from modules.core.bill_matcher import BillMatcher


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


# Create bills tab content
def create_bills_tab():
    """Create the Bills tab with bill management and matching."""
    return html.Div([
        html.H3("Fakturahantering", className="mt-3 mb-4"),
        
        # Add new bill section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Lägg till faktura", className="card-title"),
                        dbc.Row([
                            dbc.Col([
                                html.Label("Namn:", className="fw-bold"),
                                dbc.Input(id='bill-name-input', type='text', placeholder='T.ex. Elräkning December'),
                            ], width=6),
                            dbc.Col([
                                html.Label("Belopp (SEK):", className="fw-bold"),
                                dbc.Input(id='bill-amount-input', type='number', placeholder='0.00'),
                            ], width=6),
                        ], className="mb-3"),
                        dbc.Row([
                            dbc.Col([
                                html.Label("Förfallodatum:", className="fw-bold"),
                                dbc.Input(id='bill-due-date-input', type='date'),
                            ], width=6),
                            dbc.Col([
                                html.Label("Kategori:", className="fw-bold"),
                                dcc.Dropdown(
                                    id='bill-category-dropdown',
                                    options=[{'label': cat, 'value': cat} for cat in CATEGORIES.keys()],
                                    value='Övrigt'
                                ),
                            ], width=6),
                        ], className="mb-3"),
                        dbc.Row([
                            dbc.Col([
                                html.Label("Beskrivning:", className="fw-bold"),
                                dbc.Textarea(id='bill-description-input', placeholder='Valfri beskrivning...'),
                            ], width=12),
                        ], className="mb-3"),
                        dbc.Row([
                            dbc.Col([
                                dbc.Button("Lägg till faktura", id='add-bill-btn', color="primary", className="me-2"),
                                dbc.Button("Importera från PDF (demo)", id='import-pdf-btn', color="secondary"),
                                dbc.Button("Matcha fakturor", id='match-bills-btn', color="info", className="ms-2"),
                            ], width=12),
                        ]),
                        html.Div(id='bill-add-status', className="mt-3")
                    ])
                ])
            ], width=12)
        ], className="mb-4"),
        
        # Bills display section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Aktiva fakturor", className="card-title"),
                        dcc.Dropdown(
                            id='bill-status-filter',
                            options=[
                                {'label': 'Alla', 'value': 'all'},
                                {'label': 'Väntande', 'value': 'pending'},
                                {'label': 'Betalda', 'value': 'paid'},
                                {'label': 'Förfallna', 'value': 'overdue'}
                            ],
                            value='all',
                            className="mb-3"
                        ),
                        html.Div(id='bills-table-container'),
                    ])
                ])
            ], width=12)
        ]),
        
        # Store and interval for auto-refresh
        dcc.Store(id='selected-bill-id', data=None),
        dcc.Interval(id='bills-interval', interval=5000, n_intervals=0)
    ], className="p-3")


# Create loans tab content
def create_loans_tab():
    """Create the Loans tab with loan management and simulation."""
    return html.Div([
        html.H3("Lånehantering", className="mt-3 mb-4"),
        
        # Add new loan section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Lägg till lån", className="card-title"),
                        dbc.Row([
                            dbc.Col([
                                html.Label("Namn:", className="fw-bold"),
                                dbc.Input(id='loan-name-input', type='text', placeholder='T.ex. Bolån'),
                            ], width=6),
                            dbc.Col([
                                html.Label("Huvudbelopp (SEK):", className="fw-bold"),
                                dbc.Input(id='loan-principal-input', type='number', placeholder='0.00'),
                            ], width=6),
                        ], className="mb-3"),
                        dbc.Row([
                            dbc.Col([
                                html.Label("Årsränta (%):", className="fw-bold"),
                                dbc.Input(id='loan-interest-input', type='number', placeholder='3.5', step='0.1'),
                            ], width=4),
                            dbc.Col([
                                html.Label("Löptid (månader):", className="fw-bold"),
                                dbc.Input(id='loan-term-input', type='number', placeholder='360', value='360'),
                            ], width=4),
                            dbc.Col([
                                html.Label("Startdatum:", className="fw-bold"),
                                dbc.Input(id='loan-start-date-input', type='date'),
                            ], width=4),
                        ], className="mb-3"),
                        dbc.Row([
                            dbc.Col([
                                html.Label("Bindningstid slutar (valfritt):", className="fw-bold"),
                                dbc.Input(id='loan-fixed-end-date-input', type='date'),
                            ], width=6),
                            dbc.Col([
                                html.Label("Beskrivning:", className="fw-bold"),
                                dbc.Input(id='loan-description-input', type='text', placeholder='Valfri beskrivning...'),
                            ], width=6),
                        ], className="mb-3"),
                        dbc.Button("Lägg till lån", id='add-loan-btn', color="primary"),
                        html.Div(id='loan-add-status', className="mt-3")
                    ])
                ])
            ], width=12)
        ], className="mb-4"),
        
        # Loans display section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Aktiva lån", className="card-title"),
                        html.Div(id='loans-table-container'),
                    ])
                ])
            ], width=12)
        ], className="mb-4"),
        
        # Interest rate simulation section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Simulera ränteförändring", className="card-title"),
                        dbc.Row([
                            dbc.Col([
                                html.Label("Välj lån:", className="fw-bold"),
                                dcc.Dropdown(id='loan-selector', placeholder='Välj ett lån...')
                            ], width=6),
                            dbc.Col([
                                html.Label("Ny ränta (%):", className="fw-bold"),
                                dbc.Input(id='new-interest-input', type='number', placeholder='4.5', step='0.1'),
                            ], width=4),
                            dbc.Col([
                                dbc.Button("Simulera", id='simulate-btn', color="info", className="mt-4"),
                            ], width=2),
                        ]),
                        html.Div(id='simulation-result', className="mt-3")
                    ])
                ])
            ], width=12)
        ], className="mb-4"),
        
        # Amortization schedule section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Återbetalningsplan", className="card-title"),
                        dcc.Graph(id='amortization-graph'),
                    ])
                ])
            ], width=12)
        ]),
        
        # Store and interval for auto-refresh
        dcc.Store(id='selected-loan-id', data=None),
        dcc.Interval(id='loans-interval', interval=5000, n_intervals=0)
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
            children=create_bills_tab()
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
            children=create_loans_tab()
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


# Callback: Add Bill
@app.callback(
    Output('bill-add-status', 'children'),
    Input('add-bill-btn', 'n_clicks'),
    [State('bill-name-input', 'value'),
     State('bill-amount-input', 'value'),
     State('bill-due-date-input', 'value'),
     State('bill-category-dropdown', 'value'),
     State('bill-description-input', 'value')],
    prevent_initial_call=True
)
def add_bill(n_clicks, name, amount, due_date, category, description):
    """Add a new bill."""
    if not name or not amount or not due_date:
        return dbc.Alert("Fyll i namn, belopp och förfallodatum", color="warning")
    
    try:
        bill_manager = BillManager()
        bill = bill_manager.add_bill(
            name=name,
            amount=float(amount),
            due_date=due_date,
            description=description or "",
            category=category or "Övrigt"
        )
        return dbc.Alert(f"✓ Faktura '{name}' tillagd!", color="success", dismissable=True)
    except Exception as e:
        return dbc.Alert(f"Fel: {str(e)}", color="danger")


# Callback: Import Bills from PDF
@app.callback(
    Output('bill-add-status', 'children', allow_duplicate=True),
    Input('import-pdf-btn', 'n_clicks'),
    prevent_initial_call=True
)
def import_bills_from_pdf(n_clicks):
    """Import bills from PDF (demo with placeholder data)."""
    try:
        bill_manager = BillManager()
        pdf_parser = PDFBillParser()
        
        # Use placeholder data
        count = pdf_parser.import_bills_to_manager("placeholder.pdf", bill_manager)
        
        return dbc.Alert(f"✓ {count} fakturor importerade från PDF (demo)", color="success", dismissable=True)
    except Exception as e:
        return dbc.Alert(f"Fel: {str(e)}", color="danger")


# Callback: Match Bills to Transactions
@app.callback(
    Output('bill-add-status', 'children', allow_duplicate=True),
    Input('match-bills-btn', 'n_clicks'),
    prevent_initial_call=True
)
def match_bills(n_clicks):
    """Match pending bills to transactions."""
    try:
        bill_manager = BillManager()
        account_manager = AccountManager()
        matcher = BillMatcher(bill_manager, account_manager)
        
        matches = matcher.match_bills_to_transactions()
        
        if matches:
            return dbc.Alert(f"✓ {len(matches)} fakturor matchade mot transaktioner!", color="success", dismissable=True)
        else:
            return dbc.Alert("Inga matchningar hittades", color="info", dismissable=True)
    except Exception as e:
        return dbc.Alert(f"Fel: {str(e)}", color="danger")


# Callback: Update Bills Table
@app.callback(
    Output('bills-table-container', 'children'),
    [Input('bill-status-filter', 'value'),
     Input('bills-interval', 'n_intervals'),
     Input('add-bill-btn', 'n_clicks'),
     Input('import-pdf-btn', 'n_clicks'),
     Input('match-bills-btn', 'n_clicks')]
)
def update_bills_table(status_filter, n, add_clicks, import_clicks, match_clicks):
    """Update the bills table based on status filter."""
    try:
        bill_manager = BillManager()
        
        # Get bills based on filter
        if status_filter == 'all':
            bills = bill_manager.get_bills()
        else:
            bills = bill_manager.get_bills(status=status_filter)
        
        if not bills:
            return html.P("Inga fakturor funna", className="text-muted")
        
        # Create table
        df = pd.DataFrame(bills)
        table = dash_table.DataTable(
            id='bills-table',
            columns=[
                {'name': 'ID', 'id': 'id'},
                {'name': 'Namn', 'id': 'name'},
                {'name': 'Belopp', 'id': 'amount'},
                {'name': 'Förfallodatum', 'id': 'due_date'},
                {'name': 'Status', 'id': 'status'},
                {'name': 'Kategori', 'id': 'category'},
            ],
            data=df.to_dict('records'),
            style_cell={'textAlign': 'left', 'padding': '10px'},
            style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
            style_data_conditional=[
                {
                    'if': {'filter_query': '{status} = "overdue"'},
                    'backgroundColor': '#ffebee',
                    'color': '#c62828'
                },
                {
                    'if': {'filter_query': '{status} = "paid"'},
                    'backgroundColor': '#e8f5e9',
                    'color': '#2e7d32'
                }
            ],
            row_selectable='single',
            selected_rows=[]
        )
        
        return table
    except Exception as e:
        return html.P(f"Fel vid laddning av fakturor: {str(e)}", className="text-danger")


# Callback: Add Loan
@app.callback(
    Output('loan-add-status', 'children'),
    Input('add-loan-btn', 'n_clicks'),
    [State('loan-name-input', 'value'),
     State('loan-principal-input', 'value'),
     State('loan-interest-input', 'value'),
     State('loan-term-input', 'value'),
     State('loan-start-date-input', 'value'),
     State('loan-fixed-end-date-input', 'value'),
     State('loan-description-input', 'value')],
    prevent_initial_call=True
)
def add_loan(n_clicks, name, principal, interest_rate, term_months, start_date, fixed_end_date, description):
    """Add a new loan."""
    if not name or not principal or not interest_rate or not start_date:
        return dbc.Alert("Fyll i namn, belopp, ränta och startdatum", color="warning")
    
    try:
        loan_manager = LoanManager()
        loan = loan_manager.add_loan(
            name=name,
            principal=float(principal),
            interest_rate=float(interest_rate),
            start_date=start_date,
            term_months=int(term_months) if term_months else 360,
            fixed_rate_end_date=fixed_end_date if fixed_end_date else None,
            description=description or ""
        )
        return dbc.Alert(f"✓ Lån '{name}' tillagt!", color="success", dismissable=True)
    except Exception as e:
        return dbc.Alert(f"Fel: {str(e)}", color="danger")


# Callback: Update Loans Table
@app.callback(
    Output('loans-table-container', 'children'),
    [Input('loans-interval', 'n_intervals'),
     Input('add-loan-btn', 'n_clicks')]
)
def update_loans_table(n, add_clicks):
    """Update the loans table."""
    try:
        loan_manager = LoanManager()
        loans = loan_manager.get_loans(status='active')
        
        if not loans:
            return html.P("Inga aktiva lån funna", className="text-muted")
        
        # Create table with calculated monthly payment
        loans_display = []
        for loan in loans:
            monthly_payment = loan_manager.calculate_monthly_payment(
                loan['current_balance'],
                loan['interest_rate'],
                loan['term_months']
            )
            loans_display.append({
                'id': loan['id'],
                'name': loan['name'],
                'balance': f"{loan['current_balance']:,.2f}",
                'interest_rate': f"{loan['interest_rate']}%",
                'monthly_payment': f"{monthly_payment:,.2f}",
                'term_months': loan['term_months']
            })
        
        df = pd.DataFrame(loans_display)
        table = dash_table.DataTable(
            id='loans-table',
            columns=[
                {'name': 'ID', 'id': 'id'},
                {'name': 'Namn', 'id': 'name'},
                {'name': 'Saldo (SEK)', 'id': 'balance'},
                {'name': 'Ränta', 'id': 'interest_rate'},
                {'name': 'Månadsbetalning (SEK)', 'id': 'monthly_payment'},
                {'name': 'Löptid (mån)', 'id': 'term_months'},
            ],
            data=df.to_dict('records'),
            style_cell={'textAlign': 'left', 'padding': '10px'},
            style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
            row_selectable='single',
            selected_rows=[]
        )
        
        return table
    except Exception as e:
        return html.P(f"Fel vid laddning av lån: {str(e)}", className="text-danger")


# Callback: Update Loan Selector
@app.callback(
    Output('loan-selector', 'options'),
    [Input('loans-interval', 'n_intervals'),
     Input('add-loan-btn', 'n_clicks')]
)
def update_loan_selector(n, add_clicks):
    """Update loan selector dropdown."""
    loan_manager = LoanManager()
    loans = loan_manager.get_loans(status='active')
    return [{'label': loan['name'], 'value': loan['id']} for loan in loans]


# Callback: Simulate Interest Rate Change
@app.callback(
    Output('simulation-result', 'children'),
    Input('simulate-btn', 'n_clicks'),
    [State('loan-selector', 'value'),
     State('new-interest-input', 'value')],
    prevent_initial_call=True
)
def simulate_interest_change(n_clicks, loan_id, new_interest):
    """Simulate interest rate change for selected loan."""
    if not loan_id or not new_interest:
        return dbc.Alert("Välj ett lån och ange ny ränta", color="warning")
    
    try:
        loan_manager = LoanManager()
        result = loan_manager.simulate_interest_change(loan_id, float(new_interest))
        
        if not result:
            return dbc.Alert("Lån hittades inte", color="danger")
        
        return dbc.Card([
            dbc.CardBody([
                html.H6(f"Simulering för: {result['loan_name']}", className="card-title"),
                html.P(f"Nuvarande saldo: {result['current_balance']:,.2f} SEK"),
                html.Hr(),
                html.P([
                    html.Strong("Nuvarande ränta: "),
                    f"{result['current_interest_rate']}%"
                ]),
                html.P([
                    html.Strong("Nuvarande månadsbetalning: "),
                    f"{result['current_monthly_payment']:,.2f} SEK"
                ]),
                html.Hr(),
                html.P([
                    html.Strong("Ny ränta: "),
                    f"{result['new_interest_rate']}%"
                ]),
                html.P([
                    html.Strong("Ny månadsbetalning: "),
                    f"{result['new_monthly_payment']:,.2f} SEK"
                ]),
                html.Hr(),
                html.P([
                    html.Strong("Skillnad: "),
                    html.Span(
                        f"{result['difference']:+,.2f} SEK ({result['difference_percent']:+.2f}%)",
                        style={'color': '#dc3545' if result['difference'] > 0 else '#28a745', 'fontWeight': 'bold'}
                    )
                ])
            ])
        ], color='light', className="mt-3")
    except Exception as e:
        return dbc.Alert(f"Fel: {str(e)}", color="danger")


# Callback: Update Amortization Graph
@app.callback(
    Output('amortization-graph', 'figure'),
    [Input('loan-selector', 'value'),
     Input('loans-interval', 'n_intervals')]
)
def update_amortization_graph(loan_id, n):
    """Update amortization schedule graph for selected loan."""
    if not loan_id:
        fig = go.Figure()
        fig.add_annotation(
            text="Välj ett lån för att visa återbetalningsplan",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    try:
        loan_manager = LoanManager()
        schedule = loan_manager.get_amortization_schedule(loan_id, months=12)
        
        if not schedule:
            fig = go.Figure()
            fig.add_annotation(
                text="Ingen återbetalningsplan tillgänglig",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig
        
        df = pd.DataFrame(schedule)
        
        fig = go.Figure()
        
        # Add balance line
        fig.add_trace(go.Scatter(
            x=df['month'],
            y=df['balance'],
            mode='lines+markers',
            name='Kvarstående saldo',
            line=dict(color='#0d6efd', width=3),
            marker=dict(size=6)
        ))
        
        # Add principal and interest as stacked bar
        fig.add_trace(go.Bar(
            x=df['month'],
            y=df['principal'],
            name='Amortering',
            marker_color='#28a745'
        ))
        
        fig.add_trace(go.Bar(
            x=df['month'],
            y=df['interest'],
            name='Ränta',
            marker_color='#ffc107'
        ))
        
        fig.update_layout(
            title='Återbetalningsplan (12 månader)',
            xaxis_title='Månad',
            yaxis_title='Belopp (SEK)',
            hovermode='x unified',
            template='plotly_white',
            barmode='stack'
        )
        
        return fig
    except Exception as e:
        fig = go.Figure()
        fig.add_annotation(
            text=f"Fel: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig


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
