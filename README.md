# 📊 Insights – Agentdriven hushållsekonomi med AI, YAML och Dash

Insights är ett transparent, modulärt och agentförberett system för hushållsekonomi. Det kombinerar regelbaserad och AI-driven transaktionsklassificering, prognoser, frågebaserad analys och full kontroll över konton, fakturor, inkomster och lån – allt styrt via YAML och ett interaktivt Dash-gränssnitt.

## 🎯 Projektstatus: Sprint 9 - Admin Dashboard för AI-träning och kategorisering

**Sprint 9 Status:** Komplett Admin Dashboard för effektiv AI-träning och kategorihantering!

Sprint 9 har implementerat:
- ✅ **Admin Dashboard**: Kraftfullt verktyg för admins att träna AI och hantera kategorier
- ✅ **Avancerad filtrering**: Filtrera transaktioner på källa, datum, belopp, kategori och konto
- ✅ **Bulk-operationer**: Uppdatera och träna AI med flera transaktioner samtidigt
- ✅ **Kategorihantering**: Skapa, slå ihop och ta bort kategorier direkt i dashboarden
- ✅ **Statistik**: Kategorifördelning, okategoriserade transaktioner och AI-träffsäkerhet
- ✅ **Alla CSV-format**: Stöd för Nordea, Amex och Mastercard
- ✅ **Omfattande tester**: 56 tester godkända (20 nya för Admin Dashboard)
- ✅ **Säkerhet**: CodeQL-godkänd utan säkerhetsproblem
- ✅ **Dokumentation**: Fullständig användarguide och implementationssammanfattning

**Sprint 8 Status (tidigare):** Förbättrad filtrering av interna överföringar, persistent månadval, utökad prognosgraf och ny Personer-panel!

Sprint 8 har implementerat:
- ✅ **Filtrering av interna överföringar**: Överföringar mellan egna konton exkluderas nu från alla utgiftsberäkningar
- ✅ **Persistent månadval i Historik**: Valt månad sparas i sessionen och återställs vid sidladdning
- ✅ **Utökad Saldo & prognos-graf**: Visar nu förväntat saldo, kumulativa inkomster och kumulativa utgifter
- ✅ **Valfri lånehantering**: Löptid för lån är nu valfritt för dynamiska återbetalningar
- ✅ **Personer-panel**: Ny flik för att hantera familjemedlemmar, spåra inkomster och analysera utgifter per person
- ✅ **Inkomsthistorik**: Visualisering av inkomster över tid per person
- ✅ **Per-person utgiftsanalys**: Detaljerad uppdelning av utgifter per kategori baserat på kreditkortsallokeringar
- ✅ **Omfattande tester**: 255 tester godkända (från 245), 10 nya tester för PersonManager

**Sprint 7 Status (tidigare):** OCR-baserad låneimport, utökad datamodell och smart transaktionsmatchning implementerad!

Sprint 7 har implementerat:
- ✅ **OCR-baserad låneimport**: Ladda upp skärmdumpar av lån och extrahera automatiskt alla detaljer
- ✅ **Utökad lånemodell**: 20+ fält inklusive lånenummer, långivare, kontonummer, låntagare, säkerheter
- ✅ **Smart transaktionsmatchning**: Matcha automatiskt transaktioner via kontonummer eller lånenamn
- ✅ **Separat spårning**: Amorteringar och räntebetalningar spåras oberoende av varandra
- ✅ **Förbättrad dashboard**: Visar lånenummer, långivare, kontonummer, totalt amorterat och betald ränta
- ✅ **Redigerbart formulär**: Granska och editera OCR-extraherade uppgifter innan sparande
- ✅ **Transaktionslänkning**: Koppla betalningar till specifika transaktioner med transaction_id
- ✅ **Kontonormalisering**: Hanterar olika format av kontonummer (bindestreck, mellanslag)
- ✅ **Dokumentation**: Omfattande användardokumentation och YAML-exempel
- ✅ **Omfattande tester**: 242 tester godkända (från 187), 14 valfria OCR-tester

**Sprint 6 Status (tidigare):** Komplett dataflöde med scheduled/posted transactions, förbättrad fakturamatchning och editerbara fakturor!

Sprint 6 har implementerat:
- ✅ **Transaktionsstatus-system**: Automatisk separation av 'scheduled' (framtida), 'posted' (bokförda) och 'paid' transaktioner
- ✅ **Metadata för transaktioner**: source, source_uploaded_at, is_bill, bill_due_date, account_number, matched_to_bill_id, imported_historical
- ✅ **CSV-import med statuslogik**: Framtida transaktioner markeras automatiskt som 'scheduled', historiska som 'posted'
- ✅ **Förbättrad PDF-fakturaimport**: Extraherar kontonummer, sätter is_bill=true, status='scheduled', normaliserar kontonummer
- ✅ **Kontonummer-baserad matchning**: Fakturor matchas mot transaktioner via kontonummer, belopp och datum med tolerans
- ✅ **Automatisk faktura-till-transaktion-matchning**: Uppdaterar både faktura och transaktion med matched_to_bill_id
- ✅ **Dashboard-förbättringar**: Real-time uppdateringar med dcc.Store, scheduled vs posted separation
- ✅ **Månadanalys-förbättringar**: Visar både kommande fakturor (scheduled) och bokförda transaktioner (posted), överföringsrekommendationer
- ✅ **Editerbara fakturor**: Inline-editering i Bills-tab med kategori, underkategori, belopp, datum, status, "Markera som betald" och "Träna AI"-knappar
- ✅ **AI-träning från fakturor**: Lägg till fakturadata till training_data.yaml direkt från UI
- ✅ **Omfattande tester**: Alla 187 tester godkända

**Sprint 5 Status (tidigare):** Avancerad analys, historik och AI i Insights implementerad!

Sprint 5 har implementerat:
- ✅ Agentdriven analys och simulering med naturligt språk
- ✅ Historik med månadssammanställningar, kategoritrender och saldohistorik
- ✅ Kontohantering med möjlighet att redigera konton
- ✅ Inkomsthantering med manuell registrering per person och konto
- ✅ Förbättrad PDF-fakturaimport med faktisk PDF-parsing (med pdfplumber)
- ✅ AI-träningslogik från manuell kategorisering
- ✅ Settings panel med konfigurerbara inställningar
- ✅ Omfattande tester för alla nya moduler (142 passing tests)

**Sprint 4 Status (tidigare):** Faktura- och lånehantering implementerad!

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

## 🎨 Nytt GitHub-inspirerat tema!

Insights har nu ett helt nytt, modernt gränssnitt inspirerat av GitHub.com:
- **Mörkt och ljust tema** med smidig växling
- **Sidofältsnavigering** för enklare åtkomst
- **Professionell design** med GitHubs färgschema och typografi
- **Responsiv layout** som fungerar på alla enheter

Se [THEME_GUIDE.md](THEME_GUIDE.md) för mer information om det nya temat.

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

4. **Byt tema:** Klicka på knappen i övre högra hörnet (🌙/☀️) för att växla mellan mörkt och ljust tema

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
- **Automatisk detektering av internöverföringar** mellan konton
  - Transaktioner markeras med "Flytt mellan konton (Konto A → Konto B)"
  - Överföringar exkluderas automatiskt från prognoser och kassaflödesberäkningar
  - Påverkar inte utgifts- eller inkomststatistik

### 4. Fakturor
- Aktiva och hanterade fakturor
- Automatisk matchning mot transaktioner
- PDF-import med faktisk PDF-parsing (pdfplumber)
- Schemaläggning av betalningar
- Prognosintegration och historik

### 5. Kreditkort
- **NYtt: Kreditkortshantering** med generellt stöd för alla korttyper (Amex, Visa, Mastercard, etc)
  - Lägg till kreditkortskonton med namn, typ, kreditgräns, färg och ikon
  - **Redigera och ta bort kreditkort** via dashboard (namn, typ, kreditgräns, färg, ikon)
  - CSV-import av transaktioner från kontoutdrag (generiskt format med Date, Description, Amount)
  - **Excel-import** (.xlsx) - Automatisk konvertering av Excel-filer till CSV-format
  - **Stöd för svensk Mastercard CSV** med två format:
    - **Format 1 (Aktuell export)**: Datum, Specifikation, Ort, Belopp (YYYY-MM-DD, decimal punkt)
    - **Format 2 (Generisk)**: Datum, Beskrivning, Belopp (MM/DD/YYYY, komma decimal)
  - Automatisk kategorisering av kreditkortstransaktioner
  - **Redigera kategori och underkategori** för varje kreditkortstransaktion
  - Visa aktuellt saldo, tillgänglig kredit och utnyttjandegrad per kort
  - **Kategorifördelning per kort** med detaljerad utgiftsuppdelning
  - Transaktionshistorik med filtrering
  - AI-träning på kreditkortstransaktioner (via manuell kategorisering)
  - **Automatisk betalningsmatching** mot bankkonto (uppdaterar kortsaldo automatiskt)
  - **Detekterar svensk BG-betalning** (t.ex. "Betalning BG 595-4300 SEB KORT BANK")
  - **Visuell markering av kreditkortsbetalningar** (t.ex. "Inbetalning till kreditkort Mastercard")
  - **Stilfulla kortikoner** för Amex, Visa, Mastercard med varumärkesspecifik design

