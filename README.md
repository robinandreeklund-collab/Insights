# 📊 Insights – Agentdriven hushållsekonomi med AI, YAML och Dash

Insights är ett transparent, modulärt och agentförberett system för hushållsekonomi. Det kombinerar regelbaserad och AI-driven transaktionsklassificering, prognoser, frågebaserad analys och full kontroll över konton, fakturor, inkomster och lån – allt styrt via YAML och ett interaktivt Dash-gränssnitt.

## 🎯 Projektstatus: Sprint 4

**Sprint 4 Status:** Faktura- och lånehantering implementerad!

Sprint 4 har implementerat:
- ✅ Fakturor-tab med fakturahantering
- ✅ Möjlighet att lägga till, visa, redigera och ta bort fakturor
- ✅ PDF-fakturaimport (placeholder-implementation för demo)
- ✅ Automatisk fakturamatchning mot transaktioner
- ✅ Schemaläggning av betalningar
- ✅ Lån-tab med lånehantering
- ✅ Lägg till och hantera lån med ränta och bindningstid
- ✅ Visualisering av återbetalningsplan
- ✅ Simulering av ränteförändringar
- ✅ Omfattande tester för alla nya moduler

**Sprint 3 Status (tidigare):** Dashboard-integration och interaktiv visualisering fungerar!

Sprint 3 har implementerat:
- ✅ Drag-and-drop CSV-upload direkt i dashboarden
- ✅ Interaktiv prognosgraf (line chart) över framtida saldo
- ✅ Utgiftsfördelning per kategori med pie chart
- ✅ Transaktionsbläddring med paginering (50 per sida)
- ✅ UI för manuell kategorisering med dropdowns
- ✅ Realtidsuppdateringar av saldo och grafer
- ✅ Fullständig dashboard-integration med alla Sprint 2-funktioner

**Sprint 2 Status (tidigare):** CSV-import, kategorisering och prognoser fungerar!

Sprint 2 har implementerat:
- ✅ CSV-import med Nordea-format
- ✅ Automatisk kontoskapande från filnamn
- ✅ Regelbaserad och AI-driven kategorisering (hybrid)
- ✅ Prognosmotorer för framtida saldo
- ✅ YAML-databas med konton, transaktioner och träningsdata
- ✅ Omfattande enhetstester

**Sprint 1 Status (tidigare):** Grundläggande struktur och dashboard är på plats.

I Sprint 1 satte vi upp:
- ✅ Mappstruktur enligt `project_structure.yaml`
- ✅ Grundmoduler i `modules/core/` (stubs utan faktisk logik)
- ✅ Tomma YAML-datafiler för framtida användning
- ✅ Dashboard med alla paneler/tabbar
- ✅ Grundläggande enhetstester
- ✅ Requirements och installation

## 🚀 Kom igång

### Snabbstart

1. **Installera beroenden:**
```bash
pip install -r requirements.txt
```

2. **Starta dashboarden:**
```bash
python dashboard/dashboard_ui.py
```

