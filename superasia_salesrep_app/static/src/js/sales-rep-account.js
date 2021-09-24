odoo.define('superaia_salesrep_app.sales_rep_account', function (require) {
    'use strict';
    
    var publicWidget = require('web.public.widget');
    
    publicWidget.registry.searchAccountTable = publicWidget.Widget.extend({
        selector: '#wrap',
        events: {
            'keyup #search-input': '_onSearchAccounts',
        },

        _onSearchAccounts: function (ev) {
            var $input = $(ev.currentTarget);
            
            if ($('#all-accounts-table').length) {
                var oTable = $('#all-accounts-table').DataTable();
                oTable.search($input.val()).draw() ;
            }

        }


    });
});