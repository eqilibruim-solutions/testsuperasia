odoo.define('superaia_salesrep_app.sales_rep_product_list', function (require) {
    'use strict';
    
    var publicWidget = require('web.public.widget');

    
    publicWidget.registry.imageModalPopup = publicWidget.Widget.extend({
        selector: '.oe_website_sale',
        events: {
            'click .img-pop': '_imgModalPopUp',
        },

        _imgModalPopUp: function (ev) {
            ev.preventDefault()
            $('.imagepreview').attr('src', $(ev.currentTarget).find('img').attr('src'));
            $('#imagemodal').modal('show'); 
        }


    });

    publicWidget.registry.salesRepShopHeader = publicWidget.Widget.extend({
        selector: '.sale_rep_product_list #function_top_menu',
        events:{
            'change form.js_attributes input, form.js_attributes select': '_onChangeAttributeApp',
         },
         _onChangeAttributeApp: function (ev) {
            if (!ev.isDefaultPrevented()) {
                ev.preventDefault();
                $(ev.currentTarget).closest("form").submit();
            }
          },
        });
    
    publicWidget.registry.salesRepProductCategory = publicWidget.Widget.extend({
        selector: '.sale_rep_product_list',
        events: {
            'change select#product-category': '_onChangeProductCategory',
            },
            _onChangeProductCategory: function (ev) {
                let categoryUrl = $(ev.currentTarget).val();
                window.location.href = categoryUrl;
            },
        });
});
