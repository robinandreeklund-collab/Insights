# Admin Dashboard Guide

## Översikt

Admin Dashboard är ett kraftfullt verktyg för att träna AI:n och hantera kategorisering av alla importerade transaktioner. Dashboarden är tillgänglig via navigeringsmenyn och ger administratörer fullständig kontroll över kategorisering och AI-träning.

## Funktioner

### 1. Statistiköversikt

Överst på admin-dashboarden visas följande nyckeltal:

- **Totalt transaktioner**: Antal importerade transaktioner från alla källor
- **Okategoriserade**: Antal transaktioner utan kategori (med procentandel)
- **Aktiva kategorier**: Antal unika kategorier i systemet
- **Kategoriserade**: Antal transaktioner med tilldelad kategori

### 2. Filtrering av Transaktioner

Dashboarden erbjuder kraftfulla filtreringsalternativ:

#### Filterkriterier:
- **Källa**: Filtrera på importkälla (t.ex. `import.csv`, `amex.csv`, `mastercard.csv`)
- **Konto**: Filtrera på specifikt bankkonto
- **Kategori**: Filtrera på befintlig kategori
- **Status**: 
  - Alla: Visa alla transaktioner
  - Okategoriserade: Visa endast transaktioner utan kategori
  - Kategoriserade: Visa endast kategoriserade transaktioner
- **Datumintervall**: Filtrera mellan start- och slutdatum

#### Så här använder du filter:
1. Välj önskade filterkriterier från dropdown-menyer och datumväljare
2. Klicka på "Applicera filter"-knappen
3. Transaktionslistan uppdateras automatiskt

### 3. Transaktionslista

Transaktionslistan visar all matchande data i en interaktiv tabell med följande kolumner:

- **Välj**: Checkbox för att välja transaktioner för bulk-åtgärder
- **Datum**: Transaktionsdatum
- **Beskrivning**: Transaktionsbeskrivning
- **Belopp**: Transaktionsbelopp
- **Kategori**: Nuvarande kategori (markerad om okategoriserad)
- **Underkategori**: Nuvarande underkategori
- **Konto**: Kontot transaktionen tillhör
- **Källa**: Importkällan

#### Funktioner:
- **Sortering**: Klicka på kolumnrubriker för att sortera
- **Paginering**: 50 transaktioner per sida med navigeringsknappar
- **Markering**: Klicka i checkboxar eller använd "Välj alla"/"Avmarkera alla"-knappar
- **Färgkodning**: Okategoriserade transaktioner markeras med orange bakgrund

### 4. Bulk-åtgärder

Med bulk-åtgärder kan du uppdatera flera transaktioner samtidigt:

#### Steg-för-steg:
1. Välj transaktioner i listan (använd checkboxar eller "Välj alla")
2. Välj önskad kategori från dropdown-menyn
3. Välj underkategori (om tillämpligt)
4. Klicka på en av följande knappar:
   - **Uppdatera valda**: Uppdaterar kategorin för alla valda transaktioner
   - **Träna AI med valda**: Lägger till valda transaktioner i träningsdata för AI:n

#### Resultat:
- Statusmeddelande visar antal uppdaterade/tränade transaktioner
- Tabellen uppdateras automatiskt med nya kategorier
- AI-träningsdata sparas i `yaml/training_data.yaml`

### 5. Kategorihantering

Admin-dashboarden inkluderar tre verktyg för kategorihantering:

#### 5.1 Skapa Kategori

Skapa nya kategorier med valfria underkategorier:

**Steg:**
1. Gå till fliken "Skapa kategori"
2. Ange kategorinamn (t.ex. "Transport")
3. (Valfritt) Ange underkategorier, en per rad:
   ```
   Bränsle
   Kollektivtrafik
   Taxi
   ```
4. Klicka på "Skapa"

**Resultat:**
- Ny kategori skapas i systemet
- Blir omedelbart tillgänglig i alla dropdown-menyer
- Sparas i `yaml/categories.yaml`

#### 5.2 Slå ihop Kategorier

Slå ihop två kategorier till en:

**Steg:**
1. Gå till fliken "Slå ihop kategorier"
2. Välj källkategori (den som ska försvinna)
3. Välj målkategori (den som ska behållas)
4. Klicka på "Slå ihop"

**Resultat:**
- Alla transaktioner från källkategorin flyttas till målkategorin
- Källkategorin tas bort från systemet
- Träningsdata uppdateras automatiskt
- Statusmeddelande visar antal uppdaterade transaktioner

