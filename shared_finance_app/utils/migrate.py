import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

def after_migrate():

    try:

        new_prop = frappe.get_doc({
            "default_value": "0",
            "doc_type": "Payment Request",
            "docstatus": 0,
            "doctype": "Property Setter",
            "doctype_or_field": "DocField",
            "field_name": "currency",
            "modified": "2022-10-16 14:38:31.442080",
            "name": "Payment Request-currency-read_only",
            "property": "read_only",
            "property_type": "Check",
            "value": "0"

        })
        new_prop.insert(ignore_permissions=True, ignore_mandatory=True, ignore_if_duplicate=True)

        # new_prop = frappe.get_doc({
        #     "default_value": "0",
        #     "doc_type": "Journal Entry",
        #     "docstatus": 0,
        #     "doctype": "Property Setter",
        #     "doctype_or_field": "DocField",
        #     "field_name": "finance_book",
        #     "modified": "2022-10-16 14:38:31.442080",
        #     "name": "Payment Request-currency-read_only",
        #     "property": "read_only",
        #     "property_type": "Check",
        #     "value": "0"

        # })
        # new_prop.insert(ignore_permissions=True, ignore_mandatory=True, ignore_if_duplicate=True)

        # PWA is a standalone document (not created from a reference), so the user must be
        # able to pick the Company; core ERPNext makes it read-only and not mandatory.
        for prop, value in (("read_only", "0"), ("reqd", "1")):
            make_property_setter(
                "Payment Request", "company", prop, value, "Check", validate_fields_for_doctype=False
            )

        frappe.db.set_value("DocType", "Payment Request", "in_create", 0)
        frappe.db.commit()
        
        # Force clear structural cache
        frappe.clear_cache(doctype="Payment Request")
        
    except:
        pass