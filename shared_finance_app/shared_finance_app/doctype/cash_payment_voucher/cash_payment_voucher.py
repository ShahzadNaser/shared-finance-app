# -*- coding: utf-8 -*-
# Copyright (c) 2021, mesa_safd@hotmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import datetime
import frappe
from frappe.utils import money_in_words
from frappe.model.document import Document
from jawaerp import update_next_state
import erpnext
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import get_accounting_dimensions
from frappe.utils import flt, getdate, add_days
from frappe import _ 
import json
class CashPaymentVoucher(Document):

	def before_save(self):
		# update_next_state(self)
		# total = 0
		# for item in self.cash_payment_voucher_account:
		# 	total += item.gross_amount

		# self.total = total
		self.total_amount_in_words = money_in_words(self.total)
		self.calculate_total()
 	# self.updat_row_cost_center()

	# def updat_row_cost_center(self):
	# 	if self.cost_center:
	# 		for row in self.cash_payment_voucher_account:
	# 			row.cost_center
	def before_submit(self):
		self.calculate_total()

	def calculate_total(self, ret=False):
		total_vat = 0.0
		gross_amount = 0.0
		net_amount = 0.0
  
		for row in self.cash_payment_voucher_account:
			if row.charge_to=='Employee' and row.employee:

				total_salary_slip=frappe.db.sql(""" select ifnull(sum(net_pay),0) from `tabSalary Slip` 
				                                       where docstatus=1 and employee='{0}' """.format(row.employee))
				if len(total_salary_slip)>0:
					total_salary_slip=total_salary_slip[0][0]
				else:
					total_salary_slip=0.0

				total_employee_clearnce=frappe.db.sql(""" select ifnull(sum(deserve_amount),0) from `tabEmployee Clearance`
				                                          where docstatus=1 and employee='{0}' """.format(row.employee))
				if len(total_employee_clearnce)>0:
					total_employee_clearnce=total_employee_clearnce[0][0]
				else:
					total_employee_clearnce=0.0

				row.paid_amount=total_salary_slip+total_employee_clearnce
				print("Total salary slip {0}".format(total_salary_slip))
				print("Total clearnce {0}".format(total_employee_clearnce))

				total_cpv=frappe.db.sql(""" select ifnull(sum(c.net_amount),0) from `tabCash Payment Voucher` cpv,
				`tabCash Payment Voucher Account` c
				  where cpv.docstatus=1 and c.parent=cpv.name and  c.employee='{0}'
				   """.format(row.employee))

				if len(total_cpv)>0:
					total_cpv=total_cpv[0][0]
				else:
					total_cpv=0.0
				print("Total CPV {0}".format(total_cpv))
				row.balance_amount=row.paid_amount-total_cpv








			if flt(row.vat_amount):
				total_vat += flt(row.vat_amount)
			else:
				if flt(row.vat_percent):	
					row.vat_amount = flt(row.net_amount) * (flt(row.vat_percent) / 100)
					total_vat += flt(row.vat_amount)
			gross_amount += flt(row.gross_amount)
			net_amount += flt(row.net_amount)

		if ret:
			return total_vat

		if total_vat:
			self.total_vat = flt(total_vat)

		if gross_amount:
			self.total = flt(gross_amount)

		if net_amount:
			self.net_amount = flt(net_amount)

	def on_submit(self):
		if not self.mode_of_payment or not self.finance_book or not self.cost_center:
			frappe.throw("Mode of Payment, Finance book or Cost Center should not be blank")

		if self.auto_create_jv == 1:
			self.make_non_department_jv()
			self.make_department_jv()

		# if frappe.db.get_single_value('JawaHR Settings', 'auto_salary_from_cpv'):
		# 	self.create_additional_salaries()

		# Calculate and update total_vat if it is not calculated.
		if not self.total_vat:
			total_vat = self.calculate_total(True)
			if total_vat:
				frappe.db.set_value("Cash Payment Voucher", self.name, "total_vat", flt(total_vat))

	def create_additional_salaries(self) -> None:
		"""Creates an Additional Salary for rows that have item which are `Employee Advance`"""
		salary_component = frappe.get_value("Salary Component", {"is_cpv": 1})
		# payroll_date1 = self.posting_date + datetime.timedelta(days=30)
		payroll_date = add_days(getdate(self.posting_date), -30)

		for i, row in enumerate(self.cash_payment_voucher_account):
			if not frappe.get_value("Item", row.item, "is_employee_advance"):
				continue
			elif not row.get("employee"):
				frappe.throw(_("Row {}: Employee field is mandatory for Employee Advance Items").format(i + 1))

			if not salary_component:
				frappe.throw(_("Row {}: Please check 'Is CPV' field in a Salary Component").format(i + 1))

			self.create_additional_salary_for_row(row, salary_component, payroll_date, self.company)

	def create_additional_salary_for_row(self, row, salary_component, payroll_date, company):
		"""Creates an Additional Salary for an employee"""
		additional_salary_dict = {
			"doctype": "Additional Salary",
			"amount": row.gross_amount,
			"salary_component": salary_component,
			"payroll_date": payroll_date,
			"company": company,
			"employee": row.employee,
			"overwrite_salary_structure_amount": 1,
			"deduct_full_tax_on_selected_payroll_date": 0,
			"sector": frappe.get_value("Employee", row.employee, "sector")
		}
		doc = frappe.get_doc(additional_salary_dict)
		doc.insert()
		doc.submit()
		return doc

	def make_non_department_jv(self):
		accounting_dimensions = get_accounting_dimensions() or []
		accounts = []
		if self.party_type != "Department":
			if frappe.db.get_value('Mode of Payment Account', {'parent': self.mode_of_payment,'company': self.company}, ['default_account']):
				if self.total > 0.0:
					total = 0.0
					vat_accounts = {}
					for d in self.cash_payment_voucher_account:
						if d.ledger_account and d.gross_amount > 0.0:
							total += flt(d.gross_amount)
							debit_entry = ({
							'account': d.ledger_account,
							"party_type": self.party_type if not d.employee else "Employee",
							"party": self.pay_to if self.party_type !="Employee" else d.employee,
							'branch': self.location,
							'debit_in_account_currency': flt(d.net_amount),
							'credit_in_account_currency': 0.0,
							'cost_center' : d.cost_center,
							'finance_book' : self.finance_book
							})

							for dimension in accounting_dimensions:
								debit_entry.update({dimension: d.get(dimension)})

							accounts.append(debit_entry)	
							if d.vat_5:
								if d.vat_5 not in vat_accounts:
									from erpnext.stock.get_item_details import get_item_tax_map
									tax_map = get_item_tax_map(self.company,d.vat_5,as_json=False)
									vat_entry = dict(debit_entry)

									for tax_type in tax_map:
										vat_entry["account"] = str(tax_type)

									vat_entry["debit_in_account_currency"] = flt(flt(d.gross_amount) - flt(d.net_amount))							
									vat_accounts[d.vat_5] = vat_entry
								else:
									vat_accounts[d.vat_5]["debit_in_account_currency"] += flt(flt(d.gross_amount) - flt(d.net_amount))

					for account in vat_accounts:
						accounts.append(vat_accounts[account])

					accounts.append(self.update_accounting_dimensions({
					'account': frappe.db.get_value('Mode of Payment Account', {'parent': self.mode_of_payment,'company': self.company}, ['default_account']),
					'credit_in_account_currency': flt(total),
					'debit_in_account_currency': 0.0,
					'branch': self.location,
					'cost_center' : self.cost_center, 
					'finance_book' : self.finance_book
					}, accounting_dimensions))
					self.total =  flt(total)
					self.net_amount = flt(total)

					journal_entry = frappe.get_doc({
					'doctype': 'Journal Entry',
					'company': self.company,
					'cheque_no': self.name,
					'posting_date': self.posting_date,
					'cheque_date': self.posting_date,
					'accounts': accounts,
					'finance_book': self.finance_book
					})
					journal_entry.insert(ignore_permissions=True,ignore_mandatory=True)
					frappe.msgprint("New Journal Entry Created In Draft Mode",title='Success')

			else:
				frappe.throw("No Default Account Found For Mode Of Payment : "+ self.mode_of_payment,title='Accounts Not Set')


	def make_department_jv(self):
		accounting_dimensions = get_accounting_dimensions() or []
		accounts_department  = []
		if self.party_type == "Department":
			if frappe.db.get_value('Mode of Payment Account', {'parent': self.mode_of_payment,'company': self.company}, ['default_account']):
				if self.total > 0.0:
					total = 0.0
					vat_accounts = {}
					for d in self.cash_payment_voucher_account:
						if d.ledger_account and d.gross_amount > 0.0:
							total += flt(d.gross_amount)
							debit_entry = ({
							'account': d.ledger_account,
							'debit_in_account_currency': flt(d.net_amount),
							"party_type": self.party_type if not d.employee else "Employee",
							"party": self.pay_to if not d.employee else d.employee,
							'credit_in_account_currency': 0.0,
							'department': self.pay_to,
							'branch': self.location,
							'cost_center' : self.cost_center,
							'finance_book' : self.finance_book,
							'reference_type':'Cash Payment Voucher',
							'reference_name':self.name

							})

							for dimension in accounting_dimensions:
								debit_entry.update({dimension: d.get(dimension)})

							accounts_department.append(debit_entry)
							if d.vat_5:
								if d.vat_5 not in vat_accounts:
									from erpnext.stock.get_item_details import get_item_tax_map
									tax_map = get_item_tax_map(self.company,d.vat_5,as_json=False)
									vat_entry = dict(debit_entry)
									for tax_type in tax_map:
										vat_entry["account"] = str(tax_type)

									vat_entry["debit_in_account_currency"] = flt(flt(d.gross_amount) - flt(d.net_amount))							
									vat_accounts[d.vat_5] = vat_entry
								else:
									vat_accounts[d.vat_5]["debit_in_account_currency"] += flt(flt(d.gross_amount) - flt(d.net_amount))

					for account in vat_accounts:
						accounts_department.append(vat_accounts[account])
								
					accounts_department.append(self.update_accounting_dimensions({
					'account': frappe.db.get_value('Mode of Payment Account', {'parent': self.mode_of_payment,'company': self.company}, ['default_account']),
					'credit_in_account_currency': flt(total) ,
					'debit_in_account_currency': 0.0,
					'department': self.pay_to,
					'branch': self.location,
					'cost_center' : self.cost_center,
					'finance_book' : self.finance_book
					}, accounting_dimensions))

					self.total =  flt(total)
					self.net_amount = flt(total)

					journal_entry = frappe.get_doc({
					'doctype': 'Journal Entry',
					'company': self.company,
					'cheque_no': self.name,
					'posting_date': self.posting_date,
					'cheque_date': self.posting_date,
					'cost_center' : self.cost_center,
					'finance_book': self.finance_book,
					'accounts': accounts_department,
					})
					journal_entry.insert(ignore_permissions=True,ignore_mandatory=True)
					frappe.msgprint("New Journal Entry Created In Draft Mode",title='Success')

			else:
				frappe.throw("No Default Account Found For Mode Of Payment : "+ self.mode_of_payment,title='Accounts Not Set')

	def update_accounting_dimensions(self, row, accounting_dimensions):
		for dimension in accounting_dimensions:
			row.update({dimension: self.get(dimension)})		
		return row	

	def on_cancel(self):
		jv = frappe.get_list('Journal Entry', filters={'cheque_no': self.name}, fields=['name'])
		for i in jv:
			if i:
				ec = frappe.get_doc("Journal Entry",i)
				if ec.docstatus == 1:
					ec.flags.ignore_permissions=True
					ec.cancel()
				if ec.docstatus == 0:
					ec = frappe.get_doc("Journal Entry",i)
					ec.flags.ignore_permissions=True
					ec.delete()	

	

	




