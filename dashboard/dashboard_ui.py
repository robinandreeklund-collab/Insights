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
from modules.core.history_viewer import HistoryViewer
from modules.core.income_tracker import IncomeTracker
from modules.core.agent_interface import AgentInterface
from modules.core.settings_panel import SettingsPanel
from modules.core.ai_trainer import AITrainer
from modules.core.category_manager import CategoryManager


def clear_data_on_exit(signum=None, frame=None):
    """Clear transactions, accounts, bills, and loans data files on exit.
    
    Note: training_data.yaml is preserved to maintain AI learning.
    """
    print("\n\nClearing data files before exit...")
    
    yaml_dir = "yaml"
    transactions_file = os.path.join(yaml_dir, "transactions.yaml")
    accounts_file = os.path.join(yaml_dir, "accounts.yaml")
    bills_file = os.path.join(yaml_dir, "bills.yaml")
    loans_file = os.path.join(yaml_dir, "loans.yaml")
    
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
        
        # Reset bills.yaml
        if os.path.exists(bills_file):
            with open(bills_file, 'w', encoding='utf-8') as f:
                yaml.dump({'bills': []}, f, default_flow_style=False, allow_unicode=True)
            print(f"✓ Cleared {bills_file}")
        
        # Reset loans.yaml
        if os.path.exists(loans_file):
            with open(loans_file, 'w', encoding='utf-8') as f:
                yaml.dump({'loans': []}, f, default_flow_style=False, allow_unicode=True)
            print(f"✓ Cleared {loans_file}")
        
        print("Data files cleared successfully! (training_data.yaml preserved)")
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
# Initialize category manager and load categories
category_manager = CategoryManager()
CATEGORIES = category_manager.get_categories()

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
    """Create the Input tab with drag-and-drop CSV upload and income input."""
    return html.Div([
        html.H3("Inmatning", className="mt-3 mb-4"),
        
        # CSV Import section
        dbc.Row([
            dbc.Col([
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
            ], width=12)
        ], className="mb-4"),
        
        # Income input section
        dbc.Row([
            dbc.Col([
                create_income_section()
            ], width=12)
        ])
    ], className="p-3")


# Create accounts tab content with transaction browser
def create_accounts_tab():
    """Create the Accounts tab with transaction browser and manual categorization."""
    return html.Div([
        html.H3("Konton", className="mt-3 mb-4"),
        
        # Account selector and management
        dbc.Row([
            dbc.Col([
                html.Label("Välj konto:", className="fw-bold"),
                dcc.Dropdown(
                    id='account-selector',
                    placeholder="Välj ett konto...",
                    className="mb-3"
                )
            ], width=6),
            dbc.Col([
                html.Label("Hantera konto:", className="fw-bold"),
                html.Div([
                    dbc.Button("Redigera konto", id='edit-account-btn', size="sm", color="primary", className="me-2"),
                    dbc.Button("Ta bort konto", id='delete-account-btn', size="sm", color="danger"),
                ], className="mt-2")
            ], width=6)
        ]),
        
        # Account edit modal
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Redigera konto")),
            dbc.ModalBody([
                html.Label("Kontonamn:", className="fw-bold mb-2"),
                dbc.Input(id='edit-account-name-input', type='text', placeholder='Kontonamn'),
                html.Div(id='edit-account-status', className="mt-2")
            ]),
            dbc.ModalFooter([
                dbc.Button("Avbryt", id='edit-account-cancel-btn', color="secondary"),
                dbc.Button("Spara", id='edit-account-save-btn', color="primary")
            ])
        ], id='edit-account-modal', is_open=False),
        
        # Delete confirmation modal
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Bekräfta borttagning")),
            dbc.ModalBody([
                html.P(id='delete-account-confirm-text'),
            ]),
            dbc.ModalFooter([
                dbc.Button("Avbryt", id='delete-account-cancel-btn', color="secondary"),
                dbc.Button("Ta bort", id='delete-account-confirm-btn', color="danger")
            ])
        ], id='delete-account-modal', is_open=False),
        
        html.Div(id='account-action-status', className="mt-2"),
        
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
        
        # Categorization section with dropdown selectors
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Kategorisering", className="card-title"),
                        html.P("Välj en transaktion i tabellen ovan för att kategorisera den", className="text-muted mb-3"),
                        html.Div(id='categorization-form'),
                    ])
                ])
            ], width=12)
        ], className="mb-4"),
        
        # Action buttons section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("AI-träning", className="card-title"),
                        html.P("Träna AI-modellen med manuellt kategoriserade transaktioner", className="text-muted mb-3"),
                        dbc.Button("🤖 Träna med AI", id='train-from-table-btn', color="success", className="me-2"),
                        html.Div(id='table-action-status', className="mt-3")
                    ])
                ])
            ], width=12)
        ]),
        
        # Loan matching section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Lånmatchning", className="card-title"),
                        html.P("Matcha valda transaktioner till lån för att automatiskt uppdatera lånesaldon.", 
                               className="text-muted mb-3"),
                        dbc.Row([
                            dbc.Col([
                                html.Label("Välj lån:", className="fw-bold"),
                                dcc.Dropdown(
                                    id='loan-match-dropdown',
                                    placeholder="Välj ett lån att matcha till...",
                                    className="mb-2"
                                )
                            ], width=8),
                            dbc.Col([
                                dbc.Button("Matcha till lån", id='match-loan-btn', color="info", className="mt-4"),
                            ], width=4)
                        ]),
                        html.Div(id='loan-match-status', className="mt-3")
                    ])
                ])
            ], width=12)
        ]),
        
        # Store for current page and table changes
        dcc.Store(id='current-page', data=0),
        dcc.Store(id='selected-transaction-id', data=None),
        dcc.Store(id='table-refresh-trigger', data=0),
        
        # Interval for auto-refresh of dropdowns (not the table data)
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
                                dbc.Button("Matcha fakturor", id='match-bills-btn', color="info", className="me-2"),
                            ], width=12),
                        ]),
                        html.Div(id='bill-add-status', className="mt-3")
                    ])
                ])
            ], width=12)
        ], className="mb-4"),
        
        # PDF import section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Importera fakturor från PDF", className="card-title"),
                        html.P("Ladda upp en PDF-fil med fakturor för att automatiskt extrahera fakturainformation"),
                        dcc.Upload(
                            id='upload-pdf-bills',
                            children=html.Div([
                                html.I(className="bi bi-file-pdf", style={'fontSize': '48px'}),
                                html.Br(),
                                'Dra och släpp eller klicka för att välja PDF-fil'
                            ]),
                            style={
                                'width': '100%',
                                'height': '150px',
                                'lineHeight': '150px',
                                'borderWidth': '2px',
                                'borderStyle': 'dashed',
                                'borderRadius': '10px',
                                'textAlign': 'center',
                                'backgroundColor': '#f8f9fa'
                            },
                            multiple=False
                        ),
                        html.Div(id='pdf-import-status', className="mt-3")
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


# Create history tab content
def create_history_tab():
    """Create the History tab with monthly summaries and trends."""
    return html.Div([
        html.H3("Historik", className="mt-3 mb-4"),
        
        # Month selector
        dbc.Row([
            dbc.Col([
                html.Label("Välj månad:", className="fw-bold"),
                dcc.Dropdown(
                    id='history-month-selector',
                    placeholder="Välj en månad...",
                    className="mb-3"
                )
            ], width=4)
        ]),
        
        # Monthly summary section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Månadssammanfattning", className="card-title"),
                        html.Div(id='monthly-summary-display')
                    ])
                ])
            ], width=12)
        ], className="mb-4"),
        
        # Category trends section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Kategoritrender", className="card-title"),
                        dcc.Dropdown(
                            id='trend-category-selector',
                            options=[{'label': cat, 'value': cat} for cat in CATEGORIES.keys()],
                            value='Mat & Dryck',
                            className="mb-3"
                        ),
                        dcc.Graph(id='category-trend-graph')
                    ])
                ])
            ], width=12)
        ], className="mb-4"),
        
        # Top expenses section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Största utgifter", className="card-title"),
                        html.Div(id='top-expenses-display')
                    ])
                ])
            ], width=12)
        ]),
        
        # Interval for auto-refresh
        dcc.Interval(id='history-interval', interval=5000, n_intervals=0)
    ], className="p-3")


# Create agent tab content
def create_agent_tab():
    """Create the Agent Analysis tab with query interface."""
    return html.Div([
        html.H3("Frågebaserad analys", className="mt-3 mb-4"),
        html.P("Ställ frågor om din ekonomi i naturligt språk. Exempel: 'Hur mycket har jag kvar i november?', 'Visa fakturor', 'Simulera ränta 4.5%'"),
        
        # Query input section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Ställ en fråga", className="card-title"),
                        dbc.Textarea(
                            id='agent-query-input',
                            placeholder='Skriv din fråga här...',
                            style={'minHeight': '100px'},
                            className="mb-3"
                        ),
                        dbc.Button("Skicka fråga", id='agent-submit-btn', color="primary"),
                    ])
                ])
            ], width=12)
        ], className="mb-4"),
        
        # Response section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Svar", className="card-title"),
                        html.Div(id='agent-response-display', style={'whiteSpace': 'pre-line', 'minHeight': '200px'})
                    ])
                ])
            ], width=12)
        ], className="mb-4"),
        
        # Example queries
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Exempel på frågor", className="card-title"),
                        html.Ul([
                            html.Li("Hur mycket saldo har jag?"),
                            html.Li("Visa alla fakturor"),
                            html.Li("Vilka lån har jag?"),
                            html.Li("Simulera ränteökning till 4.5%"),
                            html.Li("Visa inkomster denna månad"),
                            html.Li("Största utgifter denna månad"),
                            html.Li("Trend för Mat & Dryck"),
                        ])
                    ])
                ])
            ], width=12)
        ])
    ], className="p-3")


# Create income tab content (add to Input tab)
def create_income_section():
    """Create income input section to be added to Input tab."""
    return dbc.Card([
        dbc.CardBody([
            html.H5("Lägg till inkomst", className="card-title mb-3"),
            dbc.Row([
                dbc.Col([
                    html.Label("Person:", className="fw-bold"),
                    dbc.Input(id='income-person-input', type='text', placeholder='T.ex. Robin'),
                ], width=4),
                dbc.Col([
                    html.Label("Konto:", className="fw-bold"),
                    dcc.Dropdown(id='income-account-dropdown', placeholder='Välj konto...'),
                ], width=4),
                dbc.Col([
                    html.Label("Kategori:", className="fw-bold"),
                    dcc.Dropdown(
                        id='income-category-dropdown',
                        options=[
                            {'label': 'Lön', 'value': 'Lön'},
                            {'label': 'Bonus', 'value': 'Bonus'},
                            {'label': 'Återbäring', 'value': 'Återbäring'},
                            {'label': 'Övrigt', 'value': 'Övrigt'}
                        ],
                        value='Lön'
                    ),
                ], width=4),
            ], className="mb-3"),
            dbc.Row([
                dbc.Col([
                    html.Label("Belopp (SEK):", className="fw-bold"),
                    dbc.Input(id='income-amount-input', type='number', placeholder='0.00'),
                ], width=4),
                dbc.Col([
                    html.Label("Datum:", className="fw-bold"),
                    dbc.Input(id='income-date-input', type='date'),
                ], width=4),
                dbc.Col([
                    html.Label("Beskrivning:", className="fw-bold"),
                    dbc.Input(id='income-description-input', type='text', placeholder='Valfri beskrivning...'),
                ], width=4),
            ], className="mb-3"),
            dbc.Button("Lägg till inkomst", id='add-income-btn', color="success"),
            html.Div(id='income-add-status', className="mt-3")
        ])
    ])


# Create settings tab content
def create_settings_tab():
    """Create the Settings tab with configuration options."""
    return html.Div([
        html.H3("Inställningar", className="mt-3 mb-4"),
        
        # General settings
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Allmänna inställningar", className="card-title"),
                        dbc.Row([
                            dbc.Col([
                                html.Label("Valuta:", className="fw-bold"),
                                dcc.Dropdown(
                                    id='settings-currency',
                                    options=[
                                        {'label': 'SEK - Svenska kronor', 'value': 'SEK'},
                                        {'label': 'EUR - Euro', 'value': 'EUR'},
                                        {'label': 'USD - US Dollar', 'value': 'USD'}
                                    ],
                                    value='SEK'
                                )
                            ], width=6),
                            dbc.Col([
                                html.Label("Decimaler:", className="fw-bold"),
                                dcc.Slider(
                                    id='settings-decimals',
                                    min=0, max=4, step=1, value=2,
                                    marks={i: str(i) for i in range(5)}
                                )
                            ], width=6)
                        ], className="mb-3"),
                    ])
                ])
            ], width=12)
        ], className="mb-4"),
        
        # Display settings
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Visningsinställningar", className="card-title"),
                        dbc.Row([
                            dbc.Col([
                                html.Label("Transaktioner per sida:", className="fw-bold"),
                                dcc.Slider(
                                    id='settings-items-per-page',
                                    min=10, max=200, step=10, value=50,
                                    marks={i: str(i) for i in [10, 50, 100, 200]}
                                )
                            ], width=6),
                            dbc.Col([
                                html.Label("Uppdateringsintervall (sekunder):", className="fw-bold"),
                                dcc.Slider(
                                    id='settings-refresh-interval',
                                    min=1, max=60, step=1, value=5,
                                    marks={i: str(i) for i in [1, 5, 10, 30, 60]}
                                )
                            ], width=6)
                        ], className="mb-3"),
                        dbc.Checklist(
                            id='settings-display-options',
                            options=[
                                {'label': ' Automatisk uppdatering', 'value': 'auto_refresh'},
                                {'label': ' Visa cirkeldiagram', 'value': 'show_pie'},
                                {'label': ' Visa prognosgraf', 'value': 'show_forecast'}
                            ],
                            value=['auto_refresh', 'show_pie', 'show_forecast'],
                            inline=True
                        )
                    ])
                ])
            ], width=12)
        ], className="mb-4"),
        
        # Notification settings
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Notifieringar", className="card-title"),
                        dbc.Checklist(
                            id='settings-notifications',
                            options=[
                                {'label': ' Fakturavarningar', 'value': 'bill_reminders'},
                                {'label': ' Lågt saldolarm', 'value': 'low_balance'}
                            ],
                            value=['bill_reminders', 'low_balance'],
                            inline=True,
                            className="mb-3"
                        ),
                        dbc.Row([
                            dbc.Col([
                                html.Label("Påminnelse dagar före förfallodatum:", className="fw-bold"),
                                dbc.Input(id='settings-reminder-days', type='number', value=3, min=0, max=30)
                            ], width=6),
                            dbc.Col([
                                html.Label("Lågt saldo gräns (SEK):", className="fw-bold"),
                                dbc.Input(id='settings-low-balance-threshold', type='number', value=1000.0, step=100)
                            ], width=6)
                        ])
                    ])
                ])
            ], width=12)
        ], className="mb-4"),
        
        # AI Training settings
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("AI-träning för kategorisering", className="card-title"),
                        html.P("Träna AI-modellen från manuella kategoriseringar för att förbättra automatisk kategorisering.", 
                               className="text-muted"),
                        
                        html.Div(id='ai-training-stats', className="mb-3"),
                        
                        dbc.Row([
                            dbc.Col([
                                dbc.Button("Visa träningsdata", id='view-training-data-btn', color="info", className="me-2"),
                                dbc.Button("Starta träning", id='start-training-btn', color="success", className="me-2"),
                                dbc.Button("Rensa träningsdata", id='clear-training-data-btn', color="warning"),
                            ], width=12)
                        ]),
                        
                        html.Div(id='ai-training-status', className="mt-3")
                    ])
                ])
            ], width=12)
        ], className="mb-4"),
        
        # Save button
        dbc.Row([
            dbc.Col([
                dbc.Button("Spara inställningar", id='save-settings-btn', color="primary", size="lg"),
                dbc.Button("Återställ till standard", id='reset-settings-btn', color="secondary", size="lg", className="ms-2"),
                html.Div(id='settings-save-status', className="mt-3")
            ], width=12)
        ]),
        
        # Interval for AI training stats update
        dcc.Interval(id='ai-training-interval', interval=10000, n_intervals=0)
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
            children=create_history_tab()
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
            children=create_agent_tab()
        ),
        
        # Inställningar
        dcc.Tab(
            label="Inställningar",
            value="settings",
            children=create_settings_tab()
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


# Callback: Open Edit Account Modal
@app.callback(
    [Output('edit-account-modal', 'is_open'),
     Output('edit-account-name-input', 'value')],
    [Input('edit-account-btn', 'n_clicks'),
     Input('edit-account-cancel-btn', 'n_clicks'),
     Input('edit-account-save-btn', 'n_clicks')],
    [State('account-selector', 'value'),
     State('edit-account-modal', 'is_open')]
)
def toggle_edit_account_modal(edit_clicks, cancel_clicks, save_clicks, selected_account, is_open):
    """Toggle edit account modal."""
    ctx = callback_context
    if not ctx.triggered:
        return False, ""
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'edit-account-btn' and selected_account:
        return True, selected_account
    elif button_id in ['edit-account-cancel-btn', 'edit-account-save-btn']:
        return False, ""
    
    return is_open, selected_account or ""


# Callback: Save Edited Account
@app.callback(
    Output('edit-account-status', 'children'),
    Input('edit-account-save-btn', 'n_clicks'),
    [State('account-selector', 'value'),
     State('edit-account-name-input', 'value')]
)
def save_edited_account(n_clicks, old_name, new_name):
    """Save edited account name."""
    if not n_clicks or not old_name or not new_name:
        return ""
    
    if old_name == new_name:
        return dbc.Alert("Inget ändrat", color="info", dismissable=True)
    
    manager = AccountManager()
    result = manager.update_account(old_name, new_name=new_name)
    
    if result:
        return dbc.Alert(f"Konto uppdaterat från '{old_name}' till '{new_name}'", color="success", dismissable=True)
    else:
        return dbc.Alert("Kunde inte uppdatera konto", color="danger", dismissable=True)


# Callback: Open Delete Account Modal
@app.callback(
    [Output('delete-account-modal', 'is_open'),
     Output('delete-account-confirm-text', 'children')],
    [Input('delete-account-btn', 'n_clicks'),
     Input('delete-account-cancel-btn', 'n_clicks'),
     Input('delete-account-confirm-btn', 'n_clicks')],
    [State('account-selector', 'value'),
     State('delete-account-modal', 'is_open')]
)
def toggle_delete_account_modal(delete_clicks, cancel_clicks, confirm_clicks, selected_account, is_open):
    """Toggle delete account modal."""
    ctx = callback_context
    if not ctx.triggered:
        return False, ""
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'delete-account-btn' and selected_account:
        return True, f"Är du säker på att du vill ta bort kontot '{selected_account}'? Alla transaktioner för detta konto kommer att behållas men kontot kommer att försvinna från listan."
    elif button_id in ['delete-account-cancel-btn', 'delete-account-confirm-btn']:
        return False, ""
    
    return is_open, ""


# Callback: Confirm Delete Account
@app.callback(
    Output('account-action-status', 'children'),
    Input('delete-account-confirm-btn', 'n_clicks'),
    State('account-selector', 'value')
)
def confirm_delete_account(n_clicks, account_name):
    """Delete the selected account."""
    if not n_clicks or not account_name:
        return ""
    
    manager = AccountManager()
    success = manager.delete_account(account_name)
    
    if success:
        return dbc.Alert(f"Konto '{account_name}' har tagits bort", color="success", dismissable=True, duration=4000)
    else:
        return dbc.Alert("Kunde inte ta bort konto", color="danger", dismissable=True, duration=4000)


# Callback: Update Transaction Table
@app.callback(
    [Output('transaction-table-container', 'children'),
     Output('page-info', 'children')],
    [Input('account-selector', 'value'),
     Input('current-page', 'data'),
     Input('table-refresh-trigger', 'data')],
    State('selected-transaction-id', 'data')
)
def update_transaction_table(account_name, current_page, refresh_trigger, selected_tx_id):
    """Update the transaction table for the selected account."""
    if not account_name:
        return html.P("Välj ett konto för att visa transaktioner", className="text-muted"), ""
    
    manager = AccountManager()
    transactions = manager.get_account_transactions(account_name)
    
    if not transactions:
        return html.P("Inga transaktioner funna", className="text-muted"), ""
    
    # Pagination - use settings
    panel = SettingsPanel()
    per_page = panel.get_setting('display', 'items_per_page') or 50
    current_page = current_page or 0
    total_pages = (len(transactions) - 1) // per_page + 1
    start_idx = current_page * per_page
    end_idx = min(start_idx + per_page, len(transactions))
    page_transactions = transactions[start_idx:end_idx]
    
    # Create table (non-editable, selection-based)
    df = pd.DataFrame(page_transactions)
    
    # Try to find and re-select the previously selected transaction
    selected_rows = []
    if selected_tx_id:
        for idx, tx in enumerate(page_transactions):
            tx_id = f"{tx.get('date')}_{tx.get('description')}_{tx.get('amount')}"
            if tx_id == selected_tx_id:
                selected_rows = [idx]
                break
    
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
            },
            {
                'if': {'column_id': 'category'},
                'backgroundColor': '#e8f4f8'
            },
            {
                'if': {'column_id': 'subcategory'},
                'backgroundColor': '#e8f4f8'
            }
        ],
        row_selectable='single',
        selected_rows=selected_rows
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
    """Handle pagination buttons."""
    if not account_name:
        return 0
    
    ctx = callback_context
    if not ctx.triggered:
        return current_page or 0
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    current_page = current_page or 0
    
    manager = AccountManager()
    transactions = manager.get_account_transactions(account_name)
    panel = SettingsPanel()
    per_page = panel.get_setting('display', 'items_per_page') or 50
    total_pages = (len(transactions) - 1) // per_page + 1
    
    if button_id == 'prev-page-btn' and current_page > 0:
        return current_page - 1
    elif button_id == 'next-page-btn' and current_page < total_pages - 1:
        return current_page + 1
    
    return current_page


# Callback: Store Selected Transaction ID
@app.callback(
    Output('selected-transaction-id', 'data'),
    [Input('transaction-table', 'selected_rows'),
     Input('transaction-table', 'data')]
)
def store_selected_transaction(selected_rows, table_data):
    """Store the ID of the selected transaction for persistence across refreshes."""
    if not selected_rows or not table_data:
        return None
    
    selected_tx = table_data[selected_rows[0]]
    # Create a unique ID from date, description, and amount
    tx_id = f"{selected_tx.get('date')}_{selected_tx.get('description')}_{selected_tx.get('amount')}"
    return tx_id


# Callback: Show Categorization Form
@app.callback(
    Output('categorization-form', 'children'),
    [Input('transaction-table', 'selected_rows'),
     Input('transaction-table', 'data')]
)
def show_categorization_form(selected_rows, table_data):
    """Show the categorization form when a transaction is selected."""
    if not selected_rows or not table_data:
        return html.P("Välj en transaktion i tabellen ovan genom att klicka på raden", className="text-muted")
    
    selected_tx = table_data[selected_rows[0]]
    
    # Reload categories to get any newly added ones
    categories = category_manager.get_categories()
    
    # IMPORTANT: Also load categories from existing transactions
    # This ensures categories that were created before CategoryManager are available
    account_manager = AccountManager()
    all_transactions = account_manager.get_all_transactions()
    
    # Discover unique categories from transactions
    for tx in all_transactions:
        cat = tx.get('category')
        subcat = tx.get('subcategory')
        if cat and cat not in categories:
            categories[cat] = []
        if cat and subcat and subcat not in categories[cat]:
            categories[cat].append(subcat)
    
    # Get current category and subcategory values
    # Handle None, empty string, or missing keys
    current_category = selected_tx.get('category')
    current_subcategory = selected_tx.get('subcategory')
    
    # If empty or None, use defaults ONLY if they don't have values
    if not current_category or current_category == '':
        current_category = 'Övrigt'
    if not current_subcategory or current_subcategory == '':
        current_subcategory = 'Okategoriserat'
    
    # Get subcategory options for the current category
    subcategory_options = []
    if current_category and current_category in categories:
        subcategory_options = [{'label': subcat, 'value': subcat} for subcat in categories[current_category]]
    
    return html.Div([
        html.H6(f"Kategorisera: {selected_tx['description']}", className="mb-3"),
        dbc.Row([
            dbc.Col([
                html.Label("Kategori:", className="fw-bold"),
                dcc.Dropdown(
                    id='category-dropdown',
                    options=[{'label': cat, 'value': cat} for cat in categories.keys()],
                    value=current_category,
                    className="mb-3",
                    clearable=False
                )
            ], width=6),
            dbc.Col([
                html.Label("Underkategori:", className="fw-bold"),
                dcc.Dropdown(
                    id='subcategory-dropdown',
                    options=subcategory_options,
                    value=current_subcategory,
                    className="mb-3",
                    clearable=False
                )
            ], width=6),
        ]),
        dbc.Button("💾 Spara kategorisering", id='save-category-btn', color="primary", className="mt-2 me-2"),
        html.Div(id='category-save-status', className="mt-2"),
        
        html.Hr(className="my-4"),
        
        # Add new category/subcategory section
        html.H6("Hantera kategorier", className="mb-3 mt-3"),
        dbc.Row([
            dbc.Col([
                html.Label("Ny huvudkategori:", className="fw-bold"),
                dbc.Input(id='new-category-input', placeholder="T.ex. Hälsa", className="mb-2")
            ], width=6),
            dbc.Col([
                dbc.Button("➕ Lägg till kategori", id='add-category-btn', color="info", className="mt-4"),
            ], width=6)
        ], className="mb-3"),
        dbc.Row([
            dbc.Col([
                html.Label("Ny underkategori (lägg till i vald kategori):", className="fw-bold"),
                dbc.Input(id='new-subcategory-input', placeholder="T.ex. Läkarbesök", className="mb-2")
            ], width=6),
            dbc.Col([
                dbc.Button("➕ Lägg till underkategori", id='add-subcategory-btn', color="info", className="mt-4"),
            ], width=6)
        ]),
        html.Div(id='category-management-status', className="mt-2")
    ])


# Callback: Update Subcategory Options
@app.callback(
    Output('subcategory-dropdown', 'options'),
    Input('category-dropdown', 'value')
)
def update_subcategory_options(category):
    """Update subcategory options based on selected category."""
    categories = category_manager.get_categories()
    
    # Also load categories from existing transactions
    account_manager = AccountManager()
    all_transactions = account_manager.get_all_transactions()
    
    # Discover unique categories from transactions
    for tx in all_transactions:
        cat = tx.get('category')
        subcat = tx.get('subcategory')
        if cat and cat not in categories:
            categories[cat] = []
        if cat and subcat and subcat not in categories[cat]:
            categories[cat].append(subcat)
    
    if category and category in categories:
        return [{'label': subcat, 'value': subcat} for subcat in categories[category]]
    return []


