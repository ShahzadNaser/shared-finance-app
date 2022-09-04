import frappe

import json
from erpnext.accounts.doctype.payment_request.payment_request import PaymentRequest
from erpnext.accounts.doctype.payment_entry.payment_entry import get_company_defaults
from frappe.utils import flt, nowdate
from frappe import _, scrub
from erpnext.accounts.utils import get_account_currency
from erpnext.accounts.party import get_party_account
from erpnext.accounts.doctype.journal_entry.journal_entry import get_default_bank_cash_account
from erpnext.accounts.doctype.bank_account.bank_account import get_party_bank_account
from erpnext.accounts.doctype.invoice_discounting.invoice_discounting import get_party_account_based_on_invoice_discounting
from erpnext.accounts.doctype.payment_entry.payment_entry import get_reference_as_per_payment_terms

class CustomPaymentRequest(PaymentRequest):
	def before_save(self, *args, **kwargs):
		if hasattr(super(), "before_save"):
			super().befor_save()

		if self.pay_to_party == 0:
			self.calculate_totals()
		# self.validate_reference_doc()

	def calculate_totals(self):
		self.grand_total = 0
		self.total_of_advance_paid = 0
		self.total_now_being_requested = 0
		for row in self.payment_request_item:
			self.grand_total += row.amount or 0
			self.total_of_advance_paid += row.less_advance_paid or 0
			self.total_now_being_requested += row.now_being_request or 0


	def validate_reference_document(self):

		if self.pay_to_party == 1 and (not self.reference_doctype or not self.reference_name) and len(self.payment_request_reference) == 0:
			frappe.throw(_("To create a Payment Request reference document is required"))
		if self.pay_to_party==0 and len(self.payment_request_item)==0 :
			frappe.throw(_("To create a Payment Request reference payment request items is required"))


		# if self.pay_to_party == 1 and (not self.reference_doctype or not self.reference_name):
		# 	frappe.throw(_("To create a Payment Request reference document is required"))

		# frappe.msgprint(super(PaymentRequest, self))
		# self.validate_reference_document_custom()
		# super(PaymentRequest, self).validate_reference_document()

	# def validate_reference_document_custom(self):

	def validate_currency(self):
		if self.pay_to_party == 1 and self.reference_doctype and self.reference_name:
			ref_doc = frappe.get_doc(self.reference_doctype, self.reference_name)
			if self.payment_account and ref_doc.currency != frappe.db.get_value("Account", self.payment_account, "account_currency"):
				frappe.throw(_("Transaction currency must be same as Payment Gateway currency"))

	def validate_reference_doc(self):
		if self.pay_to_party == 1 and frappe.db.get_value(self.reference_doctype, self.reference_name,"docstatus") != 1:
			frappe.throw("<b>{0}</b> must be submitted.".format(self.reference_name))
	
	def on_submit(self):
		if self.payment_request_type == 'Outward':
			self.db_set('status', 'Initiated')
			return
		elif self.payment_request_type == 'Inward':
			self.db_set('status', 'Requested')

		send_mail = self.payment_gateway_validation() if self.payment_gateway else None
		if self.pay_to_party == 1:
			ref_doc = frappe.get_doc(self.reference_doctype, self.reference_name)
			if (hasattr(ref_doc, "order_type") and getattr(ref_doc, "order_type") == "Shopping Cart") \
				or self.flags.mute_email:
				send_mail = False

			if send_mail:
				self.set_payment_request_url()
				self.send_email()
				self.make_communication_entry()


def on_submit_via_hooks(self, method):
	try:
		if self.pay_to_party == 1:
			# if(self.reference_doctype and self.reference_name):
			PaymentRequest.create_payment_entry = create_payment_entry
			self.create_payment_entry(submit=False)
			# payment_entry = self.create_payment_entry(submit=False)
			# payment_entry.insert(ignore_permissions=True)
		else:
			# if(self.reference_doctype and self.reference_name):
			make_journal_voucher(self.name, self, show_msg=False)
	except Exception as error:
		traceback = frappe.get_traceback()
		frappe.log_error(message=traceback, title="Error While making PE/JE .")
		frappe.throw("Something went wrong please try again.")

