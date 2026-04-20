import frappe


def before_submit(doc, event=None):
    """
    Set per-request flag so the patched validate_sales_invoice_taxes
    (applied in shared_finance_app/__init__.py at startup) skips
    ZATCA validation when Pass ZATCA is enabled in Omnieast Settings.
    """
    try:
        settings = frappe.get_single("Omnieast Settings")
        frappe.flags.skip_zatca_validation = bool(settings.pass_zatca)
    except Exception:
        frappe.flags.skip_zatca_validation = False
