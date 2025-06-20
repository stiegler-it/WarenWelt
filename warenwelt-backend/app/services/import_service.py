import csv
import io
from typing import List, Dict, Any, Optional, Tuple # Tuple for return type with errors
from datetime import date, datetime # datetime for potential timestamp fields in future
from decimal import Decimal, InvalidOperation as DecimalInvalidOperation

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.product_model import Product, ProductTypeEnum, ProductStatusEnum
from app.models.supplier_model import Supplier
from app.models.product_category_model import ProductCategory
from app.models.tax_rate_model import TaxRate

# Assuming schemas are structured to accept necessary fields for creation
from app.schemas.product_schema import ProductCreate
from app.schemas.supplier_schema import SupplierCreate
from app.schemas.product_category_schema import ProductCategoryCreate # For creating categories on the fly

# Import relevant services
from app.services import product_service, supplier_service, product_category_service, tax_rate_service

# Helper to process CSV content
def _read_csv_content(csv_file_content: bytes) -> Tuple[List[Dict[str, str]], List[str]]:
    """
    Reads CSV content and returns a list of dictionaries and the header.
    Tries UTF-8, then Latin-1 encoding. Assumes semicolon delimiter.
    """
    decoded_content = ""
    try:
        decoded_content = csv_file_content.decode('utf-8-sig') # utf-8-sig handles BOM
    except UnicodeDecodeError:
        try:
            decoded_content = csv_file_content.decode('latin-1')
        except UnicodeDecodeError as e_latin:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"CSV-Dekodierungsfehler: Weder UTF-8 noch Latin-1 erfolgreich. Originalfehler: {str(e_latin)}")

    try:
        # Use io.StringIO to treat the string as a file
        csv_file_like_object = io.StringIO(decoded_content)
        # Sniff dialect to be more robust, but for now, hardcode semicolon
        # dialect = csv.Sniffer().sniff(csv_file_like_object.read(1024)); csv_file_like_object.seek(0)
        # csv_reader = csv.DictReader(csv_file_like_object, dialect=dialect)
        csv_reader = csv.DictReader(csv_file_like_object, delimiter=';')
        header = csv_reader.fieldnames if csv_reader.fieldnames else []
        data = [row for row in csv_reader]
        if not data and not header : # Empty or malformed CSV
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CSV-Datei ist leer oder das Format konnte nicht erkannt werden (möglicherweise falscher Delimiter?). Erwartet Semikolon als Trennzeichen.")
        return data, header
    except csv.Error as e_csv:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"CSV-Formatfehler: {str(e_csv)}")
    except Exception as e_gen: # Catch-all for other unexpected errors during CSV parsing
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Allgemeiner Fehler beim Lesen der CSV-Datei: {str(e_gen)}")


# --- Supplier Import ---
def import_suppliers_from_csv(db: Session, csv_file_content: bytes) -> Dict[str, Any]:
    rows, header = _read_csv_content(csv_file_content)
    imported_count = 0
    skipped_count = 0
    errors_log: List[Dict[str, Any]] = [] # Renamed for clarity

    # Define expected/required columns for suppliers
    # Adjust these based on your actual CSV structure and SupplierCreate schema
    expected_supplier_fields = ['supplier_number', 'company_name', 'first_name', 'last_name', 'email', 'phone', 'is_internal']
    required_supplier_fields = ['supplier_number']

    # Basic header validation
    if not all(rf in header for rf in required_supplier_fields):
        missing_headers = [rf for rf in required_supplier_fields if rf not in header]
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Fehlende Pflichtspalten in der Lieferanten-CSV: {', '.join(missing_headers)}")

    for i, row_data in enumerate(rows, start=1): # row_data is a dict from DictReader
        row_number_for_error = i + 1 # Account for header row in error reporting for user

        # Validate required fields in data row
        if not row_data.get(required_supplier_fields[0], "").strip(): # Check supplier_number
            errors_log.append({"row": row_number_for_error, "message": f"Fehlende Pflichtwert: {required_supplier_fields[0]}", "data": row_data})
            skipped_count += 1
            continue

        supplier_num = row_data.get('supplier_number', '').strip()
        if supplier_service.get_supplier_by_number(db, supplier_number=supplier_num):
            errors_log.append({"row": row_number_for_error, "message": f"Lieferantennummer '{supplier_num}' existiert bereits.", "data": row_data})
            skipped_count += 1
            continue

        try:
            # Prepare data for SupplierCreate schema
            supplier_create_data = {
                "supplier_number": supplier_num,
                "company_name": row_data.get('company_name', '').strip() or None,
                "first_name": row_data.get('first_name', '').strip() or None,
                "last_name": row_data.get('last_name', '').strip() or None,
                "email": row_data.get('email', '').strip() or None,
                "phone": row_data.get('phone', '').strip() or None,
                "is_internal": row_data.get('is_internal', 'false').strip().lower() in ['true', '1', 'wahr']
            }
            # Validate with Pydantic schema before attempting to create
            supplier_pydantic = SupplierCreate(**supplier_create_data)
            supplier_service.create_supplier(db, supplier_in=supplier_pydantic)
            imported_count += 1
        except HTTPException as e_http: # Catch validation errors from SupplierCreate or create_supplier
             errors_log.append({"row": row_number_for_error, "message": f"Validierungsfehler: {e_http.detail}", "data": row_data})
             skipped_count += 1
        except Exception as e_gen: # Catch any other error during processing this row
            errors_log.append({"row": row_number_for_error, "message": f"Allgemeiner Fehler: {str(e_gen)}", "data": row_data})
            skipped_count += 1

    return {"imported_count": imported_count, "skipped_count": skipped_count, "errors": errors_log}


