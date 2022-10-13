from __future__ import unicode_literals
from frappe import _

def get_data():
	return {
		'fieldname': 'cheque_no',
		"non_standard_fieldnames": {"Journal Entry": "reference_name"},
		'transactions': [
			{
				'label': _('Payment'),
				'items': ['Journal Entry']
			}
		]
	}