@frappe.whitelist()
def getTax_Percent(item_tax_template):
	tax_percent = frappe.db.sql("""select sum(tax_rate) from `tabItem Tax Template Detail` where parent = %s;""",(item_tax_template))
	return tax_percent[0][0] if tax_percent else 0

@frappe.whitelist()
def getParty_Name(party,party_type):
	if party and party_type == 'Customer':
		return frappe.db.get_value("Customer", party, "customer_f_name")
	elif party and party_type == 'Supplier':
		return frappe.db.get_value("Supplier", party, "supplier_name")	
	elif party and party_type == 'Employee':
		return frappe.db.get_value("Employee", party, "employee_name")
	elif party and party_type == 'Department':
		return frappe.db.get_value("Department", party, "department_name")	


## api for auto fetch ledger_account when department selected 
@frappe.whitelist()
def getDept_Account(party_name):	
	return frappe.db.get_value("Department", {"department_name":party_name}, "account")	



@frappe.whitelist()
def make_journal_entries(docnames = None):
	if not docnames:
		return 
	docnames = json.loads(docnames)
	doclist = []
	accounts = []
	for doc in docnames:
		journal_entry = frappe.db.get_value("Cash Payment Voucher", doc, ["company", "name", "posting_date", "cost_center", "finance_book", "party_name", "pay_to", "location", "cost_center", "net_amount"])
		
		ledger_account = frappe.db.get_value("Department", {"department_name":journal_entry[5]}, "account")
		accounts.append({
			'account': ledger_account,
			'credit_in_account_currency': 0.0 ,
			'debit_in_account_currency':journal_entry[9] ,
			'department': journal_entry[6],
			'branch':journal_entry[7],
			'cost_center' : journal_entry[3],
			'finance_book' : journal_entry[4]
		})

	 
		journal_entry = frappe.get_doc({
			'doctype': 'Journal Entry',
			'company': journal_entry[0],
			'cheque_no': journal_entry[1],
			'posting_date': journal_entry[2],
			'cheque_date': journal_entry[2],
			'cost_center' : journal_entry[3],
			'finance_book': journal_entry[4], 
			'voucher_type': "Journal Entry",
			'accounts': accounts,

		})
		
		journal_entry.flags.ignore_mandatory = 1
		journal_entry.flags.ignore_permissions = 1
		journal_entry.insert(ignore_permissions=True)
		journal_entry.submit()	

	return doclist

