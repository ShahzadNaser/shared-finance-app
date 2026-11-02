frappe.provide("shared_finance_app");

// Reject/Revise remarks are shown while the document is back in Draft or a Rejected state.
// No else branch: the form clears the intro on every refresh, and clearing it here would hide intros set by other scripts.
shared_finance_app.show_action_remarks = function (frm) {
	const current_state = frm.doc.workflow_state || "";
	if (frm.doc.custom_action_remarks && (current_state === "Draft" || current_state.includes("Rejected"))) {
		frm.set_intro(frm.doc.custom_action_remarks, "red");
	}
};

// Use as the doctype's before_workflow_action. Frappe freezes the screen before this runs,
// so unfreeze before throwing or prompting.
shared_finance_app.before_workflow_action = function (frm, { require_attachment = false } = {}) {
	const action = frm.selected_workflow_action;

	// docinfo is used because frm.attachments only exists when the form sidebar is shown
	if (require_attachment && action === "Submit for Approval" && !(frm.get_docinfo().attachments || []).length) {
		frappe.dom.unfreeze();
		frappe.throw({
			title: __("Missing Attachment"),
			message: __("Please attach a required file before submitting for approval."),
		});
	}

	if (!["Reject", "Revise"].includes(action)) return;

	// The remarks are held on the server and written by the workflow action's own save
	return new Promise((resolve, reject) => {
		frappe.dom.unfreeze();

		frappe.prompt(
			[
				{
					label: __("Remarks / Reason"),
					fieldname: "user_remarks",
					fieldtype: "Text",
					reqd: 1,
					description: __("Please provide a reason for this action."),
				},
			],
			(values) => {
				frappe.dom.freeze(__("Saving Remarks..."));
				frappe
					.xcall("shared_finance_app.utils.workflow.set_pending_action_remarks", {
						doctype: frm.doctype,
						name: frm.docname,
						action: action,
						remarks: values.user_remarks,
					})
					.then(() => resolve())
					.catch(() => {
						frappe.dom.unfreeze();
						reject();
					});
			},
			__("Mandatory Remarks For {0} Action", [`<b>${__(action)}</b>`]),
			__("Submit")
		);
	});
};
