# -*- coding: utf-8 -*-
# Copyright (c) 2021, mesa_safd@hotmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, erpnext
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import make_autoname, getseries, get_default_naming_series
import json
from frappe.utils import get_link_to_form, flt
from frappe.permissions import add_user_permission

class NewArrival(Document):
	def validate(self):
		if self.is_new():
			self.validate_duplicate()
		if self.salary and not self.flags.ignore_custom_validate:
			self.validate_salary_dependent_fields()
			self.validate_basic_salary()

	def validate_salary_dependent_fields(self):
		required_fields = [
      		{"field":"visa_category", "title":"Visa Category"},
			{"field":"sector", "title":"Sector"},
			{"field":"nationality", "title":"Nationality"},
			{"field":"agency", "title":"Agency"}
   		]
		for row in required_fields:
			if not self.get(row.get("field")):
				frappe.throw(_("Please add <b>{}</b> before adding Salary Details.".format(row.get("title"))))

	def validate_basic_salary(self):
		basic = 0
		for component in self.get("salary"):
			if(flt(component.get("amount")) > 0 and component.get("salary_component") == "Basic"):
				basic = component.get("amount")
		if basic == 0:
			frappe.throw(_("<b> Basic </b> Salary is required in Salary Details."))


	def validate_duplicate(self):
		duplicate_passport_no = frappe.db.exists('New Arrival', {'passport_no': self.passport_no,'docstatus': ["!=",2]})
		if duplicate_passport_no:
			frappe.throw(('New Arrival already exist for the passport number {0}.').format(
				self.passport_no, get_link_to_form('New Arrival', duplicate_passport_no)))

		duplicate_border_no = frappe.db.exists('New Arrival', {'border_no': self.border_no, 'docstatus': ["!=",2]})
		if duplicate_border_no:
			frappe.throw(('New Arrival already exist for the border number {0}.').format(
				self.border_no, get_link_to_form('New Arrival', duplicate_border_no)))

	def before_submit(self):
		if not self.salary or not len(self.salary):
			frappe.throw(_("Salary Detail is required."))
		if not self.employee_name:
			frappe.throw(_("Employee Name is required for submission of New Arrival"))
		if not self.border_entry_date:
			frappe.throw(_("Border Entry Date is required for submission of New Arrival"))
		if not self.project_name:
			frappe.throw(_("Project is required for submission of New Arrival"))
		if not self.location_branch:
			frappe.throw(_("Location (Branch) is required for submission of New Arrival"))
		if not self.finance_book:
			frappe.throw(_("Finance Book is required for submission of New Arrival"))
		if not self.holiday_list:
			frappe.throw(_("Holiday List is required for submission of New Arrival"))

		# update status New-Arrival on submission
		self.update_status()

	def on_update_after_submit(self):
		employee_number = self.employee_number or frappe.db.get_value('Employee',{'passport_number': self.passport_no},"name") or frappe.db.get_value('Employee',{'new_arrival': self.name},"name")
		if employee_number and frappe.db.exists('Employee', employee_number):
			frappe.db.set_value('Employee', employee_number, dict({'agency':self.agency,'client_code':self.client,'contract': self.contract}))
			frappe.db.commit()

	def on_submit(self):
		# if not self.employee_number:
		# 	frappe.throw(_("Employee Number is required."))

		employee_number = self.employee_number or frappe.db.get_value('Employee',{'passport_number': self.passport_no},"name") or frappe.db.get_value('Employee',{'new_arrival': self.name},"name")

		if employee_number and frappe.db.exists('Employee', employee_number):
			# frappe.db.set_value('Employee', self.employee_number, 'passport_number', self.passport_no)
			# frappe.db.set_value('Employee', self.employee_number, 'client_code', self.client)
			# frappe.db.set_value('Employee', self.employee_number, 'contract', self.contract)
			# frappe.db.set_value('Employee', self.employee_number, 'location', self.camp_location)
			# frappe.db.set_value('Employee', self.employee_number, 'new_arrival', self.name)
			
			frappe.db.set_value('Employee', employee_number, dict({'new_arrival':self.name,'location':self.camp_location,'employee_contract': self.employee_contract, 'client_code': self.client, 'passport_number': self.passport_no,'sales_order': self.sales_order}))

			frappe.db.commit()

			name, first_name, date_of_joining, company = frappe.db.get_value('Employee',employee_number, ["name", "first_name", "date_of_joining", "company"])

			if not frappe.db.exists("Salary Structure Assignment",{"docstatus":1, "from_date":date_of_joining,"employee":name}):
				add_salary_structure_assignemnt(employee=name , employee_name=first_name, doj= date_of_joining,
					company=company , salary=self.get("salary"), new_arrival=self.name)

			if not self.employee_contract:
				add_contract(self, name)


			# if frappe.session.user != "Administrator" and not frappe.db.exists('User Permission', {'allow': 'Employee','for_value': name,'user': frappe.session.user}):
			# 	add_user_permission("Employee", name, frappe.session.user,ignore_permissions=True)


		if self.employee_name and not frappe.db.exists('Employee', self.employee_number):
			emp = frappe.new_doc("Employee")
			emp.employee = self.employee_name
			emp.first_name = self.employee_name
			emp.employee_name = self.employee_name
			emp.employee_number = self.employee_number
			emp.employee_type = self.sector
			emp.nationality = self.nationality
			emp.gender = self.gender
			emp.date_of_birth = self.date_of_birth
			emp.agency = self.agency
			emp.client_code = self.client
			emp.contract = self.contract
			emp.saudi_id_iqama_number = self.iqama_number
			emp.iqama_issue_date = self.iqama_issue_date
			emp.iqama_profession = self.iqama_profession
			emp.iqama_expiry = self.iqama_expiry_date
			emp.passport_number = self.passport_no
			emp.date_of_issue = self.passport_expiry_date
			emp.visa_entry_number = self.visa_number
			emp.location = self.camp_location
			emp.project_name = self.project_name
			emp.branch = self.location_branch
			emp.location_branch = self.location_branch
			emp.finance_book = self.finance_book
			emp.holiday_list = self.holiday_list
			emp.date_of_joining = self.border_entry_date
			emp.border_number = self.border_no
			emp.new_arrival = self.name
			emp.sales_order = self.sales_order
			emp.old_employee = 1
			emp.company = self.company or erpnext.get_default_company()
			emp.flags.ignore_permissions = True
			emp.flags.ignore_mandatory = True
			emp.save()
	
			if not self.employee_number:
				frappe.db.set_value('New Arrival', self.get("name"), 'employee_number', emp.employee_number)

			add_salary_structure_assignemnt(employee=emp.name , employee_name=emp.first_name,
				doj= emp.date_of_joining, company=emp.company , salary=self.get("salary"), new_arrival=self.name)
			add_contract(self,emp.name)

			# if frappe.session.user != "Administrator" and not frappe.db.exists('User Permission', {'allow': 'Employee','for_value': emp.name,'user': frappe.session.user}):
			# 	add_user_permission("Employee", emp.name, frappe.session.user, ignore_permissions=True)

	def before_save(self):
		if self.status == 'New-Arrival' and (not self.employee_number or self.is_new()):
			self.employee_number = ""
			# self.set_employee_number() ## disabled for few days
		if self.border_no and self.border_no != frappe.db.get_value("New Arrival", self.name, "border_no"):
			self.status = "Border Number Updated"

		if self.status == "Non-Arrival" and self.status != frappe.db.get_value("New Arrival", self.name, "status"):
			self.non_arrival_updated_date = frappe.utils.nowdate()
		elif self.status == "New-Arrival" and self.status != frappe.db.get_value("New Arrival", self.name, "status"):
			self.new_arrival_updated_date = frappe.utils.nowdate()
		elif self.status == "Border Number Updated" and self.status != frappe.db.get_value("New Arrival", self.name, "status"):
			self.border_number_updated_date = frappe.utils.nowdate()
		elif self.status == "IQAMA Medical Updates" and self.status != frappe.db.get_value("New Arrival", self.name, "status"):
			self.iqama_updated_date = frappe.utils.nowdate()

		if not self.company:
			self.company = erpnext.get_default_company()

		if not self.passport_no and self.status != "Ready To Travel":
			frappe.throw(_("Passport Numbber must required in case for {0}.".format(self.status)))

	def set_employee_number(self):
		prefix = get_default_naming_series("Employee")

		if self.sector == "ADMIN":
			prefix = "1"
		elif self.sector == "INDUSTRIAL":
			prefix = "2"
		elif self.sector == "Domestic":
			prefix = "7"
		elif self.sector == "SHARAKA":
			prefix = "8"
		elif self.sector == "SADARA":
			prefix = "9"

		doc_name = make_autoname(prefix+".#####", "", self)

		if frappe.db.exists("Employee",doc_name):
			self.set_employee_number()

		self.employee_number =  doc_name

	def on_cancel(self):
		self.unlink_contract()
		self.unlink_employee()
		self.unlink_ss_assignment()
		
  		# code for monkey patching
		# import frappe.model.naming as original
		# from jawaerp.utils.common import revert_series_if_last
		# original.revert_series_if_last = revert_series_if_last

		employee_number = None
		if self.employee_number and frappe.db.get_value("Employee",self.employee_number):
			employee_number = self.employee_number
		elif frappe.db.get_value("Employee",filters={"passport_number" :self.passport_no}):
			employee_number = frappe.db.get_value("Employee",filters={"passport_number" :self.passport_no})

		# Cancel/Delete Salary Structure Assignment
		if employee_number:		
			ssa_docname = frappe.db.get_value("Salary Structure Assignment",filters={"employee" : employee_number})
			if ssa_docname:
				ssa_doc = frappe.get_doc('Salary Structure Assignment', ssa_docname)
				if ssa_doc.get("docstatus") == 1:
					ssa_doc.ignore_linked_doctypes = ('Employee')
					ssa_doc.flags.ignore_permissions = True
					ssa_doc.cancel()
			else:
				frappe.delete_doc("Salary Structure Assignment",ssa_docname,force=1, ignore_permissions=True)

			# Delete Employee
			frappe.delete_doc("Employee",employee_number,force=1, ignore_permissions=True)

		# Cancel/Delete Contract
		contract_docname = self.employee_contract
		if not self.employee_contract:		
			contract_docname = frappe.db.get_value("Contract",filters={"contract_id" : self.get("passport_no")})

		if contract_docname:
			con_doc = frappe.get_doc('Contract', contract_docname)
			if con_doc.get("docstatus") == 1:
				con_doc.ignore_linked_doctypes = ('New Arrival')
				con_doc.flags.ignore_permissions = True
				con_doc.cancel()
			else:
				frappe.delete_doc("Contract",contract_docname,force=1, ignore_permissions=True)
		# make employee number field empty 
		frappe.db.set_value('New Arrival', self.get("name"), 'employee_number', "")
		frappe.db.commit()
	def update_status(self):
		self.status = "New-Arrival"


	def unlink_contract(self) -> None:
		"""Removes the link between `New Arrival` and `Contract`"""
		links = frappe.get_all("Contract", {"new_arrival": self.name})
		if not links:
			return
		links = [row["name"] for row in links]
		command = """
			UPDATE tabContract SET new_arrival = NULL
			WHERE name IN %(links)s
		"""
		frappe.db.sql(command, {"links": links})



	def unlink_employee(self) -> None:
		"""Removes the link between `New Arrival` and `Employee`"""
		links = frappe.get_all("Employee", {"new_arrival": self.name})
		if not links:
			return
		links = [row["name"] for row in links]
		command = """
			UPDATE tabEmployee SET new_arrival = NULL
			WHERE name IN %(links)s
		"""
		frappe.db.sql(command, {"links": links})

	def unlink_ss_assignment(self) -> None:
		"""Removes the link between `New Arrival` and `Salary Structure Assignment`"""
		links = frappe.get_all("Salary Structure Assignment", {"new_arrival": self.name})
		if not links:
			return
		links = [row["name"] for row in links]
		command = """
			UPDATE `tabSalary Structure Assignment` SET new_arrival = NULL
			WHERE name IN %(links)s
		"""
		frappe.db.sql(command, {"links": links})

