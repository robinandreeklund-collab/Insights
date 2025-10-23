"""Insights Dashboard - Sprint 3 Enhanced Dashboard with Interactive Features."""

import dash
from dash import html, dcc, Input, Output, State, callback_context, dash_table
from dash.exceptions import PreventUpdate
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
from modules.core.credit_card_manager import CreditCardManager
from modules.core.loan_manager import LoanManager
from modules.core.parse_pdf_bills import PDFBillParser
from modules.core.bill_matcher import BillMatcher
from modules.core.history_viewer import HistoryViewer
from modules.core.income_tracker import IncomeTracker
from modules.core.agent_interface import AgentInterface
from modules.core.settings_panel import SettingsPanel
from modules.core.ai_trainer import AITrainer
from modules.core.category_manager import CategoryManager

# Import icon helpers using importlib to avoid sys.path modification
import importlib.util
import traceback

icons_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'icons.py')
try:
    spec = importlib.util.spec_from_file_location("icons", icons_path)
    icons = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(icons)
    home_icon = icons.home_icon
    upload_icon = icons.upload_icon
    graph_icon = icons.graph_icon
    account_icon = icons.account_icon
    credit_card_icon = icons.credit_card_icon
    calendar_icon = icons.calendar_icon
    chart_icon = icons.chart_icon
    gear_icon = icons.gear_icon
    history_icon = icons.history_icon
    question_icon = icons.question_icon
    moon_icon = icons.moon_icon
    sun_icon = icons.sun_icon
    beaker_icon = icons.beaker_icon
    get_card_icon = icons.get_card_icon
except Exception:
    # Fallback if icons not available
    traceback.print_exc()
    def home_icon(size=16): return ""
    def upload_icon(size=16): return ""
    def graph_icon(size=16): return ""
    def account_icon(size=16): return ""
    def credit_card_icon(size=16): return ""
    def calendar_icon(size=16): return ""
    def chart_icon(size=16): return ""
    def gear_icon(size=16): return ""
    def history_icon(size=16): return ""
    def question_icon(size=16): return ""
    def moon_icon(size=16): return ""
    def sun_icon(size=16): return ""
    def beaker_icon(size=16): return ""
    def get_card_icon(card_type, size=48): return ""


def clear_data_on_exit(signum=None, frame=None):
    """Clear transactions, accounts, bills, loans, and credit cards data files on exit.
    
    Note: training_data.yaml is preserved to maintain AI learning.
    """
    print("\n\nClearing data files before exit...")
    
    yaml_dir = "yaml"
    transactions_file = os.path.join(yaml_dir, "transactions.yaml")
    accounts_file = os.path.join(yaml_dir, "accounts.yaml")
    bills_file = os.path.join(yaml_dir, "bills.yaml")
    loans_file = os.path.join(yaml_dir, "loans.yaml")
    credit_cards_file = os.path.join(yaml_dir, "credit_cards.yaml")
    
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
        
        # Reset credit_cards.yaml
        if os.path.exists(credit_cards_file):
            with open(credit_cards_file, 'w', encoding='utf-8') as f:
                yaml.dump({'cards': []}, f, default_flow_style=False, allow_unicode=True)
            print(f"✓ Cleared {credit_cards_file}")
        
        print("Data files cleared successfully! (training_data.yaml preserved)")
    except Exception as e:
        print(f"Error clearing data files: {e}")
    
    sys.exit(0)



# Initialize Dash app with custom CSS
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    assets_folder='../assets'
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
            ], width=8),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Snabböversikt", className="card-title"),
                        html.Div(id='quick-overview-display'),
                    ])
                ])
            ], width=4)
        ], className="mb-4"),
        
        # Saldo per konto
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Saldo per konto", className="card-title"),
                        html.Div(id='account-balances-display'),
                    ])
                ])
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Kommande utgifter (30 dagar)", className="card-title"),
                        html.Div(id='upcoming-expenses-display'),
                    ])
                ])
            ], width=6)
        ], className="mb-4"),
        
        # Inkomster per person
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Inkomster per person (denna månad)", className="card-title"),
                        html.Div(id='income-by-person-display'),
                    ])
                ])
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Topputgifter (senaste 30 dagarna)", className="card-title"),
                        html.Div(id='top-expenses-display'),
                    ])
                ])
            ], width=6)
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
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Varningar och insikter", className="card-title"),
                        html.Div(id='alerts-insights-display'),
                    ])
                ])
            ], width=6)
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
                dbc.Input(id='edit-account-name-input', type='text', placeholder='Kontonamn', className="mb-3"),
                html.Label("Person/Ägare:", className="fw-bold mb-2"),
                dbc.Input(id='edit-account-person-input', type='text', placeholder='T.ex. Robin'),
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
                        html.Div(id='training-readiness-status', className="mb-3"),
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
                            ], width=4),
                            dbc.Col([
                                html.Label("Kategori:", className="fw-bold"),
                                dcc.Dropdown(
                                    id='bill-category-dropdown',
                                    options=[{'label': cat, 'value': cat} for cat in CATEGORIES.keys()],
                                    value='Övrigt'
                                ),
                            ], width=4),
                            dbc.Col([
                                html.Label("Underkategori:", className="fw-bold"),
                                dcc.Dropdown(
                                    id='bill-subcategory-dropdown',
                                    placeholder='Välj underkategori...'
                                ),
                            ], width=4),
                        ], className="mb-3"),
                        dbc.Row([
                            dbc.Col([
                                html.Label("Konto:", className="fw-bold"),
                                dcc.Dropdown(
                                    id='bill-account-dropdown',
                                    placeholder='Välj konto (valfritt)...'
                                ),
                            ], width=6),
                            dbc.Col([
                                html.Label("Beskrivning:", className="fw-bold"),
                                dbc.Input(id='bill-description-input', type='text', placeholder='Valfri beskrivning...'),
                            ], width=6),
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
        
        # Bills display section with account grouping
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Fakturor per konto", className="card-title"),
                        html.P("Fakturor grupperade efter vilket konto de ska belasta", className="text-muted"),
                        html.Div(id='account-summary-container', className="mb-4"),
                    ])
                ])
            ], width=12)
        ], className="mb-4"),
        
        # Detailed bills display section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Alla fakturor", className="card-title"),
                        dcc.Dropdown(
                            id='bill-status-filter',
                            options=[
                                {'label': 'Alla', 'value': 'all'},
                                {'label': 'Schemalagda', 'value': 'scheduled'},
                                {'label': 'Väntande', 'value': 'pending'},
                                {'label': 'Betalda', 'value': 'paid'},
                                {'label': 'Förfallna', 'value': 'overdue'}
                            ],
                            value='all',
                            className="mb-3"
                        ),
                        dash_table.DataTable(
                            id='bills-table',
                            columns=[
                                {'name': 'ID', 'id': 'id'},
                                {'name': 'Namn', 'id': 'name'},
                                {'name': 'Belopp', 'id': 'amount'},
                                {'name': 'Förfallodatum', 'id': 'due_date'},
                                {'name': 'Status', 'id': 'status'},
                                {'name': 'Kategori', 'id': 'category'},
                                {'name': 'Konto', 'id': 'account'},
                            ],
                            data=[],
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
                        ),
                    ])
                ])
            ], width=12)
        ]),
        
        # Bill edit modal
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Redigera faktura")),
            dbc.ModalBody([
                dbc.Row([
                    dbc.Col([
                        html.Label("Namn:", className="fw-bold"),
                        dbc.Input(id='edit-bill-name', type='text'),
                    ], width=6),
                    dbc.Col([
                        html.Label("Belopp (SEK):", className="fw-bold"),
                        dbc.Input(id='edit-bill-amount', type='number'),
                    ], width=6),
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        html.Label("Förfallodatum:", className="fw-bold"),
                        dbc.Input(id='edit-bill-due-date', type='date'),
                    ], width=4),
                    dbc.Col([
                        html.Label("Kategori:", className="fw-bold"),
                        dcc.Dropdown(
                            id='edit-bill-category',
                            options=[{'label': cat, 'value': cat} for cat in CATEGORIES.keys()]
                        ),
                    ], width=4),
                    dbc.Col([
                        html.Label("Underkategori:", className="fw-bold"),
                        dcc.Dropdown(id='edit-bill-subcategory'),
                    ], width=4),
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        html.Label("Konto:", className="fw-bold"),
                        dcc.Dropdown(id='edit-bill-account'),
                    ], width=6),
                    dbc.Col([
                        html.Label("Beskrivning:", className="fw-bold"),
                        dbc.Input(id='edit-bill-description', type='text'),
                    ], width=6),
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        html.Label("Status:", className="fw-bold"),
                        dcc.Dropdown(
                            id='edit-bill-status-dropdown',
                            options=[
                                {'label': 'Schemalagd', 'value': 'scheduled'},
                                {'label': 'Väntande', 'value': 'pending'},
                                {'label': 'Betald', 'value': 'paid'},
                                {'label': 'Förfallen', 'value': 'overdue'}
                            ]
                        ),
                    ], width=6),
                ], className="mb-3"),
                html.Div(id='edit-bill-status-message', className="mt-2")
            ]),
            dbc.ModalFooter([
                dbc.Button("Avbryt", id='edit-bill-cancel-btn', color="secondary", className="me-2"),
                dbc.Button("Markera som betald", id='edit-bill-mark-paid-btn', color="success", className="me-2"),
                dbc.Button("Träna AI", id='edit-bill-train-ai-btn', color="info", className="me-2"),
                dbc.Button("Spara", id='edit-bill-save-btn', color="primary")
            ])
        ], id='edit-bill-modal', is_open=False),
        
        # Line item edit modal
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Redigera raduppgift")),
            dbc.ModalBody([
                dbc.Row([
                    dbc.Col([
                        html.Label("Leverantör:", className="fw-bold"),
                        dbc.Input(id='edit-line-item-vendor', type='text'),
                    ], width=6),
                    dbc.Col([
                        html.Label("Datum:", className="fw-bold"),
                        dbc.Input(id='edit-line-item-date', type='date'),
                    ], width=6),
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        html.Label("Beskrivning:", className="fw-bold"),
                        dbc.Input(id='edit-line-item-description', type='text'),
                    ], width=12),
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        html.Label("Belopp (SEK):", className="fw-bold"),
                        dbc.Input(id='edit-line-item-amount', type='number'),
                    ], width=4),
                    dbc.Col([
                        html.Label("Kategori:", className="fw-bold"),
                        dcc.Dropdown(
                            id='edit-line-item-category',
                            options=[{'label': cat, 'value': cat} for cat in CATEGORIES.keys()]
                        ),
                    ], width=4),
                    dbc.Col([
                        html.Label("Underkategori:", className="fw-bold"),
                        dcc.Dropdown(id='edit-line-item-subcategory'),
                    ], width=4),
                ], className="mb-3"),
                html.Div(id='edit-line-item-status', className="mt-2")
            ]),
            dbc.ModalFooter([
                dbc.Button("Avbryt", id='edit-line-item-cancel-btn', color="secondary"),
                dbc.Button("Spara", id='edit-line-item-save-btn', color="primary")
            ])
        ], id='edit-line-item-modal', is_open=False),
        
        # Store and interval for auto-refresh
        dcc.Store(id='selected-bill-id', data=None),
        dcc.Store(id='edit-bill-id', data=None),
        dcc.Store(id='edit-line-item-data', data=None),  # Store line item being edited
        dcc.Interval(id='bills-interval', interval=5000, n_intervals=0)
    ], className="p-3")


# Create loans tab content

# Create credit cards tab content
def create_credit_cards_tab():
    """Create the credit cards management tab."""
    return html.Div([
        html.H2("Kreditkortshantering", className="mb-4"),
        
        # Add new credit card section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Lägg till nytt kreditkort", className="card-title"),
                        dbc.Row([
                            dbc.Col([
                                html.Label("Kortnamn:", className="fw-bold"),
                                dbc.Input(id='card-name-input', type='text', placeholder='t.ex. Amex Platinum'),
                            ], width=6),
                            dbc.Col([
                                html.Label("Korttyp:", className="fw-bold"),
                                dcc.Dropdown(
                                    id='card-type-dropdown',
                                    options=[
                                        {'label': 'American Express', 'value': 'American Express'},
                                        {'label': 'Visa', 'value': 'Visa'},
                                        {'label': 'Mastercard', 'value': 'Mastercard'},
                                        {'label': 'Annat', 'value': 'Other'}
                                    ],
                                    placeholder='Välj korttyp'
                                ),
                            ], width=6),
                        ], className="mb-3"),
                        dbc.Row([
                            dbc.Col([
                                html.Label("Sista 4 siffror:", className="fw-bold"),
                                dbc.Input(id='card-last-four-input', type='text', placeholder='1234', maxLength=4),
                            ], width=4),
                            dbc.Col([
                                html.Label("Kreditgräns (SEK):", className="fw-bold"),
                                dbc.Input(id='card-limit-input', type='number', placeholder='50000'),
                            ], width=4),
                            dbc.Col([
                                html.Label("Färg:", className="fw-bold"),
                                dbc.Input(id='card-color-input', type='color', value='#1f77b4'),
                            ], width=4),
                        ], className="mb-3"),
                        dbc.Button("Lägg till kort", id='add-card-btn', color="primary"),
                        html.Div(id='card-add-status', className="mt-3")
                    ])
                ])
            ], width=12)
        ], className="mb-4"),
        
        # Credit cards overview section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Mina kreditkort", className="card-title"),
                        html.Div(id='credit-cards-overview')
                    ])
                ])
            ], width=12)
        ], className="mb-4"),
        
        # Edit/Delete Card Modals
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Redigera kreditkort")),
            dbc.ModalBody([
                html.Label("Kortnamn:", className="fw-bold"),
                dbc.Input(id='edit-card-name', type='text', className="mb-2"),
                html.Label("Korttyp:", className="fw-bold"),
                dcc.Dropdown(
                    id='edit-card-type',
                    options=[
                        {'label': 'American Express', 'value': 'American Express'},
                        {'label': 'Visa', 'value': 'Visa'},
                        {'label': 'Mastercard', 'value': 'Mastercard'},
                        {'label': 'Annat', 'value': 'Other'}
                    ],
                    className="mb-2"
                ),
                html.Label("Sista 4 siffror:", className="fw-bold"),
                dbc.Input(id='edit-card-last-four', type='text', maxLength=4, className="mb-2"),
                html.Label("Kreditgräns (SEK):", className="fw-bold"),
                dbc.Input(id='edit-card-limit', type='number', className="mb-2"),
                html.Label("Färg:", className="fw-bold"),
                dbc.Input(id='edit-card-color', type='color', className="mb-2"),
                dcc.Store(id='edit-card-id-store'),
                html.Div(id='edit-card-status', className="mt-2")
            ]),
            dbc.ModalFooter([
                dbc.Button("Avbryt", id='edit-card-cancel', color="secondary"),
                dbc.Button("Spara", id='edit-card-save', color="primary")
            ])
        ], id='edit-card-modal', is_open=False),
        
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Bekräfta borttagning")),
            dbc.ModalBody([
                html.P(id='delete-card-confirm-text'),
                dcc.Store(id='delete-card-id-store')
            ]),
            dbc.ModalFooter([
                dbc.Button("Avbryt", id='delete-card-cancel', color="secondary"),
                dbc.Button("Ta bort", id='delete-card-confirm', color="danger")
            ])
        ], id='delete-card-modal', is_open=False),
        
        # CSV Import section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Importera transaktioner från CSV", className="card-title"),
                        dcc.Dropdown(
                            id='card-import-selector',
                            placeholder='Välj kort för import...',
                            className="mb-3"
                        ),
                        dcc.Upload(
                            id='upload-card-csv',
                            children=html.Div([
                                html.I(className="bi bi-filetype-csv", style={'fontSize': '48px'}),
                                html.Br(),
                                'Dra och släpp eller klicka för att välja CSV-fil'
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
                        html.Div(id='card-csv-import-status', className="mt-3")
                    ])
                ])
            ], width=12)
        ], className="mb-4"),
        
        # Card details and transactions section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Kortdetaljer och transaktioner", className="card-title"),
                        dcc.Dropdown(
                            id='card-details-selector',
                            placeholder='Välj kort för detaljer...',
                            className="mb-3"
                        ),
                        html.Div(id='card-details-container')
                    ])
                ])
            ], width=12)
        ], className="mb-4"),
    ], className="p-3")


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
                        html.Div(id='history-top-expenses-display')
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


# Create monthly analysis tab content
def create_monthly_analysis_tab():
    """Create the Monthly Analysis tab with expense breakdown and transfer recommendations."""
    return html.Div([
        html.H3("Månadsanalys", className="mt-3 mb-4"),
        
        # Month/interval selector
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Välj period", className="card-title"),
                        dbc.Row([
                            dbc.Col([
                                html.Label("Startmånad:", className="fw-bold"),
                                dcc.Dropdown(
                                    id='analysis-start-month',
                                    placeholder="Välj startmånad...",
                                    className="mb-2"
                                )
                            ], width=6),
                            dbc.Col([
                                html.Label("Slutmånad:", className="fw-bold"),
                                dcc.Dropdown(
                                    id='analysis-end-month',
                                    placeholder="Välj slutmånad...",
                                    className="mb-2"
                                )
                            ], width=6),
                        ]),
                        dbc.Button("Analysera period", id='analyze-period-btn', color="primary", className="mt-2"),
                    ])
                ])
            ], width=12)
        ], className="mb-4"),
        
        # Kommande fakturor denna månad
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Kommande fakturor denna månad (Scheduled)", className="card-title"),
                        html.Div(id='monthly-upcoming-bills-display'),
                    ])
                ])
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Bokförda transaktioner denna månad (Posted)", className="card-title"),
                        html.Div(id='monthly-posted-transactions-display'),
                    ])
                ])
            ], width=6)
        ], className="mb-4"),
        
        # Inkomster per person och konto
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Inkomster per person och konto", className="card-title"),
                        html.Div(id='monthly-income-breakdown-display'),
                    ])
                ])
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Utgiftssummering", className="card-title"),
                        html.Div(id='monthly-expense-summary-display'),
                    ])
                ])
            ], width=6)
        ], className="mb-4"),
        
        # Transfer recommendations
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Förslag på överföringar till gemensamt konto", className="card-title"),
                        html.P("Baserat på inkomster och gemensamma utgifter", className="text-muted mb-3"),
                        
                        # Options for calculation
                        dbc.Row([
                            dbc.Col([
                                html.Label("Gemensamma kategorier:", className="fw-bold"),
                                dcc.Dropdown(
                                    id='shared-categories-selector',
                                    options=[{'label': cat, 'value': cat} for cat in CATEGORIES.keys()],
                                    value=['Boende', 'Mat & Dryck'],
                                    multi=True,
                                    className="mb-3"
                                )
                            ], width=12),
                        ]),
                        
                        dbc.Button("Beräkna överföringar", id='calculate-transfers-btn', color="success"),
                        html.Div(id='transfer-recommendations-display', className="mt-3"),
                    ])
                ])
            ], width=12)
        ]),
        
        # Interval for auto-refresh
        dcc.Interval(id='monthly-analysis-interval', interval=10000, n_intervals=0)
    ], className="p-3")


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


# Main app layout with GitHub-inspired design
app.layout = html.Div([
    # Storage components for state management
    dcc.Store(id='bills-update-trigger', storage_type='memory'),
    dcc.Store(id='incomes-update-trigger', storage_type='memory'),
    dcc.Store(id='transactions-update-trigger', storage_type='memory'),
    dcc.Store(id='theme-store', storage_type='local', data='dark'),
    dcc.Store(id='current-tab', storage_type='memory', data='overview'),
    
    # Top Navigation Bar
    html.Div([
        html.Div([
            html.Div([
                html.Span("📊", style={'fontSize': '24px', 'marginRight': '8px'}),
                html.Span("Insights", style={'fontWeight': '600', 'fontSize': '16px'}),
                html.Span(" / Hushållsekonomi", className="top-navbar-repo"),
            ], className="top-navbar-brand"),
            html.Div([
                html.Button([
                    html.Span(id='theme-icon', children="🌙"),
                ], id='theme-toggle-btn', className="theme-toggle"),
            ], className="top-navbar-actions"),
        ], style={'display': 'flex', 'alignItems': 'center', 'width': '100%'}),
    ], className="top-navbar"),
    
    # Container with sidebar and main content
    html.Div([
        # Sidebar Navigation
        html.Div([
            html.Nav([
                html.Ul([
                    html.Li([
                        html.A([
                            html.Span("🏠", className="sidebar-nav-icon", style={'display': 'inline-block'}),
                            html.Span("Ekonomisk översikt", style={'marginLeft': '8px'}),
                        ], href="#", id="nav-overview", className="sidebar-nav-link active"),
                    ], className="sidebar-nav-item"),
                    html.Li([
                        html.A([
                            html.Span("📤", className="sidebar-nav-icon", style={'display': 'inline-block'}),
                            html.Span("Inmatning", style={'marginLeft': '8px'}),
                        ], href="#", id="nav-input", className="sidebar-nav-link"),
                    ], className="sidebar-nav-item"),
                    html.Li([
                        html.A([
                            html.Span("👤", className="sidebar-nav-icon", style={'display': 'inline-block'}),
                            html.Span("Konton", style={'marginLeft': '8px'}),
                        ], href="#", id="nav-accounts", className="sidebar-nav-link"),
                    ], className="sidebar-nav-item"),
                    html.Li([
                        html.A([
                            html.Span("💳", className="sidebar-nav-icon", style={'display': 'inline-block'}),
                            html.Span("Fakturor", style={'marginLeft': '8px'}),
                        ], href="#", id="nav-bills", className="sidebar-nav-link"),
                    ], className="sidebar-nav-item"),
                    html.Li([
                        html.A([
                            html.Span("💎", className="sidebar-nav-icon", style={'display': 'inline-block'}),
                            html.Span("Kreditkort", style={'marginLeft': '8px'}),
                        ], href="#", id="nav-credit-cards", className="sidebar-nav-link"),
                    ], className="sidebar-nav-item"),
                    html.Li([
                        html.A([
                            html.Span("📜", className="sidebar-nav-icon", style={'display': 'inline-block'}),
                            html.Span("Historik", style={'marginLeft': '8px'}),
                        ], href="#", id="nav-history", className="sidebar-nav-link"),
                    ], className="sidebar-nav-item"),
                    html.Li([
                        html.A([
                            html.Span("📅", className="sidebar-nav-icon", style={'display': 'inline-block'}),
                            html.Span("Månadsanalys", style={'marginLeft': '8px'}),
                        ], href="#", id="nav-monthly-analysis", className="sidebar-nav-link"),
                    ], className="sidebar-nav-item"),
                    html.Li([
                        html.A([
                            html.Span("📈", className="sidebar-nav-icon", style={'display': 'inline-block'}),
                            html.Span("Lån", style={'marginLeft': '8px'}),
                        ], href="#", id="nav-loans", className="sidebar-nav-link"),
                    ], className="sidebar-nav-item"),
                    html.Li([
                        html.A([
                            html.Span("❓", className="sidebar-nav-icon", style={'display': 'inline-block'}),
                            html.Span("Frågebaserad analys", style={'marginLeft': '8px'}),
                        ], href="#", id="nav-agent", className="sidebar-nav-link"),
                    ], className="sidebar-nav-item"),
                    html.Li([
                        html.A([
                            html.Span("⚙️", className="sidebar-nav-icon", style={'display': 'inline-block'}),
                            html.Span("Inställningar", style={'marginLeft': '8px'}),
                        ], href="#", id="nav-settings", className="sidebar-nav-link"),
                    ], className="sidebar-nav-item"),
                ], className="sidebar-nav"),
            ]),
        ], className="sidebar"),
        
        # Main Content Area
        html.Div([
            html.Div(id='tab-content', children=create_overview_tab()),
        ], className="main-content"),
    ], className="insights-container"),
], style={'backgroundColor': 'var(--gh-canvas-default)'})


# Navigation callbacks
@app.callback(
    [Output('tab-content', 'children'),
     Output('current-tab', 'data')] +
    [Output(f'nav-{tab}', 'className') for tab in ['overview', 'input', 'accounts', 'bills', 'credit-cards', 'history', 'monthly-analysis', 'loans', 'agent', 'settings']],
    [Input(f'nav-{tab}', 'n_clicks') for tab in ['overview', 'input', 'accounts', 'bills', 'credit-cards', 'history', 'monthly-analysis', 'loans', 'agent', 'settings']],
    prevent_initial_call=True
)
def navigate_tabs(*args):
    """Handle sidebar navigation clicks."""
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Map navigation IDs to tab content
    tab_map = {
        'nav-overview': ('overview', create_overview_tab()),
        'nav-input': ('input', create_input_tab()),
        'nav-accounts': ('accounts', create_accounts_tab()),
        'nav-bills': ('bills', create_bills_tab()),
        'nav-credit-cards': ('credit-cards', create_credit_cards_tab()),
        'nav-history': ('history', create_history_tab()),
        'nav-monthly-analysis': ('monthly-analysis', create_monthly_analysis_tab()),
        'nav-loans': ('loans', create_loans_tab()),
        'nav-agent': ('agent', create_agent_tab()),
        'nav-settings': ('settings', create_settings_tab()),
    }
    
    if button_id not in tab_map:
        raise PreventUpdate
    
    tab_id, content = tab_map[button_id]
    
    # Update active class for nav items
    nav_classes = []
    for tab in ['overview', 'input', 'accounts', 'bills', 'credit-cards', 'history', 'monthly-analysis', 'loans', 'agent', 'settings']:
        if f'nav-{tab}' == button_id:
            nav_classes.append('sidebar-nav-link active')
        else:
            nav_classes.append('sidebar-nav-link')
    
    return [content, tab_id] + nav_classes


# Theme toggle callback
@app.callback(
    Output('theme-store', 'data'),
    Output('theme-icon', 'children'),
    Input('theme-toggle-btn', 'n_clicks'),
    State('theme-store', 'data'),
    prevent_initial_call=True
)
def toggle_theme(n_clicks, current_theme):
    """Toggle between light and dark themes."""
    if n_clicks is None:
        raise PreventUpdate
    
    # Toggle theme
    new_theme = 'light' if current_theme == 'dark' else 'dark'
    
    # Update icon - moon for dark theme (toggle to light), sun for light theme (toggle to dark)
    icon = "☀️" if new_theme == 'dark' else "🌙"
    
    return new_theme, icon


