# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2013 ZestyBeanz Technologies Pvt. Ltd.
#    (http://wwww.zbeanztech.com)
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

from datetime import date
import time
from openerp.osv import orm, fields
from openerp.osv import fields, osv
from openerp.tools.translate import _

class payment_order_create(osv.osv_memory):
    _inherit = 'payment.order.create'

    def create_payment(self, cr, uid, ids, context=None):
        flag = 0
        partner_pool = self.pool.get('res.partner')
        payment_pool = self.pool.get('payment.order.create').browse(cr, uid, ids, context=context)[0]
        if not  payment_pool.entries:
            flag = 1
        for payment in payment_pool.entries:
            part_obj = partner_pool.browse(cr, uid, payment.partner_id.id, context=context)
            for bank in part_obj.bank_ids:
                if bank.eft_check == True:
                    flag = 1
        if flag == 0:
            raise osv.except_osv(_('Warning!'), _('Select a bank where EFT is True for the partner!'))

        res=super(payment_order_create, self).create_payment( cr, uid, ids, context=context)
        return res

payment_order_create()


class payment_line(osv.osv):
    _inherit = 'payment.line'

    def _get_total(self, cursor, user, ids, name, args, context=None):
        if not ids:
            return {}
        currency_obj = self.pool.get('res.currency')
        move_obj=self.pool.get('account.move.line')
        inv_obj=self.pool.get('account.invoice')
        if context is None:
            context = {}
        res = {}

        # Added Code in the For Loop.....
        # Connected to Account account.move.line table with the help of move id retrieved the name of reference.
        # Connected to Account Invoice account.invoice with the help of reference and retrieved the residual (balance).
        for line in self.browse(cursor, user, ids, context=context):
            ctx = context.copy()
            ctx['date'] = line.order_id.date_done or time.strftime('%Y-%m-%d')
            currency_output= currency_obj.compute(cursor, user, line.currency.id,
                    line.company_currency.id,
                    line.move_line_id.stored_invoice_id.residual, context=ctx)
            res[line.id] = currency_output
        return res

    _columns={
              'total': fields.function(_get_total, string='Total Amount',
                        type='float', store=True,
                        help='Balance Amount for Particular Invoice'),
              }

class payment_order(osv.osv):
    _inherit="payment.order"
    _columns={
              'company_filter':fields.boolean('Group Companies'),
              'fixed_message':fields.char('EFT Message',size=8,required=1),
              }

class eft_export(orm.Model):
    '''EFT Export'''
    _name = 'banking.export.eft'
    _description = __doc__
    _rec_name = 'identification'

    _columns = {
        'payment_order_ids': fields.many2many(
            'payment.order',
            'account_payment_order_clieop_rel',
            'banking_export_clieop_id', 'account_order_id',
            'Payment Orders',
            readonly=True),
        'testcode':
            fields.selection([('T', _('Yes')), ('P', _('No'))],
                             'Test Run', readonly=True),
        'daynumber':
            fields.integer('ClieOp Transaction nr of the Day', readonly=True),
        'duplicates':
            fields.integer('Number of Duplicates', readonly=True),
        'prefered_date':
            fields.date('Prefered Processing Date',readonly=True),
        'no_transactions':
            fields.integer('Number of Transactions', readonly=True),
        'check_no_accounts':
            fields.char('Check Number Accounts', size=5, readonly=True),
        'total_amount':
            fields.float('Total Amount', readonly=True),
        'identification':
            fields.char('Identification', size=6, readonly=True, select=True),
        'filetype':
            fields.selection([
                ('CREDBET', 'Payment Batch'),
                ('SALARIS', 'Salary Payment Batch'),
                ('INCASSO', 'Direct Debit Batch'),
                ], 'File Type', size=7, readonly=True, select=True),
        'date_generated':
            fields.date('Generation Date', readonly=True, select=True),
        'file':
            fields.binary('ClieOp File', readonly=True,),
        'filename': fields.char(
            'File Name', size=32,
        ),
        'state':
            fields.selection([
                ('draft', 'Draft'),
                ('sent', 'Sent'),
                ('done', 'Reconciled'),
            ], 'State', readonly=True),
    }

    def get_daynr(self, cr, uid, context=None):
        '''
        Return highest day number
        '''
        last = 1
        last_ids = self.search(cr, uid, [
                ('date_generated', '=',
                 fields.date.context_today(self, cr,uid,context))
                ], context=context)
        if last_ids:
            last = 1 + max([x['daynumber'] for x in self.read(
                        cr, uid, last_ids, ['daynumber'],
                        context=context)])
        return last

    _defaults = {
        'date_generated': fields.date.context_today,
        'duplicates': 1,
        'state': 'draft',
        'daynumber': get_daynr,
    }
