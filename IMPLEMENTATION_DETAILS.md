# Implementering av förbättrad faktura- och översiktshantering

Denna implementation täcker sex huvudsakliga förbättringsområden för Insights-systemet:

## 1. Kontonummer-matchning för fakturor

### Problem
Tidigare matchades fakturor endast via exakt kontonamn, vilket gjorde det svårt att matcha fakturor från PDF:er där kontonamnet kan vara "MAT 1722 20 34439" mot ett konto i systemet som heter exakt "MAT 1722 20 34439".

### Lösning
- **Ny funktion**: `extract_account_number()` i `account_manager.py`
  - Extraherar kontonummer från fullständiga kontonamn
  - Stöder mönstret: 4 siffror + 2 siffror + 5 siffror (t.ex. "1722 20 34439")
  
- **Ny funktion**: `get_account_by_number()` i `AccountManager`
  - Hittar konton via kontonummer oavsett prefix
  - Normaliserar och jämför kontonummer utan mellanslag

- **Uppdaterad funktion**: `normalize_account_number()` i `bill_manager.py`
  - Normaliserar kontonummer när fakturor skapas
  - Används automatiskt i `BillManager.add_bill()`

### Exempel
```python
# Konto i systemet: "MAT 1722 20 34439"
# PDF-faktura anger: "1722 20 34439" eller "MAT 1722 20 34439"

manager = AccountManager()
account = manager.get_account_by_number("1722 20 34439")
# Hittar kontot "MAT 1722 20 34439"
```

## 2. Real-time uppdateringar av ekonomisk översikt

### Lösning
- **Interval-baserad uppdatering**: Alla översiktssektioner uppdateras automatiskt via Dash intervals
  - `overview-interval`: 5000ms (5 sekunder)
  - `monthly-analysis-interval`: 10000ms (10 sekunder)
  - `bills-interval`: 5000ms (5 sekunder)

- **Callback-triggers**: Callbacks triggas när:
  - Nya fakturor läggs till
  - PDF importeras
  - Inkomster registreras
  - Fakturor matchas

### Komponenter som uppdateras automatiskt
- Totalt saldo
- Saldo per konto
- Kommande utgifter
- Inkomster per person
- Topputgifter
- Varningar och insikter
- Prognos och kategorifördelning

## 3. Utökad ekonomisk översikt

### Nya sektioner i översikten

#### 3.1 Snabböversikt
- Totalt saldo över alla konton
- Antal konton i systemet

#### 3.2 Saldo per konto
- Lista alla konton med aktuellt saldo
- Visar person/ägare för varje konto

#### 3.3 Kommande utgifter (30 dagar)
- Visar alla väntande fakturor inom 30 dagar
- Total summa av kommande utgifter
- Lista med namn, belopp och förfallodatum

#### 3.4 Inkomster per person (denna månad)
- Grupperar inkomster per person
- Visar total inkomst för varje person

#### 3.5 Topputgifter (senaste 30 dagarna)
- De 5 största utgifterna
- Sorterade efter belopp

#### 3.6 Varningar och insikter
- **Förfallna fakturor**: Röd varning om det finns förfallna fakturor
- **Lågt saldo**: Gul varning om totalt saldo < 1000 SEK
- **Kommande fakturor**: Blå information om fakturor inom 7 dagar

## 4. Redigerbara fakturor

### UI-komponenter
- **Edit Bill Modal**: Modal-dialog för att redigera fakturor
  - Namn, belopp, förfallodatum
  - Kategori och underkategori
  - Konto och beskrivning

### Funktionalitet
1. **Öppna redigering**: Klicka på faktura i tabellen
2. **Visa data**: Modalen fylls i automatiskt med fakturans data
3. **Redigera**: Ändra fält efter behov
4. **Spara**: Uppdaterar fakturan i databasen

### Callbacks
- `toggle_edit_bill_modal()`: Öppnar/stänger modal och fyller i data
- `save_edited_bill()`: Sparar ändringar till fakturan
- `update_edit_bill_subcategory_options()`: Uppdaterar underkategorier baserat på vald kategori
- `update_edit_bill_account_options()`: Uppdaterar tillgängliga konton

## 5. Underkategori-stöd för fakturor

### Datamodell
```yaml
bill:
  id: BILL-0001
  name: Elräkning December
  category: Boende
  subcategory: Elektricitet  # Nytt fält
  amount: 850.0
  # ... övriga fält
```

### UI-komponenter
- **Subcategory dropdown vid skapande**: Välj underkategori när du lägger till faktura
- **Subcategory dropdown vid redigering**: Redigera underkategori för befintlig faktura
- **Dynamisk uppdatering**: Underkategorier uppdateras baserat på vald huvudkategori

### Callbacks
- `update_bill_subcategory_options()`: Uppdaterar underkategorier när kategori ändras
- Integrerat i `add_bill()` och `save_edited_bill()`

## 6. Månadsanalys-panel

### Översikt
Ny tab "Månadsanalys" som ger en heltäckande bild av månadens ekonomi.

