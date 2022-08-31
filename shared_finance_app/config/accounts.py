from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
        {
            "label": _("Accounts Receivable"),
			"items": [
                {
                    "type": "doctype",
                    "name": "Employee Clearance",
                    "description": _("Employee Clearance"),
                    "onboard": 1,
                },
                {
                    "type": "doctype",
                    "name": "Loan Application",
                    "description": _("Loan Application"),
                    "onboard": 1,
                },
                {
                    "type": "doctype",
                    "name": "Loan",
                    "description": _("Loan"),
                    "onboard": 1,
                },
                {
                    "type": "doctype",
                    "name": "Loan Type",
                    "description": _("Loan Type"),
                    "onboard": 1,
                },
             
            ]
        },
        {
            "label": _("Accounts Payable"),
			"items": [ 
                {
                    "type": "doctype",
                    "name": "Cash Payment Voucher",
                    "description": _("Cash Payment Voucher"),
                    "onboard": 1,
                },
                {
                    "type": "report",
                    "name": "Item wise CPV Register",
                    "is_query_report": True,
                    "doctype": "Cash Payment Voucher"
                }, 
                {
                    "type": "doctype",
                    "name": "Payment Request",
                    "description": _("Payment Request"),
                    "onboard": 1,
                }
            ]
        },
        {
            "label": _("General Ledger"),
			"items": [
                {
                    "type": "report",
                    "name": "Statement of Account",
                    "is_query_report": True,
                    "doctype": "GL Entry"
                }, 
            ]
        },
        {
            "label": _("Banking and Payments"),
			"items": [
                {
                    "type": "doctype",
                    "name": "Bank Reconciliation",
                    "description": _("Bank Reconciliation."),
                    "onboard": 1,
                },
            ]
        },
        {
            "label": _("Payroll"),
			"items": [
                {
                    "type": "doctype",
                    "name": "Payroll Entry",
                    "description": _("Payroll Entry."),
                    "onboard": 1,
                },
                {
                    "type": "report",
                    "name": "Account Payroll Report",
                    "is_query_report": True,
                    "doctype": "Payroll Entry"
                },  
                {
                    "type": "report",
                    "name": "WPS Report",
                    "is_query_report": True,
                    "doctype": "Salary Slip"
                },
                {
					"type": "doctype",
					"name": "Timesheet Upload Tool",
					"onboard": 1,
					"dependencies": ["Salary Structure", "Employee"],
				},
            ]
        },
       {
            "label": _("Cost Allocation"),
			"items": [
                {
                    "type": "doctype",
                    "name": "Cost Allocation Tool",
                    "description": _("Cost Allocation Tool"),
                    "onboard": 1,
                },
               
            ]
        },
        {
            "label": _("JawaHR Settings"),

            "items": [
                {
                    "type": "doctype",
                    "name": "JawaHR Settings"
                },
            ]
        },
        {
			"label": _("Reports"),
			"items": [
				{
					"type": "report",
					"is_query_report": True,
					"name": "Contract Charges Report"
				},
        		{
					"type": "report",
					"is_query_report": True,
					"name": "Settlements",
					"label": _("Settlements Report"),     
				},
        		{
					"type": "report",
					"is_query_report": True,
					"name": "Employee Salary History",
					"label": _("Employee Salary History Report"),     
				},
                {
					"type": "report",
					"is_query_report": True,
					"name": "Domestic Sales Report",
					"label": _("Domestic Sales Report"),     
				},
                {
					"type": "report",
					"name": "Manpower Contract",
					"onboard": 1,
					"is_query_report": True
				}
			]
		}


   
    ]

