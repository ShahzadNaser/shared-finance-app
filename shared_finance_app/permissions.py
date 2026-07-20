import frappe
from frappe import _


def has_permission_cpv(doc, user=None, permission_type=None):
    if "Finance Support" in frappe.get_roles (frappe.session.user):
        return 

    if doc.get("department") == 'Finance Support - OMATRA':
        return False
    return 

def permission_query_conditions_cpv(user=None):
    if "Finance Support" in frappe.get_roles (frappe.session.user):
        return 
    
    return f"(ifnull(`tabCash Payment Voucher`.department, '')='' or `tabCash Payment Voucher`.department != 'Finance Support - OMATRA')"

def has_permission_pwa(doc, user=None, permission_type=None):
    if "Finance Support" in frappe.get_roles (frappe.session.user):
        return 

    if doc.get("department") == 'Finance Support - OMATRA':
        return False
    return 

def permission_query_conditions_pwa(user=None):
    if "Finance Support" in frappe.get_roles (frappe.session.user):
        return 
    
    return f"(ifnull(`tabPayment Request`.department, '')='' or `tabPayment Request`.department != 'Finance Support - OMATRA')"