# @frappe.whitelist()
# def make_multiple_journal_entries(docnames = None):
# 	if not docnames:
# 		return 

# 	docnames = json.loads(docnames)
# 	doclist = []
# 	for name in docnames:
# 		doc = make_journal_voucher(name)
# 		doclist.append(doc)

# 	return doclist

# @frappe.whitelist()
# def make_journal_voucher(cpv_name, doc=None, show_msg=True):
# 	from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import get_accounting_dimensions
# 	if not doc:
# 		cpv = frappe.get_doc('Cash Payment Voucher',cpv_name) 

# 	accounting_dimensions = get_accounting_dimensions() or []
# 	accounts = []
# 	if cpv.party_type != "Department" and not frappe.db.exists("Journal Entry", {'cheque_no':cpv.name}):
# 		if frappe.db.get_value('Mode of Payment Account', {'parent': cpv.mode_of_payment,'company': cpv.company}, ['default_account']):
# 			if cpv.total > 0.0:
# 				total = 0.0
# 				vat_accounts = {}
# 				for d in cpv.cash_payment_voucher_account:
# 					if d.ledger_account and d.gross_amount > 0.0:
# 						total += flt(d.gross_amount)
# 						debit_entry = ({
# 						'account': d.ledger_account,
# 						"party_type": cpv.party_type,
# 						"party": cpv.pay_to,
# 						'branch': cpv.location,
# 						'debit_in_account_currency': flt(d.net_amount),
# 						'credit_in_account_currency': 0.0,
# 						'cost_center' : d.cost_center,
# 						'finance_book' : cpv.finance_book
# 						})

