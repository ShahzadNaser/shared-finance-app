import frappe


def _patch_zatca_module():
    """
    Patch zatca_erpgulf's validate_sales_invoice_taxes at import time so it
    respects the per-request frappe.flags.skip_zatca_validation flag.
    This is thread-safe because frappe.flags is stored on frappe.local
    (thread-local storage), so each request has its own copy of the flag.
    """
    try:
        import zatca_erpgulf.zatca_erpgulf.tax_error as _tax_error

        _original = _tax_error.validate_sales_invoice_taxes

        def _patched_validate(doc, event=None):
            if frappe.flags.get("skip_zatca_validation"):
                return
            return _original(doc, event)

        _tax_error.validate_sales_invoice_taxes = _patched_validate
    except ImportError:
        pass


# Patch once when this module is first imported (i.e. when the first
# Sales Invoice before_submit hook fires).
_patch_zatca_module()


def before_submit(doc, event=None):
    """
    Set frappe.flags.skip_zatca_validation for this request if the
    'Pass ZATCA' checkbox is ticked on the Sales Invoice.

    This hook is registered in shared_finance_app and runs before
    zatca_erpgulf's hook because shared_finance_app appears earlier
    in the installed-apps list.
    """
    frappe.flags.skip_zatca_validation = bool(doc.get("custom_pass_zatca"))