### Funktioner

#### 6.1 Periodväljare
- Välj start- och slutmånad
- Analysera en specifik period
- Standardvärde: Aktuell månad

#### 6.2 Kommande fakturor denna månad
- Tabell med alla väntande fakturor
- Namn, belopp, förfallodatum, kategori
- Total summa för månaden

#### 6.3 Inkomster per person och konto
- Grupperat per person
- Visar alla konton och deras inkomster
- Total inkomst per person

#### 6.4 Utgiftssummering
- Grupperat per kategori
- Visar belopp och procentandel
- Total utgift för perioden

#### 6.5 Överföringsrekommendationer
Använder `net_balance_splitter` för att beräkna rättvisa överföringar.

**Input:**
- Inkomster per person och konto
- Utgifter per kategori
- Lista med gemensamma kategorier (t.ex. "Boende", "Mat & Dryck")

**Output:**
- Total gemensam utgift
- Fördelning per person baserat på inkomst
- Rekommenderat belopp att överföra till gemensamt konto

**Exempel:**
```
Robin (inkomst 30,000 SEK):
  Andel av utgifter: 60%
  Ska överföra: 7,200 SEK

Partner (inkomst 20,000 SEK):
  Andel av utgifter: 40%
  Ska överföra: 4,800 SEK

Totala gemensamma utgifter: 12,000 SEK
```

### Net Balance Splitter-modul

#### Klasser och funktioner
- **NetBalanceSplitter**: Huvudklass för beräkningar
  - `calculate_shared_expenses()`: Beräknar varje persons andel
  - `calculate_transfer_recommendations()`: Ger överföringsförslag
  - `split_balance_after_expenses()`: Beräknar vem som ska få tillbaka pengar

#### Beräkningslogik
1. **Inkomstbaserad fördelning** (default):
   - Andel = Person inkomst / Total inkomst
   - Används om ingen anpassad fördelning anges

2. **Anpassad fördelning** (optional):
   - Kan ange specifika fördelningsandelar
   - T.ex. 50/50 oavsett inkomst

#### API
```python
from modules.core.net_balance_splitter import calculate_transfer_recommendations

recommendations = calculate_transfer_recommendations(
    income_by_person_and_account={
        'Robin': {'1722 20 34439': 30000.0},
        'Partner': {'1709 20 72840': 20000.0}
    },
    expenses_by_category={
        'Boende': 8000.0,
        'Mat & Dryck': 4000.0,
        'Transport': 3000.0
    },
    shared_categories=['Boende', 'Mat & Dryck'],
    custom_ratios=None  # Optional: {'Robin': 0.5, 'Partner': 0.5}
)
```

## Tester

### Nya tester
- `test_net_balance_splitter.py`: 7 tester för net_balance_splitter-modulen
  - Grundläggande beräkningar
  - Anpassade fördelningar
  - Edge cases (ingen inkomst)
  - Wrapper-funktioner

### Testresultat
- **Totalt antal tester**: 187 (180 befintliga + 7 nya)
- **Status**: Alla tester passerar
- **Coverage**: Fullständig täckning av nya moduler

## Användargränssnitt

### Ekonomisk översikt
```
┌─────────────────────────────────────────┐
│ Ekonomisk översikt                      │
├─────────────────────────────────────────┤
│ ┌─────────────┐  ┌─────────────────┐   │
│ │ Saldo och   │  │ Snabböversikt   │   │
│ │ prognos     │  │ - Totalt: X SEK │   │
│ │ [Graf]      │  │ - Konton: Y st  │   │
│ └─────────────┘  └─────────────────┘   │
│                                          │
│ ┌──────────────┐  ┌──────────────────┐ │
│ │ Saldo per    │  │ Kommande        │ │
│ │ konto        │  │ utgifter        │ │
│ │ - Konto1: X  │  │ - Faktura1: X   │ │
│ │ - Konto2: Y  │  │ - Faktura2: Y   │ │
│ └──────────────┘  └──────────────────┘ │
│                                          │
│ ┌──────────────┐  ┌──────────────────┐ │
│ │ Inkomster    │  │ Topputgifter    │ │
│ │ per person   │  │ - Utgift1: X    │ │
│ │ - Robin: X   │  │ - Utgift2: Y    │ │
│ └──────────────┘  └──────────────────┘ │
│                                          │
│ ┌──────────────┐  ┌──────────────────┐ │
│ │ Utgifts-     │  │ Varningar och   │ │
│ │ fördelning   │  │ insikter        │ │
│ │ [Cirkeldiag] │  │ ⚠ Förfallna     │ │
│ └──────────────┘  └──────────────────┘ │
└─────────────────────────────────────────┘
```