# Apply theme to body
app.clientside_callback(
    """
    function(theme) {
        if (theme === 'light') {
            document.documentElement.setAttribute('data-theme', 'light');
        } else {
            document.documentElement.removeAttribute('data-theme');
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output('theme-store', 'modified_timestamp'),
    Input('theme-store', 'data')
)


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


# Callback: Update Enhanced Overview Sections
@app.callback(
    [Output('quick-overview-display', 'children'),
     Output('account-balances-display', 'children'),
     Output('upcoming-expenses-display', 'children'),
     Output('income-by-person-display', 'children'),
     Output('top-expenses-display', 'children'),
     Output('alerts-insights-display', 'children')],
    Input('overview-interval', 'n_intervals')
)
def update_enhanced_overview(n):
    """Update the enhanced overview sections with detailed information."""
    from datetime import datetime, timedelta
    
    manager = AccountManager()
    accounts = manager.get_accounts()
    bill_manager = BillManager()
    income_tracker = IncomeTracker()
    
    # 1. Quick Overview
    total_balance = sum(acc.get('balance', 0) for acc in accounts)
    num_accounts = len(accounts)
    quick_overview = html.Div([
        html.P([html.Strong("Totalt saldo: "), f"{total_balance:,.2f} SEK"], className="mb-2"),
        html.P([html.Strong("Antal konton: "), str(num_accounts)], className="mb-2"),
    ])
    
    # 2. Account Balances
    if accounts:
        account_rows = []
        for acc in accounts:
            person = acc.get('person', '')
            person_text = f" ({person})" if person else ""
            account_rows.append(
                html.P([
                    html.Strong(f"{acc['name']}{person_text}: "),
                    f"{acc.get('balance', 0):,.2f} SEK"
                ], className="mb-1")
            )
        account_balances = html.Div(account_rows)
    else:
        account_balances = html.P("Inga konton tillgängliga", className="text-muted")
    
    # 3. Upcoming Expenses (next 30 days from bills)
    upcoming_bills = bill_manager.get_upcoming_bills(days=30)
    if upcoming_bills:
        total_upcoming = sum(b['amount'] for b in upcoming_bills)
        upcoming_display = html.Div([
            html.P([html.Strong("Totalt: "), f"{total_upcoming:,.2f} SEK"], className="mb-2 text-danger"),
            html.Hr(),
            html.Div([
                html.P(f"{b['name']}: {b['amount']:,.2f} SEK ({b['due_date']})", className="mb-1 small")
                for b in upcoming_bills[:5]  # Show first 5
            ])
        ])
    else:
        upcoming_display = html.P("Inga kommande fakturor", className="text-muted")
    
    # 4. Income by Person (this month)
    current_month = datetime.now().strftime('%Y-%m')
    income_by_person = income_tracker.get_income_by_person(
        start_date=f"{current_month}-01",
        end_date=f"{current_month}-31"
    )
    if income_by_person:
        income_rows = []
        for person, amount in income_by_person.items():
            income_rows.append(
                html.P([html.Strong(f"{person}: "), f"{amount:,.2f} SEK"], className="mb-1")
            )
        income_display = html.Div(income_rows)
    else:
        income_display = html.P("Inga registrerade inkomster denna månad", className="text-muted")
    
    # 5. Top Expenses (last 30 days)
    transactions = manager.get_all_transactions()
    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    recent_expenses = [
        tx for tx in transactions 
        if tx.get('amount', 0) < 0 and tx.get('date', '') >= thirty_days_ago
    ]
    recent_expenses.sort(key=lambda x: x.get('amount', 0))
    
    if recent_expenses:
        top_5 = recent_expenses[:5]
        expense_rows = []
        for tx in top_5:
            expense_rows.append(
                html.P(
                    f"{tx.get('description', 'N/A')}: {abs(tx.get('amount', 0)):,.2f} SEK",
                    className="mb-1 small"
                )
            )
        top_expenses_display = html.Div(expense_rows)
    else:
        top_expenses_display = html.P("Inga utgifter senaste 30 dagarna", className="text-muted")
    
    # 6. Alerts and Insights
    alerts = []
    
    # Check for overdue bills
    overdue_bills = bill_manager.get_bills(status='overdue')
    if overdue_bills:
        alerts.append(
            dbc.Alert([
                html.I(className="bi bi-exclamation-triangle-fill me-2"),
                f"{len(overdue_bills)} förfallna faktura(or)!"
            ], color="danger", className="mb-2")
        )
    
    # Check for low balance
    if total_balance < 1000:
        alerts.append(
            dbc.Alert([
                html.I(className="bi bi-exclamation-circle-fill me-2"),
                "Lågt saldo!"
            ], color="warning", className="mb-2")
        )
    
    # Check for upcoming bills in next 7 days
    upcoming_7_days = bill_manager.get_upcoming_bills(days=7)
    if upcoming_7_days:
        alerts.append(
            dbc.Alert([
                html.I(className="bi bi-info-circle-fill me-2"),
                f"{len(upcoming_7_days)} faktura(or) förfaller inom 7 dagar"
            ], color="info", className="mb-2")
        )
    
    if not alerts:
        alerts.append(html.P("Inga varningar för närvarande", className="text-muted"))
    
    alerts_display = html.Div(alerts)
    
    return quick_overview, account_balances, upcoming_display, income_display, top_expenses_display, alerts_display


# Callback: Update Account Selector
@app.callback(
    Output('account-selector', 'options'),
    Input('accounts-interval', 'n_intervals')
)
def update_account_selector(n):
    """Update the account selector dropdown with account names and persons.
    
    Displays accounts in format: "Account Name (Person)" if person is set,
    otherwise just "Account Name".
    
    Args:
        n: Interval counter (unused but required by Dash)
        
    Returns:
        List of dropdown options with label and value
    """
    manager = AccountManager()
    accounts = manager.get_accounts()
    # Display person name if available
    return [
        {
            'label': f"{acc['name']} ({acc.get('person', '')})" if acc.get('person') else acc['name'],
            'value': acc['name']
        } 
        for acc in accounts
    ]


# Callback: Open Edit Account Modal
@app.callback(
    [Output('edit-account-modal', 'is_open'),
     Output('edit-account-name-input', 'value'),
     Output('edit-account-person-input', 'value')],
    [Input('edit-account-btn', 'n_clicks'),
     Input('edit-account-cancel-btn', 'n_clicks'),
     Input('edit-account-save-btn', 'n_clicks')],
    [State('account-selector', 'value'),
     State('edit-account-modal', 'is_open')]
)
def toggle_edit_account_modal(edit_clicks, cancel_clicks, save_clicks, selected_account, is_open):
    """Toggle edit account modal and populate fields."""
    ctx = callback_context
    if not ctx.triggered:
        return False, "", ""
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'edit-account-btn' and selected_account:
        # Load account data to populate fields
        manager = AccountManager()
        account = manager.get_account_by_name(selected_account)
        if account:
            return True, account.get('name', ''), account.get('person', '')
        return True, selected_account, ""
    elif button_id in ['edit-account-cancel-btn', 'edit-account-save-btn']:
        return False, "", ""
    
    return is_open, selected_account or "", ""


# Callback: Save Edited Account
@app.callback(
    Output('edit-account-status', 'children'),
    Input('edit-account-save-btn', 'n_clicks'),
    [State('account-selector', 'value'),
     State('edit-account-name-input', 'value'),
     State('edit-account-person-input', 'value')]
)
def save_edited_account(n_clicks, old_name, new_name, person):
    """Save edited account name and person field.
    
    Handles updating both the account name and person/owner field.
    Provides detailed feedback about what changed.
    
    Args:
        n_clicks: Number of button clicks (trigger)
        old_name: Original account name
        new_name: New account name
        person: Person/owner name for the account
        
    Returns:
        Alert component with success/info message
    """
    if not n_clicks or not old_name or not new_name:
        return ""
    
    manager = AccountManager()
    
    # Check what changed
    changed = False
    messages = []
    
    # Update name if changed
    if old_name != new_name:
        result = manager.update_account(old_name, new_name=new_name)
        if result:
            messages.append(f"Namn ändrat från '{old_name}' till '{new_name}'")
            changed = True
            old_name = new_name  # Update for person change
    
    # Update person field
    account = manager.get_account_by_name(old_name)
    if account and account.get('person', '') != (person or ''):
        result = manager.update_account(old_name, person=person or '')
        if result:
            messages.append(f"Person uppdaterad till: {person if person else '(ingen angiven)'}")
            changed = True
    
    if changed:
        return dbc.Alert(". ".join(messages), color="success", dismissable=True)
    else:
        return dbc.Alert("Inget ändrat", color="info", dismissable=True)


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
    
    # Add special labels for transfers and credit card payments
    df['special_label'] = df.apply(lambda row: 
        row.get('transfer_label', '') if row.get('is_internal_transfer') else 
        row.get('credit_card_payment_label', ''), axis=1)
    
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
            {'name': 'Info', 'id': 'special_label'},
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
            },
            {
                'if': {'column_id': 'special_label'},
                'backgroundColor': '#fff3cd',
                'fontWeight': 'bold',
                'color': '#856404'
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
    # Check if this is actually a button click (n_clicks must be > 0)
    if not n_clicks or n_clicks == 0:
        raise PreventUpdate
    
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


# Callback: Update Training Readiness Status
@app.callback(
    Output('training-readiness-status', 'children'),
    Input('accounts-interval', 'n_intervals')
)
def update_training_readiness(n):
    """Update training readiness indicator in accounts tab.
    
    Shows a visual indicator of whether AI training is ready based on
    the number of manual categorizations available.
    
    Args:
        n: Interval counter (unused but required by Dash)
        
    Returns:
        Alert component showing training readiness status
    """
    try:
        trainer = AITrainer()
        stats = trainer.get_training_stats()
        
        if stats['total_samples'] == 0:
            return dbc.Alert([
                html.I(className="bi bi-info-circle me-2"),
                "Ingen träningsdata tillgänglig. Börja med att kategorisera transaktioner manuellt."
            ], color="info", className="mb-0 py-2")
        
        if stats['ready_to_train']:
            return dbc.Alert([
                html.I(className="bi bi-check-circle me-2"),
                f"✓ Redo att träna! ({stats['manual_samples']} manuella kategoriseringar)"
            ], color="success", className="mb-0 py-2")
        else:
            needed = stats['min_samples_needed'] - stats['manual_samples']
            return dbc.Alert([
                html.I(className="bi bi-exclamation-triangle me-2"),
                f"Behöver {needed} fler manuella kategoriseringar för att träna (har {stats['manual_samples']}/{stats['min_samples_needed']})"
            ], color="warning", className="mb-0 py-2")
    except Exception as e:
        return None


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


# Callback: Update Bill Subcategory Options
@app.callback(
    Output('bill-subcategory-dropdown', 'options'),
    Input('bill-category-dropdown', 'value')
)
def update_bill_subcategory_options(category):
    """Update subcategory dropdown based on selected category."""
    if not category:
        return []
    
    subcategories = CATEGORIES.get(category, [])
    return [{'label': sub, 'value': sub} for sub in subcategories]


# Callback: Update Bill Account Dropdown
@app.callback(
    Output('bill-account-dropdown', 'options'),
    Input('bills-interval', 'n_intervals')
)
def update_bill_account_dropdown(n):
    """Update the bill account dropdown with available accounts."""
    manager = AccountManager()
    accounts = manager.get_accounts()
    options = [{'label': 'Inget specifikt konto', 'value': ''}]
    for acc in accounts:
        options.append({'label': acc['name'], 'value': acc['name']})
    return options


# Callback: Add Bill
@app.callback(
    Output('bill-add-status', 'children'),
    Input('add-bill-btn', 'n_clicks'),
    [State('bill-name-input', 'value'),
     State('bill-amount-input', 'value'),
     State('bill-due-date-input', 'value'),
     State('bill-category-dropdown', 'value'),
     State('bill-subcategory-dropdown', 'value'),
     State('bill-account-dropdown', 'value'),
     State('bill-description-input', 'value')],
    prevent_initial_call=True
)
def add_bill(n_clicks, name, amount, due_date, category, subcategory, account, description):
    """Add a new bill with subcategory and account support."""
    if not name or not amount or not due_date:
        return dbc.Alert("Fyll i namn, belopp och förfallodatum", color="warning")
    
    try:
        bill_manager = BillManager()
        
        bill = bill_manager.add_bill(
            name=name,
            amount=float(amount),
            due_date=due_date,
            description=description or "",
            category=category or "Övrigt",
            subcategory=subcategory or "",
            account=account or None
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



# Callback: Update Account Summary
@app.callback(
    Output('account-summary-container', 'children'),
    [Input('add-bill-btn', 'n_clicks'),
     Input('upload-pdf-bills', 'contents'),
     Input('match-bills-btn', 'n_clicks')],
    [State('bills-interval', 'n_intervals')]
)
def update_account_summary(add_clicks, pdf_contents, match_clicks, n):
    """Display summary of bills grouped by account."""
    try:
        bill_manager = BillManager()
        summaries = bill_manager.get_account_summary()
        
        if not summaries:
            return html.P("Inga fakturor funna", className="text-muted")
        
        # Create cards for each account
        account_cards = []
        
        for summary in summaries:
            account = summary['account']
            bill_count = summary['bill_count']
            pending_count = summary['pending_count']
            total_amount = summary['total_amount']
            bills = summary['bills']
            
            # Create a table for bills in this account
            bills_list = []
            for bill in bills:
                status_badge_color = {
                    'pending': 'warning',
                    'paid': 'success',
                    'overdue': 'danger'
                }.get(bill.get('status', 'pending'), 'secondary')
                
                bills_list.append(
                    html.Tr([
                        html.Td(bill['name']),
                        html.Td(f"{bill['amount']:.2f} SEK"),
                        html.Td(bill['due_date']),
                        html.Td(bill['category']),
                        html.Td(dbc.Badge(bill.get('status', 'pending'), color=status_badge_color))
                    ])
                )
            
            # Create card for this account
            card = dbc.Card([
                dbc.CardHeader([
                    html.H5([
                        html.I(className="bi bi-bank me-2"),
                        f"Konto: {account}"
                    ], className="mb-0")
                ]),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.P([
                                html.Strong("Antal fakturor: "),
                                html.Span(f"{bill_count} st", className="badge bg-primary ms-2")
                            ], className="mb-2"),
                            html.P([
                                html.Strong("Väntande: "),
                                html.Span(f"{pending_count} st", className="badge bg-warning text-dark ms-2")
                            ], className="mb-2"),
                            html.P([
                                html.Strong("Total summa: "),
                                html.Span(f"{total_amount:.2f} SEK", className="badge bg-info text-dark ms-2")
                            ], className="mb-3"),
                        ], width=12)
                    ]),
                    html.Hr(),
                    html.H6("Fakturor:", className="mb-3"),
                    dbc.Table([
                        html.Thead([
                            html.Tr([
                                html.Th("Namn"),
                                html.Th("Belopp"),
                                html.Th("Förfallodatum"),
                                html.Th("Kategori"),
                                html.Th("Status")
                            ])
                        ]),
                        html.Tbody(bills_list)
                    ], bordered=True, hover=True, responsive=True, size='sm')
                ])
            ], className="mb-3")
            
            account_cards.append(card)
        
        return account_cards
        
    except Exception as e:
        return html.P(f"Fel vid laddning av kontoöversikt: {str(e)}", className="text-danger")


# Callback: Update Bills Table
@app.callback(
    Output('bills-table', 'data'),
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
            return []
        
        # Filter out nested fields that DataTable can't handle
        # Only include the columns that are defined in the table
        table_data = []
        for bill in bills:
            table_data.append({
                'id': bill.get('id', ''),
                'name': bill.get('name', ''),
                'amount': bill.get('amount', 0),
                'due_date': bill.get('due_date', ''),
                'status': bill.get('status', ''),
                'category': bill.get('category', ''),
                'account': bill.get('account', '')
            })
        
        return table_data
    except Exception as e:
        print(f"Error loading bills: {str(e)}")
        return []


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
    Output('history-top-expenses-display', 'children'),
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
        raise PreventUpdate
    
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
        raise PreventUpdate


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
            # Show detailed results
            rules_created = result.get('rules_created', 0)
            categories = result.get('categories_trained', [])
            
            return dbc.Alert([
                html.H5("✓ Träning genomförd!", className="alert-heading"),
                html.P(result['message']),
                html.Hr(),
                html.Div([
                    html.P([
                        html.Strong("Nya kategoriseringsregler: "), 
                        f"{rules_created} st"
                    ], className="mb-2"),
                    html.P([
                        html.Strong("Tränade kategorier: "),
                        ", ".join(categories) if categories else "Inga"
                    ], className="mb-2"),
                    html.P([
                        html.I(className="bi bi-check-circle me-2"),
                        "AI-modellen är nu uppdaterad och kommer användas vid automatisk kategorisering av nya transaktioner."
                    ], className="mb-0 text-success")
                ])
            ], color="success", dismissable=True, duration=10000)
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


# Callback: Update Edit Bill Subcategory Options
@app.callback(
    Output('edit-bill-subcategory', 'options'),
    Input('edit-bill-category', 'value')
)
def update_edit_bill_subcategory_options(category):
    """Update edit bill subcategory dropdown based on selected category."""
    if not category:
        return []
    
    subcategories = CATEGORIES.get(category, [])
    return [{'label': sub, 'value': sub} for sub in subcategories]


# Callback: Update Edit Bill Account Options
@app.callback(
    Output('edit-bill-account', 'options'),
    Input('bills-interval', 'n_intervals')
)
def update_edit_bill_account_options(n):
    """Update the edit bill account dropdown with available accounts."""
    manager = AccountManager()
    accounts = manager.get_accounts()
    options = [{'label': 'Inget specifikt konto', 'value': ''}]
    for acc in accounts:
        options.append({'label': acc['name'], 'value': acc['name']})
    return options


# Callback: Open Edit Bill Modal (from table click)
@app.callback(
    [Output('edit-bill-modal', 'is_open'),
     Output('edit-bill-id', 'data'),
     Output('edit-bill-name', 'value'),
     Output('edit-bill-amount', 'value'),
     Output('edit-bill-due-date', 'value'),
     Output('edit-bill-category', 'value'),
     Output('edit-bill-subcategory', 'value'),
     Output('edit-bill-account', 'value'),
     Output('edit-bill-description', 'value'),
     Output('edit-bill-status-dropdown', 'value')],
    [Input('bills-table', 'selected_rows'),
     Input('edit-bill-cancel-btn', 'n_clicks'),
     Input('edit-bill-save-btn', 'n_clicks'),
     Input('edit-bill-mark-paid-btn', 'n_clicks')],
    [State('bills-table', 'data'),
     State('edit-bill-modal', 'is_open'),
     State('edit-bill-id', 'data')]
)
def toggle_edit_bill_modal(selected_rows, cancel_clicks, save_clicks, mark_paid_clicks, table_data, is_open, current_bill_id):
    """Toggle edit bill modal and populate fields."""
    ctx = callback_context
    if not ctx.triggered:
        return False, None, "", 0, "", "", "", "", "", ""
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'bills-table' and selected_rows and table_data:
        # Load bill data
        selected_bill = table_data[selected_rows[0]]
        bill_id = selected_bill.get('id')
        
        bill_manager = BillManager()
        bill = bill_manager.get_bill_by_id(bill_id)
        
        if bill:
            return (True, bill_id, bill.get('name', ''), bill.get('amount', 0),
                    bill.get('due_date', ''), bill.get('category', ''),
                    bill.get('subcategory', ''), bill.get('account', ''),
                    bill.get('description', ''), bill.get('status', 'scheduled'))
        
        return True, bill_id, "", 0, "", "", "", "", "", ""
    
    elif button_id in ['edit-bill-cancel-btn', 'edit-bill-save-btn', 'edit-bill-mark-paid-btn']:
        return False, None, "", 0, "", "", "", "", "", ""
    
    return is_open, current_bill_id, "", 0, "", "", "", "", "", ""


# Callback: Save Edited Bill
@app.callback(
    Output('edit-bill-status-message', 'children'),
    Input('edit-bill-save-btn', 'n_clicks'),
    [State('edit-bill-id', 'data'),
     State('edit-bill-name', 'value'),
     State('edit-bill-amount', 'value'),
     State('edit-bill-due-date', 'value'),
     State('edit-bill-category', 'value'),
     State('edit-bill-subcategory', 'value'),
     State('edit-bill-account', 'value'),
     State('edit-bill-description', 'value'),
     State('edit-bill-status-dropdown', 'value')],
    prevent_initial_call=True
)
def save_edited_bill(n_clicks, bill_id, name, amount, due_date, category, subcategory, account, description, status):
    """Save changes to edited bill."""
    if not n_clicks or not bill_id:
        return ""
    
    try:
        bill_manager = BillManager()
        updates = {
            'name': name,
            'amount': float(amount) if amount else 0,
            'due_date': due_date,
            'category': category or 'Övrigt',
            'subcategory': subcategory or '',
            'account': account or None,
            'description': description or '',
            'status': status or 'scheduled'
        }
        
        success = bill_manager.update_bill(bill_id, updates)
        
        if success:
            return dbc.Alert("✓ Faktura uppdaterad!", color="success", dismissable=True)
        else:
            return dbc.Alert("Kunde inte hitta fakturan", color="warning", dismissable=True)
    except Exception as e:
        return dbc.Alert(f"Fel: {str(e)}", color="danger", dismissable=True)


# Callback: Mark Bill as Paid
@app.callback(
    Output('edit-bill-status-message', 'children', allow_duplicate=True),
    Input('edit-bill-mark-paid-btn', 'n_clicks'),
    State('edit-bill-id', 'data'),
    prevent_initial_call=True
)
def mark_bill_as_paid(n_clicks, bill_id):
    """Mark bill as paid."""
    if not n_clicks or not bill_id:
        return ""
    
    try:
        bill_manager = BillManager()
        success = bill_manager.mark_as_paid(bill_id)
        
        if success:
            return dbc.Alert("✓ Faktura markerad som betald!", color="success", dismissable=True)
        else:
            return dbc.Alert("Kunde inte hitta fakturan", color="warning", dismissable=True)
    except Exception as e:
        return dbc.Alert(f"Fel: {str(e)}", color="danger", dismissable=True)


# Callback: Train AI from Bill
@app.callback(
    Output('edit-bill-status-message', 'children', allow_duplicate=True),
    Input('edit-bill-train-ai-btn', 'n_clicks'),
    [State('edit-bill-id', 'data'),
     State('edit-bill-name', 'value'),
     State('edit-bill-category', 'value'),
     State('edit-bill-subcategory', 'value')],
    prevent_initial_call=True
)
def train_ai_from_bill(n_clicks, bill_id, name, category, subcategory):
    """Add bill information to AI training data."""
    if not n_clicks or not bill_id:
        return ""
    
    try:
        from modules.core.ai_trainer import AITrainer
        
        trainer = AITrainer()
        
        # Add training sample
        trainer.add_training_sample(
            description=name or '',
            category=category or 'Övrigt',
            subcategory=subcategory or ''
        )
        
        return dbc.Alert("✓ Träningsdata tillagd för AI!", color="success", dismissable=True)
    except Exception as e:
        return dbc.Alert(f"Fel: {str(e)}", color="danger", dismissable=True)


# Callback: Update Monthly Analysis Month Dropdowns
@app.callback(
    [Output('analysis-start-month', 'options'),
     Output('analysis-end-month', 'options')],
    Input('monthly-analysis-interval', 'n_intervals')
)
def update_monthly_analysis_months(n):
    """Update month dropdowns for monthly analysis."""
    from modules.core.history_viewer import HistoryViewer
    
    try:
        viewer = HistoryViewer()
        months = viewer.get_all_months()
        options = [{'label': month, 'value': month} for month in months]
        return options, options
    except:
        # Fallback to current month if no data
        from datetime import datetime
        current_month = datetime.now().strftime('%Y-%m')
        options = [{'label': current_month, 'value': current_month}]
        return options, options


# Callback: Update Monthly Upcoming Bills
@app.callback(
    Output('monthly-upcoming-bills-display', 'children'),
    Input('analyze-period-btn', 'n_clicks'),
    [State('analysis-start-month', 'value'),
     State('analysis-end-month', 'value')],
    prevent_initial_call=False
)
def update_monthly_upcoming_bills(n_clicks, start_month, end_month):
    """Display upcoming bills for selected month."""
    from datetime import datetime
    
    # Default to current month
    if not start_month:
        start_month = datetime.now().strftime('%Y-%m')
    
    bill_manager = BillManager()
    # Get both scheduled and pending bills
    scheduled_bills = bill_manager.get_bills(status='scheduled')
    pending_bills = bill_manager.get_bills(status='pending')
    all_bills = scheduled_bills + pending_bills
    
    # Filter bills for the month
    month_bills = [
        b for b in all_bills 
        if b.get('due_date', '').startswith(start_month)
    ]
    
    if not month_bills:
        return html.P("Inga kommande fakturor för denna månad", className="text-muted")
    
    total_amount = sum(b['amount'] for b in month_bills)
    
    bill_rows = []
    for bill in sorted(month_bills, key=lambda x: x.get('due_date', '')):
        bill_rows.append(
            html.Tr([
                html.Td(bill['name']),
                html.Td(f"{bill['amount']:,.2f} SEK"),
                html.Td(bill['due_date']),
                html.Td(bill.get('category', 'N/A')),
                html.Td(bill.get('status', 'N/A').title())
            ])
        )
    
    return html.Div([
        html.H6(f"Totalt: {total_amount:,.2f} SEK ({len(month_bills)} fakturor)", className="mb-3 text-danger"),
        dbc.Table([
            html.Thead(html.Tr([
                html.Th("Namn"),
                html.Th("Belopp"),
                html.Th("Förfallodatum"),
                html.Th("Kategori"),
                html.Th("Status")
            ])),
            html.Tbody(bill_rows)
        ], bordered=True, hover=True, size='sm')
    ])


# Callback: Update Monthly Posted Transactions
@app.callback(
    Output('monthly-posted-transactions-display', 'children'),
    Input('analyze-period-btn', 'n_clicks'),
    [State('analysis-start-month', 'value'),
     State('analysis-end-month', 'value')],
    prevent_initial_call=False
)
def update_monthly_posted_transactions(n_clicks, start_month, end_month):
    """Display posted transactions for selected month."""
    from datetime import datetime
    
    # Default to current month
    if not start_month:
        start_month = datetime.now().strftime('%Y-%m')
    
    manager = AccountManager()
    all_transactions = manager.get_all_transactions()
    
    # Filter posted transactions for the month
    posted_txs = [
        tx for tx in all_transactions
        if tx.get('status') == 'posted' and tx.get('date', '').startswith(start_month)
    ]
    
    if not posted_txs:
        return html.P("Inga bokförda transaktioner för denna månad", className="text-muted")
    
    # Separate expenses and incomes
    expenses = [tx for tx in posted_txs if tx.get('amount', 0) < 0]
    incomes = [tx for tx in posted_txs if tx.get('amount', 0) > 0]
    
    total_expenses = sum(abs(tx['amount']) for tx in expenses)
    total_incomes = sum(tx['amount'] for tx in incomes)
    
    return html.Div([
        html.Div([
            html.P([
                html.Strong("Utgifter: "),
                html.Span(f"{total_expenses:,.2f} SEK", className="text-danger")
            ], className="mb-1"),
            html.P([
                html.Strong("Inkomster: "),
                html.Span(f"{total_incomes:,.2f} SEK", className="text-success")
            ], className="mb-1"),
            html.P([
                html.Strong("Netto: "),
                html.Span(f"{(total_incomes - total_expenses):,.2f} SEK", 
                         className="text-primary fw-bold")
            ], className="mb-2"),
        ]),
        html.Hr(),
        html.Small(f"{len(posted_txs)} bokförda transaktioner totalt", className="text-muted")
    ])


# Callback: Update Monthly Income Breakdown
@app.callback(
    Output('monthly-income-breakdown-display', 'children'),
    Input('analyze-period-btn', 'n_clicks'),
    [State('analysis-start-month', 'value'),
     State('analysis-end-month', 'value')],
    prevent_initial_call=False
)
def update_monthly_income_breakdown(n_clicks, start_month, end_month):
    """Display income breakdown per person and account."""
    from datetime import datetime
    
    # Default to current month
    if not start_month:
        start_month = datetime.now().strftime('%Y-%m')
    
    income_tracker = IncomeTracker()
    incomes = income_tracker.get_incomes(
        start_date=f"{start_month}-01",
        end_date=f"{start_month}-31"
    )
    
    if not incomes:
        return html.P("Inga registrerade inkomster för denna period", className="text-muted")
    
    # Group by person and account
    from collections import defaultdict
    person_account_income = defaultdict(lambda: defaultdict(float))
    
    for inc in incomes:
        person = inc.get('person', 'Okänd')
        account = inc.get('account', 'Okänt konto')
        amount = inc.get('amount', 0)
        person_account_income[person][account] += amount
    
    # Build display
    person_sections = []
    for person, accounts in person_account_income.items():
        total_person = sum(accounts.values())
        account_rows = []
        for account, amount in accounts.items():
            account_rows.append(
                html.P(f"  {account}: {amount:,.2f} SEK", className="mb-1 small")
            )
        
        person_sections.append(html.Div([
            html.H6(f"{person}: {total_person:,.2f} SEK", className="mb-2"),
            html.Div(account_rows, className="ms-3 mb-3")
        ]))
    
    return html.Div(person_sections)


# Callback: Update Monthly Expense Summary
@app.callback(
    Output('monthly-expense-summary-display', 'children'),
    Input('analyze-period-btn', 'n_clicks'),
    [State('analysis-start-month', 'value'),
     State('analysis-end-month', 'value')],
    prevent_initial_call=False
)
def update_monthly_expense_summary(n_clicks, start_month, end_month):
    """Display expense summary by category."""
    from datetime import datetime
    
    # Default to current month
    if not start_month:
        start_month = datetime.now().strftime('%Y-%m')
    
    manager = AccountManager()
    transactions = manager.get_all_transactions()
    
    # Filter expenses for the month
    month_expenses = [
        tx for tx in transactions
        if tx.get('date', '').startswith(start_month) and tx.get('amount', 0) < 0
    ]
    
    if not month_expenses:
        return html.P("Inga utgifter för denna period", className="text-muted")
    
    # Group by category
    from collections import defaultdict
    category_totals = defaultdict(float)
    
    for tx in month_expenses:
        category = tx.get('category', 'Okategoriserad')
        amount = abs(tx.get('amount', 0))
        category_totals[category] += amount
    
    total_expenses = sum(category_totals.values())
    
    # Sort by amount
    sorted_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
    
    category_rows = []
    for category, amount in sorted_categories:
        percent = (amount / total_expenses * 100) if total_expenses > 0 else 0
        category_rows.append(
            html.P(f"{category}: {amount:,.2f} SEK ({percent:.1f}%)", className="mb-1")
        )
    
    return html.Div([
        html.H6(f"Totalt: {total_expenses:,.2f} SEK", className="mb-3 text-danger"),
        html.Small("Detta är totala utgifter. Välj gemensamma kategorier nedan för överföringsberäkning.", 
                  className="text-muted fst-italic"),
        html.Hr(),
        html.Div(category_rows)
    ])


# Callback: Calculate Transfer Recommendations
@app.callback(
    Output('transfer-recommendations-display', 'children'),
    Input('calculate-transfers-btn', 'n_clicks'),
    [State('analysis-start-month', 'value'),
     State('shared-categories-selector', 'value')],
    prevent_initial_call=True
)
def calculate_transfer_recommendations_callback(n_clicks, month, shared_categories):
    """Calculate and display transfer recommendations."""
    from datetime import datetime
    from modules.core.net_balance_splitter import calculate_transfer_recommendations
    
    # Default to current month
    if not month:
        month = datetime.now().strftime('%Y-%m')
    
    if not shared_categories:
        return dbc.Alert("Välj minst en gemensam kategori", color="warning")
    
    try:
        # Get income by person and account
        income_tracker = IncomeTracker()
        incomes = income_tracker.get_incomes(
            start_date=f"{month}-01",
            end_date=f"{month}-31"
        )
        
        from collections import defaultdict
        income_by_person_account = defaultdict(lambda: defaultdict(float))
        
        for inc in incomes:
            person = inc.get('person', 'Okänd')
            account = inc.get('account', 'Okänt konto')
            amount = inc.get('amount', 0)
            income_by_person_account[person][account] += amount
        
        # Convert to regular dict
        income_by_person_account = {
            person: dict(accounts) 
            for person, accounts in income_by_person_account.items()
        }
        
        # Get scheduled bills by category (upcoming expenses)
        bill_manager = BillManager()
        scheduled_bills = bill_manager.get_bills(status='scheduled')
        pending_bills = bill_manager.get_bills(status='pending')
        all_upcoming_bills = scheduled_bills + pending_bills
        
        # Filter bills for the selected month
        month_bills = [
            b for b in all_upcoming_bills 
            if b.get('due_date', '').startswith(month)
        ]
        
        expenses_by_category = defaultdict(float)
        for bill in month_bills:
            category = bill.get('category', 'Okategoriserad')
            amount = bill.get('amount', 0)
            expenses_by_category[category] += amount
        
        expenses_by_category = dict(expenses_by_category)
        
        # Calculate recommendations
        recommendations = calculate_transfer_recommendations(
            income_by_person_account,
            expenses_by_category,
            shared_categories=shared_categories
        )
        
        # Build display
        total_shared = recommendations['total_shared_expenses']
        persons = recommendations['persons']
        
        if not persons:
            return dbc.Alert("Ingen inkomstdata tillgänglig för beräkning", color="warning")
        
        person_cards = []
        for person, info in persons.items():
            person_cards.append(
                dbc.Card([
                    dbc.CardBody([
                        html.H5(person, className="card-title"),
                        html.P([
                            html.Strong("Total inkomst: "),
                            f"{info['total_income']:,.2f} SEK"
                        ], className="mb-2"),
                        html.P([
                            html.Strong("Andel av utgifter: "),
                            f"{info['ratio']*100:.1f}%"
                        ], className="mb-2"),
                        html.Hr(),
                        html.H6([
                            html.Strong("Ska överföra: "),
                            html.Span(f"{info['should_transfer']:,.2f} SEK", 
                                     className="text-success")
                        ], className="mb-0")
                    ])
                ], className="mb-3")
            )
        
        return html.Div([
            dbc.Alert([
                html.H5("Sammanfattning", className="alert-heading"),
                html.P(f"Totala kommande gemensamma utgifter: {total_shared:,.2f} SEK"),
                html.P(f"Baserat på {len(shared_categories)} gemensam{'ma' if len(shared_categories) > 1 else ''} kategori{'er' if len(shared_categories) > 1 else ''}: {', '.join(shared_categories)}"),
                html.Small([
                    "OBS: Beräkningen baseras på ",
                    html.Strong("kommande schemalagda fakturor"),
                    " för denna månad i de valda kategorierna."
                ], className="text-muted fst-italic")
            ], color="info", className="mb-3"),
            html.Div(person_cards)
        ])
    
    except Exception as e:
        return dbc.Alert(f"Fel vid beräkning: {str(e)}", color="danger")


# ==== AMEX WORKFLOW CALLBACKS ====




# ===== CREDIT CARD CALLBACKS =====

# Credit Card Callbacks

# Callback: Add Credit Card
@app.callback(
    Output('card-add-status', 'children'),
    Input('add-card-btn', 'n_clicks'),
    [State('card-name-input', 'value'),
     State('card-type-dropdown', 'value'),
     State('card-last-four-input', 'value'),
     State('card-limit-input', 'value'),
     State('card-color-input', 'value')],
    prevent_initial_call=True
)
def add_credit_card(n_clicks, name, card_type, last_four, limit, color):
    """Add a new credit card."""
    if not name or not card_type or not last_four or not limit:
        return dbc.Alert("Fyll i alla fält", color="warning")
    
    try:
        manager = CreditCardManager()
        card = manager.add_card(
            name=name,
            card_type=card_type,
            last_four=last_four,
            credit_limit=float(limit),
            display_color=color or "#1f77b4",
            icon="credit-card"
        )
        
        return dbc.Alert(f"✓ Kreditkort '{name}' tillagt!", color="success", dismissable=True)
    except Exception as e:
        return dbc.Alert(f"Fel: {str(e)}", color="danger")


# Callback: Update Credit Cards Overview
@app.callback(
    [Output('credit-cards-overview', 'children'),
     Output('card-import-selector', 'options'),
     Output('card-details-selector', 'options')],
    Input('add-card-btn', 'n_clicks')
)
def update_cards_overview(n_clicks):
    """Update the credit cards overview display and dropdowns."""
    try:
        manager = CreditCardManager()
        cards = manager.get_cards(status='active')
        
        if not cards:
            return (
                html.P("Inga kreditkort tillagda än. Lägg till ditt första kort ovan.", className="text-muted"),
                [],
                []
            )
        
        # Create card summary cards
        card_elements = []
        dropdown_options = []
        
        for card in cards:
            summary = manager.get_card_summary(card['id'])
            
            # Card display
            card_elem = dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.H5(f"{card['name']} (****{card['last_four']})", className="mb-1"),
                            html.P(card['card_type'], className="text-muted mb-2"),
                        ], width=6),
                        dbc.Col([
                            html.Div([
                                html.Div([
                                    html.Iframe(
                                        srcDoc=get_card_icon(card.get('card_type', ''), size=48),
                                        style={
                                            'width': '48px',
                                            'height': '48px',
                                            'border': 'none',
                                            'overflow': 'hidden'
                                        }
                                    )
                                ], style={'display': 'inline-block'})
                            ], style={'textAlign': 'right'})
                        ], width=4),
                        dbc.Col([
                            html.Div([
                                dbc.Button("✏️", id={'type': 'edit-card-btn', 'index': card['id']}, 
                                          size="sm", color="primary", outline=True, className="me-1"),
                                dbc.Button("🗑️", id={'type': 'delete-card-btn', 'index': card['id']}, 
                                          size="sm", color="danger", outline=True),
                            ], style={'textAlign': 'right'})
                        ], width=2),
                    ]),
                    html.Hr(),
                    dbc.Row([
                        dbc.Col([
                            html.Small("Aktuellt saldo:", className="text-muted d-block"),
                            html.Strong(f"{summary['current_balance']:,.2f} SEK", className="d-block fs-5"),
                        ], width=4),
                        dbc.Col([
                            html.Small("Tillgänglig kredit:", className="text-muted d-block"),
                            html.Strong(f"{summary['available_credit']:,.2f} SEK", className="d-block fs-5"),
                        ], width=4),
                        dbc.Col([
                            html.Small("Utnyttjande:", className="text-muted d-block"),
                            html.Strong(f"{summary['utilization_percent']:.1f}%", className="d-block fs-5"),
                        ], width=4),
                    ]),
                    html.Div([
                        dbc.Progress(value=summary['utilization_percent'], max=100, 
                                   color="danger" if summary['utilization_percent'] > 70 else ("warning" if summary['utilization_percent'] > 30 else "success"),
                                   className="mt-2")
                    ]),
                    html.Hr(),
                    dbc.Row([
                        dbc.Col([
                            html.Small(f"Transaktioner: {summary['total_transactions']}", className="text-muted"),
                        ], width=6),
                        dbc.Col([
                            html.Small(f"Totalt spenderat: {summary['total_spent']:,.2f} SEK", className="text-muted"),
                        ], width=6),
                    ]),
                ])
            ], className="mb-3", style={'borderLeft': f"4px solid {card.get('display_color', '#1f77b4')}"})
            
            card_elements.append(card_elem)
            
            # Add to dropdown options
            dropdown_options.append({
                'label': f"{card['name']} (****{card['last_four']})",
                'value': card['id']
            })
        
        return html.Div(card_elements), dropdown_options, dropdown_options
        
    except Exception as e:
        return dbc.Alert(f"Fel: {str(e)}", color="danger"), [], []


# Callback: Import CSV Transactions
@app.callback(
    Output('card-csv-import-status', 'children'),
    Input('upload-card-csv', 'contents'),
    [State('upload-card-csv', 'filename'),
     State('card-import-selector', 'value')],
    prevent_initial_call=True
)
def import_card_csv(contents, filename, card_id):
    """Import transactions from uploaded CSV file."""
    if contents is None or not card_id:
        return dbc.Alert("Välj ett kort först", color="warning")
    
    try:
        # Decode the uploaded file
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        
        # Save to temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as tmp_file:
            tmp_file.write(decoded)
            tmp_path = tmp_file.name
        
        try:
            # Import transactions
            manager = CreditCardManager()
            count = manager.import_transactions_from_csv(card_id, tmp_path)
            
            return dbc.Alert(
                f"✓ {count} transaktioner importerade från {filename}!",
                color="success",
                dismissable=True
            )
        finally:
            # Clean up temporary file
            import os
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    except Exception as e:
        return dbc.Alert(f"Fel vid import: {str(e)}", color="danger")


# Callback: Display Card Details and Transactions
@app.callback(
    Output('card-details-container', 'children'),
    Input('card-details-selector', 'value')
)
def display_card_details(card_id):
    """Display detailed information and transactions for selected card."""
    if not card_id:
        return ""
    
    try:
        manager = CreditCardManager()
        summary = manager.get_card_summary(card_id)
        transactions = manager.get_transactions(card_id)
        
        # Summary section
        summary_elem = dbc.Alert([
            html.H6(f"{summary['name']} (****{summary['card_type']})", className="alert-heading"),
            html.P([
                html.Strong("Saldo: "), f"{summary['current_balance']:,.2f} SEK", html.Br(),
                html.Strong("Kreditgräns: "), f"{summary['credit_limit']:,.2f} SEK", html.Br(),
                html.Strong("Tillgänglig kredit: "), f"{summary['available_credit']:,.2f} SEK", html.Br(),
                html.Strong("Utnyttjande: "), f"{summary['utilization_percent']:.1f}%", html.Br(),
            ])
        ], color="info", className="mb-3")
        
        # Category breakdown
        if summary['category_breakdown']:
            category_data = [{'Kategori': cat, 'Belopp': amount} 
                           for cat, amount in summary['category_breakdown'].items()]
            category_df = pd.DataFrame(category_data)
            
            category_elem = html.Div([
                html.H6("Utgifter per kategori"),
                dash_table.DataTable(
                    data=category_df.to_dict('records'),
                    columns=[{'name': col, 'id': col} for col in category_df.columns],
                    style_table={'overflowX': 'auto'},
                    style_cell={'textAlign': 'left', 'padding': '10px'},
                    style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'}
                )
            ], className="mb-3")
        else:
            category_elem = ""
        
        # Transactions table
        if transactions:
            tx_df = pd.DataFrame(transactions)
            # Select relevant columns
            display_cols = ['date', 'vendor', 'description', 'amount', 'category', 'subcategory']
            tx_df = tx_df[[col for col in display_cols if col in tx_df.columns]]
            
            # Add ID column for editing (hidden)
            if 'id' in pd.DataFrame(transactions).columns:
                tx_df['id'] = pd.DataFrame(transactions)['id']
            
            transactions_elem = html.Div([
                html.H6(f"Transaktioner ({len(transactions)})"),
                html.P("Klicka på en transaktion för att redigera kategori", className="text-muted small"),
                dash_table.DataTable(
                    id='card-transactions-table',
                    data=tx_df.to_dict('records'),
                    columns=[{'name': col.title(), 'id': col} for col in tx_df.columns if col != 'id'],
                    style_table={'overflowX': 'auto'},
                    style_cell={'textAlign': 'left', 'padding': '10px'},
                    style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
                    page_size=20,
                    row_selectable='single'
                ),
                html.Div(id='card-tx-edit-container', className="mt-3")
            ])
        else:
            transactions_elem = html.P("Inga transaktioner funna. Importera från CSV.", className="text-muted")
        
        return html.Div([summary_elem, category_elem, transactions_elem])
        
    except Exception as e:
        return dbc.Alert(f"Fel: {str(e)}", color="danger")


# Callback: Open Edit Card Modal
@app.callback(
    [Output('edit-card-modal', 'is_open'),
     Output('edit-card-name', 'value'),
     Output('edit-card-type', 'value'),
     Output('edit-card-last-four', 'value'),
     Output('edit-card-limit', 'value'),
     Output('edit-card-color', 'value'),
     Output('edit-card-id-store', 'data')],
    [Input({'type': 'edit-card-btn', 'index': dash.dependencies.ALL}, 'n_clicks'),
     Input('edit-card-cancel', 'n_clicks'),
     Input('edit-card-save', 'n_clicks')],
    [State('edit-card-id-store', 'data'),
     State('edit-card-name', 'value'),
     State('edit-card-type', 'value'),
     State('edit-card-last-four', 'value'),
     State('edit-card-limit', 'value'),
     State('edit-card-color', 'value')],
    prevent_initial_call=True
)
def handle_edit_card_modal(edit_clicks, cancel_clicks, save_clicks, 
                           stored_card_id, name, card_type, last_four, limit, color):
    """Handle edit card modal open/close and save."""
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    trigger_id = ctx.triggered[0]['prop_id']
    
    # Cancel button
    if 'edit-card-cancel' in trigger_id:
        return False, None, None, None, None, '#1f77b4', None
    
    # Save button
    if 'edit-card-save' in trigger_id and stored_card_id:
        try:
            manager = CreditCardManager()
            updates = {
                'name': name,
                'card_type': card_type,
                'last_four': last_four,
                'credit_limit': float(limit) if limit else 0.0,
                'display_color': color
            }
            manager.update_card(stored_card_id, updates)
            return False, None, None, None, None, '#1f77b4', None
        except Exception as e:
            # Keep modal open on error
            return True, name, card_type, last_four, limit, color, stored_card_id
    
    # Edit button clicked
    if 'edit-card-btn' in trigger_id:
        # Find which card was clicked
        button_data = ctx.triggered[0]['prop_id']
        import json
        # Extract index from pattern matching callback
        start = button_data.index('"index":"') + len('"index":"')
        end = button_data.index('"', start)
        card_id = button_data[start:end]
        
        # Load card data
        manager = CreditCardManager()
        card = manager.get_card_by_id(card_id)
        
        if card:
            return (True, 
                   card.get('name'), 
                   card.get('card_type'),
                   card.get('last_four'),
                   card.get('credit_limit'),
                   card.get('display_color', '#1f77b4'),
                   card_id)
    
    raise PreventUpdate


# Callback: Open Delete Card Modal
@app.callback(
    [Output('delete-card-modal', 'is_open'),
     Output('delete-card-confirm-text', 'children'),
     Output('delete-card-id-store', 'data')],
    [Input({'type': 'delete-card-btn', 'index': dash.dependencies.ALL}, 'n_clicks'),
     Input('delete-card-cancel', 'n_clicks'),
     Input('delete-card-confirm', 'n_clicks')],
    [State('delete-card-id-store', 'data')],
    prevent_initial_call=True
)
def handle_delete_card_modal(delete_clicks, cancel_clicks, confirm_clicks, stored_card_id):
    """Handle delete card modal open/close and confirm."""
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    trigger_id = ctx.triggered[0]['prop_id']
    
    # Cancel button
    if 'delete-card-cancel' in trigger_id:
        return False, "", None
    
    # Confirm button
    if 'delete-card-confirm' in trigger_id and stored_card_id:
        try:
            manager = CreditCardManager()
            manager.delete_card(stored_card_id)
            return False, "", None
        except Exception as e:
            return True, f"Fel vid borttagning: {str(e)}", stored_card_id
    
    # Delete button clicked
    if 'delete-card-btn' in trigger_id:
        # Find which card was clicked
        button_data = ctx.triggered[0]['prop_id']
        import json
        start = button_data.index('"index":"') + len('"index":"')
        end = button_data.index('"', start)
        card_id = button_data[start:end]
        
        # Load card data
        manager = CreditCardManager()
        card = manager.get_card_by_id(card_id)
        
        if card:
            message = f"Är du säker på att du vill ta bort kreditkortet {card.get('name')} (****{card.get('last_four')})?  Detta kommer även ta bort alla transaktioner för detta kort."
            return True, message, card_id
    
    raise PreventUpdate


# Callback: Handle Credit Card Transaction Selection and Editing
@app.callback(
    Output('card-tx-edit-container', 'children'),
    [Input('card-transactions-table', 'selected_rows'),
     Input('card-details-selector', 'value')],
    State('card-transactions-table', 'data'),
    prevent_initial_call=True
)
def handle_card_tx_selection(selected_rows, card_id, table_data):
    """Display edit form when a transaction is selected."""
    if not selected_rows or not table_data or not card_id:
        return ""
    
    selected_idx = selected_rows[0]
    selected_tx = table_data[selected_idx]
    
    # Category manager for dropdowns
    cat_manager = CategoryManager()
    categories = cat_manager.get_categories()
    
    category_options = [{'label': cat, 'value': cat} for cat in categories.keys()]
    
    selected_category = selected_tx.get('category', '')
    subcategory_options = []
    if selected_category and selected_category in categories:
        subcategory_options = [{'label': sub, 'value': sub} for sub in categories[selected_category]]
    
    return dbc.Card([
        dbc.CardBody([
            html.H6("Redigera transaktion", className="card-title"),
            html.P(f"{selected_tx.get('description', '')} - {selected_tx.get('amount', 0)} SEK", className="text-muted"),
            dbc.Row([
                dbc.Col([
                    html.Label("Kategori:", className="fw-bold"),
                    dcc.Dropdown(
                        id='edit-card-tx-category',
                        options=category_options,
                        value=selected_category,
                        placeholder='Välj kategori'
                    )
                ], width=6),
                dbc.Col([
                    html.Label("Underkategori:", className="fw-bold"),
                    dcc.Dropdown(
                        id='edit-card-tx-subcategory',
                        options=subcategory_options,
                        value=selected_tx.get('subcategory', ''),
                        placeholder='Välj underkategori'
                    )
                ], width=6),
            ], className="mb-3"),
            dbc.ButtonGroup([
                dbc.Button("💾 Spara kategorisering", id='save-card-tx-btn', color="primary", size="sm"),
                dbc.Button("🤖 Träna AI", id='train-card-tx-btn', color="success", size="sm", className="ms-2"),
            ]),
            html.Div(id='card-tx-edit-status', className="mt-2"),
            dcc.Store(id='selected-card-tx-idx', data=selected_idx),
            dcc.Store(id='selected-card-id', data=card_id)
        ])
    ], className="border-primary")


@app.callback(
    Output('edit-card-tx-subcategory', 'options'),
    Input('edit-card-tx-category', 'value')
)
def update_card_tx_subcategories(category):
    """Update subcategory options when category changes."""
    if not category:
        return []
    
    cat_manager = CategoryManager()
    categories = cat_manager.get_categories()
    
    if category in categories:
        return [{'label': sub, 'value': sub} for sub in categories[category]]
    
    return []


@app.callback(
    Output('card-tx-edit-status', 'children'),
    [Input('save-card-tx-btn', 'n_clicks'),
     Input('train-card-tx-btn', 'n_clicks')],
    [State('selected-card-id', 'data'),
     State('card-transactions-table', 'data'),
     State('selected-card-tx-idx', 'data'),
     State('edit-card-tx-category', 'value'),
     State('edit-card-tx-subcategory', 'value')],
    prevent_initial_call=True
)
def save_card_tx_category(save_clicks, train_clicks, card_id, table_data, tx_idx, category, subcategory):
    """Save credit card transaction category."""
    ctx = callback_context
    if not ctx.triggered or tx_idx is None or not table_data:
        raise PreventUpdate
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    try:
        manager = CreditCardManager()
        selected_tx = table_data[tx_idx]
        tx_id = selected_tx.get('id')
        
        if not tx_id:
            return dbc.Alert("Fel: Transaktions-ID saknas", color="danger", dismissable=True)
        
        # Update transaction
        success = manager.update_transaction(
            card_id=card_id,
            transaction_id=tx_id,
            category=category,
            subcategory=subcategory
        )
        
        if not success:
            return dbc.Alert("Fel vid uppdatering", color="danger", dismissable=True)
        
        # If train button was clicked, also train AI
        if 'train-card-tx-btn' in trigger_id:
            trainer = AITrainer()
            trainer.add_training_entry(
                description=selected_tx.get('description', ''),
                category=category,
                subcategory=subcategory,
                manual=True
            )
            return dbc.Alert("✓ Kategorisering sparad och AI tränad!", color="success", dismissable=True)
        
        return dbc.Alert("✓ Kategorisering sparad!", color="success", dismissable=True)
        
    except Exception as e:
        return dbc.Alert(f"Fel: {str(e)}", color="danger", dismissable=True)


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