# 						for dimension in accounting_dimensions:
# 							debit_entry.update({dimension: d.get(dimension)})

# 						accounts.append(debit_entry)	
# 						if d.vat_5:
# 							if d.vat_5 not in vat_accounts:
# 								from erpnext.stock.get_item_details import get_item_tax_map
# 								tax_map = get_item_tax_map(cpv.company,d.vat_5,as_json=False)
# 								vat_entry = dict(debit_entry)

# 								for tax_type in tax_map:
# 									vat_entry["account"] = str(tax_type)
# 								vat_entry["debit_in_account_currency"] = flt(flt(d.gross_amount) - flt(d.net_amount))							
# 								vat_accounts[d.vat_5] = vat_entry
# 							else:
# 								vat_accounts[d.vat_5]["debit_in_account_currency"] += flt(flt(d.gross_amount) - flt(d.net_amount))

# 				for account in vat_accounts:
# 					accounts.append(vat_accounts[account])

# 				accounts.append(cpv.update_accounting_dimensions({
# 				'account': frappe.db.get_value('Mode of Payment Account', {'parent': cpv.mode_of_payment,'company': cpv.company}, ['default_account']),
# 				'credit_in_account_currency': flt(total),
# 				'debit_in_account_currency': 0.0,
# 				'branch': cpv.location,
# 				'cost_center' : cpv.cost_center, 
# 				'finance_book' : cpv.finance_book
# 				}, accounting_dimensions))
# 				cpv.total =  flt(total)
# 				cpv.net_amount = flt(total)

