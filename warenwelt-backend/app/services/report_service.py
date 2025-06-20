from sqlalchemy.orm import Session, joinedload, selectinload
from typing import List, Optional, Dict
from datetime import date, timedelta, datetime
from decimal import Decimal

from app.models.sale_model import Sale, SaleItem, PaymentMethodEnum
from app.models.product_model import Product, ProductTypeEnum # ProductCategory, TaxRate also from product_model if needed
from app.schemas import report_schema as ReportSchema # Alias for clarity
# from app.services import sale_service # Not strictly needed if we replicate/adapt daily summary logic here
from sqlalchemy import func # For sum, count etc.

# --- Daily Summary Report (copied and adapted from sale_service.py for cohesion) ---
# This could also stay in sale_service and be called from here.
# For now, including a version here to make report_service more self-contained for these report types.

def get_daily_sales_summary(db: Session, report_date: date) -> ReportSchema.DailySummaryReport:
    start_datetime = datetime.combine(report_date, datetime.min.time())
    end_datetime = datetime.combine(report_date, datetime.max.time())

    sales_on_date = db.query(Sale).options(
        joinedload(Sale.items).joinedload(SaleItem.product) # Product needed for commission calculation
    ).filter(
        Sale.transaction_time >= start_datetime,
        Sale.transaction_time <= end_datetime
    ).all()

    overall_total_amount = Decimal("0.00")
    overall_transaction_count = len(sales_on_date)
    summary_by_payment_method_dict: Dict[str, Dict[str, any]] = {}
    total_commission_to_suppliers = Decimal("0.00")

    for sale_entry in sales_on_date:
        overall_total_amount += sale_entry.total_amount
        payment_method_str = sale_entry.payment_method.value

        if payment_method_str not in summary_by_payment_method_dict:
            summary_by_payment_method_dict[payment_method_str] = {
                "total_amount": Decimal("0.00"),
                "transaction_count": 0
            }
        summary_by_payment_method_dict[payment_method_str]["total_amount"] += sale_entry.total_amount
        summary_by_payment_method_dict[payment_method_str]["transaction_count"] += 1

        for item in sale_entry.items:
            # SaleItem.commission_amount_at_sale already stores (quantity * product.purchase_price for commission items)
            if item.product and item.product.product_type == ProductTypeEnum.COMMISSION:
                total_commission_to_suppliers += item.commission_amount_at_sale

    summary_list = [
        ReportSchema.DailySalesReportItem( # Using the specific item schema for daily reports
            payment_method=pm,
            total_amount=data["total_amount"],
            transaction_count=data["transaction_count"]
        ) for pm, data in summary_by_payment_method_dict.items()
    ]

    all_pm_values = [e.value for e in PaymentMethodEnum]
    existing_pm_in_summary = [item.payment_method for item in summary_list]
    for pm_value in all_pm_values:
        if pm_value not in existing_pm_in_summary:
            summary_list.append(ReportSchema.DailySalesReportItem(
                payment_method=pm_value, total_amount=Decimal("0.00"), transaction_count=0
            ))
    summary_list.sort(key=lambda x: x.payment_method)

    return ReportSchema.DailySummaryReport(
        report_date=report_date,
        overall_total_amount=overall_total_amount,
        overall_transaction_count=overall_transaction_count,
        summary_by_payment_method=summary_list,
        total_commission_paid_to_suppliers=total_commission_to_suppliers
    )


