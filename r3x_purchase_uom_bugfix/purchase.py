# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2013 Excedo Technologies  & Solutions Pvt. Ltd.
#    (http://wwww.excedo.in)
#    contact@zbeanztech.com
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv
from datetime import datetime, timedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
    
class purchase_order_line(osv.osv):
    _inherit = "purchase.order.line"
        
    def onchange_product_uom(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, context=None):
        """
        onchange handler of product_uom.
        """
        if context is None:
            context = {}
        context['load_from_uom_change'] = True
        return super(purchase_order_line, self).onchange_product_uom(cr, uid, ids, 
                    pricelist_id,product_id,qty,uom_id,partner_id, date_order=date_order, 
                    fiscal_position_id=fiscal_position_id, date_planned=date_planned,
                    name=name, price_unit=price_unit, context=context)
        
        
    def onchange_product_id(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, context=None):
        """
        onchange handler of product_id.
        """
        if context is None:
            context = {}
        if not context.get('load_from_uom_change',False):
            uom_id = False
            
        res = super(purchase_order_line, self).onchange_product_id(cr, uid, ids,pricelist_id,
                            product_id,qty,uom_id,partner_id,date_order=date_order, 
                            fiscal_position_id=fiscal_position_id, date_planned=date_planned,
                            name=name, price_unit=price_unit, context=context)
        return res
    
    
purchase_order_line()   
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: