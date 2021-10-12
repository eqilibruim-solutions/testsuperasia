odoo.define('superaia_salesrep_app.select_account', function (require) {
    'use strict';
    
    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');
    
    publicWidget.registry.select_account = publicWidget.Widget.extend({
        selector: '#saleOderModalCenter',
        events: {
          'change select': '_onClickSelectOption'
        },

        start: function () {
            $('#saleOderModalCenter').on('shown.bs.modal', function() {
                $(this).find('select').each(function() {
                  $(this).select2({
                    theme: 'bootstrap',
                    dropdownParent: $('#saleOderModalCenter'),
                    placeholder: 'Select a Account..',
                    width: '100%'
                  });
                  $(this).select2("open");

                  $(this).on('select2:select', function(e) {
                    var data = e.params.data;
                    console.log(data);
                  });
                });
              });
            return this._super.apply(this, arguments);
        },

        _onClickSelectOption: function(ev) {
          var $selectElm = $(ev.currentTarget);
          var accountID = $selectElm.selected().val();
          if (accountID) {
            ajax.jsonRpc('/selected-account/update', 'call', {
              'account_id': accountID,
            }).then(function(data) {
              if(data.redirect_url) {
                  window.location = data.redirect_url;
              }
          })
            
          }
          debugger;
          
        }

    });
});