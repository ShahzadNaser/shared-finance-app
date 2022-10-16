frappe.listview_settings['Payment Request']["onload"] = function (doclist) {
        const make_payment_entry = () => {
			const selected_docs = doclist.get_checked_items();
			const docnames = doclist.get_checked_items(true);

			if (selected_docs.length > 0) {
				for (let doc of selected_docs) {
					if (!doc.docstatus) {
						frappe.throw(__("Cannot create a Payment Entry from Draft documents."));
					}else if(!doc.payment_gateway_account && doc.pay_to_party == 1){
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
				for (let doc of selected_docs) {
					if (!doc.docstatus) {
						frappe.throw(__("Cannot create a Journal Entry from Draft documents."));
					}else if(doc.pay_to_party){
						frappe.throw(__("Pay To Party must be uncheck."));
					}
				};

				frappe.call({
					method: "shared_finance_app.overrides_class.payment_request.make_journal_entries",
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