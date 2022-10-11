// Copyright (c) 2021, mesa_safd@hotmail.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('New Arrival', {
	refresh(frm){
		frm.set_query("project_name", function() {
			return {
				filters:[
					['is_group', '=', 0],
				]
			};
		});
		frm.set_query("sales_order", function() {
			return {
				filters: {'customer': cur_frm.doc.client}
			}
		});

		// if (frm.doc.employee_number){
		// 	frm.add_custom_button(__("Employee"), function(){
		// 			frappe.route_options = {
		// 				"name": frm.doc.employee_number,
		// 			};
		// 			frappe.set_route("Employee", "Form");
		// 		});
		
		// 	frm.add_custom_button(__("Contract"), function(){
		// 			frappe.route_options = {
		// 				"party_name": frm.doc.employee_number,
		// 			};
		// 			frappe.set_route("Contract", "Form");
		// 	});
		// }

		if(!frm.is_new() && !frm.doc.contract && frm.doc.docstatus == 1){
			frm.add_custom_button(__("Create Contract"), function() {
				$('[data-label="Create%20Contract"]').prop("disabled", true);
				frappe.call({
					method: "jawaerp.jawaerp.doctype.new_arrival.new_arrival.create_contract",
					args: {
						doc: frm.doc,
					},
					callback: function(r) {
						if(r.message) {
							setTimeout(function(){
								frm.refresh();
							},300);
						}
					}
				});
			}).addClass("btn-primary");
		}
		if(frm.is_new()){
			frm.set_value('employee_contract',"");
			frm.set_value('contract',"");
		}
	},
	sector(frm){
		if(!frm.doc.__islocal && frm.doc.sector == 'INDUSTRIAL') {
			frm.set_df_property('passport_no', 'reqd', 1);
		}
		else if(!frm.doc.__islocal && frm.doc.sector in ['SHARAKA','Domestic']) {
			frm.set_df_property('passport_no', 'reqd', 1);
			frm.set_df_property('date_of_arrival', 'reqd', 1);
		}

		if (frm.doc.sector == 'INDUSTRIAL')
		{
			frm.set_df_property("client", "reqd", 1);
			frm.set_df_property("contract", "reqd", 1);
		}
		else if ( frm.doc.sector in ['SHARAKA','Domestic']) {
			frm.set_df_property("client", "reqd", 0);
			frm.set_df_property("contract", "reqd", 0);
		}

	},
	status: function(frm){
		frm.set_df_property('camp_location', 'reqd', 0);
		if(frm.doc.status == "New Arrival" || frm.doc.employee_number)
			frm.set_df_property('camp_location', 'reqd', 1);

		// frm.trigger("update_property");
	},
	employee_number: function(frm){
		frm.set_df_property('camp_location', 'reqd', 0);
		if(frm.doc.status == "New Arrival" || frm.doc.employee_number)
			frm.set_df_property('camp_location', 'reqd', 1);
	},
	// update_property: function(frm){
	// 	let temp_statuses = ["Non-Arrival","New-Arrival","Border Number Updated","IQAMA Medical Updates"];
	// 	frm.set_df_property('created_date', 'reqd', 0);
	// 	frm.set_df_property('modified_date', 'reqd', 0);
	// 	if(temp_statuses.includes(frm.doc.status)){
	// 		frm.set_df_property('created_date', 'reqd', 1);
	// 		frm.set_df_property('modified_date', 'reqd', 1);
		
	// 	}
	// }
	on_submit: function(frm){
		// this is to reload doc after submit.
		// because fields which updated on submitt hook not reflected so we need to reload_doc method which refresh the page and fields ll appear
		// setTimeout(function(){
		// 	cur_frm.reload_doc();
		// },2000);
	}
});