def on_cancel(self, method):
	try:
		doc = None
		if self.pay_to_party == 1:
			if frappe.db.exists("Payment Entry",{"reference_no":self.name}):
				doc = frappe.get_doc("Payment Entry",{"reference_no":self.name})
		else:
			je_name = frappe.db.get_value("Journal Entry Account",{"reference_name":self.name}, "parent")
			if je_name:
				doc = frappe.get_doc("Journal Entry",je_name)
		if doc:
			if doc.docstatus == 1:
				doc.cancel()
			elif doc.docstatus == 0:
				doc.delete()

	except Exception as error:
		traceback = frappe.get_traceback()
		frappe.log_error(message=traceback, title="Error While Canceling PE/JE .")
		frappe.throw("Something went wrong please try again.")


@frappe.whitelist()
def make_journal_voucher(pr_name, doc=None, show_msg=True):
	from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import get_accounting_dimensions
	if not doc:
		doc = frappe.get_doc('Payment Request',pr_name)

	company = frappe.defaults.get_defaults().company

	je = frappe.new_doc('Journal Entry')
	je.voucher_type = 'Journal Entry'
	je.posting_date = doc.transaction_date
	je.company =  company 
	je.finance_book = doc.finance_book
	je.cheque_no = doc.name
	je.cheque_date = doc.transaction_date
	je.user_remark = doc.remark_ #'Payment Request'

	dimensions = get_accounting_dimensions()
	for acc in doc.payment_request_item:
		if acc.account:

			total_debit = acc.now_being_request
			total_credit = 0.0
			if acc.now_being_request < 0:
				total_credit = abs(acc.now_being_request)
				total_debit = 0.0

			temp_dict = {
				'account': acc.account,
				'cost_center': acc.cost_center,
				'finance_book': acc.finance_book,
				'reference_name': doc.name,
				'reference_type': 'Payment Request',
				'debit_in_account_currency': total_debit,
				'credit_in_account_currency': total_credit,
				'party_type':acc.party_type,
				'party':acc.party,
				'user_remark': acc.remarks

			}

			# if frappe.db.get_value("Account", acc.account, "account_type") in ["Receivable", "Payable"]:
			# 	if not doc.get("party_type") or not doc.get("party"):
			# 		frappe.throw(_("Party Type and Party is required for Receivable / Payable account {0}").format(acc.account))

			# 	temp_dict["party_type"] = doc.get("party_type")
			# 	temp_dict["party"] = doc.get("party")
			
			for dimension in dimensions:
				if acc.get(dimension):
					temp_dict[dimension] = acc.get(dimension)

			je.append("accounts", temp_dict)


	je.append("accounts", {
		'account': frappe.db.get_value("Mode of Payment Account",
				{"parent": doc.mode_of_payment, "company": company}, "default_account"),
		'cost_center': doc.cost_center,
		'finance_book': doc.finance_book,
		'reference_name': doc.name,
		'reference_type': 'Payment Request',
		'credit_in_account_currency': doc.total_now_being_requested,
		'debit_in_account_currency': 0.0,
		'user_remark': doc.reimbursement_type

	})

	je.insert(ignore_permissions=True)
	je.save()
	# je.submit()
	if show_msg:
		frappe.db.commit()

	if je:	
		doc.reference_jv = je.name
		# doc.flags.ignore_validate = True
		doc.flags.ignore_validate_update_after_submit = True
		doc.save()
		if show_msg:
			frappe.db.commit()
			frappe.msgprint("Journal Entry record successfully created!")
		else:
			return doc
	else:
		return False

@frappe.whitelist()
def make_journal_entries(docnames = None):
	if not docnames:
		return 
	docnames = json.loads(docnames)
	doclist = []
	for name in docnames:
		if frappe.db.exists("Payment Request",{"pay_to_party": True, "name": name}):
			frappe.throw("Pay To Party must be uncheck.")
		doc = make_journal_voucher(name)
		doclist.append(doc)

	return doclist