# 				journal_entry = frappe.get_doc({
# 				'doctype': 'Journal Entry',
# 				'company': cpv.company,
# 				'cheque_no': cpv.name,
# 				'posting_date': cpv.posting_date,
# 				'cheque_date': cpv.posting_date,
# 				'accounts': accounts,
# 				'finance_book': cpv.finance_book
# 				})
# 				journal_entry.insert(ignore_permissions=True,ignore_mandatory=True)
# 				frappe.msgprint("New Journal Entry Created In Draft Mode",title='Success')

# 		else:
# 			frappe.throw("No Default Account Found For Mode Of Payment : "+ cpv.mode_of_payment,title='Accounts Not Set')


# 	accounts_department  = []
# 	if cpv.party_type == "Department" and not frappe.db.exists("Journal Entry", {'cheque_no':cpv.name}):
# 		if frappe.db.get_value('Mode of Payment Account', {'parent': cpv.mode_of_payment,'company': cpv.company}, ['default_account']):
# 			if cpv.total > 0.0:
# 				total = 0.0
# 				vat_accounts = {}
# 				for d in cpv.cash_payment_voucher_account:
# 					if d.ledger_account and d.gross_amount > 0.0:
# 						total += flt(d.gross_amount)
# 						debit_entry = ({
# 						'account': d.ledger_account,
# 						'debit_in_account_currency': flt(d.net_amount),
# 						'credit_in_account_currency': 0.0,
# 						'department': cpv.pay_to,
# 						'branch': cpv.location,
# 						'cost_center' : cpv.cost_center,
# 						'finance_book' : cpv.finance_book
# 						})

# 						for dimension in accounting_dimensions:
# 							debit_entry.update({dimension: d.get(dimension)})

# 						accounts_department.append(debit_entry)
# 						if d.vat_5:
# 							if d.vat_5 not in vat_accounts:
# 								from erpnext.stock.get_item_details import get_item_tax_map
# 								tax_map = get_item_tax_map(cpv.company,d.vat_5,as_json=False)
# 								vat_entry = dict(debit_entry)
# 								for tax_type in tax_map:
# 									vat_entry["account"] = str(tax_type)
# 								vat_entry["debit_in_account_currency"] = flt(flt(d.gross_amount) - flt(d.net_amount))							
# 								vat_accounts[d.vat_5] = vat_entry
# 							else:
# 								vat_accounts[d.vat_5]["debit_in_account_currency"] += flt(flt(d.gross_amount) - flt(d.net_amount))

