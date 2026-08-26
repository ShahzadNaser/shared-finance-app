// Copyright (c) 2021, mesa_safd@hotmail.com and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Cash Payment Voucher", "refresh", function(frm) {
// 	cur_frm.set_query("pay_to", function() {
// 		return {
// 			"filters": {
// 					"company": frm.doc.company,
// 					"status": "Active"
// 				}
// 		};
// 	});
// });

var employee_added = false;
cur_frm.set_query("ledger_account", "cash_payment_voucher_account", function(doc, cdt, cdn) {
	var d = locals[cdt][cdn];
	return{
		filters: [
			['Account', 'company', '=', doc.company],
			['Account', 'is_group', '=', 0]
		]
	};
});

cur_frm.set_query("item", "cash_payment_voucher_account", function(doc, cdt, cdn) {
	var d = locals[cdt][cdn];
	return{
		filters: [
			['Item', 'is_purchase_item', '=',1]
		]
	};
});


frappe.ui.form.on("Cash Payment Voucher", {
	refresh: (frm) => {
		if (window.innerWidth <= 501) {   
			setTimeout(() => {
				let $btn = $('.page-head .sidebar-toggle-btn');
				
				if ($btn.length > 0) {
						// 1. Remove Frappe's native workspace toggle class
						$btn.removeClass('sidebar-toggle-btn').addClass('custom-mobile-btn');
						
						// 2. FIX: Hide the double-arrow and force the three-line menu to show
						$btn.find('.sidebar-toggle-icon').hide(); // Hides the >>
						$btn.find('.sidebar-toggle-placeholder').show(); // Shows the 3 lines
						
						// 3. Attach our smart toggle logic
						$('.custom-mobile-btn').off('click').on('click', function(e) {
						e.preventDefault();
						
						let $sideSection = $('.layout-side-section');
						let $formSidebar = $('.form-sidebar');
						let $htmlTag = $('html');
						
						// Toggle logic for the button itself
						if ($sideSection.hasClass('show')) {
							$sideSection.removeClass('show');
							$formSidebar.removeClass('opened').addClass('hidden-xs hidden-sm');
							$htmlTag.css('overflow-y', '');
							$(document).off('click.customSidebar'); 
						} else {
							// OPEN Sidebar
							$sideSection.addClass('show');
							$formSidebar.addClass('opened').removeClass('hidden-xs hidden-sm');
							$htmlTag.css('overflow-y', 'hidden'); 
							
							// Smart Closing Listener
							setTimeout(() => {
								$(document).on('click.customSidebar', function(event) {
									let $target = $(event.target);
									
									// Ignore clicks on our custom button
									if ($target.closest('.custom-mobile-btn').length > 0) return;
									
									// Check where the user clicked
									let clickedOutside = $target.closest('.layout-side-section').length === 0;
									let clickedAction = $target.closest('button, a, [data-action], .icon').length > 0;
									let isModal = $target.closest('.modal, .modal-dialog').length > 0;
									
									// If interacting with a popup (like the attachment upload), do NOT close
									if (isModal) return;
									
									// If clicked outside, or clicked an action button inside the sidebar -> Close
									if (clickedOutside || clickedAction) {
											$sideSection.removeClass('show');
											$formSidebar.removeClass('opened').addClass('hidden-xs hidden-sm');
											$htmlTag.css('overflow-y', '');
											
											$(document).off('click.customSidebar'); 
									}
								});
							}, 50);
						}
						});
				}
			}, 500);
		}
		
		frm.trigger("clear_employee");

		set_party_filter(frm);
		set_company_filters(frm);

		let help_box = frm.get_field('custom_department_manager').$wrapper.find('.help-box');
        
		if (help_box.length) {
			// Appling color
			help_box[0].style.setProperty('color', '#2490EF', 'important');
			help_box[0].style.setProperty('font-weight', 'bold', 'important');
		}

		if(frm.doc.department){
			frm.trigger("set_department_manager");
		}

		let current_state = frm.doc.workflow_state || '';

        if (frm.doc.custom_action_remarks && (current_state === 'Draft' || current_state.includes('Rejected'))) {
            frm.set_intro(frm.doc.custom_action_remarks, 'red');
        } else {
            frm.set_intro('');
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

		if (frm.selected_workflow_action === 'Paid') {
            return new Promise((resolve, reject) => {
                
                frappe.dom.unfreeze();

                let uploader = new frappe.ui.FileUploader({
                    doctype: frm.doctype,
                    docname: frm.docname,
                    folder: 'Home/Attachments',
                    on_success: (file_doc) => {
                        // Once the file is successfully uploaded, resolve the promise
                        resolve();
                    }
                });

                // If the user closes the upload window without uploading a file, reject the promise
                // This cancels the workflow transition
                uploader.dialog.onhide = () => {
                    reject();
                };
            });
        }

		if (frm.selected_workflow_action === 'Submit for Approval') {
            // Check if the attachments list is empty
            if (frm.selected_workflow_action === 'Submit for Approval') {
				if (frm.attachments.get_attachments().length === 0) {
					frappe.dom.unfreeze();
					frappe.throw({
						title: __('Missing Attachment'),
						message: __('Please attach a required file before submitting for approval.')
					});
				}
			}
        }
    },
	company: (frm, cdt, cdn) => {
		frm.set_value("party_type", "");
		frm.set_value("pay_to", "");
        frm.set_value("party_name", "");
		frm.set_value("cost_center", "");
        frm.set_value("department", "");
        
        // Re-apply filter
        set_party_filter(frm);
		set_company_filters(frm);
	},
	pay_to: (frm, cdt, cdn) => {
		set_party_name(frm);
		if (frm.doc.party_type === "Department" && frm.doc.pay_to) {
            frm.set_value("department", frm.doc.pay_to);
        } else {
			frm.set_value("department", "");
		}
	},
	party_type: (frm, cdt, cdn) => {
		frm.set_value("pay_to","");
		frm.set_value("party_name","");

		set_party_filter(frm);
	},

	party_name: (frm, cdt, cdn) =>{
		if (frm.doc.party_type == "Department" && frm.doc.pay_to){	
			// console.log("dd");	
			frappe.call({
				method:"shared_finance_app.shared_finance_app.doctype.cash_payment_voucher.cash_payment_voucher.getDept_Account",
				args:{
					party_name : frm.doc.party_name,
				},
				
				callback:function(r) {
					// console.log(r.message);
					frappe.model.add_child(cur_frm.doc, "Cash Payment Voucher Account", "cash_payment_voucher_account")
					frm.doc.cash_payment_voucher_account.forEach(function(v){
						frappe.model.set_value(v.doctype, v.name, "ledger_account", r.message)
						frm.refresh_fields();
					
					})

					
				
				}
			});
		}
	},
	cost_center: (frm, cdt, cdn) => {
		$.each(frm.doc.cash_payment_voucher_account,  function(i,  d) {
            d.cost_center = frm.doc.cost_center;
        });
        frm.refresh_fields();
	},
	department: (frm, cdt, cdn) => {
		$.each(frm.doc.cash_payment_voucher_account,  function(i,  d) {
            d.department = frm.doc.department;
        });
        frm.refresh_fields();
		frm.trigger("set_department_manager");
	},
    set_department_manager: function(frm) {
		if (frm.doc.department) {
			return frappe.call({
				method: 'shared_finance_app.overrides_class.payment_request.get_department_manager',
				args: {
					"department": frm.doc.department,
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
	},
	location: (frm, cdt, cdn) => {
		$.each(frm.doc.cash_payment_voucher_account,  function(i,  d) {
            d.branch = frm.doc.location;
        });
        frm.refresh_fields();
	},
	validate: (frm, cdt, cdn) => {
		set_party_name(frm);
	},
	before_save: function(frm){
		calculate_total(frm);
		frm.trigger("clear_employee");
	},
	before_submit: (frm, cdt, cdn) => {
		if(frm.doc.docstatus==1 && typeof(frm.doc.mode_of_payment) == "undefined" || typeof(frm.doc.finance_book) == "undefined") {
           	frappe.throw("Mode of Payment or Finance book should not be blank");
        }
	},
	employee: function(frm) {
		if(frm.doc.employee){
			employee_added = true;
		}     
   	},
	clear_employee: function(frm){
		if(frm.is_new() && !employee_added){
			frm.doc.employee = "";
			frm.doc.cash_payment_voucher_account.forEach(function(item){
				item.employee = "";
			});
		}
	}
})



frappe.ui.form.on("Cash Payment Voucher Account", {
	net_amount: (frm, cdt, cdn) => {
		calculate_tax(frm, cdt, cdn);
		calculate_values(frm, cdt, cdn); 
		calculate_total(frm);      
	},

	vat_5: (frm, cdt, cdn) => {
		calculate_tax(frm, cdt, cdn);
		calculate_values(frm, cdt, cdn);
		calculate_total(frm);
	},
	vat_percent: (frm, cdt, cdn) => {
		calculate_tax(frm, cdt, cdn);
		calculate_values(frm, cdt, cdn);
		calculate_total(frm);
	},
	cash_payment_voucher_account_remove: (frm, cdt, cdn) => {
		calculate_total(frm);
	},
	cash_payment_voucher_account_add: (frm, cdt, cdn) => {
		var row = locals[cdt][cdn];
		if (frm.doc.cost_center && !row.cost_center){
			frappe.model.set_value(cdt, cdn, "cost_center", frm.doc.cost_center);
		}
		$.each(frm.doc.cash_payment_voucher_account,  function(i,  d) {
            d.cost_center = frm.doc.cost_center;
        });
		frm.refresh_fields();
	},
	employee: function(frm, cdt, cdn) {
		let child = locals[cdt][cdn]; 
		if(child.employee){
			 employee_added = true;
		}     
   	}
});

function calculate_tax(frm, cdt, cdn) {
	var row = locals[cdt][cdn];
	if (row.vat_5) {
		frappe.call({
			method: "shared_finance_app.shared_finance_app.doctype.cash_payment_voucher.cash_payment_voucher.getTax_Percent",
			args: {
				item_tax_template: row.vat_5,
			},
			callback: function (r) {
				frappe.model.set_value(cdt, cdn, "vat_percent", r.message);
				frappe.model.set_value(cdt, cdn, "gross_amount", row.net_amount + (row.net_amount) * (r.message / 100));
			}
		});
	}
	if (!row.item_tax_template) {
		frappe.model.set_value(cdt, cdn, "tax_percent", 0);
	}
}

function calculate_values(frm, cdt, cdn) {
	var row = locals[cdt][cdn];
	frappe.model.set_value(cdt, cdn, "gross_amount", row.net_amount + (row.net_amount) * (row.vat_percent / 100));
	frappe.model.set_value(cdt, cdn, "vat_amount", (row.net_amount) * (row.vat_percent / 100));
}

function calculate_total(frm) {
	var net_amount = 0;
	var gross_amount = 0;
	var items = frm.doc.cash_payment_voucher_account;
		for (var i = 0; i < items.length; i++) {
			gross_amount += items[i].gross_amount;
			net_amount += items[i].net_amount;
		}
		frm.set_value("total", gross_amount);
		frm.set_value("total_vat", gross_amount - net_amount || 0);
		frm.set_value("net_amount", net_amount);
		cur_frm.refresh_fields();
}

function set_party_name(frm) {
	if (frm.doc.pay_to && frm.doc.party_type) {
		frappe.call({
			method: "shared_finance_app.shared_finance_app.doctype.cash_payment_voucher.cash_payment_voucher.getParty_Name",
			args: {
				party : frm.doc.pay_to,
				party_type : frm.doc.party_type
			},
			callback: function (r) {
				frm.set_value("party_name",r.message);
			}
		});
	}
}

function set_party_filter(frm) {
    if (frm.doc.party_type && frm.doc.company && ["Employee", "Department"].includes(frm.doc.party_type)) {
        frm.set_query("pay_to", function() {
            return {
                filters: {
                    company: frm.doc.company
                }
            };
        });
    } else {
        frm.set_query("pay_to", function() { return {}; });
    }
}

function set_company_filters(frm) {
    if (frm.doc.company) {
        frm.set_query("cost_center", function() {
            return {
                filters: {
                    company: frm.doc.company,
                    is_group: 0
                }
            };
        });

        frm.set_query("department", function() {
            return {
                filters: {
                    company: frm.doc.company,
					is_group: 0
                }
            };
        });
    } else {
        frm.set_query("cost_center", function() { return {}; });
        frm.set_query("department", function() { return {}; });
    }
}
// cur_frm.set_query("vat_5", "cash_payment_voucher_account", function (doc, cdt, cdn) {
// 	return {
// 		filters: {
// 			"is_sales": 0
// 		},
// 	};
// });