@frappe.whitelist()
def make_payment_entries(docnames = None):
	if not docnames:
		return 
	docnames = json.loads(docnames)
	doclist = []
	for name in docnames:
		PaymentRequest.create_payment_entry = create_payment_entry
		doc = frappe.get_doc("Payment Request", name)
		payment_entry = doc.create_payment_entry(submit=False)
		payment_entry.finance_book = doc.get("finance_book")
		payment_entry.insert(ignore_permissions=True)
		doclist.append(payment_entry)

	return doclist


def create_payment_entry(self, submit=True):
	"""create entry"""
	frappe.flags.ignore_account_permission = True

	if self.reference_doctype and self.reference_name:
		ref_doc = frappe.get_doc(self.reference_doctype, self.reference_name)
	
		if self.reference_doctype == "Sales Invoice":
			party_account = ref_doc.debit_to
		elif self.reference_doctype == "Purchase Invoice":
			party_account = ref_doc.credit_to
		else:
			party_account = get_party_account("Customer", ref_doc.get("customer"), ref_doc.company)

		party_account_currency = ref_doc.get("party_account_currency") or get_account_currency(party_account)

		bank_amount = self.grand_total
		if party_account_currency == ref_doc.company_currency and party_account_currency != self.currency:
			party_amount = ref_doc.base_grand_total
		else:
			party_amount = self.grand_total

		payment_entry = get_payment_entry(self.reference_doctype, self.reference_name,
			party_amount=party_amount, bank_account=self.payment_account, bank_amount=bank_amount)

		payment_entry.update({
			"reference_no": self.name,
			"reference_date": self.transaction_date,#nowdate(),
			"posting_date": self.transaction_date,
			"finance_book": self.finance_book,
			"remarks": self.remark_ #"Payment Entry against {0} {1} via Payment Request {2}".format(self.reference_doctype,self.reference_name, self.name)
		})
		payment_entry.finance_book = self.finance_book
		if payment_entry.difference_amount:
			company_details = get_company_defaults(ref_doc.company)

			payment_entry.append("deductions", {
				"account": company_details.exchange_gain_loss_account,
				"cost_center": company_details.cost_center,
				"amount": payment_entry.difference_amount
			})

		payment_entry.insert(ignore_permissions=True)
		if submit:
			payment_entry.submit()

		return payment_entry

	else:
		grand_total = 0.0
		references = []
		for row in self.payment_request_reference:
			grand_total += row.allocated_amount or 0
			references.append({
				'reference_doctype':row.reference_doctype,
				'reference_name':row.reference_name,
				'due_date':row.due_date,
				'bill_no':row.bill_no,
				'payment_term':row.payment_term,
				'total_amount':row.total_amount,
				'outstanding_amount':row.outstanding_amount,
				'allocated_amount':row.allocated_amount,
				'exchange_rate':row.exchange_rate
			})

		if (self.party_type == "Customer" or self.party_type == "Student"):
			payment_type = "Receive"
		else:
			payment_type = "Pay"
		mode_of_payment_account = frappe.db.get_value('Mode of Payment Account', {'parent': self.mode_of_payment,'company': self.company}, ['default_account'])	
	
		paid_from = self.party_account if payment_type =="Receive" else mode_of_payment_account
		paid_from_account_currency = frappe.db.get_value('Account',paid_from,'account_currency')
		paid_to = mode_of_payment_account if payment_type =="Receive" else self.party_account
		paid_to_account_currency = frappe.db.get_value('Account',paid_to,'account_currency')

		pe = frappe.get_doc({
			'doctype': 'Payment Entry',
			'company': self.company,
			'payment_type': payment_type,
			'cost_center': self.get("cost_center"),
			'posting_date': self.transaction_date,
			'mode_of_payment' : self.get("mode_of_payment"),
			'party_type': self.party_type,
			'party': self.get("party"),
			'paid_from': paid_from,
			'paid_from_account_currency': paid_from_account_currency,
			'paid_to': paid_to,
			'paid_to_account_currency': paid_to_account_currency,
			'paid_amount': grand_total,
			'base_paid_amount' : grand_total,
			'received_amount': grand_total,
			"reference_no": self.name,
			"reference_date": self.transaction_date,
			"posting_date": self.transaction_date,
			"finance_book": self.finance_book,
			"remarks": self.remark_, #"Payment Entry via Payment Request <b>{0}</b>".format(self.name),
			'references' : references
		})

		pe.setup_party_account_field()
		pe.set_missing_values()
		pe.set_exchange_rate()
		pe.insert(ignore_permissions=True)
		if submit:
			pe.submit()

		return pe

