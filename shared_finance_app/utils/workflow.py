import frappe
from frappe import _
from frappe.model.workflow import get_workflow, get_workflow_name
from frappe.utils import escape_html, get_fullname

REMARKS_ACTIONS = ("Reject", "Revise")
SUBMIT_FOR_APPROVAL = "Submit for Approval"

BULK_WORKFLOW_CMD = "frappe.model.workflow.bulk_workflow_approval"
# bulk_workflow_approval runs 20+ documents in a background job, where form_dict is empty
BULK_WORKFLOW_JOB = "frappe.model.workflow._bulk_workflow_action"


def is_reject_or_revise_state(state):
	return state == "Draft" or "Rejected" in state


def is_bulk_workflow_action():
	if frappe.form_dict.get("cmd") == BULK_WORKFLOW_CMD:
		return True

	job = getattr(frappe.local, "job", None)
	return bool(job and job.method == BULK_WORKFLOW_JOB)


def get_remarks_cache_key(doctype, name):
	return f"shared_finance_app:action_remarks:{doctype}:{name}"


@frappe.whitelist()
def set_pending_action_remarks(doctype, name, action, remarks):
	"""Hold the Reject/Revise remarks until the workflow action saves the document.

	They are written by `handle_reject_revise` within the same save, so a failed
	workflow action leaves no remarks behind.
	"""
	if action not in REMARKS_ACTIONS:
		frappe.throw(_("Remarks are only taken for the Reject and Revise actions"))

	if not (remarks or "").strip():
		frappe.throw(_("Remarks are mandatory"))

	frappe.has_permission(doctype, "read", name, throw=True)

	cache_key = get_remarks_cache_key(doctype, name)
	frappe.cache.set_value(
		cache_key,
		{"action": action, "remarks": remarks},
		user=frappe.session.user,
		expires_in_sec=600,
	)

	# set_value ignores Redis connection errors; the remarks are mandatory, so don't let them get lost
	if not frappe.cache.get_value(cache_key, user=frappe.session.user, expires=True):
		frappe.throw(_("Could not save the remarks, please try again."))


def handle_reject_revise(doc):
	"""Called from before_save: block Reject/Revise from the list view and write the action remarks."""
	current_state = doc.workflow_state or ""

	# New documents have no previous state (has_value_changed is always True for them)
	if not doc.get_doc_before_save():
		return

	if not is_reject_or_revise_state(current_state) or not doc.has_value_changed("workflow_state"):
		return

	if is_bulk_workflow_action():
		frappe.throw(
			_(
				"<b>Action Blocked:</b> You cannot Reject or Revise directly from the List View. Please click on the document to open it, then take your action so you can provide mandatory remarks.<br>"
			)
		)

	cache_key = get_remarks_cache_key(doc.doctype, doc.name)
	# expires=True: the value is set with an expiry, so don't keep it in frappe.local.cache
	pending = frappe.cache.get_value(cache_key, user=frappe.session.user, expires=True)
	if not pending:
		return

	frappe.cache.delete_value(cache_key, user=frappe.session.user)
	doc.custom_action_remarks = "This document was <b>{0}</b> by <b>{1}</b>. <b>Remarks:</b> {2}".format(
		escape_html(pending.get("action")),
		escape_html(get_fullname(frappe.session.user)),
		escape_html(pending.get("remarks")),
	)


def validate_submit_for_approval_attachment(doc, method=None):
	"""doc_events validate: "Submit for Approval" needs at least one attachment, also from the list view or API."""
	if not doc.get("workflow_state") or not doc.has_value_changed("workflow_state"):
		return

	previous = doc.get_doc_before_save()
	if not previous or not get_workflow_name(doc.doctype):
		return

	is_submit_for_approval = any(
		t.action == SUBMIT_FOR_APPROVAL and t.state == previous.workflow_state and t.next_state == doc.workflow_state
		for t in get_workflow(doc.doctype).transitions
	)
	if not is_submit_for_approval:
		return

	if not frappe.db.exists("File", {"attached_to_doctype": doc.doctype, "attached_to_name": doc.name}):
		frappe.throw(
			_("Please attach a required file before submitting for approval."), title=_("Missing Attachment")
		)
