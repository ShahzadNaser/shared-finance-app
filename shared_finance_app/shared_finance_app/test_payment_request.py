# Copyright (c) 2026, mesa_safd@hotmail.com and Contributors
# See license.txt

"""ISS-2026-00155: Payment Request (PWA) without a reference document.

Documents are built in memory and only validated. Where the site has no submitted Purchase Invoice
(ToLeave), a stand-in one is inserted and rolled back, so nothing stays on the site.
"""

from unittest.mock import patch

import frappe
from erpnext.accounts.doctype.payment_request.payment_request import PaymentRequest
from frappe.tests import IntegrationTestCase
from frappe.utils import today

EXISTING_AMOUNT = "erpnext.accounts.doctype.payment_request.payment_request.get_existing_payment_request_amount"


class TestPaymentRequestReference(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		frappe.db.savepoint("pr_reference_test")
		self.addCleanup(frappe.db.rollback, save_point="pr_reference_test")
		self.mode_of_payment = frappe.db.get_value("Mode of Payment", {"enabled": 1}, "name")
		self.company = frappe.db.get_value("Company", {}, "name")

	def make_pr(self, **kwargs):
		values = {
			"doctype": "Payment Request",
			"payment_request_type": "Outward",
			"company": self.company,
			"mode_of_payment": self.mode_of_payment,
			"currency": "SAR",
			"grand_total": 100,
		}
		values.update(kwargs)
		return frappe.get_doc(values)

	def test_no_reference_with_items(self):
		pr = self.make_pr(pay_to_party=0, payment_request_item=[{"amount": 100, "now_being_request": 100}])
		pr.set("__islocal", 1)  # as on insert
		pr.validate()
		self.assertEqual(pr.status, "Draft")

	def test_no_reference_with_reference_rows(self):
		pr = self.make_pr(
			pay_to_party=1,
			payment_request_reference=[
				{"reference_doctype": "Purchase Invoice", "reference_name": "ACC-PINV-TEST", "allocated_amount": 100}
			],
		)
		pr.validate()

	def test_no_reference_still_validates(self):
		# the checks that don't need a reference document still run
		pr = self.make_pr(pay_to_party=0, grand_total=0, payment_request_item=[{"amount": 0}])
		self.assertRaises(frappe.ValidationError, pr.validate)

		pr = self.make_pr(pay_to_party=0)
		self.assertRaises(frappe.ValidationError, pr.validate)

	def test_no_reference_before_submit(self):
		pr = self.make_pr(pay_to_party=0, payment_request_item=[{"amount": 100}])
		pr.before_submit()
		self.assertEqual(pr.outstanding_amount, 100)
		self.assertEqual(pr.status, "Initiated")

	def get_purchase_invoice(self):
		pi = frappe.db.get_value(
			"Purchase Invoice",
			{"docstatus": 1, "outstanding_amount": [">", 0]},
			["name", "company", "supplier", "currency", "outstanding_amount"],
			as_dict=1,
		)
		return pi or self.make_stand_in_purchase_invoice()

	def make_stand_in_purchase_invoice(self):
		"""A submitted invoice with an outstanding amount, inserted without its own validations."""
		currency = frappe.get_cached_value("Company", self.company, "default_currency") or "SAR"
		pi = frappe.get_doc(
			{
				"doctype": "Purchase Invoice",
				"name": f"_T-PR-PINV-{frappe.generate_hash(length=6)}",
				"company": self.company,
				"supplier": "_T-PR-Supplier",
				"posting_date": today(),
				"currency": currency,
				"party_account_currency": currency,
				"conversion_rate": 1,
				"grand_total": 500,
				"outstanding_amount": 500,
				"docstatus": 1,
			}
		)
		pi.db_insert()
		return frappe._dict(
			name=pi.name, company=pi.company, supplier=pi.supplier, currency=currency, outstanding_amount=500
		)

	def make_referenced_pr(self, pi, **kwargs):
		values = {
			"pay_to_party": 1,
			"reference_doctype": "Purchase Invoice",
			"reference_name": pi.name,
			"company": pi.company,
			"currency": pi.currency,
			"party_type": "Supplier",
			"party": pi.supplier,
			"grand_total": 1,
		}
		values.update(kwargs)
		return self.make_pr(**values)

	def test_reference_runs_standard_checks(self):
		if not hasattr(PaymentRequest, "validate_reference_company"):
			self.skipTest("This ERPNext version has no reference company check (added in 16.52)")
		pi = self.get_purchase_invoice()
		pr = self.make_referenced_pr(pi, company="_Test Wrong Company")
		self.assertRaisesRegex(frappe.ValidationError, "does not match the company", pr.validate)

	def test_reference_amount(self):
		pi = self.get_purchase_invoice()

		with patch(EXISTING_AMOUNT, return_value=0) as existing:
			self.make_referenced_pr(pi).validate()
		self.assertEqual(existing.call_args.args[0].name, pi.name)

		# requested before + this one more than the invoice
		with patch(EXISTING_AMOUNT, return_value=pi.outstanding_amount):
			pr = self.make_referenced_pr(pi)
			self.assertRaisesRegex(frappe.ValidationError, "cannot be greater than", pr.validate)
