odoo.define('product_barcode.ClientActionCustom', function (require) {
'use strict';

var client_action_custom = require('stock_barcode.ClientAction');
var utils = require('web.utils');
var rpc = require("web.rpc");
var core = require('web.core');
var _t = core._t;
client_action_custom.include({

     _makePages: function () {
        var pages = [];
        var defaultPage = {};
        var self = this;
        if (this._getLines(this.currentState).length) {
            // from https://stackoverflow.com/a/25551041
            var groups = _.groupBy(this._getLines(this.currentState), function (line) {
                return _.map(self._getPageFields({line: true}), function (field) {
                    return utils.into(line, field[1]);
                }).join('#');
            });
            pages = _.map(groups, function (group) {
                var page = {};
                _.map(self._getPageFields({line: true}), function (field) {
                    page[field[0]] = utils.into(group[0], field[1]);
                });
                page.lines = group;
                return page;
            });
        } else {
            _.each(self._getPageFields(), function (field) {
                defaultPage[field[0]] = utils.into(self.currentState, field[1]);
            });
            defaultPage.lines = [];
        }
//        pages = _.sortBy(pages, 'sequence');
//        pages = _.sortBy(pages, 'location_name')

        // Create a new page if the pair scanned location / default destination location doesn't
        // exist yet and the scanned location isn't the one of current page.
        var currentPage = this.pages[this.currentPageIndex];
        if (this.scanned_location && currentPage.location_id !== this.scanned_location.id) {
            var alreadyInPages = _.find(pages, function (page) {
                return page.location_id === self.scanned_location.id &&
                    (self.actionParams.model === 'stock.inventory' || page.location_dest_id === self.currentState.location_dest_id.id);
            });
            if (! alreadyInPages) {
                var pageValues = {
                    location_id: this.scanned_location.id,
                    location_name: this.scanned_location.display_name,
                    lines: [],
                };
                if (self.actionParams.model === 'stock.picking') {
                    pageValues.location_dest_id = this.currentState.location_dest_id.id;
                    pageValues.location_dest_name = this.currentState.location_dest_id.display_name;
                }
                pages.push(pageValues);
            }
        }

        if (pages.length === 0) {
            pages.push(defaultPage);
        }

        return pages;
    },

    _getState: function (recordId, state) {
        var self = this;
        var def;
        if (state) {
            def = Promise.resolve(state);
        } else {
            def = this._rpc({
                'route': '/stock_barcode/get_set_barcode_view_state',
                'params': {
                    'record_id': recordId,
                    'mode': 'read',
                    'model_name': self.actionParams.model,
                },
            });
        }
        return def.then(function (res) {
            self.currentState = res[0];
            self.initialState = $.extend(true, {}, res[0]);
            self.title += self.initialState.name;
            self.groups = {
                'group_stock_multi_locations': self.currentState.group_stock_multi_locations,
                'group_tracking_owner': self.currentState.group_tracking_owner,
                'group_tracking_lot': self.currentState.group_tracking_lot,
                'group_production_lot': self.currentState.group_production_lot,
                'group_uom': self.currentState.group_uom,
                'group_manager': self.currentState.stock_group_manager,
            };
            self.show_entire_packs = self.currentState.show_entire_packs;

            return res;
        });
    },
    _incrementLines: function (params) {
        var line = this._findCandidateLineToIncrement(params);
        var isNewLine = false;
        if (line) {
            // Update the line with the processed quantity.
            if (params.product.tracking === 'none' ||
                params.lot_id ||
                params.lot_name ||
                params.force_update
                )
                {
                if (this.actionParams.model === 'stock.picking') {
                    line.qty_done += params.product.qty;
                    if (params.package_id) {
                        line.package_id = params.package_id;
                    }
                    if (params.result_package_id) {
                        line.result_package_id = params.result_package_id;
                    }
                } else if (this.actionParams.model === 'stock.inventory') {
                    line.product_qty += params.product.qty || 1;
                }
            }
        } else {
            isNewLine = true;
            // Create a line with the processed quantity.
            if (params.product.tracking === 'none' ||
                params.lot_id ||
                params.lot_name
                ) {
                line = this._makeNewLine(params.product, params.barcode, params.product.qty || 1, params.package_id, params.result_package_id);
            } else {
                line = this._makeNewLine(params.product, params.barcode, 0, params.package_id, params.result_package_id);
            }
            this._getLines(this.currentState).push(line);
            this.pages[this.currentPageIndex].lines.push(line);
        }
        if (this.actionParams.model === 'stock.picking') {
            if (params.lot_id) {
                line.lot_id = [params.lot_id];
            }
            if (params.lot_name) {
                line.lot_name = params.lot_name;
            }
        } else if (this.actionParams.model === 'stock.inventory') {
            if (params.lot_id) {
                line.prod_lot_id = [params.lot_id, params.lot_name];
            }
        }
        return {
            'id': line.id,
            'virtualId': line.virtual_id,
            'lineDescription': line,
            'isNewLine': isNewLine,
        };
    },
    _step_product: async function (barcode, linesActions) {
        if (this.actionParams.model !== 'stock.picking') {
            return this._super.apply(this, arguments);
        }
        var self = this;
        this.currentStep = 'product';
        var errorMessage;
        var product = await this._isProduct(barcode);
        if (product){
            return this._rpc({
                        model: 'stock.picking',
                        method: 'check_product_on_barcode_scanned',
                        args: [this.actionParams.pickingId, product.id],
                    }).then(function (data){
                                    if (data && data[1] === 'existing_line') {
                            if (product) {
            if (product.tracking !== 'none') {
                self.currentStep = 'lot';
            }
//            var idOrVirtualId = self.scannedLines[self.scannedLines.length - 1];
//                console.log('-----------------idOrVirtualId---------------', idOrVirtualId)
//                console.log('-----------------------------------------------', self._getLines(self.currentState))
////                var p_edit_line = _.find(self._getLines(self.currentState), function (line) {
////                    console.log('---------p_edit_line-----------',p_edit_line)
////                    return line.virtual_id === idOrVirtualId || line.id === idOrVirtualId;
////                });
//                if (p_edit_line){
//                    console.log('----------------p_edit_line----------------',p_edit_line)
//                     product.qty = p_edit_line.product_uom_qty;
//                }

            var res = self._incrementLines({'product': product, 'barcode': barcode, 'force_update': true});
            if (res.isNewLine) {
                if (self.actionParams.model === 'stock.inventory') {
                    // FIXME sle: add owner_id, prod_lot_id, owner_id, product_uom_id
                    return self._rpc({
                        model: 'product.product',
                        method: 'get_theoretical_quantity',
                        args: [
                            res.lineDescription.product_id.id,
                            res.lineDescription.location_id.id,
                        ],
                    }).then(function (theoretical_qty) {
                        res.lineDescription.theoretical_qty = theoretical_qty;
                        linesActions.push([self.linesWidget.addProduct, [res.lineDescription, self.actionParams.model]]);
                        self.scannedLines.push(res.id || res.virtualId);
                        return $.when({linesActions: linesActions});
                    });
                } else {
                    linesActions.push([self.linesWidget.addProduct, [res.lineDescription, self.actionParams.model]]);
                }
            } else {
                if (product.tracking === 'none') {
                    linesActions.push([self.linesWidget.incrementProduct, [res.id || res.virtualId, product.qty || 1, self.actionParams.model]]);
                } else {
                    var match_product = _.find(self._getLines(self.currentState), function (line) {
                    return line.id === res.id;

                });
                if (match_product && match_product.product_uom_qty > 0){
                    var currentPage = self.pages[self.currentPageIndex];
                    var currentLine = _.find(currentPage.lines, function(line){
                        return line.id === res.id
                    });
                    if (currentLine && currentLine.product_uom_qty){
                        currentLine.qty_done = currentLine.product_uom_qty
                    }
                    linesActions.push([self.linesWidget.incrementProduct, [res.id || res.virtualId, match_product.product_uom_qty, self.actionParams.model]]);
                    }
                else{
                    linesActions.push([self.linesWidget.incrementProduct, [res.id || res.virtualId, 0, self.actionParams.model]]);
                }

                }
            }
            self.scannedLines.push(res.id || res.virtualId);
            return $.when({linesActions: linesActions});
        } }
//            if (data && data[1] === 'existing_line') {
//                            if (product) {
//            if (product.tracking !== 'none') {
//                self.currentStep = 'lot';
//            }
//            var res = self._incrementLines({'product': product, 'barcode': barcode});
//            if (res.isNewLine) {
//                if (self.actionParams.model === 'stock.inventory') {
//                    // FIXME sle: add owner_id, prod_lot_id, owner_id, product_uom_id
//                    return self._rpc({
//                        model: 'product.product',
//                        method: 'get_theoretical_quantity',
//                        args: [
//                            res.lineDescription.product_id.id,
//                            res.lineDescription.location_id.id,
//                        ],
//                    }).then(function (theoretical_qty) {
//                        res.lineDescription.theoretical_qty = theoretical_qty;
//                        linesActions.push([self.linesWidget.addProduct, [res.lineDescription, self.actionParams.model]]);
//                        self.scannedLines.push(res.id || res.virtualId);
//                        return $.when({linesActions: linesActions});
//                    });
//                } else {
//                    linesActions.push([self.linesWidget.addProduct, [res.lineDescription, self.actionParams.model]]);
//                }
//            } else {
//                if (product.tracking === 'none') {
//                    linesActions.push([self.linesWidget.incrementProduct, [res.id || res.virtualId, product.qty || 1, self.actionParams.model]]);
//                } else {
//                    linesActions.push([self.linesWidget.incrementProduct, [res.id || res.virtualId, 0, self.actionParams.model]]);
//                }
//            }
//            self.scannedLines.push(res.id || res.virtualId);
//            return $.when({linesActions: linesActions});
//        } }
        if (data && data[1] === 'extra_line') {
                   self.do_warn(_t("The scanned product is not a part of the order."));
            return $.when({linesActions: linesActions});
        }
                       })}
            else {
            var success = function (res) {
                return $.when({linesActions: res.linesActions});
            };
            var fail = function (specializedErrorMessage) {
                self.currentStep = 'product';
                if (specializedErrorMessage){
                    return $.Deferred().reject(specializedErrorMessage);
                }
                if (! self.scannedLines.length) {
                    if (self.groups.group_tracking_lot) {
                        errorMessage = _t("You are expected to scan one or more products or a package available at the picking's location");
                    } else {
                        errorMessage = _t('The scanned Barcode does not correspond to any Product!!!!');
                    }
                    return $.Deferred().reject(errorMessage);
                }

                var destinationLocation = self.locationsByBarcode[barcode];
                if (destinationLocation) {
                    return self._step_destination(barcode, linesActions);
                } else {
                    errorMessage = _t('The scanned Barcode does not correspond to any Product!!!!');
                    return $.Deferred().reject(errorMessage);
                }
            };
            return self._step_lot(barcode, linesActions).then(success, function () {
                return self._step_package(barcode, linesActions).then(success, fail);
            });
        }
        },
    _step_lot: function (barcode, linesActions) {
        if (this.actionParams.model !== 'stock.picking') {
            return this._super.apply(this, arguments);
        }
        if (! this.groups.group_production_lot) {
            return Promise.reject();
        }
        this.currentStep = 'lot';
        var errorMessage;
        var self = this;
        // Bypass this step if needed.
        if (self.productsByBarcode[barcode]) {
            return self._step_product(barcode, linesActions);
        } else if (self.locationsByBarcode[barcode]) {
            return self._step_destination(barcode, linesActions);
        }
        return this._rpc({
                        model: 'stock.picking',
                        method: 'check_lot_on_barcode_scanned',
                        args: [self.actionParams.pickingId, barcode],
                    }).then(function (data){
                                    if (data && data[1] === 'existing_lot') {



        var getProductFromLastScannedLine = function () {
            if (self.scannedLines.length) {
                var idOrVirtualId = self.scannedLines[self.scannedLines.length - 1];
                var line = _.find(self._getLines(self.currentState), function (line) {
                    return line.virtual_id === idOrVirtualId || line.id === idOrVirtualId;
                });
                if (line) {
                    var product = self.productsByBarcode[line.product_barcode || line.product_id.barcode];
                    // Product was added by lot or package
                    if (!product) {
                        return false;
                    }
                    product.barcode = line.product_barcode || line.product_id.barcode;
                    return product;
                }
            }
            return false;
        };

        var getProductFromCurrentPage = function () {
            return _.map(self.pages[self.currentPageIndex].lines, function (line) {
                return line.product_id.id;
            });
        };

        var getProductFromOperation = function () {
            return _.map(self._getLines(self.currentState), function (line) {
                return line.product_id.id;
            });
        };

        var readProduct = function (product_id) {
            var product_barcode = _.findKey(self.productsByBarcode, function (product) {
                return product.id === product_id;
            });

            if (product_barcode) {
                var product = self.productsByBarcode[product_barcode];
                product.barcode = product_barcode;
                return Promise.resolve(product);
            } else {
                return self._rpc({
                    model: 'product.product',
                    method: 'read',
                    args: [product_id],
                }).then(function (product) {
                    return Promise.resolve(product[0]);
                });
            }
        };

        var getLotInfo = function (lots) {
            var products_in_lots = _.map(lots, function (lot) {
                return lot.product_id[0];
            });
            var products = getProductFromLastScannedLine();
            var product_id = _.intersection(products, products_in_lots);
            if (! product_id.length) {
                products = getProductFromCurrentPage();
                product_id = _.intersection(products, products_in_lots);
            }
            if (! product_id.length) {
                products = getProductFromOperation();
                product_id = _.intersection(products, products_in_lots);
            }
            if (! product_id.length) {
                product_id = [lots[0].product_id[0]];
            }
            return readProduct(product_id[0]).then(function (product) {
                var lot = _.find(lots, function (lot) {
                    return lot.product_id[0] === product.id;
                });
                return Promise.resolve({lot_id: lot.id, lot_name: lot.display_name, product: product});
            });
        };

        var searchRead = function (barcode) {
            // Check before if it exists reservation with the lot.
            var line_with_lot = _.find(self.currentState.move_line_ids, function (line) {
                return (line.lot_id && line.lot_id[1] === barcode) || line.lot_name === barcode;
            });
            var def;
            if (line_with_lot) {
                def = Promise.resolve([{
                    name: barcode,
                    display_name: barcode,
                    id: line_with_lot.lot_id[0],
                    product_id: [line_with_lot.product_id.id, line_with_lot.display_name],
                }]);
            } else {
                def = self._rpc({
                    model: 'stock.production.lot',
                    method: 'search_read',
                    domain: [['name', '=', barcode]],
                });
            }
            return def.then(function (res) {
                if (! res.length) {
                    errorMessage = _t('The scanned lot does not match an existing one.');
                    return Promise.reject(errorMessage);
                }
                return getLotInfo(res);
            });
        };

        var create = function (barcode, product) {
            return self._rpc({
                model: 'stock.production.lot',
                method: 'create',
                args: [{
                    'name': barcode,
                    'product_id': product.id,
                    'company_id': self.currentState.company_id[0],
                }],
            });
        };

        var def;
        if (self.currentState.use_create_lots &&
            ! self.currentState.use_existing_lots) {
            // Do not create lot if product is not set. It could happens by a
            // direct lot scan from product or source location step.
            var product = getProductFromLastScannedLine();
            if (! product  || product.tracking === "none") {
                return Promise.reject();
            }
            def = Promise.resolve({lot_name: barcode, product: product});
        } else if (! self.currentState.use_create_lots &&
                    self.currentState.use_existing_lots) {
            def = searchRead(barcode);
        } else {
            def = searchRead(barcode).then(function (res) {
                return Promise.resolve(res);
            }, function (errorMessage) {
                var product = getProductFromLastScannedLine();
                if (product && product.tracking !== "none") {
                    return create(barcode, product).then(function (lot_id) {
                        return Promise.resolve({lot_id: lot_id, lot_name: barcode, product: product});
                    });
                }
                return Promise.reject(errorMessage);
            });
        }
        return def.then(function (lot_info) {
            var product = lot_info.product;
            if (product.tracking === 'serial' && self._lot_name_used(product, barcode)){
                errorMessage = _t('The scanned serial number is already used.');
                return Promise.reject(errorMessage);
            }
//            var idOrVirtualId = self.scannedLines[self.scannedLines.length - 1];
//                var edit_line = _.find(self._getLines(self.currentState), function (line) {
//                    return line.virtual_id === idOrVirtualId || line.id === idOrVirtualId;
//                });
//                if (edit_line){
//
//                     product.qty = edit_line.product_uom_qty;
//                }
            var res = self._incrementLines({
                'product': product,
                'barcode': lot_info.product.barcode,
                'lot_id': lot_info.lot_id,
                'lot_name': lot_info.lot_name
            });
            if (res.isNewLine) {
                self.scannedLines.push(res.lineDescription.virtual_id);
                linesActions.push([self.linesWidget.addProduct, [res.lineDescription, self.actionParams.model]]);
            } else {
                if (self.scannedLines.indexOf(res.lineDescription.id) === -1) {
                    self.scannedLines.push(res.lineDescription.id || res.lineDescription.virtual_id);
                }
                var match_line = _.find(self._getLines(self.currentState), function (line) {

                    return line.id === res.id;

                });
                if (match_line && match_line.product_uom_qty > 0){
                    var currentPage = self.pages[self.currentPageIndex];
                    var currentLine = _.find(currentPage.lines, function(line){
                        return line.id === res.id
                    });
                    if (currentLine && currentLine.product_uom_qty){
                        currentLine.qty_done = currentLine.product_uom_qty
                    }
                    linesActions.push([self.linesWidget.incrementProduct, [res.id || res.virtualId, match_line.product_uom_qty, self.actionParams.model]]);

                }
                else{
                    linesActions.push([self.linesWidget.incrementProduct, [res.id || res.virtualId, 1, self.actionParams.model]]);
                }
                linesActions.push([self.linesWidget.setLotName, [res.id || res.virtualId, barcode]]);
            }
            return Promise.resolve({linesActions: linesActions});
        });
        }
        if (data && data[1] === 'extra_lot') {
                   self.do_warn(_t("The scanned Lot is not part of the order."));
                   location.reload();
            return $.when({linesActions: linesActions});}
            })
    },
});
});