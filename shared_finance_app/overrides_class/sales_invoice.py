import frappe
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice


def _patch_zatca_module():
    """
    Replace validate_sales_invoice_taxes with a wrapper that checks
    frappe.flags.skip_zatca_validation (per-request / thread-local flag).
    Guards against double-patching with a sentinel attribute.
    """
    try:
        import zatca_erpgulf.zatca_erpgulf.tax_error as _mod

        if getattr(_mod, "_patched_by_shared_finance", False):
            return

        _original = _mod.validate_sales_invoice_taxes

        def _patched(doc, event=None):
            if frappe.flags.get("skip_zatca_validation"):
                return
            return _original(doc, event)

        _mod.validate_sales_invoice_taxes = _patched
        _mod._patched_by_shared_finance = True
    except ImportError:
        pass


class CustomSalesInvoice(SalesInvoice):
    """
    Overrides Sales Invoice to apply the ZATCA skip-flag BEFORE Frappe's
    hook composer collects function references — making the bypass
    independent of app installation order.
    """

    def run_method(self, method, *args, **kwargs):
        if method == "before_submit":
            try:
                settings = frappe.get_single("Omnieast Settings")
                if settings.pass_zatca:
                    # Patch the module (idempotent) then set the per-request flag.
                    _patch_zatca_module()
                    frappe.flags.skip_zatca_validation = True
                else:
                    frappe.flags.skip_zatca_validation = False
            except Exception:
                frappe.flags.skip_zatca_validation = False

        return super().run_method(method, *args, **kwargs)
