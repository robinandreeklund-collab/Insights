# Nordea PDF Parser - Dokumentation

## Översikt

Detta är en utökad version av PDF-parsern som kan läsa och extrahera fakturor från Nordea "Hantera betalningar" PDF-filer. Systemet kan hantera flera olika konton i samma PDF-fil och sparar all information strukturerat i YAML-format.

## Funktioner

### 1. PDF-parsing med kontoinformation

Parsern kan extrahera:
- **Kontonummer** som varje faktura ska belasta
- **Fakturanamn** (t.ex. "Elräkning Vattenfall")
- **Belopp** (inklusive belopp med tusentalsavgränsare som 8,500.00)
- **Förfallodatum** (i formatet YYYY-MM-DD)
- **Kategori** (automatisk kategorisering baserad på fakturanamn)

### 2. Stöd för flera konton

En enda PDF-fil kan innehålla fakturor för flera olika konton. Parsern grupperar automatiskt fakturor per konto.

### 3. YAML-lagring

Alla fakturor sparas i `yaml/bills.yaml` med komplett information:

```yaml
bills:
- account: 3570 12 34567
  amount: 1245.5
  category: Boende
  created_at: '2025-10-22 12:55:49'
  description: 'Extraherad från PDF (Konto: 3570 12 34567)'
  due_date: '2025-11-15'
  id: BILL-0001
  name: Elräkning Vattenfall
  status: pending
```

### 4. Dashboard-visualisering

Dashboarden visar:
- **Kontoöversikt**: Lista alla konton med antal fakturor och total summa
- **Fakturadetaljer per konto**: Visar varje faktura med namn, belopp, datum, kategori och status
- **Alla fakturor**: En detaljerad tabell med alla fakturor, filtrerade på status

## PDF-format som stöds

### Nordea "Hantera betalningar" format

Parsern känner igen PDF-filer med följande struktur:

```
Nordea - Hantera betalningar

Konto: 3570 12 34567
Faktura              Belopp      Förfallodatum
Elräkning Vattenfall 1,245.50    2025-11-15
Telenor Mobilabo...  399.00      2025-11-20

Konto: 3570 98 76543
Faktura              Belopp      Förfallodatum
Hyresavi November    8,500.00    2025-11-01
```

### Andra format

Parsern har även stöd för enklare PDF-format som inte innehåller kontoinformation. I dessa fall extraheras fakturor utan kontokoppling.

## Användning

### 1. Via Dashboard

#### Importera PDF:
1. Starta dashboarden: `python dashboard/dashboard_ui.py`
2. Öppna i webbläsare: http://127.0.0.1:8050
3. Gå till fliken "Fakturor"
4. Under "Importera fakturor från PDF":
   - Dra och släpp PDF-filen ELLER
   - Klicka för att välja fil
5. Systemet importerar automatiskt alla fakturor

#### Visa fakturor per konto:
Efter import visas:
- **Kontoöversikt** överst med kort sammanfattning per konto
- **Detaljerad tabell** för varje konto med alla fakturor

### 2. Via Python-kod

#### Enkel import:

```python
from modules.core.parse_pdf_bills import PDFBillParser
from modules.core.bill_manager import BillManager

# Initialisera
parser = PDFBillParser()
bill_manager = BillManager()

# Importera från PDF
count = parser.import_bills_to_manager(
    "Nordea - Hantera betalningar.pdf",
    bill_manager
)

print(f"Importerade {count} fakturor")
```

#### Visa fakturor per konto:

```python
from modules.core.bill_manager import BillManager

bill_manager = BillManager()

# Få kontoöversikt
summaries = bill_manager.get_account_summary()

for summary in summaries:
    print(f"\nKonto: {summary['account']}")
    print(f"Antal fakturor: {summary['bill_count']}")
    print(f"Total summa: {summary['total_amount']:.2f} SEK")
    
    for bill in summary['bills']:
        print(f"  - {bill['name']}: {bill['amount']:.2f} SEK")
```

#### Få fakturor för specifikt konto:

```python
bills_by_account = bill_manager.get_bills_by_account()

# Visa fakturor för ett specifikt konto
account = "3570 12 34567"
if account in bills_by_account:
    for bill in bills_by_account[account]:
        print(f"{bill['name']}: {bill['amount']:.2f} SEK")
```

## Exempel på användning

### Test-PDF fil

En exempel-PDF finns i projektroten: `test_nordea_betalningar.pdf`

Denna innehåller:
- **3 konton** (3570 12 34567, 3570 98 76543, 3570 55 55555)
- **8 fakturor totalt**
- **Total summa: 13,140.50 SEK**

### Importera test-PDF:

```bash
cd /home/runner/work/Insights/Insights

python3 << 'EOF'
from modules.core.parse_pdf_bills import PDFBillParser
from modules.core.bill_manager import BillManager

# Rensa befintliga fakturor
import os, yaml
yaml_dir = "yaml"
bills_file = os.path.join(yaml_dir, "bills.yaml")
with open(bills_file, 'w', encoding='utf-8') as f:
    yaml.dump({'bills': []}, f, default_flow_style=False, allow_unicode=True)

# Importera
parser = PDFBillParser()
bill_manager = BillManager()
count = parser.import_bills_to_manager("test_nordea_betalningar.pdf", bill_manager)

# Visa resultat
print(f"\n✓ Importerade {count} fakturor\n")
summaries = bill_manager.get_account_summary()

for summary in summaries:
    print(f"Konto: {summary['account']}")
    print(f"  Antal: {summary['bill_count']} st")
    print(f"  Summa: {summary['total_amount']:.2f} SEK\n")
EOF
```

### Förväntat resultat:

```
✓ Importerade 8 fakturor

Konto: 3570 12 34567
  Antal: 3 st
  Summa: 2093.50 SEK

Konto: 3570 55 55555
  Antal: 3 st
  Summa: 397.00 SEK

Konto: 3570 98 76543
  Antal: 2 st
  Summa: 10650.00 SEK
```

## Kategorisering

Fakturor kategoriseras automatiskt baserat på nyckelord i namn:

| Kategori | Nyckelord |
|----------|-----------|
| **Boende** | el, elektri, hyra, internet, bredband, försäkring |
| **Nöje** | netflix, spotify, hbo, disney, viaplay |
| **Övrigt** | mobil, telefon, eller inget matchande nyckelord |

## YAML-struktur

### bills.yaml

```yaml
bills:
- id: BILL-0001
  name: Elräkning Vattenfall
  amount: 1245.5
  due_date: '2025-11-15'
  description: 'Extraherad från PDF (Konto: 3570 12 34567)'
  category: Boende
  account: 3570 12 34567          # <-- Nytt fält
  status: pending
  created_at: '2025-10-22 12:55:49'
  paid_at: null
  matched_transaction_id: null
  scheduled_payment_date: null
```

## Dashboard-gränssnitt

### Fakturor per konto (Ny sektion)

Visar kort per konto med:
- Kontonummer
- Antal fakturor (totalt och väntande)
- Total summa
- Tabell med alla fakturor för det kontot

### Alla fakturor (Befintlig sektion)

Visar alla fakturor i en tabell med:
- ID
- Namn
- Belopp
- Förfallodatum
- Status
- Kategori
- **Konto** (ny kolumn)

## Testning

### Kör alla tester:

```bash
python -m pytest tests/test_parse_pdf_bills.py tests/test_bill_manager.py -v
```

### Tester inkluderar:

- ✅ Parsning av Nordea-format
- ✅ Detektion av Nordea-format
- ✅ Extrahering med kontoinformation
- ✅ Gruppering av fakturor per konto
- ✅ Kontosammanfattning
- ✅ Kategorisering av fakturor
- ✅ YAML-lagring med konto

## API-referens

### PDFBillParser

#### `parse_pdf(pdf_path: str, use_demo_data: bool = False) -> List[Dict]`

Extrahera fakturor från PDF.

**Returns:**
```python
[
    {
        'name': 'Elräkning Vattenfall',
        'amount': 1245.5,
        'due_date': '2025-11-15',
        'description': 'Extraherad från PDF (Konto: 3570 12 34567)',
        'category': 'Boende',
        'account': '3570 12 34567'
    },
    ...
]
```

#### `import_bills_to_manager(pdf_path: str, bill_manager, use_demo_data: bool = False) -> int`

Importera fakturor direkt till BillManager.

**Returns:** Antal importerade fakturor

### BillManager

#### `get_bills_by_account() -> Dict[str, List[Dict]]`

Gruppera fakturor per konto.

**Returns:**
```python
{
    '3570 12 34567': [bill1, bill2, bill3],
    '3570 98 76543': [bill4, bill5],
    ...
}
```

#### `get_account_summary() -> List[Dict]`

Få sammanfattning per konto.

**Returns:**
```python
[
    {
        'account': '3570 12 34567',
        'bill_count': 3,
        'pending_count': 3,
        'total_amount': 2093.5,
        'bills': [...]
    },
    ...
]
```

## Troubleshooting

### Problem: PDF läses inte korrekt

**Lösning:** Kontrollera att PDF-filen:
- Innehåller textdata (inte bara bilder)
- Har rätt format med "Konto:" före varje kontoavsnitt
- Har kolumner för "Faktura", "Belopp" och "Förfallodatum"

### Problem: Fakturor får fel kategori

**Lösning:** Kategoriseringen baseras på nyckelord. Lägg till fler nyckelord i `_categorize_bill()` metoden i `parse_pdf_bills.py`.

### Problem: Belopp parsas fel

**Lösning:** Parsern stödjer både punkter och komman i belopp. Kontrollera att beloppen i PDF:en har format `X,XXX.XX` eller `XXX.XX`.

## Framtida förbättringar

Möjliga förbättringar:
- [ ] Stöd för fler PDF-format (andra banker)
- [ ] OCR-stöd för skannade PDF:er
- [ ] Automatisk matchning av fakturor mot befintliga konton i systemet
- [ ] Export av fakturor per konto
- [ ] Dashboard-filter för att visa endast ett specifikt konto

## Support

För frågor eller problem, kontakta utvecklingsteamet eller öppna ett issue på GitHub.
