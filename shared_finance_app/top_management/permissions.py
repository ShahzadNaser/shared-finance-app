# Copyright (c) 2026,contributors
# For license information, please see license.txt

"""Top Management Requests (Cash Payment Voucher, Payment Request, Material Request,
Purchase Order) are visible only to Administrator and the Top Management roles.

Works on a site where the custom field does not exist: nothing is hidden there.
"""

import frappe

FIELD = "custom_top_management_request"
TM_ROLES = {"Top Management Requester", "CEO", "Finance Director", "CFO"}
DOCTYPES = ("Cash Payment Voucher", "Payment Request", "Material Request", "Purchase Order")


def has_tm_access(user=None):
	user = user or frappe.session.user
	return user == "Administrator" or bool(TM_ROLES.intersection(frappe.get_roles(user)))


def tm_query_conditions(user=None, doctype=None):
	"""permission_query_conditions: list, report view, link search, counts, get_list."""
	if not doctype or has_tm_access(user) or not frappe.get_meta(doctype).has_field(FIELD):
		return ""

	table = "tab" + doctype.replace("`", "``")
	return f"ifnull(`{table}`.`{FIELD}`, 0) = 0"


def tm_has_permission(doc, ptype=None, user=None, debug=False):
	"""has_permission: open by URL, API, print, email, global search, mapping from the document.

	Frappe denies on any falsy value (None too), so True is returned when not denying; it only means
	"no objection", the role permissions still decide.
	"""
	if doc.get(FIELD) and not has_tm_access(user):
		return False
	return True
