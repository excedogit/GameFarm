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

import base64
import time
from openerp.osv import fields, osv
from datetime import datetime, date, timedelta
from openerp.osv import orm, fields
from openerp.tools.translate import _
from openerp import netsvc
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.addons.account_banking import sepa
from openerp.addons.gff_account_eft_export.wizard import clieop

def strpdate(arg):
    '''shortcut'''
    return datetime.strptime(arg, DEFAULT_SERVER_DATE_FORMAT).date()

def strfdate(arg):
    '''shortcut'''
    return arg.strftime(DEFAULT_SERVER_DATE_FORMAT)

class res_partner_bank(osv.osv):
    _inherit = "res.partner.bank"
    _columns = {
                'eft_user_id': fields.char('EFT User Id', size=62),
                'eft_check': fields.boolean('EFT')
                }
res_partner_bank()

class banking_export_eft_wizard(orm.TransientModel):
    _name = 'banking.export.eft.wizard'
    _description = 'Client EFT Export'
    _columns = {
        'state': fields.selection(
            [
                ('create', 'Create'),
                ('finish', 'Finish')
                ],
            'State',
            readonly=True,
        ),
        'reference': fields.char(
            'Reference', size=5,
            help=('The bank will use this reference in feedback communication '
                  'to refer to this run. Only five characters are available.'
                  ),
            ),
        'batchtype': fields.selection(
            [
                ('CLIEOPPAY', 'Payments'),
                ('CLIEOPSAL', 'Salary Payments'),
                ('CLIEOPINC', 'Direct Debits'),
            ], 'Type', readonly=True,
            ),
        'execution_date': fields.date(
            'Execution Date',
            help=('This is the date the file should be processed by the bank. '
                  'Don\'t choose a date beyond the nearest date in your '
                  'payments. The latest allowed date is 30 days from now.\n'
                  'Please keep in mind that banks only execute on working days '
                  'and typically use a delay of two days between execution date '
                  'and effective transfer date.'
                  ),
            ),
        'test': fields.boolean(
            'Test Run',
            help=('Select this if you want your bank to run a test process '
                  'rather then execute your orders for real.'
                  ),
            ),
        'fixed_message': fields.char(
            'Fixed Message', size=32,
            help=('A fixed message to apply to all transactions in addition to '
                  'the individual messages.'
                  ),
            ),
        # file fields
        'file_id': fields.many2one(
            'banking.export.eft',
            'ClieOp File',
            readonly=True
            ),
        # fields.related does not seem to support
        # fields of type selection
        'testcode': fields.selection(
            [('T', _('Yes')), ('P', _('No'))],
            'Test Run', readonly=True,
            ),
        'filetype': fields.selection(
            [
                ('CREDBET', 'Payment Batch'),
                ('SALARIS', 'Salary Payment Batch'),
                ('INCASSO', 'Direct Debit Batch'),
                ],
            'File Type',
            readonly=True,
            ),
        'prefered_date': fields.related(
            'file_id', 'prefered_date',
            type='date',
            string='Prefered Processing Date',
            readonly=True,
            ),
        'no_transactions': fields.related(
            'file_id', 'no_transactions',
            type ='integer',
            string='Number of Transactions',
            readonly=True,
            ),
        'check_no_accounts': fields.related(
            'file_id', 'check_no_accounts',
            type='char', size=5,
            string='Check Number Accounts',
            readonly=True,
            ),
        'total_amount': fields.related(
            'file_id', 'total_amount',
            type='float',
            string='Total Amount',
            readonly=True,
            ),
        'identification': fields.related(
            'file_id', 'identification',
            type='char', size=6,
            string='Identification',
            readonly=True,
            ),
        'file': fields.related(
            'file_id', 'file', type='binary',
            readonly=True,
            string='File',
            ),
        'filename': fields.related(
            'file_id', 'filename',
            type='char', size=32,
            readonly=True,
            string='Filename',
            ),
        'payment_order_ids': fields.many2many(
            'payment.order', 'rel_wiz_payorders', 'wizard_id',
            'payment_order_id', 'Payment Orders',
            readonly=True,
            ),
        }

    def create(self, cr, uid, vals, context=None):
        '''
        Retrieve a sane set of default values based on the payment orders
        from the context.
        '''
        if 'batchtype' not in vals:
            self.check_orders(cr, uid, vals, context)
        return super(banking_export_eft_wizard, self).create(
            cr, uid, vals, context)


    def check_orders(self, cr, uid, vals, context):
        '''
        Check payment type for all orders.

        Combine orders into one. All parameters harvested by the wizard
        will apply to all orders. This will in effect create one super
        batch for ClieOp, instead of creating individual parameterized
        batches. As only large companies are likely to need the individual
        settings per batch, this will do for now.
        Also mind that rates for batches are way higher than those for
        transactions. It pays to limit the number of batches.
        '''
        today = strpdate(fields.date.context_today(self, cr, uid, context=context))
        payment_order_obj = self.pool.get('payment.order')

        # Payment order ids are provided in the context
        payment_order_ids = context.get('active_ids', [])
        runs = {}
        # Only orders of same type can be combined
        payment_orders = payment_order_obj.browse(cr, uid, payment_order_ids)
        for payment_order in payment_orders:

            payment_type = payment_order.mode.type.code
            if payment_type in runs:
                runs[payment_type].append(payment_order)
            else:
                runs[payment_type] = [payment_order]

            if payment_order.date_prefered == 'fixed':
                if payment_order.date_scheduled:
                    execution_date = strpdate(payment_order.date_scheduled)
                else:
                    execution_date = today
            elif payment_order.date_prefered == 'now':
                execution_date = today
            elif payment_order.date_prefered == 'due':
                # Max processing date is 30 days past now, so limiting beyond that
                # will catch too early payments
                max_date = execution_date = today + timedelta(days=31)
                for line in payment_order.line_ids:
                    if line.move_line_id.date_maturity:
                        date_maturity = strpdate(line.move_line_id.date_maturity)
                        if date_maturity < execution_date:
                            execution_date = date_maturity
                    else:
                        execution_date = today
                if execution_date and execution_date >= max_date:
                    raise orm.except_orm(
                        _('Error'),
                        _('You can\'t create EFT orders more than 30 days in advance.')
                    )
        if len(runs) != 1:
            raise orm.except_orm(
                _('Error'),
                _('You can only combine payment orders of the same type')
            )

        type = runs.keys()[0]

        vals.update({
            'execution_date': strfdate(max(execution_date, today)),
            'batchtype': type,
            'reference': runs[type][0].reference[-5:],
            'payment_order_ids': [[6, 0, payment_order_ids]],
            'state': 'create',
            })

    def create_clieop(self, cr, uid, ids, context):
        '''
        Wizard to actually create the EFT file
        '''
        payment_order_obj = self.pool.get('payment.order')
        clieop_export = self.browse(cr, uid, ids, context)[0]
        clieopfile = None
        no_pay_orders = []
        amount = 0
        for payment_order in clieop_export.payment_order_ids:
            for line in payment_order.line_ids:
                if line:
                    amount = amount + line.total
                    no_pay_orders.append(line)
        number = 0
        collect={}
        flipped={}
        flipped_amount={}
        flipped_check={}
        records = len(no_pay_orders)

        if context.get('company_filter',''):
            for payment_order in clieop_export.payment_order_ids:
                for line in payment_order.line_ids:
                    for bank in line.partner_id.bank_ids:
                        collect.update({line.id:bank.acc_number})

            for key,value in collect.items():
                    if value not in flipped:
                        flipped[value] = [key]
                    else:
                        flipped[value].append(key)

            records = len(flipped)
            for key,val in flipped.items():
                if len(val) <=1:
                    del flipped[key]

            for data in flipped.keys():
                if  len(flipped[data]) >1:
                    cal=0
                    for id in flipped[data]:
                        for payment_order in clieop_export.payment_order_ids:
                            for line in payment_order.line_ids:
                                if line.id == id:
                                    cal = cal + line.total
                    flipped_amount.update({data:cal})

        for payment_order in clieop_export.payment_order_ids:
