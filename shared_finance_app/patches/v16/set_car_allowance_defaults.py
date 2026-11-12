"""Business Trip car allowance: store the policy defaults in Omnieast Settings.

A Single keeps no value for a field added after it was first saved, so the form would show 0.
Policy: 0.50 SAR per km of the one-way distance, when the distance is more than 200 km."""

import frappe

DEFAULTS = {"car_allowance_rate": 0.5, "car_allowance_min_km": 200}


def execute():
	for field, value in DEFAULTS.items():
		if frappe.db.get_value("Singles", {"doctype": "Omnieast Settings", "field": field}, "value", order_by=None) is None:
			frappe.db.set_single_value("Omnieast Settings", field, value)