@frappe.whitelist()
def create_contract(doc={}):
	if not doc:
		frappe.throw(_("Please Select valid document."))
	doc = json.loads(doc)

	if not doc.get("passport_no"):
		frappe.throw(_("Please Add Passport Number."))
	try:
		contract_doc = frappe.get_doc({
			"doctype":"Contract",
			"party_type":"Employee",
			"contract_id":doc.get("passport_no"),
			"sector": doc.get("sector"),
			"location": doc.get("camp_location"),
			"branch": doc.get("location_branch"),
			"new_arrival": doc.get("name")
		})
		salary_details = []
		if doc.get("salary"):
			salary_details = []
			for component in doc.get("salary"):
				if(flt(component.get("amount")) > 0):
					salary_details.append({"salary_component":component.get("salary_component"),"amount":component.get("amount")})

		if(salary_details):
			contract_doc.set("employee_details",salary_details)

		contract_doc.flags.ignore_permissions = True
		contract_doc.flags.ignore_mandatory = True
		contract_doc.save()

		frappe.db.set_value('New Arrival', doc.get("name"), 'contract', contract_doc.get("name"))
		frappe.db.commit()
		frappe.msgprint(_("Contract successfully created."))
	except Exception as e:
		frappe.log_error(message=str(frappe.get_traceback()),title="Error while creating contract")
		frappe.throw(_("Something Went Wrong Please try again."))
		return False

	return True

