// frappe.listview_settings['Cash Payment Voucher']["onload"] = function (doclist) {
// 	const make_journal_entry = () => {
// 		const selected_docs = doclist.get_checked_items();
// 		const docnames = doclist.get_checked_items(true);

// 		if (selected_docs.length > 0) {
// 			for (let doc of selected_docs) {
// 				if (!doc.docstatus) {
// 					frappe.throw(__("Cannot create a Journal Entry from Draft documents."));
// 				}
// 			};

// 			frappe.call({
// 				method: "jawaerp.jawaerp.doctype.cash_payment_voucher.cash_payment_voucher.make_journal_entries",
// 				args: {"docnames": docnames},
// 				freeze: true,
// 				callback: function(r){
// 					if(!r.exc) {
// 						let doc = frappe.model.sync(r.message);
// 						frappe.set_route("List", "Journal Entry", "List");
// 					}
// 				}
// 			});
// 		};
// 	};

// 	doclist.page.add_actions_menu_item(__('Add Journal Entry'), make_journal_entry, true);

// };


frappe.listview_settings['Cash Payment Voucher'] = {
    onload: function(doclist) {
		// const make_journal_entry = () => {
		// 	const selected_docs = doclist.get_checked_items();
		// 	const docnames = doclist.get_checked_items(true);
		// 	if (selected_docs.length > 0) {
		// 		for (let doc of selected_docs) {
		// 			if (!doc.docstatus) {
		// 				frappe.throw(__("Cannot create a Journal Entry from Draft documents."));
		// 			}
		// 		};

		// 		frappe.call({
		// 			method: "jawaerp.jawaerp.doctype.cash_payment_voucher.cash_payment_voucher.make_journal_entries",
		// 			args: {"docnames": docnames},
		// 			freeze: true,
		// 			callback: function(r){
		// 				if(!r.exc) {
		// 					let doc = frappe.model.sync(r.message);
		// 					frappe.set_route("List", "Journal Entry", "List");
		// 				}
		// 			}
		// 		});
		// 	};
		// };

       
        // doclist.page.add_action_item(__("Add Journal Entry"),
		// 	make_journal_entry, true);
       
    }
}

frappe.listview_settings['Cash Payment Voucher']["onload"] = function (doclist) {
	const make_journal_entry = () => {
		const selected_docs = doclist.get_checked_items();
		const docnames = doclist.get_checked_items(true);

		if (selected_docs.length > 0) {
			for (let doc of selected_docs) {
				if (doc.docstatus === 1) {
					frappe.throw(__("Row {0}: Cannot create a Journal Entry from Submitted documents. Please uncheck them first.", [doc.name]));
				}

				if (doc.docstatus === 2) {
					frappe.throw(__("Row {0}: Cannot create a Journal Entry from Cancelled documents. Please uncheck them first.", [doc.name]));
				}

				// Validate Workflow State
				const allowed_states = ["Final Approved"];
				if (!doc.workflow_state || !allowed_states.includes(doc.workflow_state)) {
					frappe.throw(__("Row {0}: Workflow State must be 'Final Approved'. Current state: {1}", [doc.name, doc.workflow_state || "Draft"]));
				}
			};

			frappe.call({
				method: "shared_finance_app.shared_finance_app.doctype.cash_payment_voucher.cash_payment_voucher.make_journal_voucher",
				args: {"docnames": docnames},
				freeze: true,
				callback: function(r){
					if(!r.exc) {
						let doc = frappe.model.sync(r.message);
						frappe.set_route("List", "Journal Entry", "List");
					}
				}
			});
		};
	};

	doclist.page.add_actions_menu_item(__('Add Journal Entry'), make_journal_entry, true);

};