# Callback: Add New Category
@app.callback(
    [Output('category-management-status', 'children'),
     Output('new-category-input', 'value')],
    Input('add-category-btn', 'n_clicks'),
    State('new-category-input', 'value'),
    prevent_initial_call=True
)
def add_new_category(n_clicks, category_name):
    """Add a new category."""
    if not n_clicks or not category_name:
        return "", ""
    
    try:
        success = category_manager.add_category(category_name.strip())
        
        if success:
            # Reload global CATEGORIES
            global CATEGORIES
            CATEGORIES = category_manager.get_categories()
            
            return dbc.Alert(
                f"✓ Kategori '{category_name}' tillagd!", 
                color="success", 
                dismissable=True, 
                duration=3000
            ), ""
        else:
            return dbc.Alert(
                f"Kategori '{category_name}' finns redan", 
                color="warning", 
                dismissable=True, 
                duration=3000
            ), category_name
    except Exception as e:
        return dbc.Alert(f"Fel: {str(e)}", color="danger", dismissable=True, duration=3000), category_name


# Callback: Add New Subcategory
@app.callback(
    [Output('category-management-status', 'children', allow_duplicate=True),
     Output('new-subcategory-input', 'value')],
    Input('add-subcategory-btn', 'n_clicks'),
    [State('new-subcategory-input', 'value'),
     State('category-dropdown', 'value')],
    prevent_initial_call=True
)
def add_new_subcategory(n_clicks, subcategory_name, category_name):
    """Add a new subcategory to the selected category."""
    if not n_clicks or not subcategory_name or not category_name:
        return dbc.Alert(
            "Välj en kategori först innan du lägger till underkategori", 
            color="warning", 
            dismissable=True, 
            duration=3000
        ), subcategory_name
    
    try:
        success = category_manager.add_subcategory(category_name, subcategory_name.strip())
        
        if success:
            # Reload global CATEGORIES
            global CATEGORIES
            CATEGORIES = category_manager.get_categories()
            
            return dbc.Alert(
                f"✓ Underkategori '{subcategory_name}' tillagd till '{category_name}'!", 
                color="success", 
                dismissable=True, 
                duration=3000
            ), ""
        else:
            return dbc.Alert(
                f"Underkategori '{subcategory_name}' finns redan i '{category_name}'", 
                color="warning", 
                dismissable=True, 
                duration=3000
            ), subcategory_name
    except Exception as e:
        return dbc.Alert(f"Fel: {str(e)}", color="danger", dismissable=True, duration=3000), subcategory_name


# Callback: Save Manual Categorization
@app.callback(
    [Output('category-save-status', 'children'),
     Output('table-refresh-trigger', 'data')],
    Input('save-category-btn', 'n_clicks'),
    [State('transaction-table', 'selected_rows'),
     State('transaction-table', 'data'),
     State('category-dropdown', 'value'),
     State('subcategory-dropdown', 'value'),
     State('account-selector', 'value'),
     State('table-refresh-trigger', 'data')],
    prevent_initial_call=True
)
def save_manual_categorization(n_clicks, selected_rows, table_data, category, subcategory, account_name, current_trigger):
    """Save manual categorization for selected transaction - REFACTORED for reliability."""
    if not selected_rows or not table_data or not category:
        return "", current_trigger
    
    try:
        selected_tx = table_data[selected_rows[0]]
        
        # Create AccountManager instance
        manager = AccountManager()
        
        # Load transactions directly from file for most up-to-date data
        data = manager._load_yaml(manager.transactions_file)
        if not data or 'transactions' not in data:
            return dbc.Alert("⚠️ Kunde inte ladda transaktionsdata", color="danger", dismissable=True, duration=4000), current_trigger
        
        transactions = data['transactions']
        
        # Create a unique key for the selected transaction
        # Use date + description as base, and amount as discriminator
        selected_date = str(selected_tx.get('date', '')).strip()
        selected_desc = str(selected_tx.get('description', '')).strip()
        try:
            selected_amount = float(selected_tx.get('amount', 0))
        except (ValueError, TypeError):
            selected_amount = 0.0
        
        # Debug logging
        print(f"\n=== CATEGORIZATION SAVE DEBUG ===")
        print(f"Looking for transaction:")
        print(f"  Date: '{selected_date}'")
        print(f"  Description: '{selected_desc}'")
        print(f"  Amount: {selected_amount}")
        print(f"  Category: {category}")
        print(f"  Subcategory: {subcategory or '(ingen)'}")
        
        # Find and update the transaction
        transaction_found = False
        updated_count = 0
        
        for tx in transactions:
            tx_date = str(tx.get('date', '')).strip()
            tx_desc = str(tx.get('description', '')).strip()
            try:
                tx_amount = float(tx.get('amount', 0))
            except (ValueError, TypeError):
                tx_amount = 0.0
            
            # Match criteria: exact date and description, and amount within tolerance
            date_match = (tx_date == selected_date)
            desc_match = (tx_desc == selected_desc)
            amount_match = abs(tx_amount - selected_amount) < 0.01
            
            if date_match and desc_match and amount_match:
                print(f"  ✓ Found matching transaction in YAML")
                print(f"    Old category: {tx.get('category', 'N/A')}")
                print(f"    Old subcategory: {tx.get('subcategory', 'N/A')}")
                
                # Update categorization
                tx['category'] = category
                tx['subcategory'] = subcategory if subcategory else ""
                tx['categorized_manually'] = True
                
                print(f"    New category: {tx['category']}")
                print(f"    New subcategory: {tx['subcategory']}")
                
                transaction_found = True
                updated_count += 1
        
        if not transaction_found:
            print(f"  ✗ NO MATCH FOUND in {len(transactions)} transactions")
            print(f"\nFirst 3 transactions in YAML:")
            for i, tx in enumerate(transactions[:3]):
                print(f"  [{i}] Date: '{tx.get('date')}', Desc: '{tx.get('description')}', Amount: {tx.get('amount')}")
            
            return dbc.Alert(
                f"⚠️ Kunde inte hitta transaktion: '{selected_desc}' ({selected_date}, {selected_amount} SEK)", 
                color="danger", 
                dismissable=True, 
                duration=5000
            ), current_trigger
        
        # Save the modified transactions back to file
        data['transactions'] = transactions
        manager.save_transactions(data)
        
        print(f"  ✓ Saved {updated_count} transaction(s) to YAML file")
        print(f"=== END DEBUG ===\n")
        
        # Trigger table refresh by incrementing trigger
        new_trigger = (current_trigger or 0) + 1
        
        return dbc.Alert(
            f"✓ Kategorisering sparad! ({category} → {subcategory or 'Ingen underkategori'})", 
            color="success", 
            dismissable=True, 
            duration=3000
        ), new_trigger
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"\n=== ERROR IN CATEGORIZATION SAVE ===")
        print(error_trace)
        print(f"=== END ERROR ===\n")
        return dbc.Alert(
            f"⚠️ Fel vid sparande: {str(e)}", 
            color="danger", 
            dismissable=True, 
            duration=5000
        ), current_trigger