# import frappe
# from frappe import _
# import json


# def custom_validate_reference_document(self):

# 	if self.pay_to_party == 1 and (not self.reference_doctype or not self.reference_name) and len(self.payment_request_reference) == 0:
# 		frappe.throw(_("To create a Payment Request reference document is required"))

# 	if self.pay_to_party == 1 and (not self.reference_doctype or not self.reference_name):
# 		frappe.throw(_("To create a Payment Request reference document is required"))

# 	# frappe.msgprint(super(PaymentRequest, self))
# 	# self.validate_reference_document_custom()
# 	# super(PaymentRequest, self).validate_reference_document()

# # def validate_reference_document_custom(self):

# def custom_validate_currency(self):
# 	if self.pay_to_party == 1 and self.reference_doctype and self.reference_name:
# 		ref_doc = frappe.get_doc(self.reference_doctype, self.reference_name)
# 		if self.payment_account and ref_doc.currency != frappe.db.get_value("Account", self.payment_account, "account_currency"):
# 			frappe.throw(_("Transaction currency must be same as Payment Gateway currency"))

# def custom_on_submit(self):
# 	if self.payment_request_type == 'Outward':
# 		self.db_set('status', 'Initiated')
# 		return
# 	elif self.payment_request_type == 'Inward':
# 		self.db_set('status', 'Requested')

# 	send_mail = self.payment_gateway_validation() if self.payment_gateway else None
# 	if self.pay_to_party == 1:
# 		ref_doc = frappe.get_doc(self.reference_doctype, self.reference_name)
# 		if (hasattr(ref_doc, "order_type") and getattr(ref_doc, "order_type") == "Shopping Cart") \
# 			or self.flags.mute_email:
# 			send_mail = False

# 		if send_mail:
# 			self.set_payment_request_url()
# 			self.send_email()
# 			self.make_communication_entry()

# def make_overrides() -> None:
# 	"""Overrides some of the standard **PaymentRequest** class methods"""
# 	from erpnext.accounts.doctype.payment_request.payment_request import PaymentRequest

# 	PaymentRequest.validate_reference_document = custom_validate_reference_document
# 	PaymentRequest.validate_currency = custom_validate_currency
# 	PaymentRequest.on_submit = custom_on_submit


# def on_submit_via_hooks(self, method):
# 	from erpnext.accounts.doctype.payment_request.payment_request import PaymentRequest

# 	try:
# 		if self.pay_to_party == 1:
# 			# if(self.reference_doctype and self.reference_name):
# 			PaymentRequest.create_payment_entry = create_payment_entry
# 			self.create_payment_entry(submit=False)
# 			payment_entry = self.create_payment_entry(submit=False)
# 			payment_entry.finance_book = self.get("finance_book")
# 			payment_entry.insert(ignore_permissions=True)
# 		else:
# 			# if(self.reference_doctype and self.reference_name):
# 			make_journal_voucher(self.name, self, show_msg=False)
# 	except Exception as error:
# 		traceback = frappe.get_traceback()
# 		frappe.log_error(message=traceback, title="Error While making PE/JE .")
# 		frappe.throw("Something went wrong please try again.")

# def on_cancel(self, method):
# 	try:
# 		doc = None
# 		if self.pay_to_party == 1:
# 			if frappe.db.exists("Payment Entry",{"reference_no":self.name}):
# 				doc = frappe.get_doc("Payment Entry",{"reference_no":self.name})
# 		else:
# 			je_name = frappe.db.get_value("Journal Entry Account",{"reference_name":self.name}, "parent")
# 			if je_name:
# 				doc = frappe.get_doc("Journal Entry",je_name)
# 		if doc:
# 			if doc.docstatus == 1:
# 				doc.cancel()
# 			elif doc.docstatus == 0:
# 				doc.delete()

# 	except Exception as error:
# 		traceback = frappe.get_traceback()
# 		frappe.log_error(message=traceback, title="Error While Canceling PE/JE .")
# 		frappe.throw("Something went wrong please try again.")


