# Copyright (c) 2026, mesa_safd@hotmail.com and Contributors
# See license.txt

"""ISS-2026-00110: Cash Payment Voucher from an approved Business Trip.

The employee and leaves are built here (inserted without their own validations) and every test is
rolled back, so nothing stays on the site.
"""

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from shared_finance_app.shared_finance_app import business_trip as bt

COMPANY = "Omni East Company"
LOCAL, OVERSEAS = "Local With KSA", "Overseas"

# Full Diem rows as they are in the omnieast Travel Policy
POLICIES = {
	LOCAL: [
		{"min_grade": "0", "max_grade": "2", "amount": 130},
		{"min_grade": "5", "max_grade": "6", "amount": 390},
		{"min_grade": "11", "max_grade": "12", "amount": 780},
		{"min_grade": "13", "max_grade": "above", "amount": 975},
	],
	OVERSEAS: [
		{"min_grade": "0", "max_grade": "2", "amount": 0},
		{"min_grade": "5", "max_grade": "6", "amount": 520},
		{"min_grade": "11", "max_grade": "12", "amount": 975},
		{"min_grade": "13", "max_grade": "above", "amount": 1170},
	],
}

# Thu 17 - Sat 19 Sep 2026: 3 calendar days, though Fri/Sat are not leave days
FROM_DATE, TO_DATE = "2026-09-17", "2026-09-19"


class TestBusinessTripCPV(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		cls.department = frappe.db.get_value("Department", {"company": COMPANY, "is_group": 0}, "name")
		cls.branch = frappe.db.get_value("Branch", {}, "name")
		cls.employee = "_T-BT-EMP-1"
		frappe.get_doc(
			{
				"doctype": "Employee",
				"name": cls.employee,
				"first_name": "Test",
				"employee_name": "Test Business Traveller",
				"company": COMPANY,
				"status": "Active",
				"gender": "Male",
				"date_of_birth": "1990-01-01",
				"date_of_joining": "2020-01-01",
				"department": cls.department,
				"branch": cls.branch,
				"grade": "Grade 9" if frappe.db.exists("Employee Grade", "Grade 9") else None,
			}
		).db_insert()

	def setUp(self):
		frappe.set_user("Administrator")
		frappe.db.savepoint("bt_cpv_test")
		self.addCleanup(frappe.db.rollback, save_point="bt_cpv_test")
		frappe.clear_messages()

	# Per diem
	# --------

	def test_parse_grade(self):
		self.assertEqual(bt.parse_grade("Grade 9"), 9)
		self.assertEqual(bt.parse_grade("9"), 9)
		self.assertEqual(bt.parse_grade("Grade 13"), 13)
		self.assertIsNone(bt.parse_grade(None))
		self.assertIsNone(bt.parse_grade("Manager"))

	def test_rate_lookup(self):
		cases = {
			("Grade 1", LOCAL): 130,
			("Grade 1", OVERSEAS): 0,
			("Grade 5", LOCAL): 390,
			("Grade 6", OVERSEAS): 520,
			("Grade 11", LOCAL): 780,
			("Grade 12", OVERSEAS): 975,
			("Grade 13", LOCAL): 975,
			("Grade 20", OVERSEAS): 1170,
			("Grade 3", LOCAL): 0,  # no row for 3-4 in this list
			(None, LOCAL): 0,  # no grade: no rate (not the 0-2 band)
			("Grade 9", None): 0,
		}
		for (grade, travel_type), rate in cases.items():
			self.assertEqual(
				bt.get_per_diem_rate(grade, travel_type, POLICIES.get(travel_type, [])), rate, (grade, travel_type)
			)

	def test_rate_from_site_travel_policy(self):
		if not frappe.db.exists("DocType", "Travel Policy"):
			self.skipTest("Travel Policy is not installed on this site")

		expected = frappe.db.get_value(
			"Travel Policy",
			{"min_grade": "9", "travel_type": LOCAL, "diem_type": bt.FULL_DIEM},
			"amount",
		)
		if expected is None:
			self.skipTest("No Travel Policy row for grade 9")
		self.assertEqual(bt.get_per_diem_rate("Grade 9", LOCAL), expected)

	# Voucher
	# -------

	def test_mapping(self):
		leave = make_leave(self.employee, department=self.department, custom_location=self.branch)
		cpv = bt.make_cpv_from_leave_application(leave.name)
		rate = bt.get_per_diem_rate("Grade 9", LOCAL)

		self.assertTrue(cpv.is_new())
		self.assertEqual(cpv.company, COMPANY)
		self.assertEqual(cpv.party_type, "Employee")
		self.assertEqual(cpv.pay_to, self.employee)
		self.assertEqual(cpv.party_name, "Test Business Traveller")
		self.assertEqual(cpv.department, self.department)
		self.assertEqual(cpv.location, self.branch)
		self.assertEqual(cpv.cost_center, frappe.get_cached_value("Company", COMPANY, "cost_center"))
		self.assertEqual(cpv.currency, frappe.get_cached_value("Company", COMPANY, "default_currency"))
		self.assertEqual(cpv.auto_create_jv, 1)
		self.assertFalse(cpv.mode_of_payment)
		self.assertEqual(cpv.custom_leave_application, leave.name)
		self.assertEqual(cpv.total, rate * 3)  # calendar days

		self.assertEqual(len(cpv.cash_payment_voucher_account), 1)
		row = cpv.cash_payment_voucher_account[0]
		self.assertEqual(row.charge_to, "Employee")
		self.assertEqual(row.employee, self.employee)
		self.assertEqual(row.net_amount, rate * 3)
		self.assertEqual(row.gross_amount, rate * 3)
		self.assertEqual(row.cost_center, cpv.cost_center)
		self.assertEqual(row.department, self.department)
		self.assertEqual(row.branch, self.branch)
		self.assertFalse(row.ledger_account)
		self.assertFalse(row.item)
		self.assertEqual(
			row.description,
			f"BT for {self.employee} Test Business Traveller - 3 days (2 nights) from 17-09-2026 to 19-09-2026 "
			f"(3 per diem × {bt.format_amount(rate)} SR)",
		)
		self.assertEqual(cpv.description, row.description)

	def test_no_rate_opens_with_zero(self):
		leave = make_leave(self.employee, department=self.department, custom_travel_type=OVERSEAS, custom_grade=None)
		with patch.object(bt, "get_per_diem_rate", return_value=0):
			cpv = bt.make_cpv_from_leave_application(leave.name)

		self.assertEqual(cpv.total, 0)
		self.assertEqual(cpv.cash_payment_voucher_account[0].net_amount, 0)
		self.assertTrue(any("Enter the Amount" in str(m) for m in frappe.message_log))

	def test_saves_with_employee_row(self):
		"""Charge To Employee with the employee set saves, also where Employee Clearance does not exist."""
		leave = make_leave(self.employee, department=self.department)
		cpv = bt.make_cpv_from_leave_application(leave.name)
		cpv.insert()

		self.assertEqual(cpv.cash_payment_voucher_account[0].employee, self.employee)
		self.assertEqual(cpv.workflow_state, "Draft")
		# the voucher's own before_save writes the title, as for the vouchers made by hand
		self.assertTrue(cpv.custom_title.startswith(f"{cpv.total:,.2f} SAR - BT for {self.employee}"), cpv.custom_title)

	def test_one_voucher_per_trip(self):
		leave = make_leave(self.employee, department=self.department)
		first = bt.make_cpv_from_leave_application(leave.name).insert()

		self.assertRaises(frappe.ValidationError, bt.make_cpv_from_leave_application, leave.name)

		second = frappe.copy_doc(first, ignore_no_copy=False)  # as the form's Duplicate does
		self.assertFalse(second.custom_leave_application)  # Duplicate does not carry the link
		second.custom_leave_application = leave.name
		self.assertRaises(frappe.ValidationError, second.insert)

		first.db_set("docstatus", 2)  # cancelled: a new one may be made
		bt.make_cpv_from_leave_application(leave.name)

	def test_button_conditions(self):
		approved = make_leave(self.employee, department=self.department)
		self.assertEqual(bt.get_cpv_status(approved.name), {"can_create": True})

		for values in (
			{"leave_type": "Annual Leave"},
			{"docstatus": 0, "status": "Open", "workflow_state": "Draft"},
			{"workflow_state": "Department Head Approved"},
		):
			leave = make_leave(self.employee, department=self.department, **values)
			self.assertTrue(bt.get_create_errors(leave), values)
			self.assertRaises(frappe.ValidationError, bt.make_cpv_from_leave_application, leave.name)

		with patch.object(bt.frappe, "has_permission", side_effect=lambda doctype, *a, **k: doctype != bt.CPV):
			self.assertTrue(bt.get_create_errors(approved))

		cpv = bt.make_cpv_from_leave_application(approved.name).insert()
		self.assertEqual(bt.get_cpv_status(approved.name), {"cpv": cpv.name})

	def test_leave_cancel_blocked_by_voucher(self):
		leave = make_leave(self.employee, department=self.department)
		bt.validate_leave_cancel(leave)  # no voucher yet

		bt.make_cpv_from_leave_application(leave.name).insert()
		self.assertRaises(frappe.ValidationError, bt.validate_leave_cancel, leave)

	def test_long_name_fits_row(self):
		name = "Abdulrahman Mohammed Abdullah Saleh Al Qahtani Al Dosari Al Shammari"
		leave = frappe._dict(employee="100001", employee_name=name, from_date=FROM_DATE, to_date=TO_DATE)
		full = bt.get_description(leave, 3, 975)
		row = bt.get_row_description(leave, 3, 975, full)

		self.assertGreater(len(full), bt.ROW_DESCRIPTION_LENGTH)
		self.assertLessEqual(len(row), bt.ROW_DESCRIPTION_LENGTH)
		self.assertIn("Abdulrahman Al Shammari", row)
		self.assertIn("per diem × 975 SR", row)


def make_leave(employee, **values):
	"""An approved Business Trip (inserted as it is after the workflow's final approval)."""
	leave = frappe.get_doc(
		{
			"doctype": "Leave Application",
			"name": f"_T-BT-LA-{frappe.generate_hash(length=6)}",
			"employee": employee,
			"employee_name": "Test Business Traveller",
			"company": COMPANY,
			"leave_type": bt.BUSINESS_TRIP,
			"from_date": FROM_DATE,
			"to_date": TO_DATE,
			"total_leave_days": 1,
			"posting_date": FROM_DATE,
			"status": "Approved",
			"workflow_state": "Approved",
			"docstatus": 1,
			"custom_grade": "Grade 9",
			"custom_travel_type": LOCAL,
			**values,
		}
	)
	leave.db_insert()
	return leave