# 				for account in vat_accounts:
# 					accounts_department.append(vat_accounts[account])
								
# 				accounts_department.append(cpv.update_accounting_dimensions({
# 				'account': frappe.db.get_value('Mode of Payment Account', {'parent': cpv.mode_of_payment,'company': cpv.company}, ['default_account']),
# 				'credit_in_account_currency': flt(total) ,
# 				'debit_in_account_currency': 0.0,
# 				'department': cpv.pay_to,
# 				'branch': cpv.location,
# 				'cost_center' : cpv.cost_center,
# 				'finance_book' : cpv.finance_book
# 				}, accounting_dimensions))

# 				cpv.total =  flt(total)
# 				cpv.net_amount = flt(total)

# 				journal_entry = frappe.get_doc({
# 				'doctype': 'Journal Entry',
# 				'company': cpv.company,
# 				'cheque_no': cpv.name,
# 				'posting_date': cpv.posting_date,
# 				'cheque_date': cpv.posting_date,
# 				'cost_center' : cpv.cost_center,
# 				'finance_book': cpv.finance_book,
# 				'accounts': accounts_department,
# 				})
# 				journal_entry.insert(ignore_permissions=True,ignore_mandatory=True)
# 				frappe.msgprint("New Journal Entry Created In Draft Mode",title='Success')

# 		else:
# 			frappe.throw("No Default Account Found For Mode Of Payment : "+ cpv.mode_of_payment,title='Accounts Not Set')		

