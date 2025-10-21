📊 Insights – Agentdriven hushållsekonomi med AI, YAML och Dash
Insights är ett transparent, modulärt och agentförberett system för hushållsekonomi. Det kombinerar regelbaserad och AI-driven transaktionsklassificering, prognoser, frågebaserad analys och full kontroll över konton, fakturor, inkomster och lån – allt styrt via YAML och ett interaktivt Dash-gränssnitt.

🚀 Funktioner
1. Ekonomisk översikt
- Prognos 30 dagar framåt
- Utgiftsfördelning per kategori
- Agentgenererade insikter och varningar
2. Inmatning
- Importera Nordea CSV-filer
- Lägg till fakturor och inkomster manuellt
- Läs in fakturor från PDF (enskilda eller sammanställningar)
- Automatisk transaktionsklassificering (regelbaserad + AI-hybrid)
3. Konton
- Skapa och hantera konton från CSV
- Visa kontoutdrag (50 transaktioner per sida)
- Manuell kategorisering med huvud- och underkategori
- Träna AI-modellen direkt från kontoutdraget
4. Fakturor
- Aktiva och hanterade fakturor
- Automatisk matchning mot transaktioner
- Prognosintegration och historik
5. Historik
- Månadssammanställningar
- Kategoritrender över tid
- Topptransaktioner och saldohistorik
6. Lån
- Lägg till lån med ränta och bindningstid
- Visualisera återbetalning och saldo
- Simulera ränteförändringar och bindningstidens slut
7. Frågebaserad analys
- “Vad händer om räntan ökar med 2%?”
- “Hur mycket har vi kvar i november?”
- “Visa alla fakturor i oktober”

🧱 Teknisk arkitektur
- 📁 YAML-baserad datalagring
- 🧠 Agentgränssnitt för simulering och analys
- 📊 Dash-gränssnitt för interaktiv visualisering
- 🧪 Enhetstester och CI-integration
- 🔁 Modulär struktur för framtida expansion

🛠️ Installation
git clone https://github.com/dittnamn/insights.git
cd insights
pip install -r requirements.txt
python dashboard_ui.py


Kräver Python 3.10+ och Dash


Projektstruktur
bash
insights/
├── modules/
│   ├── import_bank_data.py
│   ├── categorize_expenses.py
│   ├── parse_pdf_bills.py
│   ├── forecast_engine.py
│   └── ...
├── yaml/
│   ├── transactions.yaml
│   ├── upcoming_bills.yaml
│   ├── loans.yaml
│   └── ...
├── dashboard_ui.py
├── settings_panel.yaml
├── README.md
└── requirements.txt


🧠 Vision
Insights är byggt för att vara:
- 🧩 Modulärt och transparent
- 🧠 Agentförberett och självlärande
- 🧪 Testbart och framtidssäkert
- 👥 Användarcentrerat och pedagogiskt

Vill du att jag nu genererar requirements.txt, index.yaml eller README_sprints.md för sprintstruktur och testmappning? Jag kan också hjälpa dig skapa en onboarding-guide för nya utvecklare.