#### 5.3 Ta bort Kategori

Ta bort en kategori och flytta dess transaktioner:

**Steg:**
1. Gå till fliken "Ta bort kategori"
2. Välj kategori att ta bort
3. Välj kategori att flytta transaktioner till
4. Klicka på "Ta bort"

**OBS:** Standardkategorier (Mat & Dryck, Transport, etc.) kan inte tas bort.

**Resultat:**
- Kategorin tas bort från systemet
- Alla transaktioner flyttas till vald målkategori
- Statusmeddelande visar antal flyttade transaktioner

### 6. AI-träningsstatistik

Underst på dashboarden visas detaljerad AI-träningsstatistik:

- **Totalt träningsprover**: Alla träningsprover i systemet
- **Manuella prover**: Antal manuellt kategoriserade prover
- **Kategoriseringsregler**: Totalt antal regler (med antal AI-genererade)
- **Nya prover (7 dagar)**: Antal nya träningsprover senaste veckan

### 7. Automatisk Uppdatering

Dashboarden uppdateras automatiskt var 10:e sekund för att visa:
- Senaste statistik
- Nya transaktioner
- Uppdaterade kategorier
- AI-träningsframsteg

## Arbetsflöden

### Arbetsflöde 1: Kategorisera Nya Importer

1. **Importera CSV-fil** via "Inmatning"-fliken
2. **Gå till Admin Dashboard**
3. **Filtrera på okategoriserade** transaktioner
4. **Välj alla** okategoriserade transaktioner
5. **Välj kategori och underkategori**
6. **Klicka "Uppdatera valda"** för att kategorisera
7. **Klicka "Träna AI med valda"** för att lära AI:n

### Arbetsflöde 2: Förbättra AI-noggrannhet

1. **Gå till Admin Dashboard**
2. **Filtrera på specifik källa** (t.ex. "amex.csv")
3. **Granska AI-föreslagna kategorier** i listan
4. **Korrigera felaktiga kategoriseringar**:
   - Välj transaktioner med fel kategori
   - Välj rätt kategori/underkategori
   - Klicka "Uppdatera valda"
5. **Träna AI med korrigeringar**:
   - Klicka "Träna AI med valda"
6. **Upprepa för andra källor**

### Arbetsflöde 3: Städa Kategorier

1. **Gå till Admin Dashboard**
2. **Granska kategoristatistik**
3. **Identifiera dubletter eller snarlika kategorier**
4. **Slå ihop kategorier**:
   - Gå till "Slå ihop kategorier"-fliken
   - Slå ihop "Food" med "Mat & Dryck"
   - Slå ihop "Bensin" med "Transport"
5. **Ta bort oanvända kategorier**:
   - Gå till "Ta bort kategori"-fliken
   - Välj kategori att ta bort
   - Flytta transaktioner till "Övrigt"

### Arbetsflöde 4: Skapa Specialiserade Kategorier

1. **Gå till Admin Dashboard**
2. **Gå till "Skapa kategori"-fliken**
3. **Skapa ny kategori** med underkategorier:
   ```
   Kategorinamn: Husdjur
   Underkategorier:
   Veterinär
   Hundmat
   Kattmat
   Tillbehör
   ```
4. **Filtrera och kategorisera relevanta transaktioner**
5. **Träna AI med nya kategoriseringar**

## Datakällor som Stöds

Admin Dashboard hanterar transaktioner från alla importkällor:

### 1. Kontoutdrag (Nordea CSV)
- Format: Semicolon-separated (;)
- Kolumner: Bokföringsdag, Belopp, Avsändare, Mottagare, Namn, Rubrik, Saldo, Valuta
- Källa: `import.csv` eller filnamn

### 2. American Express (Amex)
- Format: CSV
- Kolumner: Date, Description, Amount, Category
- Källa: `amex.csv`

### 3. Mastercard
- Format: CSV eller Excel (XLSX)
- Två format stöds:
  - **Format 1**: Datum, Specifikation, Ort, Belopp (YYYY-MM-DD, decimal punkt)
  - **Format 2**: Datum, Beskrivning, Belopp (MM/DD/YYYY, komma decimal)
- Källa: `mastercard.csv` eller `mastercard.xlsx`

### 4. Manuella Transaktioner
- Källa: `manual`
- Skapade direkt i systemet via "Inmatning"-fliken

