frappe.listview_settings['Payment Request']["onload"] = function (doclist) {
		const validate_selected_docs = (selected_docs) => {
			for (let doc of selected_docs) {
				// 1. Check if document is already submitted (docstatus === 1)
				if (doc.docstatus === 1) {
					frappe.throw(__("Row {0}: Cannot process Submitted documents. Please uncheck them first.", [doc.name]));
				}
				
				// 2. Check if document is cancelled (docstatus === 2)
				if (doc.docstatus === 2) {
					frappe.throw(__("Row {0}: Cannot process Cancelled documents. Please uncheck them first.", [doc.name]));
				}
				
				// 3. Check if workflow state is exactly "Final Approved"
				if (doc.workflow_state !== "Final Approved") {
					frappe.throw(__("Row {0}: Workflow State must be 'Final Approved'. Current state: {1}", [doc.name, doc.workflow_state]));
				}
			}
		};

        const make_payment_entry = () => {
			const selected_docs = doclist.get_checked_items();
			const docnames = doclist.get_checked_items(true);

			if (selected_docs.length > 0) {
				//validate
				validate_selected_docs(selected_docs);

				// Proceed with server call if validation passes
				frappe.call({
					method: "shared_finance_app.overrides_class.payment_request.make_payment_entries",
					args: { "docnames": docnames },
					freeze: true,
					callback: function(r) {
						if (!r.exc) {
							let doc = frappe.model.sync(r.message);
							frappe.set_route("List", "Payment Entry", "List");
						}
					}
				});
				
			};
		};

		const make_journal_entry = () => {
			const selected_docs = doclist.get_checked_items();
			const docnames = doclist.get_checked_items(true);

			if (selected_docs.length > 0) {
				//validate
				validate_selected_docs(selected_docs);

				frappe.call({
					method: "shared_finance_app.overrides_class.payment_request.make_common_journal_entries",
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

		doclist.page.add_actions_menu_item(__('Add Payment Entry'), make_payment_entry, true);
		doclist.page.add_actions_menu_item(__('Add Journal Entry'), make_journal_entry, true);

	};