# --- Period Summary Reports (Weekly/Monthly) ---
def get_period_sales_summary(db: Session, start_date: date, end_date: date, report_type: str) -> ReportSchema.PeriodSummaryReport:
    if start_date > end_date:
        # Or raise HTTPException(status_code=400, detail="Start date cannot be after end date")
        raise ValueError("Start date cannot be after end date for period summary.")

    # Fetch all sales within the period
    sales_in_period = db.query(Sale).options(
        joinedload(Sale.items).joinedload(SaleItem.product) # Ensure product is loaded for commission calculation
    ).filter(
        Sale.transaction_time >= datetime.combine(start_date, datetime.min.time()),
        Sale.transaction_time <= datetime.combine(end_date, datetime.max.time())
    ).all()

    overall_total_amount = Decimal("0.00")
    overall_transaction_count = len(sales_in_period)
    summary_by_payment_method_dict: Dict[str, Dict[str, any]] = {} # Using Dict for intermediary aggregation
    total_commission_to_suppliers = Decimal("0.00")

    for sale_entry in sales_in_period: # Changed 'sale' to 'sale_entry' to avoid conflict with 'Sale' type
        overall_total_amount += sale_entry.total_amount
        payment_method_str = sale_entry.payment_method.value

        if payment_method_str not in summary_by_payment_method_dict:
            summary_by_payment_method_dict[payment_method_str] = {
                "total_amount": Decimal("0.00"),
                "transaction_count": 0
            }
        summary_by_payment_method_dict[payment_method_str]["total_amount"] += sale_entry.total_amount
        summary_by_payment_method_dict[payment_method_str]["transaction_count"] += 1

        for item in sale_entry.items:
            if item.product and item.product.product_type == ProductTypeEnum.COMMISSION:
                total_commission_to_suppliers += item.commission_amount_at_sale

    summary_list = [
        ReportSchema.PeriodSummaryReportItem( # Using the specific item schema for period reports
            payment_method=pm,
            total_amount=data["total_amount"],
            transaction_count=data["transaction_count"]
        ) for pm, data in summary_by_payment_method_dict.items()
    ]

    all_pm_values = [e.value for e in PaymentMethodEnum] # Ensure all payment methods are represented
    existing_pm_in_summary = [item.payment_method for item in summary_list]
    for pm_value in all_pm_values:
        if pm_value not in existing_pm_in_summary:
            summary_list.append(ReportSchema.PeriodSummaryReportItem(
                payment_method=pm_value, total_amount=Decimal("0.00"), transaction_count=0
            ))
    summary_list.sort(key=lambda x: x.payment_method) # Consistent order

    return ReportSchema.PeriodSummaryReport(
        report_type=report_type.upper(), # "WEEKLY" or "MONTHLY"
        start_date=start_date,
        end_date=end_date,
        overall_total_amount=overall_total_amount,
        overall_transaction_count=overall_transaction_count,
        summary_by_payment_method=summary_list,
        total_commission_paid_to_suppliers=total_commission_to_suppliers
    )

# --- Revenue List Report ---
def get_revenue_list_report(db: Session, start_date: date, end_date: date) -> ReportSchema.RevenueListReport:
    if start_date > end_date:
        raise ValueError("Start date cannot be after end date for revenue list report.")

    # Query SaleItem, and join necessary related data (Sale, Product, TaxRate)
    # This fetches all individual sold items in the period.
    sale_items_in_period = db.query(SaleItem).options(
        joinedload(SaleItem.sale).joinedload(Sale.user),
        joinedload(SaleItem.product).joinedload(Product.tax_rate),
        # joinedload(SaleItem.product).joinedload(Product.category), # Uncomment if category name needed
        # joinedload(SaleItem.product).joinedload(Product.supplier) # Uncomment if supplier name needed for item
    ).join(Sale, SaleItem.sale_id == Sale.id)\
    .filter(
        Sale.transaction_time >= datetime.combine(start_date, datetime.min.time()),
        Sale.transaction_time <= datetime.combine(end_date, datetime.max.time())
    ).order_by(Sale.transaction_time, SaleItem.id).all()

    revenue_item_details: List[ReportSchema.RevenueItem] = []
    total_gross_revenue_all_items = Decimal("0.00")

    summary_product_type_agg: Dict[str, Dict[str, any]] = { # Use 'any' for value type flexibility
        pt.value: {"total_revenue": Decimal("0.00"), "total_cost_or_commission": Decimal("0.00"), "item_count": 0}
        for pt in ProductTypeEnum
    }

    for si in sale_items_in_period:
        if not si.product: continue # Should ideally not happen with good data integrity

        gross_revenue_for_line_item = si.price_at_sale * si.quantity # Total revenue for this line item
        total_gross_revenue_all_items += gross_revenue_for_line_item

        cost_or_commission_for_line_item = Decimal("0.00")
        # product.purchase_price is cost for NEW_WARE, and supplier's cut for COMMISSION items.
        # SaleItem.commission_amount_at_sale = product.purchase_price * quantity for COMMISSION items.
        if si.product.product_type == ProductTypeEnum.COMMISSION:
            cost_or_commission_for_line_item = si.commission_amount_at_sale
        elif si.product.product_type == ProductTypeEnum.NEW_WARE:
            cost_or_commission_for_line_item = (si.product.purchase_price or Decimal("0.00")) * si.quantity

        # Update aggregation for summary by product type
        prod_type_str = si.product.product_type.value
        summary_product_type_agg[prod_type_str]["total_revenue"] += gross_revenue_for_line_item
        summary_product_type_agg[prod_type_str]["total_cost_or_commission"] += cost_or_commission_for_line_item
        summary_product_type_agg[prod_type_str]["item_count"] += si.quantity

        # Tax rate details
        tax_rate_percentage = None
        if si.product.tax_rate: # Product should always have a tax_rate linked
            tax_rate_percentage = si.product.tax_rate.rate_percent
        # Note: Actual tax calculation (VAT, differential tax) is complex and would require more logic
        # and potentially dedicated tax service functions. This report provides raw data.

        revenue_item = ReportSchema.RevenueItem(
            product_id=si.product_id,
            product_sku=si.product.sku,
            product_name=si.product.name,
            product_type=prod_type_str,
            quantity_sold=si.quantity,
            price_per_unit_at_sale=si.price_at_sale,
            total_gross_revenue_for_item=gross_revenue_for_line_item,
            purchase_price_per_unit=si.product.purchase_price,
            total_cost_or_commission_for_item=cost_or_commission_for_line_item,
            tax_rate_percentage_at_sale=tax_rate_percentage,
            # Placeholder fields for differential tax would be populated here if logic existed
            sale_id=si.sale_id,
            transaction_number=si.sale.transaction_number,
            sale_transaction_time=si.sale.transaction_time
        )
        revenue_item_details.append(revenue_item)

    return ReportSchema.RevenueListReport(
        report_generated_at=datetime.now(), # Or use UTCnow if timezone consistency is important
        report_period_start_date=start_date,
        report_period_end_date=end_date,
        total_gross_revenue_all_items=total_gross_revenue_all_items,
        total_items_sold=sum(item.quantity_sold for item in revenue_item_details), # Sum of quantities from list
        summary_by_product_type=summary_product_type_agg,
        # aggregated_tax_summary would be calculated by a dedicated tax aggregation function
        revenue_items=revenue_item_details
    )


