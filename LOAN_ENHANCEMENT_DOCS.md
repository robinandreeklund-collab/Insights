# Loan Module Enhancement - Documentation

## Overview

The loan module has been enhanced with OCR (Optical Character Recognition) capabilities to automatically extract loan information from images, along with improved transaction matching and dashboard features.

## Features

### 1. Image-Based Loan Import

Upload a screenshot or image of loan information to automatically extract key details:

- Loan number
- Original and current amounts
- Amortized amount
- Interest rates (base, discount, effective)
- Rate and binding periods
- Important dates (disbursement, next change)
- Borrower names and shares
- Currency
- Collateral information
- Lender/bank details
- Payment interval
- Payment and repayment account numbers

### 2. Enhanced Data Model

The loan data model now supports extensive fields beyond the basic loan information:

**Basic Fields:**
- `name`: Loan name (e.g., "Bolån")
- `principal`: Original loan amount
- `current_balance`: Current remaining balance
- `interest_rate`: Annual interest rate (%)
- `start_date`: Loan start date
- `term_months`: Loan term in months
- `fixed_rate_end_date`: When binding period ends
- `status`: active, paid_off, or closed

**Extended Fields:**
- `loan_number`: Official loan number from lender
- `original_amount`: Original loan amount
- `current_amount`: Current loan amount
- `amortized`: Total amount amortized
- `base_interest_rate`: Base interest rate before discount
- `discount`: Interest discount applied
- `effective_interest_rate`: Effective interest rate
- `rate_period`: Interest rate period
- `binding_period`: Binding period duration
- `next_change_date`: Next interest rate change date
- `disbursement_date`: When loan was disbursed
- `borrowers`: List of borrower names
- `borrower_shares`: Dictionary of borrower shares
- `currency`: Loan currency (default: SEK)
- `collateral`: Collateral description
- `lender`: Lender/bank name
- `payment_interval`: Payment frequency
- `payment_account`: Account for payments
- `repayment_account`: Account for repayments
- `interest_payments`: List of interest payment records
- `payments`: List of amortization payment records

### 3. Automatic Transaction Matching

The system automatically matches bank transactions to loans using:

1. **Account Number Matching**: Matches transactions by payment/repayment account numbers
2. **Description Matching**: Matches by loan name, loan number, or loan ID in transaction description
3. **Keyword Matching**: Identifies loan-related transactions using keywords (bolån, lån, amortering, ränta)

When a transaction is matched:
- Amortization payments reduce the loan balance
- Interest payments are tracked separately
- Transaction ID is linked for traceability
- Matched transactions can be categorized as "amortering" or "ränteinbetalning"

### 4. Enhanced Dashboard

The loans tab now displays:
- **All loan details** including loan number, lender, and payment accounts
- **Payment history** showing both amortization and interest payments
- **Total amounts paid** (amortization and interest separately)
- **Upcoming payment events** for forecasting
- **Transaction links** for matched payments

## Usage

### Importing a Loan from Image

The image upload feature works **with or without OCR** installed:

**With Tesseract OCR (automatic extraction):**
1. Install Tesseract OCR (see installation instructions)
2. Navigate to the Loans tab (Lån) in the dashboard
3. In the "Importera lån från bild" section, click or drag-and-drop an image file
4. The system will automatically extract loan details using OCR
5. Review and edit the extracted information in the editable form
6. Click "Spara lån" to save the loan

**Without Tesseract OCR (manual entry with image reference):**
1. Navigate to the Loans tab (Lån) in the dashboard
2. In the "Importera lån från bild" section, click or drag-and-drop an image file
3. The form will appear with empty fields
4. Manually fill in the loan details using the uploaded image as a visual reference
5. Click "Spara lån" to save the loan

**Supported Image Formats:**
- PNG
- JPEG/JPG
- Other image formats supported by PIL/Pillow

**Tips for Best OCR Results (when Tesseract is installed):**
- Use high-quality, clear images
- Ensure text is readable and not blurred
- Swedish and English text are supported
- Standard loan document formats work best

### Adding a Loan Manually

If you prefer to enter loan details manually or if OCR is not available:

1. Navigate to the "Lägg till lån manuellt" section
2. Fill in at minimum: name, principal amount, interest rate, and start date
3. Optionally add binding end date and description
4. Click "Lägg till lån"