# Callback: Train AI from table
@app.callback(
    Output('table-action-status', 'children', allow_duplicate=True),
    Input('train-from-table-btn', 'n_clicks'),
    [State('transaction-table', 'data'),
     State('transaction-table', 'selected_rows')],
    prevent_initial_call=True
)
def train_ai_from_table(n_clicks, table_data, selected_rows):
    """Train AI from manually categorized transactions in the table."""
    if not n_clicks or not table_data:
        return ""
    
    try:
        trainer = AITrainer()
        
        # If rows are selected, train only from selected rows
        rows_to_train = []
        if selected_rows:
            rows_to_train = [table_data[i] for i in selected_rows]
        else:
            # Train from all rows in current view
            rows_to_train = table_data
        
        # Add training samples
        added_count = 0
        for row in rows_to_train:
            # Only add if category and subcategory are present
            if row.get('category') and row.get('subcategory'):
                trainer.add_training_sample(
                    description=row.get('description', ''),
                    category=row.get('category'),
                    subcategory=row.get('subcategory')
                )
                added_count += 1
        
        if added_count > 0:
            return dbc.Alert([
                html.H5("✓ Träningsdata tillagd!", className="alert-heading"),
                html.P(f"{added_count} transaktion{'er' if added_count > 1 else ''} tillagd{'a' if added_count > 1 else ''} till träningsdata."),
                html.Hr(),
                html.P("Gå till Inställningar → AI-träning för att starta träningen.", className="mb-0")
            ], color="success", dismissable=True, duration=8000)
        else:
            return dbc.Alert("Inga kategoriserade transaktioner att träna från", color="warning", dismissable=True, duration=4000)
    except Exception as e:
        return dbc.Alert(f"Fel: {str(e)}", color="danger", dismissable=True, duration=5000)


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


# Callback: Import Bills from PDF Upload
@app.callback(
    Output('pdf-import-status', 'children'),
    Input('upload-pdf-bills', 'contents'),
    State('upload-pdf-bills', 'filename'),
    prevent_initial_call=True
)
def import_bills_from_pdf(contents, filename):
    """Import bills from uploaded PDF file."""
    if contents is None:
        return ""
    
    try:
        # Decode the uploaded file
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        
        # Save to temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(decoded)
            tmp_path = tmp_file.name
        
        try:
            # Parse PDF and import bills
            bill_manager = BillManager()
            pdf_parser = PDFBillParser()
            
            # Parse the actual PDF file (not demo mode)
            count = pdf_parser.import_bills_to_manager(tmp_path, bill_manager, use_demo_data=False)
            
            return dbc.Alert(
                f"✓ {count} fakturor importerade från {filename}",
                color="success",
                dismissable=True
            )
        finally:
            # Clean up temporary file
            import os
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    except Exception as e:
        return dbc.Alert(f"Fel vid import av PDF: {str(e)}", color="danger", dismissable=True)
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
     Input('upload-pdf-bills', 'contents'),
     Input('match-bills-btn', 'n_clicks')]
)
def update_bills_table(status_filter, n, add_clicks, pdf_contents, match_clicks):
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


# Callback: History month selector
@app.callback(
    Output('history-month-selector', 'options'),
    Output('history-month-selector', 'value'),
    Input('history-interval', 'n_intervals')
)
def update_history_month_options(n):
    """Update available months for history view."""
    try:
        viewer = HistoryViewer()
        months = viewer.get_all_months()
        
        if not months:
            return [], None
        
        options = [{'label': month, 'value': month} for month in months]
        return options, months[0] if months else None
    except:
        return [], None


# Callback: Monthly summary display
@app.callback(
    Output('monthly-summary-display', 'children'),
    Input('history-month-selector', 'value'),
    Input('history-interval', 'n_intervals')
)
def update_monthly_summary(month, n):
    """Update monthly summary display."""
    if not month:
        return html.P("Välj en månad för att se sammanfattning.")
    
    try:
        viewer = HistoryViewer()
        summary = viewer.get_monthly_summary(month)
        
        return html.Div([
            dbc.Row([
                dbc.Col([
                    html.H6("Inkomster"),
                    html.H4(f"{summary['income']:.2f} SEK", className="text-success"),
                    html.Small(f"{summary['income_count']} transaktioner")
                ], width=3),
                dbc.Col([
                    html.H6("Utgifter"),
                    html.H4(f"{summary['expenses']:.2f} SEK", className="text-danger"),
                    html.Small(f"{summary['expense_count']} transaktioner")
                ], width=3),
                dbc.Col([
                    html.H6("Netto"),
                    html.H4(f"{summary['net']:.2f} SEK", className="text-primary"),
                    html.Small(f"Totalt {summary['total_transactions']} transaktioner")
                ], width=3),
            ])
        ])
    except Exception as e:
        return html.P(f"Fel: {str(e)}", className="text-danger")