# @frappe.whitelist()
# def make_journal_voucher(pr_name, doc=None, show_msg=True):
# 	from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import get_accounting_dimensions
# 	if not doc:
# 		doc = frappe.get_doc('Payment Request',pr_name)

# 	company = frappe.defaults.get_defaults().company

# 	je = frappe.new_doc('Journal Entry')
# 	je.voucher_type = 'Journal Entry'
# 	je.posting_date = doc.transaction_date
# 	je.company =  company 
# 	je.finance_book = doc.finance_book
# 	je.cheque_no = doc.name
# 	je.cheque_date = doc.transaction_date
# 	je.user_remark = 'Payment Request'

# 	dimensions = get_accounting_dimensions()
# 	for acc in doc.payment_request_item:
# 		if acc.account:
# 			temp_dict = {
# 				'account': acc.account,
# 				'cost_center': acc.cost_center,
# 				'finance_book': acc.finance_book,
# 				'reference_name': doc.name,
# 				'reference_type': 'Payment Request',
# 				'debit_in_account_currency': acc.now_being_request,
# 				'credit_in_account_currency': 0.0,
# 				'party_type':acc.party_type,
# 				'party':acc.party

# 			}

# 			# if frappe.db.get_value("Account", acc.account, "account_type") in ["Receivable", "Payable"]:
# 			# 	if not doc.get("party_type") or not doc.get("party"):
# 			# 		frappe.throw(_("Party Type and Party is required for Receivable / Payable account {0}").format(acc.account))

# 			# 	temp_dict["party_type"] = doc.get("party_type")
# 			# 	temp_dict["party"] = doc.get("party")
			
# 			for dimension in dimensions:
# 				if acc.get(dimension):
# 					temp_dict[dimension] = acc.get(dimension)

# 			je.append("accounts", temp_dict)

# 	je.append("accounts", {
# 		'account': frappe.db.get_value("Mode of Payment Account",
# 				{"parent": doc.mode_of_payment, "company": company}, "default_account"),
# 		'cost_center': doc.cost_center,
# 		'finance_book': doc.finance_book,
# 		'reference_name': doc.name,
# 		'reference_type': 'Payment Request',
# 		'credit_in_account_currency': doc.total_now_being_requested,
# 		'debit_in_account_currency': 0.0
# 	})

# 	je.insert(ignore_permissions=True)
# 	je.save()
# 	# je.submit()
# 	if show_msg:
# 		frappe.db.commit()

# 	if je:	
# 		doc.reference_jv = je.name
# 		doc.save()
# 		if show_msg:
# 			frappe.db.commit()
# 			frappe.msgprint("Journal Entry record successfully created!")
# 		else:
# 			return doc
# 	else:
# 		return False

# @frappe.whitelist()
# def make_journal_entries(docnames = None):
# 	if not docnames:
# 		return 
# 	docnames = json.loads(docnames)
# 	doclist = []
# 	for name in docnames:
# 		if frappe.db.exists("Payment Request",{"pay_to_party": True, "name": name}):
# 			frappe.throw("Pay To Party must be uncheck.")
# 		doc = make_journal_voucher(name)
# 		doclist.append(doc)

# 	return doclist

# @frappe.whitelist()
# def make_payment_entries(docnames = None):
# 	if not docnames:
# 		return 
# 	from erpnext.accounts.doctype.payment_request.payment_request import PaymentRequest
# 	docnames = json.loads(docnames)
# 	doclist = []
# 	for name in docnames:
# 		PaymentRequest.create_payment_entry = create_payment_entry
# 		doc = frappe.get_doc("Payment Request", name)
# 		payment_entry = doc.create_payment_entry(submit=False)
# 		payment_entry.finance_book = doc.get("finance_book")
# 		payment_entry.insert(ignore_permissions=True)
# 		doclist.append(payment_entry)

# 	return doclist


# def create_payment_entry(self, submit=True):
# 	"""create entry"""
# 	from frappe.utils import nowdate
# 	from erpnext.accounts.utils import get_account_currency
# 	from jawaerp.override_whitelist.payment_entry import get_payment_entry

# 	frappe.flags.ignore_account_permission = True

# 	ref_doc = frappe.get_doc(self.reference_doctype, self.reference_name)
	
