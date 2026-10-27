frappe.ui.form.on("Leave Application", {
    refresh:function(frm){
        let current_state = frm.doc.workflow_state || '';

        if (frm.doc.custom_action_remarks && (current_state === 'Draft' || current_state.includes('Rejected'))) {
            frm.set_intro(frm.doc.custom_action_remarks, 'red');
        } else {
            frm.set_intro('');
        }

        frm.trigger("business_trip_cpv_button");
    },

    // Cash Payment Voucher for an approved Business Trip
    business_trip_cpv_button: async function(frm) {
        if (frm.doc.leave_type !== "Business Trip" || frm.doc.docstatus !== 1 || frm.doc.status !== "Approved") {
            return;
        }

        const leave_application = frm.doc.name;
        const { message } = await frappe.call({
            method: "shared_finance_app.shared_finance_app.business_trip.get_cpv_status",
            args: { leave_application },
        });
        // the user may have moved on to another leave meanwhile
        if (!message || frm.doc.name !== leave_application) return;

        if (message.cpv) {
            frm.add_custom_button(__("View CPV"), () => {
                frappe.set_route("Form", "Cash Payment Voucher", message.cpv);
            });
        } else if (message.can_create && frappe.model.can_create("Cash Payment Voucher")) {
            frm.add_custom_button(__("Create CPV"), () => {
                frappe.call({
                    method: "shared_finance_app.shared_finance_app.business_trip.make_cpv_from_leave_application",
                    args: { leave_application: frm.doc.name },
                    freeze: true,
                    freeze_message: __("Preparing Cash Payment Voucher..."),
                    callback: (r) => {
                        if (!r.message) return;
                        // opened unsaved: Finance reviews the amounts and saves it
                        frappe.model.sync(r.message);
                        frappe.set_route("Form", "Cash Payment Voucher", r.message.name);
                    },
                });
            });
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
});