# --- Product Import ---
def import_products_from_csv(db: Session, csv_file_content: bytes) -> Dict[str, Any]:
    rows, header = _read_csv_content(csv_file_content)
    imported_count = 0
    skipped_count = 0
    errors_log: List[Dict[str, Any]] = []

    expected_product_fields = [
        'sku', 'name', 'description', 'supplier_number', 'category_name',
        'tax_rate_name', 'purchase_price', 'selling_price', 'product_type',
        'status', 'entry_date'
    ]
    required_product_fields = [
        'sku', 'name', 'supplier_number', 'category_name',
        'tax_rate_name', 'purchase_price', 'selling_price', 'product_type'
    ]

    if not all(rf in header for rf in required_product_fields):
        missing_headers = [rf for rf in required_product_fields if rf not in header]
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Fehlende Pflichtspalten in der Produkt-CSV: {', '.join(missing_headers)}")

    for i, row_data in enumerate(rows, start=1):
        row_number_for_error = i + 1 # Account for header

        if not all(row_data.get(field, "").strip() for field in required_product_fields):
            missing_vals = [field for field in required_product_fields if not row_data.get(field,"").strip()]
            errors_log.append({"row": row_number_for_error, "message": f"Fehlende Pflichtwerte: {', '.join(missing_vals)}", "data": row_data})
            skipped_count += 1
            continue

        sku_val = row_data['sku'].strip()
        try:
            if product_service.get_product_by_sku(db, sku=sku_val):
                errors_log.append({"row": row_number_for_error, "message": f"SKU '{sku_val}' existiert bereits.", "data": row_data})
                skipped_count += 1
                continue

            supplier = supplier_service.get_supplier_by_number(db, supplier_number=row_data['supplier_number'].strip())
            if not supplier:
                errors_log.append({"row": row_number_for_error, "message": f"Lieferant '{row_data['supplier_number']}' nicht gefunden.", "data": row_data})
                skipped_count += 1
                continue

            category_name_val = row_data['category_name'].strip()
            category = product_category_service.get_product_category_by_name(db, name=category_name_val)
            if not category:
                category_schema = ProductCategoryCreate(name=category_name_val)
                category = product_category_service.create_product_category(db, category_in=category_schema)

            tax_rate_name_val = row_data['tax_rate_name'].strip()
            tax_rate = tax_rate_service.get_tax_rate_by_name(db, name=tax_rate_name_val)
            if not tax_rate:
                errors_log.append({"row": row_number_for_error, "message": f"Steuersatz '{tax_rate_name_val}' nicht gefunden.", "data": row_data})
                skipped_count += 1
                continue

            purchase_price_val = Decimal(row_data['purchase_price'].replace(',', '.'))
            selling_price_val = Decimal(row_data['selling_price'].replace(',', '.'))

            product_type_val_str = row_data['product_type'].upper().strip()
            if product_type_val_str not in ProductTypeEnum.__members__:
                raise ValueError(f"Ungültiger Produkttyp: '{product_type_val_str}'. Erlaubt: {', '.join([pt.value for pt in ProductTypeEnum])}")
            product_type_val = ProductTypeEnum[product_type_val_str]

            status_str_val = row_data.get('status', '').strip().upper()
            product_status_val = ProductStatusEnum[status_str_val] if status_str_val and status_str_val in ProductStatusEnum.__members__ else ProductStatusEnum.IN_STOCK

            entry_date_str_val = row_data.get('entry_date', '').strip()
            entry_date_parsed_val = date.fromisoformat(entry_date_str_val) if entry_date_str_val else date.today()

            product_create_data = ProductCreate(
                sku=sku_val, name=row_data['name'].strip(),
                description=row_data.get('description', '').strip() or None,
                supplier_id=supplier.id, category_id=category.id, tax_rate_id=tax_rate.id,
                purchase_price=purchase_price_val, selling_price=selling_price_val,
                product_type=product_type_val, status=product_status_val, entry_date=entry_date_parsed_val
            )
            product_service.create_product(db, product_in=product_create_data)
            imported_count += 1

        except (ValueError, DecimalInvalidOperation) as ve:
            errors_log.append({"row": row_number_for_error, "message": f"Datenkonvertierungsfehler: {str(ve)}", "data": row_data})
            skipped_count += 1
        except HTTPException as e_http: # Catch validation errors from Pydantic or service layers
            errors_log.append({"row": row_number_for_error, "message": f"Validierungsfehler: {e_http.detail}", "data": row_data})
            skipped_count += 1
        except Exception as e_gen: # Catch any other error
            errors_log.append({"row": row_number_for_error, "message": f"Allgemeiner Fehler: {str(e_gen)}", "data": row_data})
            skipped_count += 1

    return {"imported_count": imported_count, "skipped_count": skipped_count, "errors": errors_log}