# 	if self.reference_doctype == "Sales Invoice":
# 		party_account = ref_doc.debit_to
# 	elif self.reference_doctype == "Purchase Invoice":
# 		party_account = ref_doc.credit_to
# 	else:
# 		from erpnext.accounts.party import get_party_account
# 		party_account = get_party_account("Customer", ref_doc.get("customer"), ref_doc.company)

# 	party_account_currency = ref_doc.get("party_account_currency") or get_account_currency(party_account)

# 	bank_amount = self.grand_total
# 	if party_account_currency == ref_doc.company_currency and party_account_currency != self.currency:
# 		party_amount = ref_doc.base_grand_total
# 	else:
# 		party_amount = self.grand_total

# 	payment_entry = get_payment_entry(self.reference_doctype, self.reference_name,
# 		party_amount=party_amount, bank_account=self.payment_account, bank_amount=bank_amount)

# 	payment_entry.update({
# 		"reference_no": self.name,
# 		"reference_date": nowdate(),
# 		"remarks": "Payment Entry against {0} {1} via Payment Request {2}".format(self.reference_doctype,
# 			self.reference_name, self.name)
# 	})

# 	if payment_entry.difference_amount:
# 		from erpnext.accounts.doctype.payment_entry.payment_entry import get_company_defaults
# 		company_details = get_company_defaults(ref_doc.company)

# 		payment_entry.append("deductions", {
# 			"account": company_details.exchange_gain_loss_account,
# 			"cost_center": company_details.cost_center,
# 			"amount": payment_entry.difference_amount
# 		})

# 	if submit:
# 		payment_entry.insert(ignore_permissions=True)
# 		payment_entry.submit()