#             payment_order_obj.write(cr, uid, payment_order.id, {'date_done':time.strftime('%Y-%m-%d')})
            payment_order_id = payment_order.id
            if not clieopfile:
                # Just once: create EFT file
                our_account_owner = payment_order.mode.bank_id.owner_name \
                        or payment_order.mode.bank_id.partner_id.name
                #reference_no = payment_order.reference
                reference_no = payment_order.fixed_message
                bank_name = payment_order.mode.bank_id.bank_name or ''
                eft_user_id = payment_order.mode.bank_id.eft_user_id or ''
                acc_owner =  payment_order.mode.bank_id.partner_id.name
                acc_number =  payment_order.mode.bank_id.acc_number
                bank = payment_order.mode.bank_id.bank.name or ''
                bank_bic = payment_order.mode.bank_id.bank_bic or ''
                if payment_order.mode.bank_id.state == 'iban':
                    our_account_nr = payment_order.mode.bank_id.acc_number_domestic
                    if not our_account_nr:
                        our_account_nr = sepa.IBAN(
                            payment_order.mode.bank_id.acc_number
                            ).localized_BBAN
                else:
                    our_account_nr = payment_order.mode.bank_id.acc_number
                if not our_account_nr:
                    raise orm.except_orm(
                        _('Error'),
                        _('Your bank account has to have a valid account number')
                    )
                clieopfile = {'CLIEOPPAY': clieop.PaymentsFile,
                              'CLIEOPINC': clieop.DirectDebitFile,
                              'CLIEOPSAL': clieop.SalaryPaymentsFile,
                             }[clieop_export['batchtype']](
                                 identification = clieop_export['reference'],
                                 execution_date = clieop_export['execution_date'],
                                 name_sender = our_account_owner,
                                 banks_name = bank_name,
                                 eft_user_id = eft_user_id,
                                 no_of_orders = "%06d" % (int(records)),    #Modified Here int(len(no_pay_orders))
                                 total_amount = amount,
                                 bank = bank,
                                 bank_bic = bank_bic,
                                 accountno_sender = our_account_nr,
                                 seqno = self.pool.get(
                                     'banking.export.eft').get_daynr(
                                     cr, uid, context=context),
                                 test = clieop_export['test']
                             )

                # ClieOp3 files can contain multiple batches, but we put all
                # orders into one single batch. Ratio behind this is that a
                # batch costs more money than a single transaction, so it is
                # cheaper to combine than it is to split. As we split out all
                # reported errors afterwards, there is no additional gain in
                # using multiple batches.
                if clieop_export['fixed_message']:
                    messages = [clieop_export['fixed_message']]
                else:
                    messages = []
                # The first payment order processed sets the reference of the
                # batch.
                batch = clieopfile.batch(
                    messages = messages,
                    batch_id = clieop_export['reference']
                )
            for line in payment_order.line_ids:
                # Check on missing partner of bank account (this can happen!)
                if not line.bank_id or not line.bank_id.partner_id:
                    raise orm.except_orm(
                        _('Error'),
                        _('There is insufficient information.\r\n'
                          'Both destination address and account '
                          'number must be provided'
                         )
                    )
                partner_bank_bic = 0
                bank_id = 0
                for bank in line.partner_id.bank_ids:
                    if bank.eft_check == True:
                        bank_id = bank.acc_number
                        partner_bank_bic = bank.bank_bic
                        break

            # Functionality to Update the Company Filter Records
                if context.get('company_filter',''):
                    if bank_id in flipped.keys():
                        if bank_id in flipped_check.keys():
                            pass
                        else:
                            kwargs = dict(
                                          reference_no = reference_no,
                                          acc_owner = acc_owner,
                                          acc_number = acc_number,
                                          ref = clieop_export['reference'],
                                          partner_bank_bic = partner_bank_bic or '',
                                          bank_bic = bank_bic,
                                          partner_bank_no = bank_id,
                                          name = line.partner_id.name,
                                          amount = flipped_amount[bank_id],
                                          reference = line.communication or None,
                                          )
                            if line.communication2:
                                kwargs['messages'] = [line.communication2]
                            other_account_nr = (
                                                line.bank_id.state == 'iban' and
                                                line.bank_id.acc_number_domestic or
                                                line.bank_id.acc_number
                            )
                            iban = sepa.IBAN(other_account_nr)
                            # Is this an IBAN account?
                            if iban.valid:
                                if iban.countrycode != 'NL':
                                    raise orm.except_orm(
                                                 _('Error'),
                                                 _('You cannot send international bank transfers '
                                          'through ClieOp3!')
                                    )
                                other_account_nr = iban.localized_BBAN
                            if clieop_export['batchtype'] == 'CLIEOPINC':
                                kwargs['accountno_beneficiary'] = our_account_nr
                                kwargs['accountno_payer'] = other_account_nr
                            else:
                                kwargs['accountno_beneficiary'] = other_account_nr
                                kwargs['accountno_payer'] = our_account_nr
                            transaction = batch.transaction(**kwargs)

                        # Making Record to Updating The Key is done i,e.., True
                            flipped_check.update({bank_id:True})
                    else:
                        kwargs = dict(
                                  reference_no = reference_no,
                                  acc_owner = acc_owner,
                                  acc_number = acc_number,
                                  ref = clieop_export['reference'],
                                  partner_bank_bic = partner_bank_bic or '',
                                  bank_bic = bank_bic,
                                  partner_bank_no = bank_id,
                                  name = line.partner_id.name,
                                  amount = line.total,
                                  reference = line.communication or None,
                                  )
                        if line.communication2:
                            kwargs['messages'] = [line.communication2]
                        other_account_nr = (
                            line.bank_id.state == 'iban' and
                            line.bank_id.acc_number_domestic or
                            line.bank_id.acc_number
                            )
                        iban = sepa.IBAN(other_account_nr)
                        # Is this an IBAN account?
                        if iban.valid:
                            if iban.countrycode != 'NL':
                                raise orm.except_orm(
                                                 _('Error'),
                                   _('You cannot send international bank transfers '
                                  'through ClieOp3!')
                                )
                            other_account_nr = iban.localized_BBAN
                        if clieop_export['batchtype'] == 'CLIEOPINC':
                            kwargs['accountno_beneficiary'] = our_account_nr
                            kwargs['accountno_payer'] = other_account_nr
                        else:
                            kwargs['accountno_beneficiary'] = other_account_nr
                            kwargs['accountno_payer'] = our_account_nr
                        transaction = batch.transaction(**kwargs)

                else:
                    kwargs = dict(
                                  reference_no = reference_no,
                                  acc_owner = acc_owner,
                                  acc_number = acc_number,
                                  ref = clieop_export['reference'],
                                  partner_bank_bic = partner_bank_bic or '',
                                  bank_bic = bank_bic,
                                  partner_bank_no = bank_id,
                                  name = line.partner_id.name,
                                  amount = line.total,
                                  reference = line.communication or None,
                                  )
                    if line.communication2:
                        kwargs['messages'] = [line.communication2]
                    other_account_nr = (
                            line.bank_id.state == 'iban' and
                            line.bank_id.acc_number_domestic or
                            line.bank_id.acc_number
                            )
                    iban = sepa.IBAN(other_account_nr)
                    # Is this an IBAN account?
                    if iban.valid:
                        if iban.countrycode != 'NL':
                            raise orm.except_orm(
                                                 _('Error'),
                                   _('You cannot send international bank transfers '
                                  'through ClieOp3!')
                                )
                        other_account_nr = iban.localized_BBAN
                    if clieop_export['batchtype'] == 'CLIEOPINC':
                        kwargs['accountno_beneficiary'] = our_account_nr
                        kwargs['accountno_payer'] = other_account_nr
                    else:
                        kwargs['accountno_beneficiary'] = other_account_nr
                        kwargs['accountno_payer'] = our_account_nr
                    transaction = batch.transaction(**kwargs)


        # Generate the specifics of this clieopfile
        order = clieopfile.order
        file_id = self.pool.get('banking.export.eft').create(
            cr, uid, dict(
                filetype = order.name_transactioncode,
                identification = order.identification,
                prefered_date = strfdate(order.preferred_execution_date),
                total_amount = int(order.total_amount or 0) / 100.0,
                check_no_accounts = order.total_accountnos,
                no_transactions = order.nr_posts,
                testcode = order.testcode,
                file = base64.encodestring(clieopfile.rawdata),
                filename = 'EFT-{0}.txt'.format(order.identification),
                daynumber = int(clieopfile.header.file_id[2:]),
                payment_order_ids = [
                    [6, 0, [x.id for x in clieop_export['payment_order_ids']]]
                     ],
                    ), context)
        self.write(cr, uid, [ids[0]], dict(
                filetype = order.name_transactioncode,
                testcode = order.testcode,
                file_id = file_id,
                state = 'finish',
                ), context)
        if payment_order_id:
            payment_order_obj.write(cr, uid, payment_order_id, {'date_done':time.strftime('%Y-%m-%d')})
        return {
            'name': _('Client EFT Export'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'domain': [],
            'context': dict(context, active_ids=ids),
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': ids[0] or False,
        }


    def cancel_clieop(self, cr, uid, ids, context):
        '''
        Cancel the ClieOp: just drop the file
        '''
        clieop_export = self.read(cr, uid, ids, ['file_id'], context)[0]
        self.pool.get('banking.export.eft').unlink(cr, uid, clieop_export['file_id'][0])
        return {'type': 'ir.actions.act_window_close'}

    def save_clieop(self, cr, uid, ids, context):
        '''
        Save the ClieOp: mark all payments in the file as 'sent', if not a test
        '''
        clieop_export = self.browse(
            cr, uid, ids, context)[0]
        if not clieop_export['test']:
            clieop_obj = self.pool.get('banking.export.eft')
            payment_order_obj = self.pool.get('payment.order')
            clieop_file = clieop_obj.write(
                cr, uid, clieop_export['file_id'].id, {'state': 'sent'}
                )
            wf_service = netsvc.LocalService('workflow')
            for order in clieop_export['payment_order_ids']:
                wf_service.trg_validate(uid, 'payment.order', order.id, 'sent', cr)
        return {'type': 'ir.actions.act_window_close'}
