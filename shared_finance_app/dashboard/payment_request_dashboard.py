from __future__ import unicode_literals
from frappe import _


def get_data(data):
	return {
		'fieldname': 'payment_request',
		'non_standard_fieldnames': {
			'Journal Entry': 'reference_name',
			'Payment Entry': 'reference_no'
		},
		'transactions': [
			{
				'label': _('Payments'),
				'items': ['Journal Entry','Payment Entry']
			}
		]
	}
