odoo.define('superasia_salesrep_app.cart_extension', function (require) {
    'use strict';
    
    var publicWidget = require('web.public.widget');
    var VariantMixin = require('sale.VariantMixin');
    var wSaleUtils = require('website_sale.utils');
    $.blockUI.defaults.css.border = '0';
    $.blockUI.defaults.css["background-color"] = '';
    $.blockUI.defaults.overlayCSS["opacity"] = '0.9';

    publicWidget.registry.SalesRepWebsiteSale = publicWidget.Widget.extend(VariantMixin, {
        selector: '.oe_website_sale',
        events: _.extend({}, VariantMixin.events || {}, {
            'change .oe_cart input.price_after_disc': '_onChangePriceAfterDisc',
            'change .oe_cart input[name="unit-disc"]': '_onChangeUnitDisc',
            'change select[name="shipping_country_id"]': '_onChangeShippingCountry',
        }),
    
        /**
         * @constructor
         */
        init: function () {
            this._super.apply(this, arguments);
            this._changePriceAfterDisc = _.debounce(this._changePriceAfterDisc.bind(this), 500);
            this._onChangeUnitDisc = _.debounce(this._onChangeUnitDisc.bind(this), 500);
            this._changeShippingCountry = _.debounce(this._changeShippingCountry.bind(this), 500);

            this.isWebsite = true;
        },

        start: function () {
            var self = this;
            var def = this._super.apply(this, arguments);
            return def;
        },

        updateDiscount: function(line_id, product_id, discountAmount) {
            let msg = "Updating ...";
            $.blockUI({
                'message': '<h2 class="text-white">' +
                    '<img alt="spinner" src="/web/static/src/img/spin.png" class="fa-pulse"/>' +
                    '<br />' + msg + '</h2>'
            });
            this._rpc({
                route: "/sales-rep/cart/update_discount",
                params: {
                    line_id: line_id,
                    product_id: product_id,
                    set_discount: discountAmount
                },
            }).then(function (data) {
                if (!('done' in data)) {
                    console.log("Discount not updated");
                }
                wSaleUtils.updateCartNavBar(data);
                $.unblockUI();

            });
        },
        _onChangePriceAfterDisc: function (ev) {
            this._changePriceAfterDisc(ev);
        },

        _changePriceAfterDisc: function (ev) {
            var $input = $(ev.currentTarget);
            var $dom = $input.closest('tr');
            let discountPrice = parseFloat($input.val() || 0, 10);
            var $unitPrice = $dom.find("input[name='unit_price']");
            var $productQty = $dom.find("input.quantity");
            var line_id = parseInt($productQty.data('line-id'), 10);
            var product_id = parseInt($productQty.data('product-id'), 10);

            if ($unitPrice.length) {
                let unitPrice = parseFloat($unitPrice.val());
                let discountAmount = parseFloat((unitPrice-discountPrice)*100/unitPrice);
                this.updateDiscount(line_id, product_id, discountAmount);
            }
        },

        _onChangeUnitDisc: function (ev) {
            this._changeUnitDisc(ev);
        },

        _changeUnitDisc: function (ev) {
            var $input = $(ev.currentTarget);
            var $dom = $input.closest('tr');
            let discountAmount = parseFloat($input.val() || 0, 10);
            var $productQty = $dom.find("input.quantity");
            var line_id = parseInt($productQty.data('line-id'), 10);
            var product_id = parseInt($productQty.data('product-id'), 10);
            if (isNaN(discountAmount) || discountAmount<0 || discountAmount > 100){
                alert("Not Allowed");
                $input.val(0.0);
                return
            }
         
            this.updateDiscount(line_id, product_id, discountAmount);
            
        },

        _onChangeShippingCountry: function (ev) {
            if (!this.$('.checkout_autoformat').length) {
                return;
            }
            this._changeShippingCountry();
        },

        _changeShippingCountry: function () {
            if (!$("#shipping_country_id").val()) {
                return;
            }
            this._rpc({
                route: "/shop/country_infos/" + $("#shipping_country_id").val(),
                params: {
                    mode: 'shipping',
                },
            }).then(function (data) {
                // placeholder phone_code
                //$("input[name='phone']").attr('placeholder', data.phone_code !== 0 ? '+'+ data.phone_code : '');
    
                // populate states and display
                var selectStates = $("select[name='shipping_state_id']");
                // dont reload state at first loading (done in qweb)
                if (selectStates.data('init')===0 || selectStates.find('option').length===1) {
                    if (data.states.length) {
                        selectStates.html('');
                        _.each(data.states, function (x) {
                            var opt = $('<option>').text(x[1])
                                .attr('value', x[0])
                                .attr('data-code', x[2]);
                            selectStates.append(opt);
                        });
                        selectStates.parent('div').show();
                    } else {
                        selectStates.val('').parent('div').hide();
                    }
                    selectStates.data('init', 0);
                } else {
                    selectStates.data('init', 0);
                }
    
                // manage fields order / visibility
                if (data.fields) {
                    // if ($.inArray('zip', data.fields) > $.inArray('city', data.fields)){
                    //     $(".div_zip").before($(".div_city"));
                    // } else {
                    //     $(".div_zip").after($(".div_city"));
                    // }
                    var all_fields = ["street", "zip", "city", "country_name"]; // "state_code"];
                    _.each(all_fields, function (field) {
                        $(".checkout_autoformat .div_" + field.split('_')[0]).toggle($.inArray(field, data.fields)>=0);
                    });
                }
            });
        },

    });
    
});

odoo.define('superasia_salesrep_app.order_page_detail', function (require) {
    'use strict';
    
    var publicWidget = require('web.public.widget');


    publicWidget.registry.SalesRepOrderPageDetail = publicWidget.Widget.extend({
        selector: '.sale_rep_order_info',
        events: {
            'keyup input[name="purchase_order-dup"]': '_onChangePONumber',
            'keyup textarea[name="note-dup"]': '_onChangeInternalNote',
            'click #sale_order_done': '_onClickDoneBtn',
        },
    
        /**
         * @constructor
         */
        init: function () {
            this._super.apply(this, arguments);
            // this._onChangePONumber = _.debounce(this._onChangePONumber.bind(this), 500);
            // this._onChangeInternalNote = _.debounce(this._onChangeInternalNote.bind(this), 500);

        },

        _onChangePONumber: function (ev) {
            if (!this.$('input[name="purchase_order"]').length) {
                return;
            }
            this._changePONumber(ev);
        },

        _changePONumber: function (ev) {
            let poNumber = $(ev.currentTarget).val();
            $('input[name="purchase_order"]').val(poNumber);
        },

        _onChangeInternalNote: function (ev) {
            if (!this.$('textarea[name="note"]').length) {
                return;
            }
            this._changeInternalNote(ev);
        },

        _changeInternalNote: function (ev) {
            let comment = $(ev.currentTarget).val();
            $('textarea[name="note"]').val(comment);
        },

        _onClickDoneBtn: function (ev) {
            ev.preventDefault();
            if ($('form#confirm_order_form').length) {
                $('form#confirm_order_form').submit();
            }
        }

    });
    
});