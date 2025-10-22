# Implementation Example - Nordea PDF Parser

## Översikt

Detta dokument visar ett praktiskt exempel på hur den nya Nordea PDF-parsern fungerar, från import av PDF till visning i dashboard.

## Test-PDF Innehåll

Vår test-PDF `test_nordea_betalningar.pdf` innehåller:

```
Nordea - Hantera betalningar

Konto: 3570 12 34567
Faktura              Belopp      Förfallodatum
Elräkning Vattenfall 1,245.50    2025-11-15
Telenor Mobilabo...  399.00      2025-11-20
Telia Internet       449.00      2025-11-25

Konto: 3570 98 76543
Faktura              Belopp      Förfallodatum
Hyresavi November    8,500.00    2025-11-01
Försäkring Länsf...  2,150.00    2025-11-10

Konto: 3570 55 55555
Faktura              Belopp      Förfallodatum
Netflix Abonnemang   119.00      2025-11-05
Spotify Premium...   179.00      2025-11-08
HBO Max             99.00       2025-11-12
```

**Totalt:** 3 konton, 8 fakturor, 13,140.50 SEK

## Steg 1: Import via Python

```python
from modules.core.parse_pdf_bills import PDFBillParser
from modules.core.bill_manager import BillManager

# Initialisera
parser = PDFBillParser()
bill_manager = BillManager()

# Importera PDF
count = parser.import_bills_to_manager(
    "test_nordea_betalningar.pdf", 
    bill_manager
)

print(f"✓ Imported {count} bills")
# Output: ✓ Imported 8 bills
```

## Steg 2: YAML Output

Efter import skapas följande i `yaml/bills.yaml`:

```yaml
bills:
- account: 3570 12 34567
  amount: 1245.5
  category: Boende
  created_at: '2025-10-22 12:55:49'
  description: 'Extraherad från PDF (Konto: 3570 12 34567)'
  due_date: '2025-11-15'
  id: BILL-0001
  matched_transaction_id: null
  name: Elräkning Vattenfall
  paid_at: null
  scheduled_payment_date: null
  status: pending

- account: 3570 12 34567
  amount: 399.0
  category: Boende
  created_at: '2025-10-22 12:55:49'
  description: 'Extraherad från PDF (Konto: 3570 12 34567)'
  due_date: '2025-11-20'
  id: BILL-0002
  matched_transaction_id: null
  name: Telenor Mobilabonnemang
  paid_at: null
  scheduled_payment_date: null
  status: pending

# ... 6 more bills ...
```

### Viktiga fält:
- **account**: Vilket konto fakturan ska belasta (nytt!)
- **amount**: Belopp i SEK
- **due_date**: Förfallodatum (YYYY-MM-DD)
- **name**: Fakturanamn från PDF
- **category**: Automatiskt kategoriserad
- **status**: pending/paid/overdue

## Steg 3: Kontosammanfattning via Python

```python
summaries = bill_manager.get_account_summary()

for summary in summaries:
    print(f"\nKonto: {summary['account']}")
    print(f"  Antal fakturor: {summary['bill_count']}")
    print(f"  Väntande: {summary['pending_count']}")
    print(f"  Total summa: {summary['total_amount']:.2f} SEK")
```

**Output:**

```
Konto: 3570 12 34567
  Antal fakturor: 3
  Väntande: 3
  Total summa: 2093.50 SEK

Konto: 3570 55 55555
  Antal fakturor: 3
  Väntande: 3
  Total summa: 397.00 SEK

Konto: 3570 98 76543
  Antal fakturor: 2
  Väntande: 2
  Total summa: 10650.00 SEK
```

## Steg 4: Dashboard-visning

När man öppnar dashboarden (http://127.0.0.1:8050) och går till fliken "Fakturor" ser man:

### A. Fakturor per konto (Ny sektion!)

Tre kort visas, ett per konto:

#### Konto: 3570 12 34567
- **Antal fakturor:** 3 st
- **Väntande:** 3 st  
- **Total summa:** 2093.50 SEK

**Fakturor:**
| Namn | Belopp | Förfallodatum | Kategori | Status |
|------|--------|---------------|----------|--------|
| Elräkning Vattenfall | 1245.50 SEK | 2025-11-15 | Boende | pending |
| Telenor Mobilabonnemang | 399.00 SEK | 2025-11-20 | Boende | pending |
| Telia Internet | 449.00 SEK | 2025-11-25 | Boende | pending |

#### Konto: 3570 55 55555
- **Antal fakturor:** 3 st
- **Väntande:** 3 st
- **Total summa:** 397.00 SEK

**Fakturor:**
| Namn | Belopp | Förfallodatum | Kategori | Status |
|------|--------|---------------|----------|--------|
| Netflix Abonnemang | 119.00 SEK | 2025-11-05 | Nöje | pending |
| Spotify Premium Family | 179.00 SEK | 2025-11-08 | Boende | pending |
| HBO Max | 99.00 SEK | 2025-11-12 | Nöje | pending |

#### Konto: 3570 98 76543
- **Antal fakturor:** 2 st
- **Väntande:** 2 st
- **Total summa:** 10650.00 SEK

**Fakturor:**
| Namn | Belopp | Förfallodatum | Kategori | Status |
|------|--------|---------------|----------|--------|
| Hyresavi November | 8500.00 SEK | 2025-11-01 | Boende | pending |
| Försäkring Länsförsäkringar | 2150.00 SEK | 2025-11-10 | Boende | pending |

### B. Alla fakturor (Uppdaterad tabell)

En detaljerad tabell med ALLA fakturor, nu med ny kolumn "Konto":

| ID | Namn | Belopp | Förfallodatum | Status | Kategori | **Konto** |
|----|------|--------|---------------|--------|----------|-----------|
| BILL-0001 | Elräkning Vattenfall | 1245.5 | 2025-11-15 | pending | Boende | **3570 12 34567** |
| BILL-0002 | Telenor Mobilabonnemang | 399 | 2025-11-20 | pending | Boende | **3570 12 34567** |
| BILL-0003 | Telia Internet | 449 | 2025-11-25 | pending | Boende | **3570 12 34567** |
| BILL-0004 | Hyresavi November | 8500 | 2025-11-01 | pending | Boende | **3570 98 76543** |
| BILL-0005 | Försäkring Länsförsäkringar | 2150 | 2025-11-10 | pending | Boende | **3570 98 76543** |
| BILL-0006 | Netflix Abonnemang | 119 | 2025-11-05 | pending | Nöje | **3570 55 55555** |
| BILL-0007 | Spotify Premium Family | 179 | 2025-11-08 | pending | Boende | **3570 55 55555** |
| BILL-0008 | HBO Max | 99 | 2025-11-12 | pending | Nöje | **3570 55 55555** |

## Funktionalitet

### 1. PDF Upload i Dashboard

1. Gå till "Fakturor" fliken
2. Under "Importera fakturor från PDF"
3. Dra och släpp `test_nordea_betalningar.pdf` ELLER klicka för att välja
4. Systemet visar: "✓ 8 fakturor importerade från test_nordea_betalningar.pdf"

### 2. Automatisk Uppdatering

- Dashboard uppdateras automatiskt var 5:e sekund
- Nya fakturor visas direkt i både kontoöversikt och tabell
- YAML-filen uppdateras omedelbart

### 3. Filtrering

Man kan filtrera "Alla fakturor" tabellen på:
- **Alla** (default)
- **Väntande** (pending)
- **Betalda** (paid)
- **Förfallna** (overdue)

## Kategorisering

Systemet kategoriserar automatiskt:

| Faktura | Detekterade nyckelord | Kategori |
|---------|----------------------|----------|
| Elräkning Vattenfall | "el", "vattenfall" | Boende |
| Telenor Mobilabonnemang | "telenor" | Övrigt |
| Telia Internet | "internet", "telia" | Boende |
| Hyresavi November | "hyresavi", "hyra" | Boende |
| Försäkring Länsförsäkringar | "försäkring" | Boende |
| Netflix Abonnemang | "netflix" | Nöje |
| Spotify Premium Family | "spotify" | Nöje |
| HBO Max | "hbo" | Nöje |

## Integration med befintliga funktioner

### Fakturamatchning

Befintlig funktionalitet "Matcha fakturor" fungerar fortfarande:
- Klicka på "Matcha fakturor" knappen
- Systemet letar efter transaktioner som matchar fakturornas belopp
- Matchade fakturor markeras som betalda

### Schemalagda betalningar

Man kan fortfarande schemalägga betalningar:
```python
bill_manager.schedule_payment(
    bill_id='BILL-0001',
    payment_date='2025-11-10'
)
```

## Testresultat

Alla 30 tester passerar:

```
tests/test_parse_pdf_bills.py::TestPDFBillParser::test_extract_nordea_payment_format PASSED
tests/test_parse_pdf_bills.py::TestPDFBillParser::test_nordea_format_detection PASSED
tests/test_parse_pdf_bills.py::TestPDFBillParser::test_bill_categorization PASSED
tests/test_parse_pdf_bills.py::TestPDFBillParser::test_import_with_accounts PASSED
tests/test_bill_manager.py::TestBillManager::test_add_bill_with_account PASSED
tests/test_bill_manager.py::TestBillManager::test_get_bills_by_account PASSED
tests/test_bill_manager.py::TestBillManager::test_get_account_summary PASSED
tests/test_bill_manager.py::TestBillManager::test_account_summary_with_mixed_status PASSED
... och 22 befintliga tester
```

## Sammanfattning av fördelar

### För användaren:
✅ Import av PDF med drag-and-drop  
✅ Automatisk kontogrupering  
✅ Tydlig översikt per konto  
✅ Ser direkt vilket konto varje faktura belastar  
✅ Total summa per konto  

### För utvecklaren:
✅ Enkel API för att hämta fakturor per konto  
✅ YAML-struktur stödjer kontofält  
✅ Bakåtkompatibel med befintlig kod  
✅ Vältestad med 30 automatiska tester  
✅ Dokumenterad med exempel  

## Nästa steg

Möjliga förbättringar:
- [ ] Exportera fakturor per konto till CSV
- [ ] Filter för att visa endast ett konto i tabellen
- [ ] Stöd för fler PDF-format (andra banker)
- [ ] Automatisk matchning mot befintliga konton i systemet
- [ ] Graf som visar utgifter per konto över tid