3. **Öppna i webbläsaren:** [http://127.0.0.1:8050](http://127.0.0.1:8050)

4. **Importera din första CSV-fil:**
   - Gå till fliken "Inmatning" i dashboarden
   - Dra och släpp en Nordea CSV-fil eller klicka för att välja fil
   - Systemet kommer automatiskt att importera och kategorisera transaktionerna
   - Gå till "Ekonomisk översikt" för att se prognoser och utgiftsfördelning
   - Gå till "Konton" för att bläddra i transaktioner och kategorisera manuellt

**Alternativt (kommandorad):**
```bash
python import_flow.py "PERSONKONTO 880104-7591 - 2025-10-21 15.38.56.csv"
```

## 🚀 Planerade funktioner

### 1. Ekonomisk översikt
- Prognos 30 dagar framåt
- Utgiftsfördelning per kategori
- Agentgenererade insikter och varningar

### 2. Inmatning
- Importera Nordea CSV-filer
- Lägg till fakturor och inkomster manuellt
- Läs in fakturor från PDF (enskilda eller sammanställningar)
- Automatisk transaktionsklassificering (regelbaserad + AI-hybrid)

### 3. Konton
- Skapa och hantera konton från CSV
- Visa kontoutdrag (50 transaktioner per sida)
- Manuell kategorisering med huvud- och underkategori
- Träna AI-modellen direkt från kontoutdraget

### 4. Fakturor
- Aktiva och hanterade fakturor
- Automatisk matchning mot transaktioner
- PDF-import (placeholder för demo)
- Schemaläggning av betalningar
- Prognosintegration och historik

### 5. Historik
- Månadssammanställningar
- Kategoritrender över tid
- Topptransaktioner och saldohistorik

### 6. Lån
- Lägg till lån med ränta och bindningstid
- Visualisera återbetalning och saldo
- Simulera ränteförändringar och bindningstidens slut
- Månadsvis amorteringsplan

### 7. Frågebaserad analys
- "Vad händer om räntan ökar med 2%?"
- "Hur mycket har vi kvar i november?"
- "Visa alla fakturor i oktober"

## 🛠️ Installation

### Krav
- Python 3.10 eller högre
- pip (Python package manager)

### Steg för steg

1. Klona repositoryt:
```bash
git clone https://github.com/robinandreeklund-collab/Insights.git
cd Insights
```

2. Installera beroenden:
```bash
pip install -r requirements.txt
```

3. Importera en CSV-fil (Nordea-format):
```bash
python import_flow.py "DIN_FIL.csv"
```
   Detta kommer att:
   - Extrahera kontonamnet från filnamnet
   - Skapa kontot om det inte finns
   - Importera och kategorisera alla transaktioner
   - Spara data i YAML-filer

   **Tips för testning:** Använd `--clear` flaggan för att rensa befintliga data före import:
```bash
python import_flow.py --clear "DIN_FIL.csv"
```
   Detta är användbart när du testar och vill importera samma fil flera gånger.

4. Starta dashboard:
```bash
python dashboard/dashboard_ui.py
```
   **OBS:** När du stoppar dashboarden med Ctrl-C kommer data filerna (`transactions.yaml` och `accounts.yaml`) att rensas automatiskt. Detta är användbart under utveckling och testning.

5. Öppna din webbläsare på: [http://127.0.0.1:8050](http://127.0.0.1:8050)

## 📁 Projektstruktur

```
Insights/
├── modules/
│   ├── core/              # Grundmoduler
│   │   ├── account_manager.py
│   │   ├── import_bank_data.py
│   │   └── categorize_expenses.py
│   ├── ui/                # UI-komponenter
│   ├── finance/           # Finansmoduler
│   ├── agent/             # Agentlogik
│   └── simulation/        # Simuleringsmoduler
├── yaml/                  # YAML-datafiler
│   ├── transactions.yaml
│   ├── accounts.yaml
│   ├── categorization_rules.yaml
│   └── training_data.yaml
├── dashboard/             # Dashboard-applikation
│   └── dashboard_ui.py
├── config/                # Konfigurationsfiler
├── tests/                 # Enhetstester
│   └── test_account_manager.py
├── docs/                  # Dokumentation
├── assets/                # Statiska filer (bilder, etc.)
├── data/                  # Importerade datafiler
├── requirements.txt       # Python-beroenden
└── README.md
```

## 🔄 Exempel på flöde

### 1. Importera CSV via Dashboard (Sprint 3)

1. Starta dashboarden: `python dashboard/dashboard_ui.py`
2. Öppna [http://127.0.0.1:8050](http://127.0.0.1:8050) i din webbläsare
3. Gå till fliken "Inmatning"
4. Dra och släpp en Nordea CSV-fil (t.ex., "PERSONKONTO 880104-7591 - 2025-10-21 15.38.56.csv")
5. Systemet kommer att:
   - Extrahera kontonamnet från filnamnet
   - Läsa och normalisera CSV-filen
   - Skapa kontot om det inte finns
   - Kategorisera alla transaktioner automatiskt
   - Visa bekräftelse med antal importerade transaktioner

### 2. Visa prognoser och utgiftsfördelning (Sprint 3)

1. Gå till fliken "Ekonomisk översikt"
2. Se nuvarande totalt saldo över alla konton
3. Studera 30-dagars prognosen (line chart) som visar förväntat saldo
4. Analysera utgiftsfördelningen per kategori (pie chart)
5. Grafer uppdateras automatiskt var 5:e sekund när ny data importeras

### 3. Bläddra och kategorisera transaktioner (Sprint 3)

1. Gå till fliken "Konton"
2. Välj ett konto från dropdown-menyn
3. Bläddra igenom transaktioner (50 per sida) med pagination
4. Klicka på en transaktion för att välja den
5. Använd dropdowns för att välja kategori och underkategori
6. Klicka "Spara kategorisering" för att:
   - Uppdatera transaktionens kategori
   - Lägga till i AI-träningsdata för framtida automatisk kategorisering
7. Tabellen uppdateras automatiskt för att visa den nya kategoriseringen

### 4. Importera CSV via kommandorad (Sprint 2)

```bash
python import_flow.py "PERSONKONTO 880104-7591 - 2025-10-21 15.38.56.csv"
```

Systemet kommer att:
1. Extrahera kontonamnet från filnamnet (t.ex., "PERSONKONTO 880104-7591")
2. Läsa och normalisera CSV-filen (Nordea-format)
3. Skapa kontot om det inte finns
4. Kategorisera alla transaktioner automatiskt med:
   - Regelbaserad kategorisering (från `yaml/categorization_rules.yaml`)
   - AI/heuristisk kategorisering för transaktioner utan regelträff
5. Spara transaktioner i `yaml/transactions.yaml`
6. Uppdatera `yaml/accounts.yaml` med kontouppgifter

### 5. Visa prognoser (via Python)

```python
from modules.core.forecast_engine import get_forecast_summary, get_category_breakdown

# Få en 30-dagars prognos
summary = get_forecast_summary(current_balance=1000.0, forecast_days=30)

print(f"Nuvarande saldo: {summary['current_balance']} SEK")
print(f"Förväntat saldo om {summary['forecast_days']} dagar: {summary['predicted_final_balance']} SEK")
print(f"Genomsnittlig daglig inkomst: {summary['avg_daily_income']} SEK")
print(f"Genomsnittlig daglig utgift: {summary['avg_daily_expenses']} SEK")

# Få utgiftsfördelning per kategori
breakdown = get_category_breakdown()
for category, amount in breakdown.items():
    print(f"{category}: {amount} SEK")
```

### 6. Kategorisera manuellt (via Python)

```python
from modules.core.account_manager import AccountManager

manager = AccountManager()

# Hämta transaktioner för ett konto
transactions = manager.get_account_transactions("PERSONKONTO 880104-7591")

# Kategorisera en transaktion manuellt
tx = transactions[0]
tx = manager.categorize_transaction(tx, "Mat & Dryck", "Matinköp")

# Träna AI-modellen från den manuella kategoriseringen
manager.train_ai_from_manual_input(tx)
```

### 7. Hantera fakturor och lån (via Dashboard eller Python - Sprint 4)

**Via Dashboard:**
1. Gå till fliken "Fakturor"
2. Fyll i fakturadetaljer (namn, belopp, förfallodatum)
3. Klicka "Lägg till faktura"
4. Använd "Importera från PDF (demo)" för att ladda in exempel-fakturor
5. Klicka "Matcha fakturor" för att automatiskt matcha mot betalda transaktioner

**För lån:**
1. Gå till fliken "Lån"
2. Fyll i låndetaljer (namn, belopp, ränta, löptid)
3. Klicka "Lägg till lån"
4. Välj ett lån och ange ny ränta för att simulera ränteförändring
5. Se återbetalningsplan i grafen

**Via Python:**
```python
from modules.core.bill_manager import BillManager
from modules.core.loan_manager import LoanManager

# Hantera fakturor
bill_manager = BillManager()
bill = bill_manager.add_bill(
    name="Elräkning December",
    amount=850.0,
    due_date="2025-12-31",
    category="Boende"
)

# Schemalägg betalning
bill_manager.schedule_payment(bill['id'], "2025-12-25")

# Hantera lån
loan_manager = LoanManager()
loan = loan_manager.add_loan(
    name="Bolån",
    principal=2000000.0,
    interest_rate=3.5,
    start_date="2025-01-01",
    term_months=360
)

# Simulera ränteförändring
simulation = loan_manager.simulate_interest_change(loan['id'], 4.5)
print(f"Ny månadsbetalning: {simulation['new_monthly_payment']} SEK")
print(f"Skillnad: {simulation['difference']} SEK ({simulation['difference_percent']}%)")
```

## 🧪 Tester

Kör enhetstester:
```bash
pytest tests/ -v
```

Kör tester med coverage:
```bash
pytest tests/ --cov=modules --cov-report=html
```

## 🧱 Teknisk arkitektur

- **📁 YAML-baserad datalagring** - All data sparas i lättlästa YAML-filer
- **🧠 Agentgränssnitt** - Frågebaserad analys och simulering
- **📊 Dash-gränssnitt** - Interaktiv visualisering och inmatning
- **🧪 Enhetstester** - Testdriven utveckling
- **🔁 Modulär struktur** - Lätt att utöka och underhålla

## 🧠 Vision

Insights är byggt för att vara:
- 🧩 **Modulärt och transparent** - Varje komponent är fristående och lättförståelig
- 🧠 **Agentförberett och självlärande** - AI-driven analys och kategorisering
- 🧪 **Testbart och framtidssäkert** - Hög testtäckning och bra kodkvalitet
- 👥 **Användarcentrerat och pedagogiskt** - Intuitivt gränssnitt och tydlig dokumentation

## 📝 Roadmap

- [x] Sprint 1: Grundstruktur och dashboard
- [x] Sprint 2: Import och kategorisering av transaktioner
  - [x] CSV-import med Nordea-format
  - [x] Regelbaserad kategorisering
  - [x] AI/heuristisk kategorisering
  - [x] Prognosmotorer
  - [x] YAML-databas
- [x] Sprint 3: Dashboard-integration och visualiseringar
  - [x] Drag-and-drop CSV-upload i dashboard
  - [x] Prognosgrafer (line chart)
  - [x] Kategorifördelningsdiagram (pie chart)
  - [x] Kontoutdragsvy med paginering
  - [x] Manuell kategorisering via UI
  - [x] Realtidsuppdateringar
- [ ] Sprint 4: Fakturor och lånhantering
  - [x] Fakturahantering (lägg till, visa, redigera, ta bort)
  - [x] PDF-fakturaimport (placeholder-implementation)
  - [x] Automatisk fakturamatchning mot transaktioner
  - [x] Schemaläggning av betalningar
  - [x] Lånehantering (lägg till, visa, redigera)
  - [x] Återbetalningsvisualisering
  - [x] Ränteförändringssimuleringar
  - [x] Tester för faktura- och lånehantering
- [ ] Sprint 5: Agentdriven analys och simulering

## 🤝 Bidra

Läs [CONTRIBUTING.md](docs/CONTRIBUTING.md) för mer information om hur du kan bidra till projektet.

## 📄 Licens

Detta projekt är licensierat under MIT-licensen.
