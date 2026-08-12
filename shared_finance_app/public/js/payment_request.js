// for deleting native refresh method and added new one
delete cur_frm.events["refresh"];
delete cur_frm.cscript["refresh"];
frappe.ui.form.get_event_handler_list("Payment Request","refresh").shift();
var employee_added = false;
frappe.ui.form.on('Payment Request', {
     refresh: function(frm) {
          // if (frm.doc.reference_jv) {
          //      frm.add_custom_button(__('Journal Entry'), function() {
          //           frappe.set_route("Form", "Journal Entry", frm.doc.reference_jv);
          //      },__("View"));
          // }
          // else 
          frm.set_query('party_type', 'payment_request_item', function(frm, cdt, cdn) {
			return {
				query: "erpnext.setup.doctype.party_type.party_type.get_party_type",
			};
		});

          frm.set_query("account", "payment_request_item", function(doc, cdt, cdn) {
               var d = locals[cdt][cdn];
               return{
                    filters: [
                         ['Account', 'company', '=', doc.company],
                         ['Account', 'is_group', '=', 0]
                    ]
               };
          });

          frm.set_query("cost_center", "payment_request_item", function(doc, cdt, cdn) {
               var d = locals[cdt][cdn];
               return{
                    filters: [
                         ['Cost Center', 'company', '=', doc.company],
                         ['Cost Center', 'is_group', '=', 0]
                    ]
               };
          });

          frm.set_query("department", "payment_request_item", function(doc, cdt, cdn) {
               var d = locals[cdt][cdn];
               return{
                    filters: [
                         ['Department', 'company', '=', doc.company],
                         ['Department', 'is_group', '=', 0]
                    ]
               };
          });

          frm.set_query('cost_center', function() {
               return {
                    filters: [
                         ['Cost Center', 'company', '=', frm.doc.company],
                         ['Cost Center', 'is_group', '=', 0]
                    ]
               };
          });

          frm.set_df_property("grand_total", "read_only", 0);
          if(frm.doc.pay_to_party === 0)
               frm.set_df_property("grand_total", "read_only", 1);
               
          // if(frm.doc.docstatus === 1 && frm.doc.payment_request_type == 'Outward' && frm.doc.pay_to_party === 0){
          //      frm.add_custom_button(__('Make Journal Entry'), () => {
          //           frappe.call({
          //                method: "jawaerp.overrides_class.payment_request.make_journal_voucher",
          //                args: {"pr_name": frm.doc.name}
          //           });
          //      });
          // }
          
          if(frm.doc.payment_request_type == 'Inward' &&
               !in_list(["Initiated", "Paid"], frm.doc.status) && !frm.doc.__islocal && frm.doc.docstatus==1){
               frm.add_custom_button(__('Resend Payment Email'), function(){
                    frappe.call({
                         method: "erpnext.accounts.doctype.payment_request.payment_request.resend_payment_email",
                         args: {"docname": frm.doc.name},
                         freeze: true,
                         freeze_message: __("Sending"),
                         callback: function(r){
                              if(!r.exc) {
                                   frappe.msgprint(__("Message Sent"));
                              }
                         }
                    });
               });
          }

          // if(!frm.doc.payment_gateway_account && frm.doc.status == "Initiated") {
          //      frm.add_custom_button(__('Create Payment Entry'), function(){
          //           frappe.call({
          //                method: "erpnext.accounts.doctype.payment_request.payment_request.make_payment_entry",
          //                args: {"docname": frm.doc.name},
          //                freeze: true,
          //                callback: function(r){
          //                     if(!r.exc) {
          //                          var doc = frappe.model.sync(r.message);
          //                          frappe.set_route("Form", r.message.doctype, r.message.name);
          //                     }
          //                }
          //           });
          //      }).addClass("btn-primary");
          // }
          frm.trigger("update_employee");

          let help_box = frm.get_field('custom_department_manager').$wrapper.find('.help-box');
        
          if (help_box.length) {
               // Appling color
               help_box[0].style.setProperty('color', '#2490EF', 'important');
               help_box[0].style.setProperty('font-weight', 'bold', 'important');
          }
          
          frm.set_query('custom_department', function() {
               return {
                    filters: [
                         ['Department', 'is_group', '!=', 1],
                         ['Department', 'company', '=', frm.doc.company]
                    ]
               };
          });

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

                    // Trigger Frappe's standard upload window
                    let uploader = new frappe.ui.FileUploader({
                         doctype: frm.doctype,
                         docname: frm.docname,
                         folder: 'Home/Attachments',
                         on_success: (file_doc) => {
                         // Once the file is successfully uploaded, resolve the promise 
                         // This allows the workflow state to automatically change to 'Paid'
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
     },
     onload: function(frm) {
          total_section_property(frm);   
     },
     pay_to_party: function(frm) {
          total_section_property(frm);  
          frm.clear_table("payment_request_reference");
          frm.refresh_fields(); 
     },
     before_save: function(frm) {
          // Only recalculate totals if NOT paying to a party (manual payment request items)
          // When pay_to_party = 1, grand_total comes from the reference document
          if (frm.doc.pay_to_party === 0) {
               update_totals(frm);
          }
          frm.trigger("update_employee");
     },
     party_type: function(frm) {
          frm.set_value("party_account","");
          frm.set_value("party","");
          frm.clear_table("payment_request_reference");
          frm.refresh_fields();
     },
     party: function(frm) {
          if (frm.doc.party && frm.doc.party_type && frm.doc.company){
               return  frappe.call({
                    method: 'erpnext.accounts.party.get_party_account',
                    args: {
                         party_type : frm.doc.party_type,
                         party : frm.doc.party,
                         company : frm.doc.company
                    },
                    callback: function(r, rt) {
                        frm.set_value("party_account",r.message);
                    }
               });
          }
     },
     get_outstanding: function(frm) {
          frm.clear_table("payment_request_reference");

		if(!frm.doc.party) {
			return;
		}

		var args = {
			"posting_date": frm.doc.transaction_date,
			"company": frm.doc.company,
			"party_type": frm.doc.party_type,
			"party": frm.doc.party,
			"cost_center": frm.doc.cost_center,
             "party_account": frm.doc.party_account
		}

		return  frappe.call({
			method: 'erpnext.accounts.doctype.payment_entry.payment_entry.get_outstanding_reference_documents',
			args: {
				args:args
			},
			callback: function(r, rt) {
				if(r.message) {
					var total_positive_outstanding = 0;
					var total_negative_outstanding = 0;

					$.each(r.message, function(i, d) {
						var c = frm.add_child("payment_request_reference");
						c.reference_doctype = d.voucher_type;
						c.reference_name = d.voucher_no;
						c.due_date = d.due_date
						c.total_amount = d.invoice_amount;
						c.outstanding_amount = d.outstanding_amount;
						c.bill_no = d.bill_no;
						c.payment_term = d.payment_term;
						c.allocated_amount = d.outstanding_amount;
					});
                            frm.refresh_fields();
				}
			}
		});
     },
     update_employee:function(frm){
          if(frm.is_new() && !employee_added){
               frm.doc.payment_request_item.forEach(function(item){
                    item.employee = "";
               });
          }
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
});


frappe.ui.form.on('Payment Request Item', {
     account: function (frm, cdt, cdn) {
        set_finance_book(frm, cdt, cdn)
     },
     amount: function(frm, cdt, cdn) {
          calc_balance(frm, cdt, cdn)

     },
     less_advance_paid: function (frm, cdt, cdn) {
          calc_balance(frm, cdt, cdn)        

     },
     now_being_request: function (frm, cdt, cdn) {
          calc_balance(frm, cdt, cdn)        

     },
     employee: function(frm, cdt, cdn) {
          let child = locals[cdt][cdn]; 
          if(child.employee){
               employee_added = true;
          }     
     }
});

var total_section_property = function(frm) {
     if (frm.doc.pay_to_party == 1){
          frm.set_df_property("total_of_advance_paid", "read_only", 0);
          frm.set_df_property("total_now_being_requested", "read_only", 0);
          frm.set_df_property("total_balance", "read_only", 0);
     }
     if (frm.doc.pay_to_party === 0){
          frm.set_df_property("total_of_advance_paid", "read_only", 1);
          frm.set_df_property("total_now_being_requested", "read_only", 1);
          frm.set_df_property("total_balance", "read_only", 1);
     }
};

var calc_balance = function(frm, cdt, cdn) {
     let child = locals[cdt][cdn]; 
     var balance_payable = child.amount - child.less_advance_paid - child.now_being_request
     frappe.model.set_value(cdt, cdn, "balance_payable", balance_payable);
     frm.refresh_fields();
     update_totals(frm);
};

var update_totals = function(frm) {
     var grand_total = 0.0;
     var total_of_advance_paid = 0.0;
     var total_now_being_requested = 0.0;
     var total_balance = 0.0;
     
     if (frm.doc.payment_request_item)
          frm.doc.payment_request_item.forEach(d => {
               grand_total += d.amount;
               total_of_advance_paid += d.less_advance_paid;
               total_now_being_requested += d.now_being_request;
               total_balance += d.balance_payable;
          });
     frm.set_value("grand_total", grand_total);
     frm.set_value("total_of_advance_paid", total_of_advance_paid);
     frm.set_value("total_now_being_requested", total_now_being_requested);
     frm.set_value("total_balance", total_balance);
     frm.refresh_fields()
};

var set_finance_book = function(frm, cdt, cdn) {
    if (frm.doc.finance_book) {
        frappe.model.set_value(cdt, cdn, "finance_book", frm.doc.finance_book);
    }
    if (frm.doc.cost_center) {
        frappe.model.set_value(cdt, cdn, "cost_center", frm.doc.cost_center);
    }
};

