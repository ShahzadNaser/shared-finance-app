import frappe
from frappe import _

from hrms.hr.doctype.leave_application.leave_application import LeaveApplication

class InsufficientLeaveBalanceError(frappe.ValidationError):
	pass

class CustomLeaveApplication(LeaveApplication):
	def before_save(self):
		if hasattr(super(), "before_save"):
			super().befor_save()

		#Reject/Revise action block from list view
		is_list_view_action = frappe.form_dict.get('cmd') == 'frappe.model.workflow.bulk_workflow_approval'

		current_state = self.workflow_state or ''

		if is_list_view_action and (current_state == 'Draft' or 'Rejected' in current_state) and self.has_value_changed('workflow_state'):
			frappe.throw("<b>Action Blocked:</b> You cannot Reject or Revise directly from the List View. Please click on the document to open it, then take your action so you can provide mandatory remarks.<br>")

	def show_insufficient_balance_message(self, leave_balance_for_consumption: float) -> None:
		# Bypass the message and error completely for Business Trips
		if self.leave_type == "Business Trip":
			return

		alloc_on_from_date, alloc_on_to_date = self.get_allocation_based_on_application_dates()

		if frappe.db.get_value("Leave Type", self.leave_type, "allow_negative"):
			if leave_balance_for_consumption != self.leave_balance:
				msg = _("Warning: Insufficient leave balance for Leave Type {0} in this allocation.").format(
					frappe.bold(self.leave_type)
				)
				msg += "<br><br>"
				msg += _(
					"Actual balances aren't available because the leave application spans over different leave allocations. You can still apply for leaves which would be compensated during the next allocation."
				)
			else:
				msg = _("Warning: Insufficient leave balance for Leave Type {0}.").format(
					frappe.bold(self.leave_type)
				)

			frappe.msgprint(msg, title=_("Warning"), indicator="orange")
		else:
			frappe.throw(
				_("Insufficient leave balance for Leave Type {0}").format(frappe.bold(self.leave_type)),
				exc=InsufficientLeaveBalanceError,
				title=_("Insufficient Balance"),
			)	
			