### Automatic Transaction Matching

To enable automatic transaction matching:

1. Ensure your loan has `payment_account` or `repayment_account` fields set
2. Import bank transactions as usual via CSV
3. The system will automatically:
   - Match transactions to loans by account number
   - Identify amortization vs. interest payments
   - Update loan balances
   - Link transactions to loans

**Manual Matching:**
You can also manually match a transaction to a loan using the transaction matching interface.

## YAML Structure

### Basic Loan Example

```yaml
loans:
  - id: LOAN-0001
    name: Bolån
    principal: 2000000.0
    current_balance: 1850000.0
    interest_rate: 3.5
    start_date: '2020-01-15'
    term_months: 360
    status: active
    created_at: '2025-01-15 10:30:00'
    payments:
      - date: '2025-01-01'
        amount: 5000.0
        timestamp: '2025-01-01 12:00:00'
        transaction_id: TXN-12345
    interest_payments: []
```

### Extended Loan Example (with OCR data)

```yaml
loans:
  - id: LOAN-0002
    name: Bolån Swedbank
    loan_number: '12345-678'
    lender: Swedbank AB
    principal: 2500000.0
    current_balance: 2350000.0
    original_amount: 2500000.0
    current_amount: 2350000.0
    amortized: 150000.0
    interest_rate: 3.45
    base_interest_rate: 3.75
    discount: 0.30
    effective_interest_rate: 3.45
    rate_period: '3 months'
    binding_period: '5 years'
    start_date: '2020-06-01'
    disbursement_date: '2020-06-01'
    next_change_date: '2025-06-01'
    fixed_rate_end_date: '2025-06-01'
    term_months: 360
    currency: SEK
    payment_interval: Monthly
    payment_account: '3300123456789'
    repayment_account: '3300987654321'
    collateral: 'Fastighet på Storgatan 123'
    borrowers:
      - Anna Svensson
      - Erik Andersson
    borrower_shares:
      Anna Svensson: 50
      Erik Andersson: 50
    status: active
    created_at: '2025-01-15 14:20:00'
    description: 'Importerat från bild. Långivare: Swedbank AB'
    payments:
      - date: '2025-01-05'
        amount: 8500.0
        timestamp: '2025-01-05 10:00:00'
        transaction_id: TXN-23456
    interest_payments:
      - date: '2025-01-05'
        amount: 6750.0
        timestamp: '2025-01-05 10:00:00'
        transaction_id: TXN-23457
```

## Migration Notes

### For Existing Loans

Existing loans will continue to work with the enhanced system. The extended fields are optional and can be added gradually:

1. Existing loans retain all their original fields
2. New fields can be added by:
   - Re-importing the loan from an image
   - Manually editing the `loans.yaml` file
   - Using the update functionality (to be added)

### Database Schema Changes

No breaking changes have been made. The loan data structure is backward compatible:
- All existing fields remain unchanged
- New fields are optional and default to `None` if not provided
- The `**kwargs` pattern in `add_loan()` accepts any additional fields

## Technical Details

### OCR Dependencies

The OCR functionality requires:
- `pytesseract>=0.3.10` - Python wrapper for Tesseract OCR
- `Pillow>=10.2.0` - Image processing
- `opencv-python-headless>=4.8.1.78` - Computer vision for image preprocessing
- **System package: Tesseract OCR executable**

#### Installing Tesseract OCR

