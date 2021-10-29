odoo.define('mwbecloud_sbportalmanager.Productconf', function (require) {
'use strict';
var ajax = require('web.ajax');

$(document).ready(function(){

        
        $(".add-row").click(function(){

            var name = $("#name").val();

            var email = $("#email").val();

            var markup = "<tr><td><input type='checkbox' id ='events_chc_box_rad_id' name='record'></td><td>" + name + "</td><td>" + email + "</td></tr>";

            $("table tbody").append(markup);

        });

        

        // Find and remove selected table rows

        $(".delete-row").click(function(){

            $("table tbody").find('input[name="record"]').each(function(){

                if($(this).is(":checked")){

                    $(this).parents("tr").remove();

                }

            });

        });


        $(".submit-rows").click(function(){
			console.log('printtttaaaatt');
			// document.getElementById('info').innerHTML = "";
        	var myTab = document.getElementById('empTable');			// var myTab = $('#events_chc_box_rad_id:checked').val();
			console.log(myTab);
	        var arrValues = new Array();


	        // loop through each row of the table.
	        for (var row = 1; row < myTab.rows.length - 1; row++) {
	        	// loop through each cell in a row.
				console.log('rpwsssss')

	            for (var c = 0; c < myTab.rows[row].cells.length; c++) {  
	                var element = myTab.rows.item(row).cells[c];

					console.log(element);
					console.log('ssssselement');
					arrValues.push(element.innerText)
	            }
	        }
	        
	        // The final output.
	        // document.getElementById('output').innerHTML = arrValues;
			console.log(arrValues);
			ajax.jsonRpc('/newquote', 'call', {'invoices_id': arrValues}).then(function (url) {
				myTempWindow = window.open(url);

				location.reload(true);
				window.location = window.location.href+'?eraseCache=true';
				$('html[manifest=saveappoffline.appcache]').attr('content', ''); 
			});
			});







    });    

});

odoo.define('superasiab2b_b2c.order_state_change', function (require) {
"use strict";
var publicWidget = require('web.public.widget');
var ajax = require('web.ajax');

publicWidget.registry.websiteSaleCartLink = publicWidget.Widget.extend({
    selector: '#set_draft_state ',
    events: {
        'click': '_onClick',
    },

	_onClick: function (ev) { 
		var $dm = $(ev.currentTarget);
		var order_id = parseInt($dm.data("order-id"),10);
		debugger;
		if (order_id) {
			ajax.jsonRpc('/order-change-state', 'call', {'order_id': order_id})
				.then(function (data) {
					window.location.reload();
				});
		}
	},
});

});


odoo.define('superasiab2b_b2c.retailer_contact_form', function (require) {
	"use strict";
	var publicWidget = require('web.public.widget');
	var ajax = require('web.ajax');
	
	publicWidget.registry.retailerContactForm = publicWidget.Widget.extend({
		selector: 'form[action="/b2baccountactivation"]',

		start: function () {
			var $inputUtmMedium = this.$el.find('input[name="utm_medium"]')
			if ($inputUtmMedium.length){
				let utmMedium = this.getURLParameter('utm_medium')
				$inputUtmMedium.val(utmMedium ? utmMedium:'')
			}
			return this._super.apply(this, arguments);
			
		},

		getURLParameter: function (sParam){
			var sPageURL = window.location.search.substring(1);
			var sURLVariables = sPageURL.split('&');
			for (var i = 0; i < sURLVariables.length; i++) 
			{
				var sParameterName = sURLVariables[i].split('=');
				if (sParameterName[0] == sParam) 
				{
					return sParameterName[1];
				}
			}
		}
	});
	
});
