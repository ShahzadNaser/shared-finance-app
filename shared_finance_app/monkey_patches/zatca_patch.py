import frappe
from zatca_erpgulf.zatca_erpgulf import tax_error

_original_validate = tax_error.validate_sales_invoice_taxes


def custom_validate_sales_invoice_taxes(doc, event=None):
    settings = frappe.get_single("Omnieast Settings")
    if settings.pass_zatca:
        return
    return _original_validate(doc, event)


tax_error.validate_sales_invoice_taxes = custom_validate_sales_invoice_taxes