### 6. Historik
- Månadssammanställningar med inkomster/utgifter/netto
- Kategoritrender över tid (6 månader)
- Topptransaktioner och största utgifter
- Saldohistorik per konto

### 7. Lån
- Lägg till lån med ränta och bindningstid
- Visualisera återbetalning och saldo
- Simulera ränteförändringar och bindningstidens slut
- Månadsvis amorteringsplan

### 8. Frågebaserad analys med AI
- Naturligt språkgränssnitt för ekonomifrågor
- "Vad händer om räntan ökar med 2%?"
- "Hur mycket saldo har jag?"
- "Visa alla fakturor"
- "Största utgifter denna månad"
- Automatisk routing till rätt modul

### 9. Inkomsthantering
- Registrera inkomster per person
- Spåra inkomster per konto
- Månadssammanställningar
- Prognoser baserat på historik

### 10. Personer (NYtt i denna version!)
- Hantera familjemedlemmar
- Registrera återkommande inkomster per person
- Betalningsdag och förväntade utbetalningar
- Inkomsthistorik visualisering
- Per-person utgiftsanalys per kategori
- Använder kreditkortsallokeringar för att dela upp utgifter mellan personer

### 11. Inställningar
- Konfigurera valuta och decimaler
- Anpassa visningsinställningar
- Aktivera/inaktivera notifieringar
- Justera gränsvärden och trösklar

### 12. Admin Dashboard (NYtt i denna version!)
- **NYtt: Admin Dashboard** för effektiv AI-träning och kategorisering
  - **Kraftfull filtrering**: Filtrera transaktioner på källa, datum, belopp, kategori, konto och okategoriserad status
  - **Transaktionslista**: Interaktiv tabell med sortering, paginering och visuell markering av okategoriserade
  - **Bulk-operationer**: Uppdatera kategori och träna AI för flera transaktioner samtidigt
  - **Kategorihantering**: 
    - Skapa nya kategorier med underkategorier
    - Slå ihop kategorier för att konsolidera data
    - Ta bort kategorier och flytta transaktioner
  - **Detaljerad statistik**:
    - Kategorifördelning (antal och belopp)
    - Okategoriserade transaktioner (antal och procent)
    - AI-träningsframsteg (totalt, manuella prover, nya prover senaste 7 dagarna)
    - Kategoriseringsregler (totalt och AI-genererade)
  - **Stöd för alla CSV-format**: Nordea, American Express, Mastercard
  - **Real-time uppdateringar**: Statistik uppdateras automatiskt var 10:e sekund
  - **Användarvänligt gränssnitt**: Tydliga instruktioner, färgkodning och direktfeedback
  - Se [ADMIN_DASHBOARD_GUIDE.md](ADMIN_DASHBOARD_GUIDE.md) för komplett användarguide

## 🔄 Senaste förbättringar (Denna version)

### Admin Dashboard
- Komplett admin-gränssnitt för AI-träning och kategorisering
- Kraftfulla filtreringsmöjligheter för att hitta rätt transaktioner
- Bulk-operationer för effektiv hantering av stora datamängder
- Kategorihantering direkt i dashboarden (skapa, slå ihop, ta bort)
- Detaljerad statistik för att följa AI-träningsframsteg
- Responsiv design med GitHub-inspirerat tema
- 20 nya tester för admin-funktionalitet (56 totalt godkända)
- Säkerhetsgodkänd med CodeQL
- Omfattande dokumentation

### Interna överföringar
- Automatisk detektering och filtrering av överföringar mellan egna konton
- Exkluderas från utgiftsstatistik och prognoser
- Visas inte i "Största utgifter" eller "Topputgifter"
- Korrekt beräkning av månadsutgifter

### Historik
- Månadsvalet i Historik är nu persistent (sparas i sessionen)
- Interna överföringar exkluderas från "Största utgifter"

