import frappe

from hrms.hr.doctype.leave_application.leave_application import LeaveApplication

class CustomLeaveApplication(LeaveApplication):
	def before_save(self):
		if hasattr(super(), "before_save"):
			super().befor_save()

		#Reject/Revise action block from list view
		is_list_view_action = frappe.form_dict.get('cmd') == 'frappe.model.workflow.bulk_workflow_approval'

		current_state = self.workflow_state or ''

		if is_list_view_action and (current_state == 'Draft' or 'Rejected' in current_state) and self.has_value_changed('workflow_state'):
			frappe.throw("<b>Action Blocked:</b> You cannot Reject or Revise directly from the List View. Please click on the document to open it, then take your action so you can provide mandatory remarks.<br>")
			