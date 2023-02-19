import frappe

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

        new_prop = frappe.get_doc({
            "default_value": "0",
            "doc_type": "Journal Entry",
            "docstatus": 0,
            "doctype": "Property Setter",
            "doctype_or_field": "DocField",
            "field_name": "finance_book",
            "modified": "2022-10-16 14:38:31.442080",
            "name": "Payment Request-currency-read_only",
            "property": "read_only",
            "property_type": "Check",
            "value": "0"

        })
        new_prop.insert(ignore_permissions=True, ignore_mandatory=True, ignore_if_duplicate=True)

        frappe.db.commit()
    except:
        pass