def add_salary_structure_assignemnt(employee=None, employee_name=None, doj=None, company=None , salary=[], new_arrival=None):

	if not employee:
		frappe.throw(_("Employee is required for auto Salary Structure Assignemnt."))
	if not doj:
		frappe.throw(_("Date of Joining is required for auto Salary Structure Assignemnt."))
	if not company:
		frappe.throw(_("Company is required for auto Salary Structure Assignemnt."))
	if not salary:
		frappe.throw(_("Salary Details required for auto Salary Structure Assignemnt."))

	s = frappe.new_doc("Salary Structure Assignment")
	s.employee = employee
	s.employee_name = employee_name
	s.from_date = doj
	s.new_arrival = new_arrival
	s.company = company
	if company:
		salary_structure = frappe.db.get_value("Company",company,"default_salary_structure")
		if not salary_structure:
			frappe.throw(_("Please add Default Salary Structure in Company."))
		s.salary_structure = salary_structure

	# to migrate the data of the old employees
	s.flags.old_employee = True
	salary_details = []
	if salary:
		for component in salary:
			if component.get("salary_component") == "Basic":
				s.base = component.get("amount")
				continue

			if( component.get("amount") > 0 ):
				salary_details.append({"salary_component":component.get("salary_component"),"amount":component.get("amount")})

	if(salary_details):
		s.set("salary_detail",salary_details)

	try:
		s.flags.ignore_permissions = True
		s.save()
		s.submit()
	except Exception as e:
		frappe.log_error(message=str(frappe.get_traceback()),title="Error while creating contract")
		frappe.throw(_("Something Went Wrong Please try again."))

def add_contract(doc={},employee_number=""):
	if not doc.get("passport_no"):
		frappe.throw(_("Please Add Passport Number."))
	try:
		if not frappe.db.exists("Contract", doc.get("passport_no")):
			contract_doc = frappe.get_doc({
				"doctype":"Contract",
				"party_type":"Employee",
				"contract_id":doc.get("passport_no"),
				"sector": doc.get("sector"),
				"location": doc.get("camp_location"),
				"branch": doc.get("location_branch"),
				"party_name": employee_number,
				"domestic_employee_id": employee_number,
				"passport_number":doc.get("passport_no"),
				"employee_name": doc.get("employee_name"),
				"client": doc.get("client"),
				"start_date": doc.get("border_entry_date"),
				"salary_structure": frappe.db.get_value("Company",doc.company,"default_salary_structure"),
				"new_arrival": doc.get("name")
			})
		else:
			contract_doc =  frappe.get_doc("Contract",doc.get("passport_no"))
			contract_doc.sector =  doc.get("sector")
			contract_doc.location = doc.get("camp_location")
			contract_doc.branch = doc.get("location_branch")
			contract_doc.party_name = employee_number
			contract_doc.party_name = employee_number
			contract_doc.domestic_employee_id = doc.get("employee_name")
			contract_doc.client = doc.get("client")
			contract_doc.start_date = doc.get("border_entry_date")
			contract_doc.passport_number = doc.get("passport_no")
			contract_doc.new_arrival = doc.get("name")
   
			contract_doc.salary_structure = frappe.db.get_value("Company",doc.company,"default_salary_structure")

		if(doc.get("nationality")):
			contract_doc.set("nationality",[{"nationality":doc.get("nationality")}])			

		salary_details = []
		if doc.get("salary"):
			salary_details = []
			for component in doc.get("salary"):
				if(component.get("amount")>0):
					salary_details.append({"salary_component":component.get("salary_component"),"amount":component.get("amount")})

		if(salary_details):
			contract_doc.set("employee_details",salary_details)

		contract_doc.flags.ignore_permissions = True
		contract_doc.flags.ignore_mandatory = True
		contract_doc.save()
		# frappe.db.set_value('New Arrival', doc.get("name"), 'contract', contract_doc.get("name"))

		# Add contract in employee on creation on new contract for an employee
		frappe.db.set_value('New Arrival', doc.get("name"), 'employee_contract', contract_doc.get("name"))
		if frappe.db.exists("Employee",employee_number):
			frappe.db.set_value('Employee', employee_number, 'employee_contract', contract_doc.get("name"))

	except Exception as e:
		frappe.log_error(message=str(frappe.get_traceback()),title="Error while creating contract")
		frappe.throw(_("Something Went Wrong Please try again."))
