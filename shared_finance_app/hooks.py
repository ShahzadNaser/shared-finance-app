# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "shared_finance_app"
app_title = "Shared Finance App"
app_publisher = "mesa_Safd"
app_description = "Shared Finance App"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "meso1132"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/shared_finance_app/css/shared_finance_app.css"
# app_include_js = "/assets/shared_finance_app/js/shared_finance_app.js"

# include js, css files in header of web template
# web_include_css = "/assets/shared_finance_app/css/shared_finance_app.css"
# web_include_js = "/assets/shared_finance_app/js/shared_finance_app.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {"Payment Request": "public/js/payment_request.js"}
doctype_list_js = {"Payment Request": "public/js/payment_request_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "shared_finance_app.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "shared_finance_app.install.before_install"
# after_install = "shared_finance_app.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "shared_finance_app.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    "Payment Request": {
        "on_submit": "shared_finance_app.overrides_class.payment_request.on_submit_via_hooks",
        "on_cancel": "shared_finance_app.overrides_class.payment_request.on_cancel",
    }
}

override_doctype_class = {
    'Payment Request': 'shared_finance_app.overrides_class.payment_request.CustomPaymentRequest'
}

override_doctype_dashboards = {
    "Payment Request": "shared_finance_app.dashboard.payment_request_dashboard.get_data"

}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"shared_finance_app.tasks.all"
# 	],
# 	"daily": [
# 		"shared_finance_app.tasks.daily"
# 	],
# 	"hourly": [
# 		"shared_finance_app.tasks.hourly"
# 	],
# 	"weekly": [
# 		"shared_finance_app.tasks.weekly"
# 	]
# 	"monthly": [
# 		"shared_finance_app.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "shared_finance_app.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "shared_finance_app.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "shared_finance_app.task.get_dashboard_data"
# }