### Ekonomisk översikt
- Saldo & prognos-grafen visar nu tre linjer:
  - Förväntat saldo (blå)
  - Kumulativa inkomster (grön, streckad)
  - Kumulativa utgifter (röd, streckad)
- Topputgifter exkluderar interna överföringar

### Lånehantering
- Löptid (månader) är nu valfritt/dynamiskt
- Kan lämnas tomt för lån utan fast löptid

### Personer-panel
- Ny flik för att hantera familjemedlemmar
- Registrera personer med månadsinkomst och betalningsdag
- Visualisera inkomsthistorik per person
- Se utgifter per kategori för varje person baserat på kreditkortsanvändning
- Stöd för framtida förväntade utbetalningar per månad

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

### 7. Frågebaserad analys med AI (Sprint 5)

**Via Dashboard:**
1. Gå till fliken "Frågebaserad analys"
2. Skriv din fråga i naturligt språk, t.ex.:
   - "Hur mycket saldo har jag?"
   - "Visa alla fakturor"
   - "Simulera ränta 4.5%"
   - "Största utgifter denna månad"
3. Klicka "Skicka fråga"
4. Agenten analyserar din fråga och genererar ett svar

**Via Python:**
```python
from modules.core.agent_interface import AgentInterface

agent = AgentInterface()
response = agent.process_query("Hur mycket har jag kvar i november?")
print(response)
```

### 8. Visa historik och trender (Sprint 5)

**Via Dashboard:**
1. Gå till fliken "Historik"
2. Välj månad från dropdown
3. Se månadssammanfattning med inkomster, utgifter och netto
4. Välj kategori för att se trend över 6 månader
5. Bläddra i största utgifter för vald månad

**Via Python:**
```python
from modules.core.history_viewer import HistoryViewer

viewer = HistoryViewer()

# Månadssammanfattning
summary = viewer.get_monthly_summary('2025-01')
print(f"Inkomster: {summary['income']} SEK")
print(f"Utgifter: {summary['expenses']} SEK")
print(f"Netto: {summary['net']} SEK")

# Kategoritrend
trend = viewer.get_category_trend('Mat & Dryck', months=6)
for month_data in trend:
    print(f"{month_data['month']}: {month_data['amount']} SEK")

# Största utgifter
top = viewer.get_top_expenses('2025-01', top_n=10)
for tx in top:
    print(f"{tx['description']}: {abs(tx['amount'])} SEK")
```

### 9. Hantera inkomster (Sprint 5)

**Via Dashboard:**
1. Gå till fliken "Inmatning"
2. Scrolla ner till "Lägg till inkomst"
3. Fyll i person, konto, belopp, datum och beskrivning
4. Klicka "Lägg till inkomst"

**Via Python:**
```python
from modules.core.income_tracker import IncomeTracker

tracker = IncomeTracker()

# Lägg till inkomst
tracker.add_income(
    person='Robin',
    account='PERSONKONTO 880104-7591',
    amount=30000.0,
    date='2025-01-25',
    description='Monthly salary',
    category='Lön'
)

# Hämta månadsink omst
monthly = tracker.get_monthly_income('2025-01')
print(f"Total inkomst: {monthly} SEK")

# Prognos
forecast = tracker.forecast_income(months=3)
for pred in forecast:
    print(f"{pred['month']}: {pred['predicted_amount']} SEK")
```

### 10. Hantera fakturor och lån (via Dashboard eller Python - Sprint 4)

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

### 11. Hantera kreditkort (Sprint 7)

**Via Dashboard:**
1. Gå till fliken "Kreditkort"
2. Fyll i kortdetaljer (namn, typ, sista 4 siffror, kreditgräns, färg)
3. Klicka "Lägg till kort"
4. Klicka på redigera-knappen (✏️) på ett kort för att redigera detaljer
5. Importera transaktioner från CSV
6. Klicka på en transaktion för att redigera kategori
7. Klicka "Träna AI" för att lära systemet från din kategorisering

**Automatisk detektering av kreditkortsbetalningar:**
Systemet detekterar automatiskt betalningar till kreditkort och markerar dem:
- "Amex Payment" → "Inbetalning till kreditkort Amex Platinum"
- Kortsaldon uppdateras automatiskt när betalningar registreras

**Via Python:**
```python
from modules.core.credit_card_manager import CreditCardManager

manager = CreditCardManager()

# Lägg till kort
card = manager.add_card(
    name="Amex Platinum",
    card_type="American Express",
    last_four="1234",
    credit_limit=50000.0,
    display_color="#006FCF"
)

# Importera transaktioner
count = manager.import_transactions_from_csv(card['id'], 'statement.csv')

# Uppdatera transaktion
manager.update_transaction(
    card_id=card['id'],
    transaction_id='TX-123',
    category='Mat & Dryck',
    subcategory='Restaurang'
)

# Ta bort kort
manager.delete_card(card['id'])
```

### 12. Internöverföringar och kassaflöde (Sprint 7)

**Automatisk detektering:**
Systemet detekterar automatiskt överföringar mellan konton:
- Matchar transaktioner med samma belopp och datum (±2 dagar)
- Markerar båda sidor med "Flytt mellan konton (Konto A → Konto B)"
- Exkluderar från prognoser och utgiftsstatistik

**Via Python:**
```python
from modules.core.account_manager import AccountManager

manager = AccountManager()

# Detektera internöverföringar
count = manager.detect_internal_transfers()
print(f"{count} överföringspar detekterade")

# Detektera kreditkortsbetalningar
cc_count = manager.detect_credit_card_payments()
print(f"{cc_count} kreditkortsbetalningar detekterade")
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
- [x] Sprint 4: Fakturor och lånhantering
  - [x] Fakturahantering (lägg till, visa, redigera, ta bort)
  - [x] PDF-fakturaimport (placeholder-implementation)
  - [x] Automatisk fakturamatchning mot transaktioner
  - [x] Schemaläggning av betalningar
  - [x] Lånehantering (lägg till, visa, redigera)
  - [x] Återbetalningsvisualisering
  - [x] Ränteförändringssimuleringar
  - [x] Tester för faktura- och lånehantering
- [x] Sprint 5: Avancerad analys, historik och AI
  - [x] Agentdriven analys med naturligt språk (agent_interface)
  - [x] Historik och statistik (history_viewer)
  - [x] Kontohantering med redigering
  - [x] Inkomsthantering (income_tracker)
  - [x] Förbättrad PDF-fakturaimport med pdfplumber
  - [x] AI-träning från manuell kategorisering
  - [x] Settings panel med konfigurerbara inställningar
  - [x] Dashboard-integration av alla nya funktioner
  - [x] Omfattande tester (142 passing tests)
- [x] Sprint 6: Data-flow och dashboard-förbättringar
  - [x] Transaktionsstatus-system (scheduled/posted/paid)
  - [x] Metadata för transaktioner och fakturor
  - [x] CSV-import med automatisk statuslogik
  - [x] Förbättrad PDF-fakturaimport med kontonummer
  - [x] Kontonummer-baserad fakturamatchning
  - [x] Dashboard real-time uppdateringar
  - [x] Månadanalys med scheduled/posted separation
  - [x] Editerbara fakturor med AI-träning
  - [x] Omfattande tester (187 passing tests)

## 📝 YAML Datamodell och Metadata

### Transaction Metadata (Sprint 6)

Transaktioner innehåller nu följande metadata-fält:

```yaml
transactions:
  - id: "unique-uuid"
    account: "PERSONKONTO 880104-7591"
    date: "2025-10-25"
    amount: -1250.50
    description: "ICA Kvantum"
    category: "Mat & Dryck"
    subcategory: "Matvaror"
    
    # Nya metadata-fält (Sprint 6)
    status: "posted"                    # 'scheduled', 'posted', eller 'paid'
    source: "import.csv"                # Källfil eller 'manual'
    source_uploaded_at: "2025-10-22 14:30:00"
    is_bill: false                      # true för fakturor, false för banktransaktioner
    bill_due_date: null                 # Förfallodatum (om is_bill=true)
    account_number: "1234 56 78901"    # Normaliserat kontonummer
    matched_to_bill_id: null           # ID för matchad faktura (om matchning gjorts)
    imported_historical: true           # true för historisk bankdata
```

### Bill Metadata (Sprint 6)

Fakturor innehåller nu utökade metadata-fält:

```yaml
bills:
  - id: "BILL-0001"
    name: "Elräkning December"
    amount: 850.0
    due_date: "2025-11-15"
    bill_due_date: "2025-11-15"        # Explicit förfallodatum
    description: "Elkostnad för december"
    category: "Boende"
    subcategory: "El"
    
    # Nya metadata-fält (Sprint 6)
    status: "scheduled"                 # 'scheduled', 'pending', 'paid', eller 'overdue'
    is_bill: true                       # Alltid true för fakturor
    source: "PDF"                       # 'PDF', 'manual', eller annat
    source_uploaded_at: "2025-10-22 13:24:37"
    account: "MAT 1722 20 34439"       # Normaliserat kontonummer
    account_number: "MAT 1722 20 34439"
    matched_transaction_id: null        # ID för matchad transaktion
    matched_to_bill_id: null           # För reverse matching
    paid_at: null
    scheduled_payment_date: null
    imported_historical: false          # Fakturor är framtida poster
    created_at: "2025-10-22 13:24:37"
```

### Import-optioner

**CSV-import med statuslogik:**

```python
from modules.core.import_bank_data import import_csv

# Markera framtida transaktioner som 'scheduled' (standard)
account_name, df = import_csv('transactions.csv', treat_future_as_scheduled=True)

# Markera alla transaktioner som 'posted', även framtida
account_name, df = import_csv('transactions.csv', treat_future_as_scheduled=False)
```

**PDF-fakturaimport:**

PDF-import extraherar automatiskt:
- Kontonummer (normaliserat)
- Fakturabelopp
- Förfallodatum
- Mottagare/fakturerare
- Sätter `is_bill=true`, `status='scheduled'`, `source='PDF'`

### Fakturamatchning

Systemet matchar automatiskt fakturor mot transaktioner baserat på:

1. **Kontonummer** (normaliserat, viktad 0.4 i confidence score)
2. **Belopp** (tolerance 5%, viktad 0.3-0.5)
3. **Datum** (tolerance ±7 dagar från förfallodatum)
4. **Beskrivning** (textsökning, viktad 0.1-0.3)

```python
from modules.core.bill_matcher import BillMatcher

matcher = BillMatcher(bill_manager, account_manager)

# Matcha alla fakturor automatiskt
matches = matcher.match_bills_to_transactions(
    tolerance_days=7,           # Sök ±7 dagar från förfallodatum
    amount_tolerance_percent=5.0  # 5% tolerance i belopp
)

# Manuell matchning
matcher.manual_match(bill_id="BILL-0001", transaction_id="TX-123")
```

### Migration Guide för befintliga YAML-filer

Om du har befintliga `transactions.yaml` eller `bills.yaml` filer:

1. **Transaktioner**: Lägg till följande fält för varje transaktion:
   ```yaml
   status: "posted"
   source: "legacy"
   source_uploaded_at: "2025-10-22 00:00:00"
   is_bill: false
   bill_due_date: null
   account_number: null
   matched_to_bill_id: null
   imported_historical: true
   ```

2. **Fakturor**: Lägg till följande fält för varje faktura:
   ```yaml
   status: "scheduled"  # eller "pending", "paid"
   is_bill: true
   source: "manual"
   source_uploaded_at: "2025-10-22 00:00:00"
   bill_due_date: "2025-11-15"  # Samma som due_date
   account_number: null  # eller kontonummer om känt
   matched_to_bill_id: null
   imported_historical: false
   ```

3. Gamla fält behålls för bakåtkompatibilitet
4. Nya importer lägger automatiskt till alla fält

### Dashboard-funktioner (Sprint 6)

**Editerbara fakturor:**
1. Gå till "Fakturor"-fliken
2. Klicka på en faktura i tabellen för att välja den
3. Modal-fönster öppnas med editerbara fält:
   - Namn, belopp, förfallodatum
   - Kategori och underkategori (dropdowns)
   - Konto (dropdown)
   - Status (dropdown: Schemalagd, Väntande, Betald, Förfallen)
4. Använd knapparna:
   - **Spara**: Spara ändringar
   - **Markera som betald**: Sätt status till 'paid'
   - **Träna AI**: Lägg till i training_data.yaml för AI-träning

**Månadanalys:**
1. Gå till "Månadsanalys"-fliken
2. Välj månad med dropdown
3. Visa:
   - **Kommande fakturor** (status='scheduled')
   - **Bokförda transaktioner** (status='posted')
   - **Inkomster per person och konto**
   - **Utgiftssummering per kategori**
   - **Överföringsförslag** baserat på NetBalanceSplitter

## 🤝 Bidra

Läs [CONTRIBUTING.md](docs/CONTRIBUTING.md) för mer information om hur du kan bidra till projektet.

## 📄 Licens

Detta projekt är licensierat under MIT-licensen.