# Callback: Category trend graph
@app.callback(
    Output('category-trend-graph', 'figure'),
    Input('trend-category-selector', 'value'),
    Input('history-interval', 'n_intervals')
)
def update_category_trend(category, n):
    """Update category trend graph."""
    try:
        viewer = HistoryViewer()
        trend = viewer.get_category_trend(category, months=6)
        
        months = [t['month'] for t in trend]
        amounts = [t['amount'] for t in trend]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=months,
            y=amounts,
            mode='lines+markers',
            name=category,
            line=dict(width=3),
            marker=dict(size=10)
        ))
        
        fig.update_layout(
            title=f'Trend för {category} (6 månader)',
            xaxis_title='Månad',
            yaxis_title='Belopp (SEK)',
            template='plotly_white'
        )
        
        return fig
    except Exception as e:
        fig = go.Figure()
        fig.add_annotation(
            text=f"Ingen data tillgänglig",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig


# Callback: Top expenses display
@app.callback(
    Output('top-expenses-display', 'children'),
    Input('history-month-selector', 'value'),
    Input('history-interval', 'n_intervals')
)
def update_top_expenses(month, n):
    """Update top expenses display."""
    if not month:
        return html.P("Välj en månad för att se största utgifter.")
    
    try:
        viewer = HistoryViewer()
        top = viewer.get_top_expenses(month, top_n=10)
        
        if not top:
            return html.P("Inga utgifter hittades.")
        
        rows = []
        for i, tx in enumerate(top, 1):
            rows.append(html.Tr([
                html.Td(str(i)),
                html.Td(tx.get('description', 'N/A')),
                html.Td(tx.get('date', 'N/A')),
                html.Td(f"{abs(tx['amount']):.2f} SEK", className="text-end")
            ]))
        
        return dbc.Table([
            html.Thead(html.Tr([
                html.Th("#"),
                html.Th("Beskrivning"),
                html.Th("Datum"),
                html.Th("Belopp", className="text-end")
            ])),
            html.Tbody(rows)
        ], striped=True, hover=True, size="sm")
    except Exception as e:
        return html.P(f"Fel: {str(e)}", className="text-danger")


# Callback: Agent query processing
@app.callback(
    Output('agent-response-display', 'children'),
    Input('agent-submit-btn', 'n_clicks'),
    State('agent-query-input', 'value'),
    prevent_initial_call=True
)
def process_agent_query(n_clicks, query):
    """Process agent query and return response."""
    if not query:
        return "Ange en fråga först."
    
    try:
        agent = AgentInterface()
        response = agent.process_query(query)
        return response
    except Exception as e:
        return f"Fel vid bearbetning av fråga: {str(e)}"


# Callback: Income account dropdown
@app.callback(
    Output('income-account-dropdown', 'options'),
    Input('overview-interval', 'n_intervals')
)
def update_income_account_dropdown(n):
    """Update account dropdown for income input."""
    try:
        manager = AccountManager()
        accounts = manager.get_accounts()
        return [{'label': acc['name'], 'value': acc['name']} for acc in accounts]
    except:
        return []


# Callback: Add income
@app.callback(
    Output('income-add-status', 'children'),
    Input('add-income-btn', 'n_clicks'),
    State('income-person-input', 'value'),
    State('income-account-dropdown', 'value'),
    State('income-amount-input', 'value'),
    State('income-date-input', 'value'),
    State('income-description-input', 'value'),
    State('income-category-dropdown', 'value'),
    prevent_initial_call=True
)
def add_income(n_clicks, person, account, amount, date, description, category):
    """Add income entry."""
    if not all([person, account, amount, date]):
        return dbc.Alert("Fyll i alla obligatoriska fält.", color="warning")
    
    try:
        tracker = IncomeTracker()
        tracker.add_income(
            person=person,
            account=account,
            amount=float(amount),
            date=date,
            description=description or "",
            category=category or "Lön"
        )
        return dbc.Alert(f"Inkomst tillagd: {amount} SEK för {person}", color="success")
    except Exception as e:
        return dbc.Alert(f"Fel: {str(e)}", color="danger")


# Callback: Load settings when tab is opened
@app.callback(
    [Output('settings-currency', 'value'),
     Output('settings-decimals', 'value'),
     Output('settings-items-per-page', 'value'),
     Output('settings-refresh-interval', 'value'),
     Output('settings-display-options', 'value'),
     Output('settings-notifications', 'value'),
     Output('settings-reminder-days', 'value'),
     Output('settings-low-balance-threshold', 'value')],
    Input('main-tabs', 'value')
)
def load_settings_on_tab_open(tab):
    """Load current settings when settings tab is opened."""
    if tab != 'settings':
        # Return current values without changing anything
        raise dash.exceptions.PreventUpdate
    
    try:
        panel = SettingsPanel()
        settings = panel.load_settings()
        
        general = settings.get('general', {})
        display = settings.get('display', {})
        notifications = settings.get('notifications', {})
        
        # Build display options list
        display_opts = []
        if display.get('auto_refresh', True):
            display_opts.append('auto_refresh')
        if display.get('show_pie_chart', True):
            display_opts.append('show_pie')
        if display.get('show_forecast_graph', True):
            display_opts.append('show_forecast')
        
        # Build notifications list
        notif_opts = []
        if notifications.get('bill_reminders', True):
            notif_opts.append('bill_reminders')
        if notifications.get('low_balance_alert', True):
            notif_opts.append('low_balance')
        
        return (
            general.get('currency', 'SEK'),
            general.get('decimal_places', 2),
            display.get('items_per_page', 50),
            display.get('refresh_interval', 5000) // 1000,  # Convert from ms to seconds
            display_opts,
            notif_opts,
            notifications.get('reminder_days_before', 3),
            notifications.get('low_balance_threshold', 1000.0)
        )
    except Exception as e:
        print(f"Error loading settings: {e}")
        raise dash.exceptions.PreventUpdate


# Callback: Save settings
@app.callback(
    Output('settings-save-status', 'children'),
    Input('save-settings-btn', 'n_clicks'),
    State('settings-currency', 'value'),
    State('settings-decimals', 'value'),
    State('settings-items-per-page', 'value'),
    State('settings-refresh-interval', 'value'),
    State('settings-display-options', 'value'),
    State('settings-notifications', 'value'),
    State('settings-reminder-days', 'value'),
    State('settings-low-balance-threshold', 'value'),
    prevent_initial_call=True
)
def save_settings(n_clicks, currency, decimals, items_per_page, refresh_interval, 
                  display_options, notifications, reminder_days, low_balance_threshold):
    """Save settings and apply them to the system."""
    try:
        panel = SettingsPanel()
        
        updates = {
            'general': {
                'currency': currency,
                'decimal_places': decimals
            },
            'display': {
                'items_per_page': items_per_page,
                'refresh_interval': refresh_interval * 1000,  # Convert to ms
                'auto_refresh': 'auto_refresh' in display_options,
                'show_pie_chart': 'show_pie' in display_options,
                'show_forecast_graph': 'show_forecast' in display_options
            },
            'notifications': {
                'bill_reminders': 'bill_reminders' in notifications,
                'low_balance_alert': 'low_balance' in notifications,
                'reminder_days_before': reminder_days,
                'low_balance_threshold': low_balance_threshold
            }
        }
        
        panel.update_settings(updates)
        return dbc.Alert([
            html.H5("✓ Inställningar sparade!", className="alert-heading"),
            html.P("Inställningarna tillämpas nu i systemet. Vissa ändringar kan kräva en omladdning av sidan.", 
                   className="mb-0")
        ], color="success", dismissable=True, duration=6000)
    except Exception as e:
        return dbc.Alert(f"Fel: {str(e)}", color="danger", dismissable=True, duration=5000)


# Callback: Reset settings
@app.callback(
    Output('settings-save-status', 'children', allow_duplicate=True),
    Input('reset-settings-btn', 'n_clicks'),
    prevent_initial_call=True
)
def reset_settings(n_clicks):
    """Reset settings to defaults."""
    try:
        panel = SettingsPanel()
        panel.reset_to_defaults()
        return dbc.Alert("Inställningar återställda till standard!", color="info")
    except Exception as e:
        return dbc.Alert(f"Fel: {str(e)}", color="danger")


# Callback: Update AI Training Stats
@app.callback(
    Output('ai-training-stats', 'children'),
    Input('ai-training-interval', 'n_intervals')
)
def update_ai_training_stats(n):
    """Update AI training statistics."""
    try:
        trainer = AITrainer()
        stats = trainer.get_training_stats()
        
        if stats['total_samples'] == 0:
            return dbc.Alert("Ingen träningsdata tillgänglig ännu. Börja med att kategorisera transaktioner manuellt.", 
                           color="info", className="mb-0")
        
        ready_badge = dbc.Badge("Redo att träna", color="success") if stats['ready_to_train'] else dbc.Badge(
            f"Behöver {stats['min_samples_needed'] - stats['manual_samples']} fler manuella kategoriseringar", 
            color="warning"
        )
        
        return html.Div([
            html.P([
                html.Strong("Träningsstatus: "), ready_badge
            ], className="mb-2"),
            html.P([
                html.Strong("Totalt antal träningsprover: "), f"{stats['total_samples']} ",
                html.Small(f"({stats['manual_samples']} manuella)", className="text-muted")
            ], className="mb-2"),
            html.P([
                html.Strong("Kategorier: "), 
                ", ".join([f"{cat} ({count})" for cat, count in stats['categories'].items()])
            ], className="mb-0") if stats['categories'] else None
        ])
    except Exception as e:
        return dbc.Alert(f"Fel vid hämtning av statistik: {str(e)}", color="danger", className="mb-0")


# Callback: Start AI Training
@app.callback(
    Output('ai-training-status', 'children'),
    Input('start-training-btn', 'n_clicks'),
    prevent_initial_call=True
)
def start_ai_training(n_clicks):
    """Start AI training from manual samples."""
    if not n_clicks:
        return ""
    
    try:
        trainer = AITrainer()
        result = trainer.train_from_samples()
        
        if result['success']:
            return dbc.Alert([
                html.H5("Träning genomförd!", className="alert-heading"),
                html.P(result['message']),
                html.Hr(),
                html.P([
                    "Kategorier som tränats: ",
                    ", ".join(result.get('categories_trained', []))
                ], className="mb-0") if result.get('categories_trained') else None
            ], color="success", dismissable=True, duration=8000)
        else:
            return dbc.Alert(result['message'], color="warning", dismissable=True, duration=6000)
    except Exception as e:
        return dbc.Alert(f"Fel vid träning: {str(e)}", color="danger", dismissable=True, duration=6000)


# Callback: Clear Training Data
@app.callback(
    Output('ai-training-status', 'children', allow_duplicate=True),
    Input('clear-training-data-btn', 'n_clicks'),
    prevent_initial_call=True
)
def clear_training_data(n_clicks):
    """Clear all training data."""
    if not n_clicks:
        return ""
    
    try:
        trainer = AITrainer()
        trainer.clear_training_data()
        
        return dbc.Alert(
            "Träningsdata rensad! AI-genererade regler behålls. Använd 'Ta bort AI-regler' om du vill ta bort dem också.",
            color="info", 
            dismissable=True, 
            duration=6000
        )
    except Exception as e:
        return dbc.Alert(f"Fel vid rensning: {str(e)}", color="danger", dismissable=True, duration=6000)


# Callback: View Training Data
@app.callback(
    Output('ai-training-status', 'children', allow_duplicate=True),
    Input('view-training-data-btn', 'n_clicks'),
    prevent_initial_call=True
)
def view_training_data(n_clicks):
    """View training data samples."""
    if not n_clicks:
        return ""
    
    try:
        trainer = AITrainer()
        training_data = trainer.get_training_data()
        
        if not training_data:
            return dbc.Alert("Ingen träningsdata tillgänglig", color="info", dismissable=True, duration=4000)
        
        # Show last 5 samples
        recent_samples = training_data[-5:]
        
        table_rows = []
        for sample in recent_samples:
            table_rows.append(html.Tr([
                html.Td(sample.get('description', '')[:50]),
                html.Td(sample.get('category', '')),
                html.Td(sample.get('subcategory', '')),
                html.Td(sample.get('added_at', ''))
            ]))
        
        return dbc.Alert([
            html.H5(f"Senaste {len(recent_samples)} träningsprover", className="alert-heading"),
            dbc.Table([
                html.Thead(html.Tr([
                    html.Th("Beskrivning"),
                    html.Th("Kategori"),
                    html.Th("Underkategori"),
                    html.Th("Tillagd")
                ])),
                html.Tbody(table_rows)
            ], bordered=True, striped=True, size="sm")
        ], color="info", dismissable=True, duration=10000)
    except Exception as e:
        return dbc.Alert(f"Fel vid visning: {str(e)}", color="danger", dismissable=True, duration=6000)


# Callback: Update loan dropdown options
@app.callback(
    Output('loan-match-dropdown', 'options'),
    Input('accounts-interval', 'n_intervals')
)
def update_loan_dropdown(n):
    """Update loan dropdown with active loans."""
    try:
        loan_manager = LoanManager()
        loans = loan_manager.get_loans(status='active')
        
        return [
            {'label': f"{loan['name']} (Saldo: {loan.get('current_balance', 0):,.2f} SEK)", 
             'value': loan['id']} 
            for loan in loans
        ]
    except Exception as e:
        print(f"Error loading loans: {e}")
        return []


# Callback: Match transaction to loan
@app.callback(
    Output('loan-match-status', 'children'),
    Input('match-loan-btn', 'n_clicks'),
    [State('transaction-table', 'selected_rows'),
     State('transaction-table', 'data'),
     State('loan-match-dropdown', 'value'),
     State('account-selector', 'value')],
    prevent_initial_call=True
)
def match_transaction_to_loan(n_clicks, selected_rows, table_data, loan_id, account_name):
    """Match selected transaction to a loan."""
    if not n_clicks or not selected_rows or not table_data or not loan_id:
        return dbc.Alert("Välj en transaktion och ett lån att matcha till", color="warning", dismissable=True, duration=4000)
    
    try:
        selected_tx = table_data[selected_rows[0]]
        
        loan_manager = LoanManager()
        result = loan_manager.match_transaction_to_loan(selected_tx, loan_id)
        
        if result and result.get('matched'):
            # Also update the transaction category
            manager = AccountManager()
            data = manager._load_yaml(manager.transactions_file)
            transactions = data.get('transactions', [])
            
            for tx in transactions:
                if (tx.get('date') == selected_tx['date'] and 
                    tx.get('description') == selected_tx['description'] and
                    tx.get('account') == account_name):
                    tx['category'] = 'Lån'
                    tx['subcategory'] = 'Lånebetalning'
                    tx['loan_id'] = loan_id
                    tx['loan_matched'] = True
                    break
            
            manager.save_transactions(data)
            
            return dbc.Alert([
                html.H5("✓ Transaktion matchad till lån!", className="alert-heading"),
                html.P(f"Lån: {result['loan_name']}"),
                html.P(f"Belopp: {result['amount']:,.2f} SEK"),
                html.P(f"Nytt saldo: {result['new_balance']:,.2f} SEK", className="mb-0")
            ], color="success", dismissable=True, duration=8000)
        else:
            return dbc.Alert("Kunde inte matcha transaktion till lån", color="danger", dismissable=True, duration=4000)
    except Exception as e:
        return dbc.Alert(f"Fel: {str(e)}", color="danger", dismissable=True, duration=5000)


if __name__ == "__main__":
    # Register signal handler for Ctrl-C
    signal.signal(signal.SIGINT, clear_data_on_exit)
    
    print("Starting Insights Dashboard (Sprint 5)...")
    print("Open your browser at: http://127.0.0.1:8050")
    print("\nPress Ctrl-C to stop the server and clear data files")
    
    try:
        app.run(debug=True, host="0.0.0.0", port=8050)
    except KeyboardInterrupt:
        clear_data_on_exit()
