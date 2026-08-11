frappe.ui.form.on("Material Request", {
    refresh:function(frm){
		let current_state = frm.doc.workflow_state || '';

		if (frm.doc.custom_action_remarks && (current_state === 'Draft' || current_state.includes('Rejected'))) {
			frm.set_intro(frm.doc.custom_action_remarks, 'red');
		} else {
			frm.set_intro('');
		}
    },
	before_workflow_action: function(frm) {
		if (['Reject', 'Revise'].includes(frm.selected_workflow_action)) {
			return new Promise((resolve, reject) => {

				frappe.dom.unfreeze();

				frappe.prompt([
						{
						label: 'Remarks / Reason',
						fieldname: 'user_remarks',
						fieldtype: 'Text',
						reqd: 1,
						description: 'Please provide a reason for this action.'
						}
				],
				function(values) {
						frappe.dom.freeze('Saving Remarks...');

						let current_user = frappe.session.user_fullname;
						let action = frm.selected_workflow_action;
						
						let professional_sentence = `This document was <b>${action}</b> by <b>${current_user}</b>. <b>Remarks:</b> ${values.user_remarks}`;
						
						frappe.db.set_value(
							frm.doctype, 
							frm.docname, 
							'custom_action_remarks',
							professional_sentence
						).then(() => {
							resolve(); 
						}).catch(() => {
							frappe.dom.unfreeze();
							frappe.msgprint('Error saving remarks.');
							reject();
						});
				},
				'Mandatory Remarks For <b>' + frm.selected_workflow_action + ' Action</b>',
				'Submit'
				);
			});
		}
	}
})