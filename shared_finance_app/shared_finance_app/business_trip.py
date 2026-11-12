# Copyright (c) 2026, mesa_safd@hotmail.com and contributors
# For license information, please see license.txt

"""Cash Payment Voucher for an approved Business Trip.

A Business Trip is a Leave Application with Leave Type "Business Trip". Once it is approved, the
"Create CPV" button opens a new, unsaved Cash Payment Voucher filled in like the BT vouchers Finance
writes by hand (per diem from the omnieast Travel Policy). Finance reviews it and saves it; nothing
is saved here.

Per diem: Half Diem when the company books the hotel ("Hotel Booked by Company" = Yes), else Full
Diem, paid per night away (to date - from date); a same-day trip is paid one diem.
Car allowance: worked out on the leave (set_car_allowance) and paid as a second voucher row.

The app is also installed on sites without omnieast (no Travel Policy, no BT fields on the leave),
so every lookup checks that its DocType / field exists.
"""

import re

import frappe
from frappe import _
from frappe.model.workflow import get_workflow_name
from frappe.utils import cint, date_diff, flt, get_link_to_form, getdate, today

BUSINESS_TRIP = "Business Trip"
APPROVED = "Approved"
CPV = "Cash Payment Voucher"
LINK_FIELD = "custom_leave_application"
FULL_DIEM = "Full Diem"
HALF_DIEM = "Half Diem"
HOTEL_FIELD = "custom_hotel_required"  # omnieast: "Hotel Booked by Company" (Yes / No)
# omnieast car allowance fields; rate and minimum distance in Omnieast Settings
MODE_FIELD = "custom_mode_of_travel"
VEHICLE_FIELD = "custom_company_vehicle_provided"
KM_FIELD = "custom_one_way_distance_km"
CAR_FIELD = "custom_car_allowance"
BY_CAR = "By Car"
SETTINGS = "Omnieast Settings"
CAR_ALLOWANCE_DEFAULTS = {"car_allowance_rate": 0.5, "car_allowance_min_km": 200}  # the travel policy
ROW_DESCRIPTION_LENGTH = 140  # Cash Payment Voucher Account.description is a Data field
NAME_PARTICLES = {"al", "el", "bin", "bint", "abu"}


@frappe.whitelist()
def get_cpv_status(leave_application):
	"""For the Leave Application button: the linked voucher, or whether one can be created."""
	if not frappe.has_permission("Leave Application", "read", leave_application):
		return {}

	cpv = get_linked_cpv(leave_application)
	if cpv:
		return {"cpv": cpv}

	leave = frappe.get_doc("Leave Application", leave_application)
	return {"can_create": not get_create_errors(leave)}


