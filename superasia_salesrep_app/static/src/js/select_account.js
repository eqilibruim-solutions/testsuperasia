odoo.define('superaia_salesrep_app.select_account', function (require) {
    'use strict';
    
    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');
    $.blockUI.defaults.css.border = '0';
    $.blockUI.defaults.css["background-color"] = '';
    $.blockUI.defaults.overlayCSS["opacity"] = '0.9';
    
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
            let msg = "Fetching Order ...";
            $.blockUI({
                'message': '<h2 class="text-white">' +
                    '<img alt="spinner" src="/web/static/src/img/spin.png" class="fa-pulse"/>' +
                    '<br />' + msg + '</h2>'
            });
            ajax.jsonRpc('/selected-account/update', 'call', {
              'account_id': accountID,
            }).then(function(data) {
              if(data.redirect_url) {
                  window.location.href = data.redirect_url;
                  $.unblockUI();
              }
            })
            
          }
          
        }

    });
});

odoo.define('superaia_salesrep_app.filter_account', function (require) {
  'use strict';
  
  var publicWidget = require('web.public.widget');
  

  publicWidget.registry.filter_account = publicWidget.Widget.extend({
      selector: '#filterCollapse',

      start: function () {
        if ($("#cityFilter").length) {
          $("#cityFilter").select2({
            theme: 'bootstrap',
          });
        }
        return this._super.apply(this, arguments);
      },

  });
});