# --- CSV Export Functions ---
import csv
import io
from typing import Any # For List[Dict[str, Any]]

def _generate_csv_string(header: List[str], data: List[Dict[str, Any]]) -> str:
    """Helper function to generate a CSV string from header and data."""
    output = io.StringIO()
    # Using QUOTE_MINIMAL and allowing dialect to handle numbers without quotes if possible.
    # For DATEV, specific quoting rules might apply. QUOTE_ALL is safer if unsure.
    writer = csv.DictWriter(output, fieldnames=header, delimiter=';', quoting=csv.QUOTE_ALL)
    writer.writeheader()
    for row in data:
        formatted_row = {}
        for key, value in row.items():
            if isinstance(value, date) or isinstance(value, datetime): # Handles both date and datetime
                formatted_row[key] = value.strftime("%d.%m.%Y") # DATEV often expects DD.MM.YYYY for dates
            elif isinstance(value, Decimal):
                # DATEV format usually expects comma as decimal separator
                formatted_row[key] = str(value).replace('.', ',')
            elif value is None:
                formatted_row[key] = "" # Empty string for None values
            else:
                formatted_row[key] = str(value) # Ensure everything else is a string
        writer.writerow(formatted_row)
    return output.getvalue()

def export_daily_sales_summary_csv(db: Session, report_date_in: date) -> str:
    summary_report = get_daily_sales_summary(db, report_date=report_date_in) # report_date_in is the correct param name

    header = ["Datum", "Zahlungsmethode", "Betrag", "Anzahl Transaktionen", "Gesamtumsatz Tag", "Gesamt Transaktionen Tag", "Gesamt Kommissionen an Lieferanten"]
    csv_data: List[Dict[str, Any]] = []

    if not summary_report.summary_by_payment_method and summary_report.overall_transaction_count == 0 :
         csv_data.append({
            "Datum": report_date_in, "Zahlungsmethode": "N/A", "Betrag": Decimal("0.00"),
            "Anzahl Transaktionen": 0, "Gesamtumsatz Tag": Decimal("0.00"),
            "Gesamt Transaktionen Tag": 0, "Gesamt Kommissionen an Lieferanten": Decimal("0.00")
        })
    else:
        for item in summary_report.summary_by_payment_method:
            csv_data.append({
                "Datum": summary_report.report_date,
                "Zahlungsmethode": item.payment_method,
                "Betrag": item.total_amount,
                "Anzahl Transaktionen": item.transaction_count,
                # These are repeated for each line but provide context if lines are separated
                "Gesamtumsatz Tag": summary_report.overall_total_amount,
                "Gesamt Transaktionen Tag": summary_report.overall_transaction_count,
                "Gesamt Kommissionen an Lieferanten": summary_report.total_commission_paid_to_suppliers or Decimal("0.00")
            })

    return _generate_csv_string(header, csv_data)