@frappe.whitelist()
def make_cpv_from_leave_application(leave_application):
	"""A new, unsaved Cash Payment Voucher for an approved Business Trip."""
	frappe.has_permission("Leave Application", "read", leave_application, throw=True)
	leave = frappe.get_doc("Leave Application", leave_application)

	errors = get_create_errors(leave)
	if errors:
		frappe.throw("<br>".join(errors), title=_("Cannot Create Cash Payment Voucher"))

	employee = frappe.db.get_value(
		"Employee",
		leave.employee,
		["name", "employee_name", "department", "branch", *employee_optional_fields()],
		as_dict=True,
	)
	company_cost_center, currency = frappe.get_cached_value(
		"Company", leave.company, ["cost_center", "default_currency"]
	)

	department = leave.department or employee.department
	cost_center = get_cost_center(employee, department, leave.company) or company_cost_center
	location = get_location(leave, employee)
	grade = leave.get("custom_grade") or employee.get("grade")
	travel_type = leave.get("custom_travel_type")
	diem_type = get_diem_type(leave)
	policy = get_travel_policy(grade, travel_type, diem_type)
	basis = frappe._dict(
		days=date_diff(leave.to_date, leave.from_date) + 1,
		paid_days=get_paid_days(leave.from_date, leave.to_date),
		rate=flt(policy.amount) if policy else 0,
		diem_type=diem_type,
	)
	per_diem = basis.rate * basis.paid_days
	description = get_description(leave, basis)
	car_allowance = flt(leave.get(CAR_FIELD))
	total = per_diem + car_allowance

	cpv = frappe.new_doc(CPV)
	cpv.update(
		{
			"company": leave.company,
			"posting_date": today(),
			"party_type": "Employee",
			"pay_to": leave.employee,
			"party_name": leave.employee_name or employee.employee_name,
			"department": department,
			"location": location,
			"cost_center": cost_center,
			"currency": currency,
			"auto_create_jv": 1,
			"mode_of_payment": None,
			"description": description
			+ (_(" + car allowance {0} SR").format(format_amount(car_allowance)) if car_allowance else ""),
			LINK_FIELD: leave.name,
		}
	)
	row = {
		"charge_to": "Employee",
		"employee": leave.employee,
		"vat_percent": 0,
		"vat_amount": 0,
		"cost_center": cost_center,
		"department": department,
		"branch": location,
	}
	cpv.append(
		"cash_payment_voucher_account",
		{
			**row,
			"net_amount": per_diem,
			"gross_amount": per_diem,
			"description": get_row_description(leave, basis, description),
		},
	)
	if car_allowance:
		cpv.append(
			"cash_payment_voucher_account",
			{
				**row,
				"net_amount": car_allowance,
				"gross_amount": car_allowance,
				"description": get_car_allowance_description(leave, car_allowance),
			},
		)
	cpv.total = cpv.net_amount = total
	cpv.total_vat = 0

	if not per_diem:
		if policy:
			# the policy exists with 0, e.g. grades 0-4 have no Overseas per diem
			message = _("Grade {0} is not eligible for per diem on {1} trips (Travel Policy {2}).").format(
				frappe.bold(grade), frappe.bold(_(travel_type)), get_link_to_form("Travel Policy", policy.name)
			)
		else:
			message = _("No per diem rate was found for this trip (grade {0}, {1}).").format(
				frappe.bold(grade or _("not set")), frappe.bold(travel_type or _("travel type not set"))
			)
		frappe.msgprint(
			message + " " + _("The per diem row opens with 0; enter the amount if one applies."),
			title=_("Enter the Amount"),
			indicator="orange",
		)

	return cpv


def get_create_errors(leave):
	"""Why a voucher cannot be created for this leave (empty when it can)."""
	errors = []
	if not frappe.get_meta(CPV).has_field(LINK_FIELD):
		return [_("Cash Payment Voucher is not linked to leaves on this site yet (run bench migrate).")]
	if not frappe.has_permission(CPV, "create"):
		errors.append(_("You are not allowed to create a Cash Payment Voucher."))
	if leave.leave_type != BUSINESS_TRIP:
		errors.append(_("Leave {0} is not a Business Trip.").format(leave.name))
	if leave.docstatus != 1 or not is_approved(leave):
		errors.append(_("Business Trip {0} is not approved yet.").format(leave.name))
	if leave.leave_type == BUSINESS_TRIP and not get_diem_type(leave):
		errors.append(_("Hotel Booked by Company (Yes / No) is not set on Business Trip {0}.").format(leave.name))

	cpv = get_linked_cpv(leave.name)
	if cpv:
		errors.append(_("Cash Payment Voucher {0} already exists for this Business Trip.").format(
			get_link_to_form(CPV, cpv)
		))
	return errors


def is_approved(leave):
	if leave.status != APPROVED:
		return False

	workflow = get_workflow_name("Leave Application")
	if not workflow:
		return True

	state_field = frappe.get_cached_value("Workflow", workflow, "workflow_state_field")
	return leave.get(state_field) == APPROVED


def get_linked_cpv(leave_application, exclude=None):
	"""The voucher already made for this leave (any state except cancelled)."""
	if not leave_application or not frappe.get_meta(CPV).has_field(LINK_FIELD):
		return None

	filters = {LINK_FIELD: leave_application, "docstatus": ["!=", 2]}
	if exclude:
		filters["name"] = ["!=", exclude]
	return frappe.db.get_value(CPV, filters, "name")


def validate_leave_cancel(doc, method=None):
	"""Leave Application before_cancel: a voucher in progress would no longer save once its leave is cancelled."""
	cpv = get_linked_cpv(doc.name)
	if cpv:
		frappe.throw(
			_(
				"Cash Payment Voucher {0} was created for this Business Trip. Cancel or delete it first, then cancel the leave."
			).format(get_link_to_form(CPV, cpv)),
			title=_("Cash Payment Voucher Exists"),
		)