**Windows:**
1. Download the installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run the installer and use default settings (installs to `C:\Program Files\Tesseract-OCR\`)
3. The installer should automatically add Tesseract to your PATH
4. If not added automatically, add `C:\Program Files\Tesseract-OCR\` to your system PATH
5. Restart your terminal/IDE
6. Verify installation: `tesseract --version`

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-swe
```

**macOS:**
```bash
brew install tesseract tesseract-lang
```

**Python packages:**
```bash
pip install pytesseract Pillow>=10.2.0 opencv-python-headless>=4.8.1.78
```

If these dependencies are not installed, the OCR feature will be disabled but the rest of the loan functionality remains available. The system will display helpful installation instructions when you try to upload an image.

### Image Processing Pipeline

1. **Upload**: Image is uploaded as base64 data
2. **Decode**: Base64 data is decoded to image
3. **Preprocessing**: Image is converted to grayscale and thresholded for better OCR
4. **OCR**: Tesseract extracts text (Swedish + English)
5. **Parsing**: Regular expressions extract structured data from text
6. **Formatting**: Amounts, dates, and rates are normalized
7. **Display**: Extracted data is shown in editable form

### Transaction Matching Algorithm

The matching algorithm prioritizes:

1. **Exact account match**: Most reliable, uses normalized account numbers
2. **Loan number match**: Matches loan number in transaction description
3. **Name match**: Matches loan name in transaction description
4. **ID match**: Matches loan ID in transaction description
5. **Keyword match**: Only if there's exactly one active loan

Payment type determination:
- Keywords like "ränta" or "interest" → interest payment
- All other matches → amortization payment

## Testing

### Running Tests

```bash
# Run all loan-related tests
pytest tests/test_loan_manager.py tests/test_loan_image_parser.py -v

# Run only loan manager tests
pytest tests/test_loan_manager.py -v

# Run only image parser tests (requires OCR dependencies)
pytest tests/test_loan_image_parser.py -v
```

### Test Coverage

- **Loan Manager**: 18 tests covering creation, updates, payments, matching, and calculations
- **Image Parser**: 14 tests covering text extraction, parsing, and edge cases
- Tests use temporary directories and are fully isolated

## Troubleshooting

### TesseractNotFoundError (Windows)

**Error**: `FileNotFoundError: [WinError 2] Det går inte att hitta filen` or `TesseractNotFoundError: tesseract is not installed or it's not in your PATH`

**This is the most common issue on Windows. The error means the Tesseract OCR executable is not installed on your system.**

**Solution for Windows:**

1. **Download Tesseract installer:**
   - Go to: https://github.com/UB-Mannheim/tesseract/wiki
   - Download the latest Windows installer (e.g., `tesseract-ocr-w64-setup-5.x.x.exe`)

2. **Install Tesseract:**
   - Run the installer
   - Use default installation path: `C:\Program Files\Tesseract-OCR\`
   - Make sure "Add to PATH" option is checked during installation

3. **Verify installation:**
   - Open a new Command Prompt or PowerShell window
   - Type: `tesseract --version`
   - You should see version information

4. **Restart the dashboard:**
   - Close and restart your Python/dashboard application
   - Try uploading an image again

**Alternative (if PATH not set automatically):**

If Tesseract is installed but still not found, manually add to PATH:
1. Open System Properties → Environment Variables
2. Under "System variables", find "Path"
3. Add: `C:\Program Files\Tesseract-OCR\`
4. Click OK and restart your terminal/IDE

**Or set path in code** (temporary workaround):

Add this line before importing the loan image parser:
```python
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

### OCR Not Working (Linux/Mac)

**Error**: "OCR dependencies inte installerade"

**Solution**:
```bash
# Install Python packages
pip install pytesseract Pillow>=10.2.0 opencv-python-headless>=4.8.1.78

# Install Tesseract executable
# Ubuntu/Debian:
sudo apt-get install tesseract-ocr tesseract-ocr-swe

# macOS:
brew install tesseract tesseract-lang
```

### Poor OCR Accuracy

**Possible causes and solutions**:
1. **Blurry image**: Use higher resolution or clearer screenshot
2. **Poor contrast**: Adjust image brightness/contrast before upload
3. **Non-standard format**: Review and edit extracted fields before saving
4. **Language issues**: Ensure Swedish language pack is installed
   - Windows: Select Swedish during Tesseract installation
   - Linux: Install `tesseract-ocr-swe` package

### Transaction Not Matching

**Checklist**:
1. Verify `payment_account` or `repayment_account` is set on loan
2. Check account number format matches transaction (ignore hyphens/spaces)
3. Ensure loan status is 'active'
4. For description-based matching, loan name/number should appear in transaction description

### Missing Fields After Import

**Common reasons**:
- Field not present in original image
- OCR couldn't recognize the field
- Field uses non-standard format

**Solution**: Manually enter missing fields in the editable form before saving

## Future Enhancements

Potential improvements for future versions:
- Support for PDF loan documents
- Bulk loan import
- Loan comparison and refinancing recommendations
- Payment schedule predictions
- Integration with bank APIs for automatic updates
- Support for multiple currencies with exchange rates
- Advanced analytics and reporting
- Loan portfolio overview

## Support

For issues, questions, or contributions, please refer to the main repository documentation.
