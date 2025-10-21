📊 Insights – Agentdriven hushållsekonomi med AI, YAML och Dash
🧱 Projektstruktur
🔹 Namn: Insights
🔹 Syfte:
Ett transparent, modulärt och agentförberett system för hushållsekonomi. Kombinerar regelbaserad och AI-driven transaktionsklassificering, prognoser, frågebaserad analys och full kontroll över konton, fakturor, inkomster och lån.

🧩 Moduler
Modul	Funktion
import_bank_data	Läser in bankfiler (CSV, Excel)
parse_transactions	Extraherar och strukturerar transaktioner
categorize_expenses	Hybridklassificering (regler + AI)
parse_pdf_bills	Extraherar fakturor från PDF
upcoming_bills	Hanterar kommande fakturor
income_tracker	Registrerar inkomster
net_balance_splitter	Fördelar kvarvarande pengar
forecast_engine	Simulerar framtida saldo
alerts_and_insights	Genererar varningar och insikter
dashboard_ui	Dash-gränssnitt för visualisering och interaktion
settings_panel	Hanterar användarinställningar
account_manager	Skapar och hanterar konton
bill_matcher	Matchar fakturor mot transaktioner
agent_interface	Tolkar frågor och genererar insikter
loan_manager	Hanterar lån, ränta, bindningstid
loan_simulator	Simulerar ränteförändringar och bindningstidens slut
history_viewer	Visar historisk utgiftsdata och insikter
📁 YAML-lagring
accounts.yaml – konton, saldo, transaktioner

transactions.yaml – transaktionsdata med kategori, AI-confidence

upcoming_bills.yaml – aktiva och hanterade fakturor

income_tracker.yaml – inkomster per person

categorization_rules.yaml – regelbas för kategorisering

training_data.yaml – AI-träningsdata

insights.yaml – agentgenererade insikter

agent_queries.yaml – frågelogg

loans.yaml – låneinformation, ränta, bindningstid

loan_simulation.yaml – simuleringar och antaganden

history.yaml – månadssammanställningar och trender

settings_panel.yaml – UI-inställningar och toggles

📊 Dash-paneler
Ekonomisk översikt

Prognos (30 dagar)

Utgiftsfördelning

Insikter och varningar

Inmatning

Importera Nordea CSV

Lägg till faktura manuellt

Lägg till inkomst

Läs in fakturor från PDF

Konton

Skapa och hantera konton

Visa kontoutdrag (50 per sida)

Manuell kategorisering + AI-träning

Fakturor

Aktiva fakturor

Hanterade fakturor

Automatisk matchning

Historik

Månadssammanställningar

Kategoritrender

Topptransaktioner

Lån

Lägg till lån (namn, ränta, bindningstid)

Visualisera utveckling

Simulera ränteförändringar

Frågebaserad analys

Agentfrågor: “Vad händer om…?”

Svar + insiktslogg

Scenarioanalys

🧠 Agentfunktioner
Frågetolkning: “Visa alla fakturor i oktober”

Insiktsgenerering: “Matkostnader överstiger 4000 kr”

Simulering: “Vad händer om räntan ökar med 2%?”

Rekommendationer: “Minska streamingkostnader med 20%”

🧪 Teststruktur
Enhetstester per modul

YAML-validering

Edge case-simulering

CI-integration (GitHub Actions)
