frappe.ui.form.on('Material Request', {
    refresh: function(frm) {
        let help_box = frm.get_field('custom_department_manager').$wrapper.find('.help-box');
    
        if (help_box.length) {
            // Appling color
            help_box[0].style.setProperty('color', '#2490EF', 'important');
            help_box[0].style.setProperty('font-weight', 'bold', 'important');
        }
        
        frm.set_query('custom_department', function() {
            return {
                    filters: [
                        ['Department', 'is_group', '=', 0],
                        ['Department', 'company', '=', frm.doc.company]
                    ]
            };
        });

        if(frm.doc.custom_department && shared_finance_app.can_update_dept_manager(frm)){
            frm.trigger("set_department_manager");
        }

        shared_finance_app.show_action_remarks(frm);
    },
    before_workflow_action: function(frm) {
        return shared_finance_app.before_workflow_action(frm, { require_attachment: true });
    },
    custom_department: function(frm) {
        if (shared_finance_app.can_update_dept_manager(frm)) {
            frm.trigger("set_department_manager");
        }
    },
    set_department_manager: function(frm) {
        if (frm.doc.custom_department) {
            return frappe.call({
                method: 'shared_finance_app.overrides_class.payment_request.get_department_manager',
                args: {
                    "department": frm.doc.custom_department,
                },
                callback: function(r) {
                    if (r && r.message) {
                            if (frm.doc.custom_department_manager !== r.message) {
                            frm.set_value('custom_department_manager', r.message);
                            }
                    }
                }
            });
        }
    }
});

