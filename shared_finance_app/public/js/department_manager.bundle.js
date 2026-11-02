frappe.provide("shared_finance_app");

// Department Manager may only be (re)fetched until the Department Manager has acted.
// The Department Manager stage is read from the active Workflow, so renaming or moving states needs no code change.
shared_finance_app.can_update_dept_manager = function (frm) {
	const DEPT_MANAGER_ROLE = "Department Manager";
	if (frm.doc.docstatus !== 0) return false;

	const state_field = frappe.workflow.get_state_fieldname(frm.doctype);
	if (!state_field) return true; // no active workflow

	const workflow_state = frm.doc[state_field];
	if (!workflow_state || workflow_state === frappe.workflow.get_default_state(frm.doctype, 0)) return true;

	const workflow = frappe.workflow.workflows[frm.doctype];
	const order = [...new Set(workflow.states.map((s) => s.state))];
	const draft_states = workflow.states.filter((s) => cint(s.doc_status) === 0).map((s) => s.state);

	// States where the Department Manager approves (skips e.g. a DM "Cancel" on a submitted state)
	const dm_positions = workflow.transitions
		.filter((t) => t.allowed === DEPT_MANAGER_ROLE && draft_states.includes(t.state))
		.map((t) => order.indexOf(t.state));
	if (!dm_positions.length) return false; // no DM step: only the initial state may update

	const position = order.indexOf(workflow_state);
	return position !== -1 && position <= Math.max(...dm_positions);
};
