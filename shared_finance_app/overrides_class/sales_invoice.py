import frappe


def _patch_zatca_module():
    """
    Patch zatca_erpgulf's validate_sales_invoice_taxes at import time so it
    respects the per-request frappe.flags.skip_zatca_validation flag.
    Thread-safe: frappe.flags is stored on frappe.local (per-request thread-local).
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


# Patch once when this module is first imported.
_patch_zatca_module()


def before_submit(doc, event=None):
    """
    Read the global Pass ZATCA flag from Omnieast Settings.
    If enabled, ZATCA validation is skipped for this request.
    """
    settings = frappe.get_single("Omnieast Settings")
    frappe.flags.skip_zatca_validation = bool(settings.pass_zatca)
