frappe.listview_settings['Payment Request']["onload"] = function (doclist) {
		const validate_selected_docs = (selected_docs) => {
			for (let doc of selected_docs) {
				// Check if document is cancelled (docstatus === 2)
				if (doc.docstatus === 2) {
					frappe.throw(__("Row {0}: Cannot process Cancelled documents.", [doc.name]));
				}
				// Check if workflow state is exactly "Final Approval"
				// if (doc.workflow_state !== "Final Approval") {
				// 	frappe.throw(__("Row {0}: Workflow State must be 'Final Approval'. Current state: {1}", [doc.name, doc.workflow_state]));
				// }
			}
		};

        const make_payment_entry = () => {
			const selected_docs = doclist.get_checked_items();
			const docnames = doclist.get_checked_items(true);

			if (selected_docs.length > 0) {
				//validate
				validate_selected_docs(selected_docs);

				for (let doc of selected_docs) {
					if (!doc.payment_gateway_account && doc.pay_to_party == 1) {
						frappe.throw(__("Document status must be Initiated."));
					}
				};

				frappe.call({
					method: "shared_finance_app.overrides_class.payment_request.make_payment_entries",
					args: {"docnames": docnames},
					freeze: true,
					callback: function(r){
						if(!r.exc) {
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
				
				for (let doc of selected_docs) {
					if(doc.pay_to_party){
						frappe.throw(__("Pay To Party must be uncheck."));
					}
				};

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