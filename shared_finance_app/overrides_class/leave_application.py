from hrms.hr.doctype.leave_application.leave_application import LeaveApplication

from shared_finance_app.utils.workflow import handle_reject_revise


class CustomLeaveApplication(LeaveApplication):
	def before_save(self):
		# HRMS v15 LeaveApplication has no before_save; keep the call if one is added later
		if hasattr(super(), "before_save"):
			super().before_save()

		handle_reject_revise(self)
