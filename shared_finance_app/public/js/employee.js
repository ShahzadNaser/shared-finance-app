frappe.ui.form.on('Employee', {
	refresh(frm) {
		// let items = ["personal_information","users_data","employment_data","others"];
		// setTimeout(function(){
		// 	init_btns(frm);
		// 	items.forEach(item => {
		// 		$('.control-input [data-fieldname="'+item+'"]').css("width","100%");
		// 		$('.control-input [data-fieldname="'+item+'"]').css("height","40px");
		// 	});
		// },100);
			

	},

	personal_information:function(frm) {
		personal_information(frm,0);
		users_data(frm,1);
		employment_data(frm,1);
		others(frm,1);    
	},
	users_data(frm) {
		personal_information(frm,1);
		users_data(frm,0);
		employment_data(frm,1);
		others(frm,1);    
	},
	employment_data:function(frm) {
	   personal_information(frm,1);
	   users_data(frm,1);
	   employment_data(frm,0);
	   others(frm,1);    
	},
	others:function(frm) {
		personal_information(frm,1);
		users_data(frm,1);
		employment_data(frm,1);    
		others(frm,0);    
	}
	
});

function init_btns(frm){
	personal_information(frm,0);
	users_data(frm,1);
	employment_data(frm,1);
	others(frm,1);    
}

function personal_information(frm,hidden) {
	if(!hidden){
		$(".btn-info").removeClass("btn-info");
		$('.control-input [data-fieldname="personal_information"]').addClass("btn-info");
	}
		
	frm.set_df_property("basic_information", "hidden", hidden);
	frm.set_df_property("emergency_contact_details", "hidden", hidden);
	frm.set_df_property("personal_details", "hidden", hidden);
	frm.set_df_property("sb53", "hidden", hidden);
	frm.set_df_property("contact_details", "hidden", hidden);
	frm.set_df_property("emergency_contact_details", "hidden", hidden);
}
function users_data(frm,hidden) {
	if(!hidden){
		$(".btn-info").removeClass("btn-info");
		$('.control-input [data-fieldname="users_data"]').addClass("btn-info");
	}

	frm.set_df_property("erpnext_user", "hidden", hidden);
}
function employment_data(frm,hidden) {
	if(!hidden){
		$(".btn-info").removeClass("btn-info");
		$('.control-input [data-fieldname="employment_data"]').addClass("btn-info");
	}

	frm.set_df_property("employment_details", "hidden", hidden);
	frm.set_df_property("job_profile", "hidden", hidden);
	frm.set_df_property("attendance_and_leave_details", "hidden", hidden);
	frm.set_df_property("salary_information", "hidden", hidden);
	frm.set_df_property("health_insurance_section", "hidden", hidden);
	frm.set_df_property("iqama_details", "hidden", hidden);
	frm.set_df_property("exit", "hidden", hidden);
}
function others(frm,hidden) {
	if(!hidden){
		$(".btn-info").removeClass("btn-info");
		$('.control-input [data-fieldname="others"]').addClass("btn-info");
	}

	frm.set_df_property("educational_qualification", "hidden", hidden);
	frm.set_df_property("previous_work_experience", "hidden", hidden);
	frm.set_df_property("history_in_company", "hidden", hidden);
	// your code here
}