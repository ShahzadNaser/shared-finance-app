// a new Cash Payment Voucher, Payment Request, Material Request or Purchase Order is
// ticked as a Top Management Request for the Top Management Requester. Ticked once per new document,
// so it stays unticked if she unticks it. Nothing happens where the field isn't on the form.
;(() => {
	if (window.__tm_request_registered) return;
	window.__tm_request_registered = true;

	const FIELD = "custom_top_management_request";
	const ticked = new Set();

	const tick_for_requester = (frm) => {
		if (!frm.is_new() || !frm.fields_dict[FIELD] || ticked.has(frm.doc.name)) return;
		if (!frappe.user.has_role("Top Management Requester")) return;

		ticked.add(frm.doc.name);
		if (!frm.doc[FIELD]) {
			frm.set_value(FIELD, 1);
		}
	};

	["Cash Payment Voucher", "Payment Request", "Material Request", "Purchase Order"].forEach((doctype) => {
		frappe.ui.form.on(doctype, {
			onload: tick_for_requester,
			refresh: tick_for_requester,
		});
	});
})();
