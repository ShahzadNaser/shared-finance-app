# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from erpnext.accounts.doctype.payment_request import payment_request
from shared_finance_app.overrides_class import payment_request as custom_payment_request
payment_request.PaymentRequest=custom_payment_request.CustomPaymentRequest





__version__ = '0.0.1'