@frappe.whitelist()
def make_journal_voucher(docnames = None, show_msg=True):
	from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import get_accounting_dimensions
	accounting_dimensions = get_accounting_dimensions() or []
	accounts = []
	if docnames == None:
		frappe.throw("No Cash payment voucher found to create Journal Entry")

	if docnames:
		doc_name = json.loads(docnames)
	try:
		for name in doc_name:
			cpv = frappe.get_doc('Cash Payment Voucher',name) 
			if cpv.party_type != "Department" and not frappe.db.exists("Journal Entry Account", {'reference_name':cpv.name}):
				if frappe.db.get_value('Mode of Payment Account', {'parent': cpv.mode_of_payment,'company': cpv.company}, ['default_account']):
					if cpv.total > 0.0:
						for d in cpv.cash_payment_voucher_account:
							if not d.ledger_account:
								frappe.throw('Account not defined in Row <b>{0}</b> in voucher no <b>{1}</b>'.format(d.idx, cpv.name))

							if d.ledger_account and d.gross_amount > 0.0:
								debit_entry = ({
								'account': d.ledger_account,
								"party_type": cpv.party_type,
								"party": cpv.pay_to,
								'branch': cpv.location,
								'debit_in_account_currency': flt(d.net_amount),
								'credit_in_account_currency': 0.0,
								'cost_center' : d.cost_center,
								'finance_book' : cpv.finance_book,
								'reference_type': cpv.doctype,
								'reference_name': cpv.name
								})

								for dimension in accounting_dimensions:
									debit_entry.update({dimension: d.get(dimension)})
		
								accounts.append(debit_entry)

								if d.vat_5:
									vat_account_table = frappe.get_doc('Item Tax Template',d.vat_5)
									for tax in vat_account_table.taxes:
										debit_entry_tax = ({
											'account': tax.tax_type,
											"debit_in_account_currency": d.vat_amount,
											'reference_type': cpv.doctype,
											'reference_name': cpv.name
										})

									for dimension in accounting_dimensions:
										debit_entry_tax.update({dimension: d.get(dimension)})

									accounts.append(debit_entry_tax)

					accounts.append(cpv.update_accounting_dimensions({
					'account': frappe.db.get_value('Mode of Payment Account', {'parent': cpv.mode_of_payment,'company': cpv.company}, ['default_account']),
					'credit_in_account_currency': flt(cpv.total),
					'debit_in_account_currency': 0.0,
					'branch': cpv.location,
					'cost_center' : cpv.cost_center, 
					'finance_book' : cpv.finance_book,
					'reference_type': cpv.doctype,
					'reference_name': cpv.name
					}, accounting_dimensions))
					cpv.auto_create_jv = 0
					cpv.save()

				else:
					frappe.throw("No Default Account Found For Mode Of Payment : "+ cpv.mode_of_payment,title='Accounts Not Set')

			if cpv.party_type == "Department" and not frappe.db.exists("Journal Entry Account", {'reference_name':cpv.name}):
				if frappe.db.get_value('Mode of Payment Account', {'parent': cpv.mode_of_payment,'company': cpv.company}, ['default_account']):
					if cpv.total > 0.0:
						for d in cpv.cash_payment_voucher_account:
							if not d.ledger_account:
								frappe.throw('Account not defined in Row <b>{0}</b> in voucher no <b>{1}</b>'.format(d.idx, cpv.name))

							if d.ledger_account and d.gross_amount > 0.0:
								debit_entry =({
								'account': d.ledger_account,
								'debit_in_account_currency': flt(d.net_amount),
								'credit_in_account_currency': 0.0,
								'department': cpv.pay_to,
								'branch': cpv.location,
								'cost_center' : cpv.cost_center,
								'finance_book' : cpv.finance_book,
								'reference_type': cpv.doctype,
								'reference_name': cpv.name
								})

								for dimension in accounting_dimensions:
									debit_entry.update({dimension: d.get(dimension)})

								accounts.append(debit_entry)

								if d.vat_5:
									vat_account_table = frappe.get_doc('Item Tax Template',d.vat_5)
									for tax in vat_account_table.taxes:
										debit_entry_tax = ({
											'account': tax.tax_type,
											"debit_in_account_currency": d.vat_amount,
											'reference_type': cpv.doctype,
											'reference_name': cpv.name
										})
								
									for dimension in accounting_dimensions:
										debit_entry_tax.update({dimension: d.get(dimension)})

									accounts.append(debit_entry_tax)		
									
					accounts.append(cpv.update_accounting_dimensions({
					'account': frappe.db.get_value('Mode of Payment Account', {'parent': cpv.mode_of_payment,'company': cpv.company}, ['default_account']),
					'credit_in_account_currency': flt(cpv.total) ,
					'debit_in_account_currency': 0.0,
					'department': cpv.pay_to,
					'branch': cpv.location,
					'cost_center' : cpv.cost_center,
					'finance_book' : cpv.finance_book,
					'reference_type': cpv.doctype,
					'reference_name': cpv.name
					}, accounting_dimensions))
					cpv.auto_create_jv = 0
					cpv.save()

				else:
					frappe.throw("No Default Account Found For Mode Of Payment : "+ cpv.mode_of_payment,title='Accounts Not Set')

		for name in doc_name:
			cpv_doc = frappe.get_doc('Cash Payment Voucher',name)
			try:
				cpv_doc.submit()
			except:
				frappe.db.rollback()
				frappe.throw("Error happen when try to submit Cash Payment Voucher {0}".format(name))

		if len(accounts) > 0:
			journal_entry = frappe.get_doc({
				'doctype': 'Journal Entry',
				'company': cpv.company,
				'cheque_no': "Against Multiple CPV",
				'posting_date': cpv.posting_date,
				'cheque_date': cpv.posting_date,
				'cost_center' : cpv.cost_center,
				'finance_book': cpv.finance_book,
				'accounts': accounts,
			})
			journal_entry.insert(ignore_permissions=True,ignore_mandatory=True)
			frappe.msgprint("New Journal Entry Created In Draft Mode",title='Success')
		else:
			frappe.db.rollback()
			frappe.throw("No Entry Found to create JV",title='No Eligible Entry')

	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback())