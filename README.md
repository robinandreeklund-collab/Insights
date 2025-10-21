# 📊 Insights – Agentdriven hushållsekonomi med AI, YAML och Dash

Insights är ett transparent, modulärt och agentförberett system för hushållsekonomi. Det kombinerar regelbaserad och AI-driven transaktionsklassificering, prognoser, frågebaserad analys och full kontroll över konton, fakturor, inkomster och lån – allt styrt via YAML och ett interaktivt Dash-gränssnitt.

## 🎯 Projektstatus: Sprint 1

**Sprint 1 Status:** Grundläggande struktur och dashboard är på plats.

I Sprint 1 har vi satt upp:
- ✅ Mappstruktur enligt `project_structure.yaml`
- ✅ Grundmoduler i `modules/core/` (stubs utan faktisk logik)
- ✅ Tomma YAML-datafiler för framtida användning
- ✅ Dashboard med alla paneler/tabbar
- ✅ Grundläggande enhetstester
- ✅ Requirements och installation

**OBS:** Endast strukturen och gränssnittet är implementerat i Sprint 1. Ingen faktisk logik för import, kategorisering eller prognoser finns ännu.

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
- Prognosintegration och historik

### 5. Historik
- Månadssammanställningar
- Kategoritrender över tid
- Topptransaktioner och saldohistorik

### 6. Lån
- Lägg till lån med ränta och bindningstid
- Visualisera återbetalning och saldo
- Simulera ränteförändringar och bindningstidens slut

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

3. Starta dashboard:
```bash
python dashboard/dashboard_ui.py
```

4. Öppna din webbläsare på: [http://127.0.0.1:8050](http://127.0.0.1:8050)

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

## 🔄 Exempel på flöde (planerat för framtida sprints)

### 1. Importera CSV
1. Gå till fliken "Inmatning"
2. Ladda upp din CSV-fil från banken
3. Systemet normaliserar och sparar transaktionerna i `yaml/transactions.yaml`

### 2. Kategorisera transaktioner
1. Gå till fliken "Konton"
2. Välj konto och visa transaktioner
3. Kategorisera manuellt eller låt AI-modellen göra det automatiskt
4. Träna AI-modellen från manuella kategoriseringar

### 3. Visa översikt
1. Gå till fliken "Ekonomisk översikt"
2. Se prognos för kommande 30 dagar
3. Visa utgiftsfördelning per kategori
4. Läs agentgenererade insikter och varningar

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
- [ ] Sprint 2: Import och kategorisering av transaktioner
- [ ] Sprint 3: Prognoser och insikter
- [ ] Sprint 4: Fakturor och lånhantering
- [ ] Sprint 5: Agentdriven analys och simulering

## 🤝 Bidra

Läs [CONTRIBUTING.md](docs/CONTRIBUTING.md) för mer information om hur du kan bidra till projektet.

## 📄 Licens

Detta projekt är licensierat under MIT-licensen.