def export_monthly_sales_summary_csv(db: Session, year: int, month: int) -> str:
    month_start_date = date(year, month, 1)
    if month == 12:
        month_end_date = date(year, month, 31)
    else:
        month_end_date = date(year, month + 1, 1) - timedelta(days=1)

    summary_report = get_period_sales_summary(db, start_date=month_start_date, end_date=month_end_date, report_type="MONTHLY_CSV_EXPORT")

    header = ["Startdatum", "Enddatum", "Zahlungsmethode", "Betrag", "Anzahl Transaktionen", "Gesamtumsatz Monat", "Gesamt Transaktionen Monat", "Gesamt Kommissionen an Lieferanten"]
    csv_data: List[Dict[str, Any]] = []

    if not summary_report.summary_by_payment_method and summary_report.overall_transaction_count == 0:
        csv_data.append({
            "Startdatum": month_start_date, "Enddatum": month_end_date, "Zahlungsmethode": "N/A",
            "Betrag": Decimal("0.00"), "Anzahl Transaktionen": 0,
            "Gesamtumsatz Monat": Decimal("0.00"), "Gesamt Transaktionen Monat": 0,
            "Gesamt Kommissionen an Lieferanten": Decimal("0.00")
        })
    else:
        for item in summary_report.summary_by_payment_method:
            csv_data.append({
                "Startdatum": summary_report.start_date,
                "Enddatum": summary_report.end_date,
                "Zahlungsmethode": item.payment_method,
                "Betrag": item.total_amount,
                "Anzahl Transaktionen": item.transaction_count,
                "Gesamtumsatz Monat": summary_report.overall_total_amount,
                "Gesamt Transaktionen Monat": summary_report.overall_transaction_count,
                "Gesamt Kommissionen an Lieferanten": summary_report.total_commission_paid_to_suppliers or Decimal("0.00")
            })
    return _generate_csv_string(header, csv_data)


# Placeholder for DATEV specific account numbers - these should come from config or a mapping
# These are SKR03 examples and highly simplified.
DATEV_ACCOUNTS_SKR03 = {
    "revenue_new_ware_19": "8400",  # Erlöse 19 % USt
    "revenue_new_ware_7": "8300",   # Erlöse 7 % USt
    "revenue_commission_margin": "8195", # Erlöse aus Vermittlungsprovisionen (beispielhaft, oder spezifisches Konto für Marge)
                                        # Alternativ: Erlöse aus sonstigen Leistungen
    "revenue_used_ware_diff_tax": "8190", # Erlöse nach §25a UStG (Differenzbesteuerung) - Dies wäre das Konto für den vollen Verkaufspreis
                                         # Die USt wird dann auf die Marge gerechnet und separat gebucht.
    "cash_payment": "1000",          # Kasse
    "card_payment_transit": "1360", # Geldtransit (für Kartenzahlungen)
    "voucher_payment": "1740",      # Verbindlichkeiten aus Gutscheinen (wenn Gutschein als Zahlungsmittel)
                                    # Oder Verrechnungskonto Gutscheine
    # Konten für die Umsatzsteuerberechnung bei Differenzbesteuerung
    "vat_on_diff_margin": "1775", # USt. nicht fällig (wenn Marge negativ oder 0) oder entsprechendes USt-Konto
                                # Die tatsächliche USt.-Buchung bei Diffbesteuerung ist komplexer.
}

