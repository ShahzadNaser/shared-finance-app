frappe.ui.form.on("Purchase Order", {
    refresh:function(frm){

        let help_box = frm.get_field('custom_department_manager').$wrapper.find('.help-box');
        
		if (help_box.length) {
			// Appling color
			help_box[0].style.setProperty('color', '#2490EF', 'important');
			help_box[0].style.setProperty('font-weight', 'bold', 'important');
		}
        
        if(frm.doc.custom_department){
            frm.trigger("set_department_manager");
        }

        frm.set_query('custom_department', function() {
            return {
				filters: [
						['Department', 'is_group', '=', 0],
						['Department', 'company', '=', frm.doc.company]
				]
			};
		});
    },
    custom_department: function(frm) {
        frm.trigger("set_department_manager");
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
})