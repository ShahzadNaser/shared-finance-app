from __future__ import unicode_literals
from frappe import _

def get_data():
	return {
		'fieldname': 'new_arrival',
		'transactions': [
			{
				'label': _('Links'),
				'items': ['Employee', 'Contract', 'Salary Structure Assignment']
			}
		]
	}