# 	return payment_entry
@frappe.whitelist()
def get_payment_entry(dt, dn, party_amount=None, bank_account=None, bank_amount=None):
	doc = frappe.get_doc(dt, dn)
	if dt in ("Sales Order", "Purchase Order") and flt(doc.per_billed, 2) > 0:
		frappe.throw(_("Can only make payment against unbilled {0}").format(dt))

	if dt in ("Sales Invoice", "Sales Order"):
		party_type = "Customer"
	elif dt in ("Purchase Invoice", "Purchase Order"):
		party_type = "Supplier"
	elif dt in ("Expense Claim", "Employee Advance", "Employee Clearance", "Payroll Entry"):
		party_type = "Employee"
	elif dt in ("Fees"):
		party_type = "Student"

	# party account
	if dt == "Sales Invoice":
		party_account = get_party_account_based_on_invoice_discounting(dn) or doc.debit_to
	elif dt == "Purchase Invoice":
		party_account = doc.credit_to
	elif dt == "Fees":
		party_account = doc.receivable_account
	elif dt == "Employee Advance":
		party_account = doc.advance_account
	elif dt == "Expense Claim":
		party_account = doc.payable_account
	else:
		party_account = get_party_account(party_type, doc.get(party_type.lower()), doc.company)

	if dt not in ("Sales Invoice", "Purchase Invoice"):
		party_account_currency = get_account_currency(party_account)
	else:
		party_account_currency = doc.get("party_account_currency") or get_account_currency(party_account)

	# payment type
	if (dt == "Sales Order" or (dt in ("Sales Invoice", "Fees") and doc.outstanding_amount > 0)) \
			or (dt == "Purchase Invoice" and doc.outstanding_amount < 0):
		payment_type = "Receive"
	else:
		payment_type = "Pay"

	# amounts
	grand_total = outstanding_amount = 0
	if party_amount:
		grand_total = outstanding_amount = party_amount
	elif dt in ("Sales Invoice", "Purchase Invoice"):
		if party_account_currency == doc.company_currency:
			grand_total = doc.base_rounded_total or doc.base_grand_total
		else:
			grand_total = doc.rounded_total or doc.grand_total
		outstanding_amount = doc.outstanding_amount
	elif dt in ("Expense Claim"):
		grand_total = doc.total_sanctioned_amount + doc.total_taxes_and_charges
		outstanding_amount = doc.grand_total \
							 - doc.total_amount_reimbursed
	elif dt == "Employee Advance":
		grand_total = doc.advance_amount
		outstanding_amount = flt(doc.advance_amount) - flt(doc.paid_amount)
	elif dt == "Fees":
		grand_total = doc.grand_total
		outstanding_amount = doc.outstanding_amount
	else:
		if party_account_currency == doc.company_currency:
			grand_total = flt(doc.get("base_rounded_total") or doc.base_grand_total)
		else:
			grand_total = flt(doc.get("rounded_total") or doc.grand_total)
		outstanding_amount = grand_total - flt(doc.advance_paid)

	# bank or cash
	bank = get_default_bank_cash_account(doc.company, "Bank", mode_of_payment=doc.get("mode_of_payment"),
										 account=bank_account)

	if not bank:
		bank = get_default_bank_cash_account(doc.company, "Cash", mode_of_payment=doc.get("mode_of_payment"),
											 account=bank_account)

	paid_amount = received_amount = 0
	if party_account_currency == bank.account_currency:
		paid_amount = received_amount = abs(outstanding_amount)
	elif payment_type == "Receive":
		paid_amount = abs(outstanding_amount)
		if bank_amount:
			received_amount = bank_amount
		else:
			# received_amount = paid_amount * doc.conversion_rate
			# By Dori
			# exclude Expense Claim since there is no conversion_rate field
			if dt not in ("Expense Claim"):
				received_amount = paid_amount * doc.conversion_rate
			else:
				received_amount = paid_amount
	else:
		received_amount = abs(outstanding_amount)
		if bank_amount:
			paid_amount = bank_amount
		else:
			# if party account currency and bank currency is different then populate paid amount as well
			# paid_amount = received_amount * doc.conversion_rate
			# By Dori
			# exclude Expense Claim since there is no conversion_rate field
			if dt not in ("Expense Claim"):
				paid_amount = received_amount * doc.conversion_rate
			else:
				paid_amount = received_amount

	pe = frappe.new_doc("Payment Entry")
	pe.payment_type = payment_type
	pe.company = doc.company
	pe.cost_center = doc.get("cost_center")
	pe.posting_date = nowdate()
	pe.mode_of_payment = doc.get("mode_of_payment")
	pe.party_type = party_type
	pe.party = doc.get(scrub(party_type))
	pe.contact_person = doc.get("contact_person")
	pe.contact_email = doc.get("contact_email")
	pe.ensure_supplier_is_not_blocked()

	pe.paid_from = party_account if payment_type == "Receive" else bank.account
	pe.paid_to = party_account if payment_type == "Pay" else bank.account
	pe.paid_from_account_currency = party_account_currency \
		if payment_type == "Receive" else bank.account_currency
	pe.paid_to_account_currency = party_account_currency if payment_type == "Pay" else bank.account_currency
	pe.paid_amount = paid_amount
	pe.received_amount = received_amount
	pe.letter_head = doc.get("letter_head")

	if pe.party_type in ["Customer", "Supplier"]:
		bank_account = get_party_bank_account(pe.party_type, pe.party)
		pe.set("bank_account", bank_account)
		pe.set_bank_account_data()

	# only Purchase Invoice can be blocked individually
	if doc.doctype == "Purchase Invoice" and doc.invoice_is_blocked():
		frappe.msgprint(_('{0} is on hold till {1}'.format(doc.name, doc.release_date)))
	else:
		if (doc.doctype in ('Sales Invoice', 'Purchase Invoice')
				and frappe.get_value('Payment Terms Template',
									 {'name': doc.payment_terms_template}, 'allocate_payment_based_on_payment_terms')):

			for reference in get_reference_as_per_payment_terms(doc.payment_schedule, dt, dn, doc, grand_total,
																outstanding_amount):
				pe.append('references', reference)
		else:
			pe.append("references", {
				'reference_doctype': dt,
				'reference_name': dn,
				"bill_no": doc.get("bill_no"),
				"due_date": doc.get("due_date"),
				'total_amount': grand_total,
				'outstanding_amount': outstanding_amount,
				'allocated_amount': outstanding_amount
			})

	pe.setup_party_account_field()
	pe.set_missing_values()
	if party_account and bank:
		pe.set_exchange_rate()
		pe.set_amounts()
	return pe
