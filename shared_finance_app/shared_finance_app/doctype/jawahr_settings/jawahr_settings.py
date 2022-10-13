# -*- coding: utf-8 -*-
# Copyright (c) 2022, mesa_safd@hotmail.com and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class JawaHRSettings(Document):
	def on_update(self):
		self.update_cache()

	@classmethod
	def update_cache(self):
		jawahr_settings = frappe.get_doc('JawaHR Settings','JawaHR Settings')
		frappe.cache().hdel("jawahr_settings", "config")
		frappe.cache().hset("jawahr_settings", "config", jawahr_settings)
		return jawahr_settings

@frappe.whitelist()
def get_setting(key="", defaul_value="", full_dict = False):
	_config = frappe.cache().hget("jawahr_settings", "config")
	if not _config:
		_config = JawaHRSettings.update_cache()

	if full_dict:
		return _config

	return _config.get(key) or defaul_value

@frappe.whitelist(allow_guest=True)
def get_settings():
    _config = get_setting("","",True)
    return _config