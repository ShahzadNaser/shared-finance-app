frappe.ui.form.on("Leave Application", {
	refresh: function (frm) {
		shared_finance_app.show_action_remarks(frm);
	},
	before_workflow_action: function (frm) {
		return shared_finance_app.before_workflow_action(frm);
	},
});