### Månadsanalys
```
┌─────────────────────────────────────────┐
│ Månadsanalys                            │
├─────────────────────────────────────────┤
│ Välj period:                            │
│ [Startmånad ▼] [Slutmånad ▼] [Analysera]│
│                                          │
│ Kommande fakturor denna månad:          │
│ ┌──────────────────────────────────┐   │
│ │ Faktura | Belopp | Datum | Kat   │   │
│ │ El      | 850 SEK| 12-31 | Boende│   │
│ └──────────────────────────────────┘   │
│                                          │
│ ┌──────────────┐  ┌──────────────────┐ │
│ │ Inkomster    │  │ Utgiftssummering│ │
│ │ per person   │  │ Boende: X SEK   │ │
│ │ Robin: X SEK │  │ Mat: Y SEK      │ │
│ └──────────────┘  └──────────────────┘ │
│                                          │
│ Överföringsförslag:                     │
│ Gemensamma kategorier: [Boende ▼]      │
│ [Beräkna överföringar]                  │
│                                          │
│ ┌─────────────────────────────────┐    │
│ │ Robin:                          │    │
│ │ Total inkomst: 30,000 SEK       │    │
│ │ Andel av utgifter: 60%          │    │
│ │ ─────────────────────────────── │    │
│ │ Ska överföra: 7,200 SEK        │    │
│ └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

### Fakturahantering med redigering
```
┌─────────────────────────────────────────┐
│ Fakturahantering                        │
├─────────────────────────────────────────┤
│ Lägg till faktura:                      │
│ Namn: [______] Belopp: [______]        │
│ Datum: [______] Kategori: [____▼]      │
│ Underkategori: [_______▼] <-- NYT!     │
│ Konto: [_______▼] Beskr: [______]      │
│ [Lägg till faktura] [Matcha fakturor]  │
│                                          │
│ Fakturor per konto:                     │
│ ┌─────────────────────────────────┐    │
│ │ Konto: MAT 1722 20 34439        │    │
│ │ Antal: 10 st | Väntande: 8 st   │    │
│ │ Total: 15,000 SEK                │    │
│ │                                  │    │
│ │ Fakturor:                        │    │
│ │ - El: 850 SEK (12-31) [Redigera]│<-- NYT!
│ │ - Mobil: 299 SEK (10-30) [Redig]│    │
│ └─────────────────────────────────┘    │
│                                          │
│ Alla fakturor:                          │
│ [Status: Alla ▼]                        │
│ ┌──────────────────────────────────┐   │
│ │ ID | Namn | Belopp | Datum | Kat │   │
│ │ (klicka på rad för att redigera) │   │
│ └──────────────────────────────────┘   │
└─────────────────────────────────────────┘

Redigera faktura (modal):
┌─────────────────────────────────────────┐
│ Redigera faktura                    [X] │
├─────────────────────────────────────────┤
│ Namn: [Elräkning December]             │
│ Belopp: [850.00] SEK                    │
│ Förfallodatum: [2025-12-31]            │
│ Kategori: [Boende ▼]                    │
│ Underkategori: [Elektricitet ▼]        │
│ Konto: [1722 20 34439 ▼]               │
│ Beskrivning: [Elkostnad för dec...]    │
│                                          │
│ [Avbryt] [Spara]                        │
└─────────────────────────────────────────┘
```

## Dokumentation

### YAML-exempel
- `yaml/bills_example.yaml`: Exempel på fakturastruktur med nya fält
- `yaml/income_tracker_example.yaml`: Exempel på inkomstdata för månadsanalys
- `yaml/net_balance_splitter_example.yaml`: Exempel på beräkningar och output

### Teknisk dokumentation
Alla funktioner är dokumenterade med docstrings som beskriver:
- Syfte
- Parametrar
- Returvärden
- Exempel på användning

## Sammanfattning av ändringar

### Nya filer
- `modules/core/net_balance_splitter.py`: Modul för beräkning av överföringar
- `tests/test_net_balance_splitter.py`: Tester för net_balance_splitter
- `yaml/bills_example.yaml`: Dokumentation med YAML-exempel
- `yaml/income_tracker_example.yaml`: Dokumentation för inkomster
- `yaml/net_balance_splitter_example.yaml`: Dokumentation för beräkningar

### Modifierade filer
- `modules/core/account_manager.py`: Lagt till kontonummer-matchning
- `modules/core/bill_manager.py`: Lagt till subcategory och kontonormalisering
- `modules/core/parse_pdf_bills.py`: Uppdaterat för subcategory-stöd
- `dashboard/dashboard_ui.py`: Utökad översikt, månadsanalys-tab, bill editing

### Statistik
- **Nya funktioner**: 15+
- **Nya callbacks**: 12
- **Nya tester**: 7
- **Totala tester**: 187 (alla passerar)
- **Nya UI-komponenter**: 6 (snabböversikt, saldo per konto, etc.)
- **Nya paneler**: 1 (månadsanalys)

## Framtida förbättringar

Möjliga utökningar:
1. Export av månadsanalys till PDF/Excel
2. Anpassningsbara fördelningsregler per kategori
3. Automatisk överföring via bankintegration
4. Historisk jämförelse av månadsanalyser
5. Push-notiser för förfallande fakturor
6. AI-förslag för budgetering baserat på historik