## Bästa Praxis

### För Kategorisering:
1. **Börja brett, förfina sen**: Använd huvudkategorier först, lägg till underkategorier senare
2. **Var konsekvent**: Använd samma kategorier för liknande transaktioner
3. **Granska regelbundet**: Kontrollera AI:ns kategoriseringar varje vecka
4. **Träna tidigt och ofta**: Ju fler träningsprover, desto bättre AI-noggrannhet

### För AI-träning:
1. **Minst 10-20 prover per kategori**: För tillförlitlig AI-träning
2. **Variera beskrivningar**: Träna på olika varianter av samma leverantör/typ
3. **Korrigera fel direkt**: Om AI:n kategoriserar fel, korrigera och träna om
4. **Övervaka träningsstatistik**: Följ "Nya prover (7 dagar)" för att se framsteg

### För Kategoristruktur:
1. **Håll det enkelt**: Max 10-15 huvudkategorier
2. **Logisk hierarki**: Underkategorier ska vara specifika varianter av huvudkategorin
3. **Undvik överlapp**: Varje transaktion ska passa i endast en kategori
4. **Dokumentera**: Använd beskrivande namn (inte förkortningar)

## Felsökning

### Problem: Inga transaktioner visas
**Lösning:**
- Kontrollera att transaktioner har importerats via "Inmatning"-fliken
- Kontrollera filterinställningar (prova "Alla" istället för specifika filter)
- Uppdatera sidan eller vänta på automatisk uppdatering

### Problem: Bulk-åtgärd fungerar inte
**Lösning:**
- Kontrollera att transaktioner är markerade i listan
- Kontrollera att kategori är vald
- Se felmeddelande för specifika detaljer

### Problem: Kategori kan inte tas bort
**Lösning:**
- Standardkategorier kan inte tas bort (Mat & Dryck, Transport, etc.)
- Använd "Slå ihop kategorier" istället för att konsolidera

### Problem: AI kategoriserar fortfarande fel efter träning
**Lösning:**
- Träna med fler exempel (minst 10-20 per kategori)
- Kontrollera att träningsprover är varierade
- Använd "Inställningar"-fliken för att köra fullständig AI-träning
- Granska befintliga kategoriseringsregler i `yaml/categorization_rules.yaml`

## Teknisk Information

### Datalagring:
- **Transaktioner**: `yaml/transactions.yaml`
- **Träningsdata**: `yaml/training_data.yaml`
- **Kategorier**: `yaml/categories.yaml`
- **Regler**: `yaml/categorization_rules.yaml`

### API-endpoints:
Admin Dashboard använder följande callbacks:
- `update_admin_stats`: Uppdatera statistik
- `populate_admin_dropdowns`: Fyll dropdown-menyer
- `update_admin_transaction_table`: Uppdatera transaktionslista
- `handle_bulk_actions`: Hantera bulk-åtgärder
- `create_category`: Skapa ny kategori
- `merge_categories`: Slå ihop kategorier
- `delete_category`: Ta bort kategori
- `update_admin_ai_stats`: Uppdatera AI-statistik

## Säkerhet

### Åtkomstkontroll:
I nuvarande version har alla användare tillgång till Admin Dashboard. För produktionsmiljö rekommenderas:

1. **Implementera autentisering**: Lägg till användarinloggning
2. **Rollbaserad åtkomst**: Endast admin-roll får tillgång
3. **Loggning**: Spåra alla kategoriseringsändringar
4. **Backup**: Regelbundna backuper av YAML-filer

### Exempel på framtida säkerhetsfunktioner:
```python
# Framtida implementation
@app.callback(...)
def admin_dashboard_access_check(session_token):
    if not is_admin(session_token):
        return "Åtkomst nekad. Endast administratörer har tillgång."
    # ... resten av callback
```

## Relaterade Guider

- [README.md](README.md) - Huvuddokumentation
- [THEME_GUIDE.md](THEME_GUIDE.md) - Tema och design
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Implementationsdetaljer

## Support

För frågor eller problem med Admin Dashboard:
1. Kontrollera denna guide först
2. Granska YAML-filer för datakorruption
3. Kör tester: `pytest tests/test_admin_dashboard.py -v`
4. Kontakta utvecklingsteamet

---

**Senast uppdaterad**: 2025-10-24  
**Version**: MVP 1.0  
**Status**: Produktionsklar
