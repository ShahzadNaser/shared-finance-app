frappe.listview_settings['Payment Request'] = {
    onload: function (listview) {
        
        // 1. Add your custom top button (Always visible)
        listview.page.add_button(__('New Payment Request'), function() {
            frappe.new_doc('Payment Request');
        }, { icon: 'add' });

        // 2. Validation Helper Function
        const validate_selected_docs = (selected_docs) => {
            for (let doc of selected_docs) {
                // Check if document is already submitted (docstatus === 1)
                if (doc.docstatus === 1) {
                    frappe.throw(__("Row {0}: Cannot process Submitted documents. Please uncheck them first.", [doc.name]));
                }
                
                // Check if document is cancelled (docstatus === 2)
                if (doc.docstatus === 2) {
                    frappe.throw(__("Row {0}: Cannot process Cancelled documents. Please uncheck them first.", [doc.name]));
                }
                
                // Check if workflow state is exactly "Paid"
                if (doc.workflow_state !== "Paid") {
                    frappe.throw(__("Row {0}: Workflow State must be 'Paid'. Current state: {1}", [doc.name, doc.workflow_state]));
                }
            }
        };

        // 3. Make Payment Entry Logic
        const make_payment_entry = () => {
            const selected_docs = listview.get_checked_items();
            const docnames = listview.get_checked_items(true);

            if (selected_docs.length > 0) {
                validate_selected_docs(selected_docs);

                for (let doc of selected_docs) {
                    if (!doc.payment_gateway_account && doc.pay_to_party == 1) {
                        frappe.throw(__("Document status must be Initiated."));
                    }
                }

                frappe.call({
                    method: "shared_finance_app.overrides_class.payment_request.make_payment_entries",
                    args: { "docnames": docnames },
                    freeze: true,
                    callback: function (r) {
                        if (!r.exc) {
                            frappe.model.sync(r.message);
                            frappe.set_route("List", "Payment Entry", "List");
                        }
                    }
                });
            }
        };

        // 4. Make Journal Entry Logic
        const make_journal_entry = () => {
            const selected_docs = listview.get_checked_items();
            const docnames = listview.get_checked_items(true);

            if (selected_docs.length > 0) {
                validate_selected_docs(selected_docs);

                for (let doc of selected_docs) {
                    if (doc.pay_to_party) {
                        frappe.throw(__("Pay To Party must be unchecked."));
                    }
                }

                frappe.call({
                    method: "shared_finance_app.overrides_class.payment_request.make_common_journal_entries",
                    args: { "docnames": docnames },
                    freeze: true,
                    callback: function (r) {
                        if (!r.exc) {
                            frappe.model.sync(r.message);
                            frappe.set_route("List", "Journal Entry", "List");
                        }
                    }
                });
            }
        };

        // 5. Add bulk actions to the 'Actions' menu (Visible when rows are checked)
        listview.page.add_actions_menu_item(__('Add Payment Entry'), make_payment_entry, true);
        listview.page.add_actions_menu_item(__('Add Journal Entry'), make_journal_entry, true);
    }
};