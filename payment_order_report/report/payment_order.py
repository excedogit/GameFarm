# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
import operator
import itertools
from openerp import pooler
from openerp.report import report_sxw

class payment_order(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        super(payment_order, self).__init__(cr, uid, name, context=context)
        self.amount = 0
        self.total=0
        self.main_total=0
        self.amount_total = 0
        self.localcontext.update( {
            'time': time,
            'get_invoice_name': self.get_invoice_name,
            'get_amount_total_in_currency': self.get_amount_total_in_currency,
            'get_amount_total': self.get_amount_total,
            'get_account_name': self.get_account_name,
            'get_lines': self.get_lines,
            'get_amount': self.get_amount,
            'get_total': self.get_total,
            'get_total_subtotal':self.get_total_subtotal,
            'get_amount_subtotal': self.get_amount_subtotal,
            'get_amount_subtotal_in_currency': self.get_amount_subtotal_in_currency,
            'get_amount_subtotal_curr': self.get_amount_subtotal_curr,
            'set_amount': self.set_amount,
            'set_total':self.set_total,
            'set_amount_total': self.set_amount_total,
            'set_main_total':self.set_main_total,
            'get_main_total':self.get_main_total
        })

    def get_invoice_name(self, invoice_id):
        if invoice_id:
            pool = pooler.get_pool(self.cr.dbname)
            value_name = pool.get('account.invoice').name_get(self.cr, self.uid, [invoice_id])
            if value_name:
                return value_name[0][1]
        return False

    def set_amount(self):
        self.amount = 0

    def set_total(self):
        self.total=0

    def set_amount_total(self):
        self.amount_total = 0

    def set_main_total(self):
        self.main_total=0

    def get_lines(self, o):
        res = []
        for payment in self.pool.get('payment.order').browse(self.cr, self.uid, [o.id]):
            for line in payment.line_ids:
                res.append({
                    'partner_id': line.partner_id.id,
                    'partner_name': line.partner_id.name,
                    'bank_account_name': self.get_account_name(line.bank_id.id) or '-',
                    'ref_name': self.get_invoice_name(line.ml_inv_ref.id),
                    'date': line.date,
                    'total': line.total or 0.0,
                    'amount': line.amount or 0.0,
                    'amount_currency': line.amount_currency
                })

        res = sorted(res, key=operator.itemgetter('partner_name'))
        groups = itertools.groupby(res, key=operator.itemgetter('partner_name'))
        result = [{'partner_name':k,'values':[x for x in v]} for k, v in groups]

        return result

    def get_amount(self, amount):
        self.amount += amount

    def get_total(self, total):
        self.total += total

    def get_total_subtotal(self):
        return self.total

    def get_amount_subtotal(self):
        return self.amount

    def get_amount_subtotal_curr(self, amount):
        self.amount_total += amount

    def get_amount_subtotal_in_currency(self):
        return self.amount_total

    def get_amount_total_in_currency(self, payment):
        total = 0.0
        if payment.line_ids:
            currency_cmp = payment.line_ids[0].currency.id
        else:
            return False
        for line in payment.line_ids:
            if currency_cmp == line.currency.id:
                total += line.amount_currency
            else:
                return False
        return total

    def get_amount_total(self, payment):
        total = 0.0
        if not payment.line_ids:
            return False
        for line in payment.line_ids:
            total += line.amount
        return total

    def get_main_total(self, payment):
        total = 0.0
        if not payment.line_ids:
            return False
        for line in payment.line_ids:
            total += line.total
        return total

    def get_account_name(self,bank_id):
        if bank_id:
            pool = pooler.get_pool(self.cr.dbname)
            value_name = pool.get('res.partner.bank').name_get(self.cr, self.uid, [bank_id])
            if value_name:
                return value_name[0][1]
        return False

report_sxw.report_sxw('report.payment.order.ext', 'payment.order', 'payment_order_report/report/order.rml', parser=payment_order, header="external")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