# This function is a conceptual starting point and needs significant refinement for actual DATEV compliance.
def export_revenue_list_datev_like_csv(db: Session, start_date_in: date, end_date_in: date) -> str:
    revenue_report = get_revenue_list_report(db, start_date=start_date_in, end_date=end_date_in)

    # DATEV Buchungsstapel Format - Kernfelder (stark vereinfacht)
    # Die genauen Spaltennamen und deren Reihenfolge sind entscheidend für DATEV.
    # Referenz: DATEV-Formatbeschreibung für ASCII-Import.
    header = [
        "Umsatz", "Gegenkonto", "Konto", "WKZ", "Belegdatum",
        "Belegfeld 1", "Buchungstext",
        # "KOST1 - Kostenstelle", "KOST2 - Kostenstelle", # Optional
        # "USt-Schlüssel (BU)", "Land USt-ID" # Wichtig für Steuer
    ]
    csv_data: List[Dict[str, Any]] = []

    # This example aggregates sales by payment method and product type for simplicity.
    # A true DATEV export might need one line per Sale, or even more detailed splits.
    # For now, let's create one summary line per Sale, which is still not fully DATEV compliant.

    # Group sale items by their sale_id to process each sale together
    sales_data: Dict[int, List[ReportSchema.RevenueItem]] = {}
    for item in revenue_report.revenue_items:
        if item.sale_id not in sales_data:
            sales_data[item.sale_id] = []
        sales_data[item.sale_id].append(item)

    for sale_id, items_in_sale in sales_data.items():
        if not items_in_sale:
            continue

        # Assume all items in a sale share the same transaction_number and date.
        # Payment method needs to be fetched from the original Sale model.
        # This is inefficient; payment_method should ideally be part of RevenueItem or fetched once per sale.
        original_sale = db.query(Sale).filter(Sale.id == sale_id).first()
        if not original_sale: continue # Should not happen

        # Determine main "Gegenkonto" (cash/card register) based on payment method
        gegenkonto_val = DATEV_ACCOUNTS_SKR03["cash_payment"] # Default
        if original_sale.payment_method == PaymentMethodEnum.CARD:
            gegenkonto_val = DATEV_ACCOUNTS_SKR03["card_payment_transit"]
        elif original_sale.payment_method == PaymentMethodEnum.VOUCHER:
             gegenkonto_val = DATEV_ACCOUNTS_SKR03["voucher_payment"]
        # MIXED payment method would require splitting the sale total, very complex here.

        # For each sale, we might create multiple booking lines if different revenue accounts are hit
        # This simplified version creates one line per product type within the sale, which is still not quite right.
        # A more accurate approach would be one line for Kasse/Bank an diverse Erlöskonten,
        # or one line per actual Erlösbuchung.
        # Let's make one line per item for now to show detail, though this is not typical for summary DATEV export.

        for item in items_in_sale:
            # Determine revenue account ("Konto")
            # This is highly dependent on tax setup (VAT rate, differential tax)
            konto_val = DATEV_ACCOUNTS_SKR03["revenue_new_ware_19"] # Default
            if item.product_type == ProductTypeEnum.NEW_WARE.value:
                # Here, one would check item.tax_rate_percentage_at_sale to pick 8400 (19%) or 8300 (7%) etc.
                if item.tax_rate_percentage_at_sale == Decimal("7.00"):
                     konto_val = DATEV_ACCOUNTS_SKR03["revenue_new_ware_7"]
                else: # Assuming 19% as default for new ware if not 7%
                     konto_val = DATEV_ACCOUNTS_SKR03["revenue_new_ware_19"]
            elif item.product_type == ProductTypeEnum.COMMISSION.value:
                # For commission items, the shop's revenue is the commission itself, not the full sale price.
                # The full price is booked against a liability to the supplier.
                # This model is too simple. If we book full price:
                # konto_val = DATEV_ACCOUNTS_SKR03["revenue_used_ware_diff_tax"] # if diff taxed
                # Or a generic commission revenue account.
                # For now, let's use a placeholder for commission sales.
                # This needs a decision: are we booking gross sales or net commission as revenue?
                # Assuming gross sales for now, with later payout:
                konto_val = DATEV_ACCOUNTS_SKR03.get("revenue_commission_placeholder", "8500") # Placeholder

            csv_data.append({
                "Umsatz": item.total_gross_revenue_for_item, # Gross revenue of the item
                "Gegenkonto": gegenkonto_val,
                "Konto": konto_val,
                "WKZ": "EUR",
                "Belegdatum": item.sale_transaction_time.date(),
                "Belegfeld 1": item.transaction_number, # Sale's transaction number
                "Buchungstext": f"{item.product_name} ({item.product_sku}) S-{item.sale_id}",
                # "USt-Schlüssel (BU)": "??", # Needs logic based on tax_rate and diff. tax
            })

    if not csv_data:
        return _generate_csv_string(header, [])

    return _generate_csv_string(header, csv_data)
