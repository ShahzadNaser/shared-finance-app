import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

# (fieldname, property, value) applied to Payment Request (PWA) on every migrate.
# NOTE: Payment Request Property Setters are synced from custom/payment_request.json
# (sync_on_migrate), which runs before this hook. Add new setters there, not here.
PAYMENT_REQUEST_PROPERTIES = (("currency", "read_only", "0"),)


def after_migrate():
	# Each step runs on its own so one failure cannot skip the others,
	# and failures go to Error Log instead of being silently ignored.
	for fieldname, prop, value in PAYMENT_REQUEST_PROPERTIES:
		existing = frappe.db.get_value(
			"Property Setter",
			{"doc_type": "Payment Request", "field_name": fieldname, "property": prop},
			"value",
		)
		if existing == value:
			continue  # already applied; re-creating would delete + re-insert it

		_run(
			f"Payment Request {fieldname}.{prop}",
			make_property_setter,
			"Payment Request",
			fieldname,
			prop,
			value,
			"Check",
			validate_fields_for_doctype=False,
		)

	_run(
		"Payment Request in_create",
		frappe.db.set_value,
		"DocType",
		"Payment Request",
		"in_create",
		0,
	)

	frappe.clear_cache(doctype="Payment Request")


def _run(title, fn, *args, **kwargs):
	try:
		fn(*args, **kwargs)
		frappe.db.commit()
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title=f"shared_finance_app after_migrate: {title}")
		print(f"shared_finance_app after_migrate failed: {title} (see Error Log)")
