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
		if(typeof(frm.doc.__islocal) == "undefined"){
			// console.log("Yes");
			frm.set_df_property('mode_of_payment',  'hidden',  0);
			frm.set_df_property('finance_book',  'hidden',  0);
			if(frappe.user.has_role('Accounts Manager') || frappe.user.has_role('Payroll & Payables') || 
			frappe.user.has_role('Accounts payable') || frappe.user.has_role('Accounts User') ||
			frappe.user.has_role('Sales & Receivable Manager') || frappe.user.has_role('Sales & Receivable')){
				var df_ledger_account = frappe.meta.get_docfield("Cash Payment Voucher Account","ledger_account", cur_frm.doc.name);
				df_ledger_account.read_only = 0;
				var df_item = frappe.meta.get_docfield("Cash Payment Voucher Account","item", cur_frm.doc.name);
				df_item.read_only = 0;
			}
		}
		// setTimeout(function () {
			frm.trigger("clear_employee");
		// },300);
	},
	pay_to: (frm, cdt, cdn) => {
		cur_frm.add_fetch('pay_to',  'finance_book',  'finance_book');
		set_party_name(frm);

	},
	party_type: (frm, cdt, cdn) => {
		frm.set_value("pay_to","");
		frm.set_value("party_name","");
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
	location: (frm, cdt, cdn) => {
		$.each(frm.doc.cash_payment_voucher_account,  function(i,  d) {
            d.branch = frm.doc.location;
        });
        frm.refresh_fields();
	},
	validate: (frm, cdt, cdn) => {
		set_party_name(frm);
	},
	after_save: (frm, cdt, cdn) => {
		if(typeof(frm.doc.__islocal) == "undefined"){
			// console.log("Yes");
			frm.set_df_property('mode_of_payment',  'hidden',  0);
			frm.set_df_property('finance_book',  'hidden',  0);
			if(frappe.user.has_role('Accounts Manager') || frappe.user.has_role('Payroll & Payables') || 
			frappe.user.has_role('Accounts payable') || frappe.user.has_role('Accounts User') ||
			frappe.user.has_role('Sales & Receivable Manager') || frappe.user.has_role('Sales & Receivable')){
				var df_ledger_account = frappe.meta.get_docfield("Cash Payment Voucher Account","ledger_account", cur_frm.doc.name);
				df_ledger_account.read_only = 0;
				var df_item = frappe.meta.get_docfield("Cash Payment Voucher Account","item", cur_frm.doc.name);
				df_item.read_only = 0;
			}
		}
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

cur_frm.set_query("vat_5", "cash_payment_voucher_account", function (doc, cdt, cdn) {
	return {
		filters: {
			"is_sales": 0
		},
	};
});