# Per diem
# --------


def parse_grade(grade):
	"""The grade number of an Employee Grade such as "Grade 9" or "9"; None when there is none."""
	match = re.search(r"\d+", str(grade or ""))
	return cint(match.group()) if match else None


def grade_in_range(grade_number, min_grade, max_grade):
	"""Travel Policy ranges are Data fields; the top one ends in "above"."""
	if not str(min_grade or "").strip().isdigit():
		return False

	if str(max_grade or "").strip().lower() == "above":
		return grade_number >= cint(min_grade)

	if not str(max_grade or "").strip().isdigit():
		return False

	return cint(min_grade) <= grade_number <= cint(max_grade)


def match_policy(policies, grade_number):
	"""The Travel Policy row whose grade range covers the grade."""
	if grade_number is None:
		return None

	for policy in policies:
		if grade_in_range(grade_number, policy.get("min_grade"), policy.get("max_grade")):
			return policy
	return None


def get_diem_type(leave):
	"""Half Diem when the company books the hotel, Full Diem when it does not; None while it is not set.

	Sites without the omnieast field pay Full Diem."""
	if not frappe.get_meta("Leave Application").has_field(HOTEL_FIELD):
		return FULL_DIEM
	return {"Yes": HALF_DIEM, "No": FULL_DIEM}.get(leave.get(HOTEL_FIELD))


def get_paid_days(from_date, to_date):
	"""Per diem is paid per night away; a same-day trip is paid one diem."""
	return max(date_diff(to_date, from_date), 1)


def get_travel_policy(grade, travel_type, diem_type=FULL_DIEM, policies=None):
	"""The Travel Policy row for the grade, travel type and diem type; None when there is none."""
	grade_number = parse_grade(grade)
	if grade_number is None or not travel_type or not diem_type:
		return None

	if policies is None:
		if not frappe.db.exists("DocType", "Travel Policy"):
			return None
		policies = frappe.get_all(
			"Travel Policy",
			filters={"travel_type": travel_type, "diem_type": diem_type},
			fields=["name", "min_grade", "max_grade", "amount"],
			order_by="name asc",
		)

	return match_policy(policies, grade_number)


def get_per_diem_rate(grade, travel_type, diem_type=FULL_DIEM, policies=None):
	"""Per diem amount for the grade, travel type and diem type; 0 when there is no Travel Policy for it."""
	policy = get_travel_policy(grade, travel_type, diem_type, policies)
	return flt(policy.get("amount")) if policy else 0


# Car allowance
# -------------


def get_car_allowance_settings():
	"""Rate per km and minimum one-way distance from Omnieast Settings; the policy values when not set."""
	values = {}
	for field, default in CAR_ALLOWANCE_DEFAULTS.items():
		value = None
		if frappe.db.exists("DocType", SETTINGS):
			value = frappe.db.get_value("Singles", {"doctype": SETTINGS, "field": field}, "value", order_by=None)
		values[field] = flt(value) if value not in (None, "") else default
	return frappe._dict(rate=values["car_allowance_rate"], min_km=values["car_allowance_min_km"])


def calculate_car_allowance(mode_of_travel, company_vehicle, one_way_km, settings=None):
	"""(amount, why) for a Business Trip.

	Paid when the employee travels by car (no flight), the company does not provide the vehicle and
	the one-way distance is more than the minimum: one-way km × rate."""
	settings = settings or get_car_allowance_settings()
	km = flt(one_way_km)

	if mode_of_travel != BY_CAR:
		return 0, _("Car allowance is paid only for trips by car.")
	if company_vehicle == "Yes":
		return 0, _("No car allowance: the company provides the vehicle.")
	if company_vehicle != "No":
		return 0, _("Set Company Vehicle Provided.")
	if km <= settings.min_km:
		return 0, _("No car allowance: it is paid only when the one-way distance is more than {0} km.").format(
			format_amount(settings.min_km)
		)

	amount = flt(km * settings.rate, 2)
	return amount, _("{0} km one way × {1} SR = {2} SR").format(
		format_amount(km), format_amount(settings.rate), format_amount(amount)
	)


@frappe.whitelist()
def get_car_allowance(mode_of_travel=None, company_vehicle=None, one_way_km=None):
	"""For the Leave Application form: the amount and why, while the trip is being filled in."""
	amount, note = calculate_car_allowance(mode_of_travel, company_vehicle, one_way_km)
	return {"amount": amount, "note": note}


def set_car_allowance(doc, method=None):
	"""Leave Application validate: the Car Allowance follows the trip (omnieast fields)."""
	if not frappe.get_meta("Leave Application").has_field(CAR_FIELD):
		return

	amount = 0
	if doc.leave_type == BUSINESS_TRIP:
		amount = calculate_car_allowance(doc.get(MODE_FIELD), doc.get(VEHICLE_FIELD), doc.get(KM_FIELD))[0]
	doc.set(CAR_FIELD, amount)


def get_car_allowance_description(leave, amount):
	"""The voucher row for the car allowance: distance and the rate it was worked out with."""
	km = flt(leave.get(KM_FIELD))
	if not km:
		return _("Car allowance - Business Trip {0}").format(leave.name)
	return _("Car allowance - {0} km one way × {1} SR (Business Trip {2})").format(
		format_amount(km), format_amount(amount / km), leave.name
	)


# Header values
# -------------


def employee_optional_fields():
	"""HRMS / omnieast fields that may not exist on every site."""
	meta = frappe.get_meta("Employee")
	return [fieldname for fieldname in ("payroll_cost_center", "grade") if meta.has_field(fieldname)]


def get_cost_center(employee, department, company):
	"""Employee payroll cost center, else the department's; only a ledger cost center of the company."""
	candidates = [employee.get("payroll_cost_center")]
	if department and frappe.get_meta("Department").has_field("payroll_cost_center"):
		candidates.append(frappe.db.get_value("Department", department, "payroll_cost_center"))

	for cost_center in candidates:
		if cost_center and frappe.db.get_value(
			"Cost Center", cost_center, ["company", "is_group"], as_dict=True
		) == {"company": company, "is_group": 0}:
			return cost_center
	return None


def get_location(leave, employee):
	for branch in (leave.get("custom_location"), employee.branch):
		if branch and frappe.db.exists("Branch", branch):
			return branch
	return None


def get_description(leave, basis, employee_name=None):
	"""Same wording as the BT vouchers Finance writes by hand, with the per diem basis.

	basis: days (calendar), paid_days, rate, diem_type."""
	nights = basis.days - 1
	diem = _("Half Diem - hotel by company") if basis.diem_type == HALF_DIEM else _("Full Diem")
	return _(
		"BT for {employee} {employee_name} - {days} {days_label} ({nights} {nights_label}) from {from_date} to {to_date} ({paid_days} × {rate} SR {diem})"
	).format(
		employee=leave.employee,
		employee_name=employee_name or leave.employee_name or "",
		days=basis.days,
		days_label=_("days") if basis.days != 1 else _("day"),
		nights=nights,
		nights_label=_("nights") if nights != 1 else _("night"),
		from_date=getdate(leave.from_date).strftime("%d-%m-%Y"),
		to_date=getdate(leave.to_date).strftime("%d-%m-%Y"),
		paid_days=basis.paid_days,
		rate=format_amount(basis.rate),
		diem=diem,
	)


def get_row_description(leave, basis, description):
	"""The row's Remarks hold 140 characters: shorten a long name (first and last word) before cutting."""
	if len(description) > ROW_DESCRIPTION_LENGTH:
		words = (leave.employee_name or "").split()
		if len(words) > 2:
			# keep the family name's particle: "Abdulrahman ... Al Shammari" -> "Abdulrahman Al Shammari"
			last = words[-2:] if words[-2].lower() in NAME_PARTICLES and len(words) > 3 else words[-1:]
			description = get_description(leave, basis, employee_name=" ".join([words[0], *last]))

	if len(description) > ROW_DESCRIPTION_LENGTH:
		description = description[: ROW_DESCRIPTION_LENGTH - 1] + "…"
	return description


def format_amount(amount):
	amount = flt(amount, 2)
	return f"{amount:.0f}" if amount == int(amount) else f"{amount:.2f}"
