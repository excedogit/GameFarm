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


from openerp.osv import osv, fields
from openerp.tools.translate import _
import re

class customer_followup(osv.osv):
    _name = 'r3x_customer_statement.followup'
    _description = 'Account Statement Follow-up'
    _rec_name = 'name'
    _columns = {
        'followup_line': fields.one2many('r3x_customer_statement.followup.line', 'followup_id', 'Follow-up'),
        'company_id': fields.many2one('res.company', 'Company', required=True),
        'name': fields.related('company_id', 'name', string = "Name"),
    }
    _defaults = {
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(cr, uid, 'account_followup.followup', context=c),
    }
    _sql_constraints = [('company_uniq', 'unique(company_id)', 'Only one follow-up per company is allowed')]


class customer_followup_line(osv.osv):

    def _get_default_template(self, cr, uid, ids, context=None):
        try:
            return self.pool.get('ir.model.data').get_object_reference(cr, uid, 'r3x_customer_statement', 'email_template_customer_account_statement')[1]
        except ValueError:
            return False

    _name = 'r3x_customer_statement.followup.line'
    _description = 'Customer Follow-up Criteria'
    _columns = {
        'name': fields.char('Follow-Up Action', size=64, required=True),
        'sequence': fields.integer('Sequence', help="Gives the sequence order when displaying a list of follow-up lines."),
        'delay': fields.integer('Due Days', help="The number of days after the due date of the invoice to wait before sending the reminder.  Could be negative if you want to send a polite alert beforehand.", required=True),
        'followup_id': fields.many2one('r3x_customer_statement.followup', 'Follow Ups', required=True, ondelete="cascade"),
        'description': fields.text('Printed Message', translate=True),
        'send_email':fields.boolean('Send an Email', help="When processing, it will send an email"),
        'send_letter':fields.boolean('Send a Letter', help="When processing, it will print a letter"),
        'manual_action':fields.boolean('Manual Action', help="When processing, it will set the manual action to be taken for that customer. "),
        'manual_action_note':fields.text('Action To Do', placeholder="e.g. Give a phone call, check with others , ..."),
        'manual_action_responsible_id':fields.many2one('res.users', 'Assign a Responsible', ondelete='set null'),
        'email_template_id':fields.many2one('email.template', 'Email Template', ondelete='set null'),
    }
    _order = 'delay'
    _sql_constraints = [('days_uniq', 'unique(followup_id, delay)', 'Days of the follow-up levels must be different')]
    _defaults = {
        'send_email': True,
        'send_letter': True,
        'manual_action':False,
        'description': """
        Dear %(partner_name)s,
        Please find the enclosed Account Statement.
Best Regards,
""",
    'email_template_id': _get_default_template,
    }


    def _check_description(self, cr, uid, ids, context=None):
        for line in self.browse(cr, uid, ids, context=context):
            if line.description:
                try:
                    line.description % {'partner_name': '', 'date':'', 'user_signature': '', 'company_name': ''}
                except:
                    return False
        return True

    _constraints = [
        (_check_description, 'Your description is invalid, use the right legend or %% if you want to use the percent character.', ['description']),
    ]



class res_partner(osv.osv):
    _inherit="res.partner"

    def get_representative_areas(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for record in self.browse(cr, uid, ids, context=context):
            rep = record.rep_id
            if rep.areas:
                res[record.id] = [x.id for x in rep.areas]
            else:
                res[record.id] = False
        return res

    def _get_customer_amounts_and_date(self, cr, uid, ids, name, arg, context=None):
        '''
        Function that computes values for the followup functional fields. Note that 'payment_amount_due'
        is similar to 'credit' field on res.partner except it filters on user's company.
        '''
        res = {}
        company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
        current_date = fields.date.context_today(self, cr, uid, context=context)
        for partner in self.browse(cr, uid, ids, context=context):
            worst_due_date = False
            amount_due = amount_overdue = 0.0
            for aml in partner.unreconciled_aml_ids:
                if (aml.company_id == company):
                    date_maturity = aml.date_maturity or aml.date
                    if not worst_due_date or date_maturity < worst_due_date:
                        worst_due_date = date_maturity
                    amount_due += aml.result
                    if (date_maturity <= current_date):
                        amount_overdue += aml.result
            res[partner.id] = amount_due
        return res

    _columns = {
                'account_move' : fields.many2one('account.move','Analytic Move',ondelete="cascade"),

                'statement_ids':fields.one2many('account.payment.display.credit', 'partner_id', domain=['&', ('reconcile_id', '=', False), '&',
                           ('account_id.active','=', True), '&', ('account_id.type', '=', 'receivable'), ('state', '!=', 'draft')],context={'group_by':'move_id'}),

                'customer_payment_amount_due':fields.function(_get_customer_amounts_and_date,
                                                 type='float', string="Balance Due"),

                'property_payment_term': fields.property(
                                        'account.payment.term',
                                        type='many2one',
                                        relation='account.payment.term',
                                        string ='Customer Payment Term',
                                        view_load=True,
                                        help="This payment term will be used instead of the default one for sale orders and customer invoices"),
                }


    def do_customer_statement_button_print(self, cr, uid, ids, context=None):
        assert(len(ids) == 1)
        company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
        #search if the partner has accounting entries to print. If not, it may not be present in the
        #psql view the report is based on, so we need to stop the user here.
        if not self.pool.get('account.payment.display.credit').search(cr, uid, [
                                                                   ('partner_id', '=', ids[0]),
                                                                   ('account_id.type', '=', 'receivable'),
                                                                   ('reconcile_id', '=', False),
                                                                   ('state', '!=', 'draft'),
                                                                   ('company_id', '=', company_id),
                                                                  ], context=context):
            raise osv.except_osv(_('Error!'),_("The partner does not have any accounting entries to print in the Customer Statement for the current company."))
        self.message_post(cr, uid, [ids[0]], body=_('Customer Statement report'), context=context)
        #build the id of this partner in the psql view. Could be replaced by a search with [('company_id', '=', company_id),('partner_id', '=', ids[0])]
        wizard_partner_ids = [ids[0] * 10000 + company_id]
        followup_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id

        if not followup_id:
            raise osv.except_osv(_('Error!'),_("There is no Customer Statement defined for the current company."))
        data = {
            'date': fields.date.today(),
            'followup_id': followup_id,
        }
        #call the print overdue report on this partner....
        return self.do_customer_statement_print(cr, uid, wizard_partner_ids, data, context=context)


    def do_customer_statement_print(self, cr, uid, wizard_partner_ids, data, context=None):
        #wizard_partner_ids are ids from special view, not from res.partner
        if not wizard_partner_ids:
            return {}
        data['partner_ids'] = wizard_partner_ids
        datas = {
             'ids': [],
             'model': 'r3x_customer_statement',
             'form': data
        }
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'r3x_customer_statement_print',
            'datas': datas,
            }

    def do_customer_mail(self, cr, uid, partner_ids, context=None):
        if context is None:
            context = {}
        ctx = context.copy()
        ctx['followup'] = True
        if partner_ids[0] == ctx.get('default_parent_id'):
            ctx['default_parent_id']=''
        #partner_ids are res.partner ids
        # If not defined by latest follow-up level, it will be the default template if it can find it
        mtp = self.pool.get('email.template')
        unknown_mails = 0
        for partner in self.browse(cr, uid, partner_ids, context=ctx):
            if partner.email and partner.email.strip():
                level = partner.latest_followup_level_id_without_lit
                if level and level.send_email and level.email_template_id and level.email_template_id.id:
                    mtp.send_mail(cr, uid, level.email_template_id.id, partner.id, context=ctx)
                else:
                    mail_template_id = self.pool.get('ir.model.data').get_object_reference(cr, uid,
                                                    'r3x_customer_account_statement', 'email_template_customer_account_statement')
                    mtp.send_mail(cr, uid, mail_template_id[1], partner.id, context=ctx)
            else:
                unknown_mails = unknown_mails + 1
                action_text = _("Email not sent because of email address of partner not filled in")
        return unknown_mails


    #Function Added from Account Voucher...................
    def display_screen(self,cr,uid,ids,context=None):
        """
        Returns a dict that contains new values and context

        @param partner_id: latest value from user input for field partner_id
        @param args: other arguments
        @param context: context arguments, like lang, time zone

        @return: Returns a dict which contains new values, and context
        """
        def _remove_noise_in_o2m():
            """if the line is partially reconciled, then we must pay attention to display it only once and
                in the good o2m.
                This function returns True if the line is considered as noise and should not be displayed
            """
            if line.reconcile_partial_id:
                if currency_id == line.currency_id.id:
                    if line.amount_residual_currency <= 0:
                        return True
                else:
                    if line.amount_residual <= 0:
                        return True
            return False

        if context is None:
            context = {}
        context_multi_currency = context.copy()

        currency_pool = self.pool.get('res.currency')
        move_line_pool = self.pool.get('account.move.line')
        partner_pool = self.pool.get('res.partner')
        journal_pool = self.pool.get('account.journal')
        line_pool = self.pool.get('account.voucher.line')
        payment_display=self.pool.get('account.payment.display.credit')

        # Unlink all the records from the Customer Statement Table and Re write the Records once again...
        payment_ids = payment_display.search(cr,uid,[('partner_id','=',ids[0])])
        if payment_ids:
            payment_display.unlink(cr,uid,payment_ids)

        
        #set default values
        default = {
            'value': {'line_dr_ids': [] ,'line_cr_ids': []},
        }

        #drop existing lines
        line_ids = ids and line_pool.search(cr, uid, [('voucher_id', '=', ids[0])]) or False
        if line_ids:
            line_pool.unlink(cr, uid, line_ids)

        partner = partner_pool.browse(cr, uid, ids[0], context=context)
        currency_id = partner.company_id.currency_id.id

        total_credit = 0.0
        total_debit = 0.0
        account_type = 'receivable'

        ids = move_line_pool.search(cr, uid, [('state','=','valid'), ('account_id.type', '=', account_type), ('reconcile_id', '=', False), ('partner_id', '=', partner.id)], context=context)

        invoice_id = context.get('invoice_id', False)
        company_currency = partner.company_id.currency_id.id
        move_lines_found = []

        #order the lines by most old first
        ids.reverse()
        account_move_lines = move_line_pool.browse(cr, uid, ids, context=context)

        #compute the total debit/credit and look for a matching open amount or invoice
        for line in account_move_lines:
            if _remove_noise_in_o2m():
                continue

            if invoice_id:
                if line.invoice.id == invoice_id:
                    #if the invoice linked to the voucher line is equal to the invoice_id in context
                    #then we assign the amount on that line, whatever the other voucher lines
                    move_lines_found.append(line.id)

            elif currency_id == line.currency_id.id:
                if line.amount_residual_currency == price:
                    move_lines_found.append(line.id)
                    break
                total_credit += line.credit and line.amount_currency or 0.0
                total_debit += line.debit and line.amount_currency or 0.0

        #voucher line creation
        for line in account_move_lines:
            price=0
            if _remove_noise_in_o2m():
                continue

            if line.currency_id and currency_id == line.currency_id.id:
                amount_original = abs(line.amount_currency)
                amount_unreconciled = abs(line.amount_residual_currency)
            else:
                #always use the amount booked in the company currency as the basis of the conversion into the voucher currency
                amount_original = currency_pool.compute(cr, uid, company_currency, currency_id, line.credit or line.debit or 0.0, context=context_multi_currency)
                amount_unreconciled = currency_pool.compute(cr, uid, company_currency, currency_id, abs(line.amount_residual), context=context_multi_currency)
            line_currency_id = line.currency_id and line.currency_id.id or company_currency
            
            rs = {
                'ref':line.ref,
                'date':line.date,
                'blocked':line.blocked,
                'company_id':line.company_id.id,                  
                'invoice_date': line.date_created,
                'reference': line.name,
                'partner_id':partner.id,
                'state':line.state,
                'reconcile_id':False, 
                'invoice_no':line.move_id.name,
                'move_id':line.move_id,
                'type': line.credit and 'dr' or 'cr',
                'move_line_id':line.id,
                'account_id':line.account_id.id,
                'amount_original': amount_original,
                'amount': (line.id in move_lines_found) and min(abs(price), amount_unreconciled) or 0.0,
                'date':line.date,
                'date_maturity':line.date_maturity,
                'amount_unreconciled': amount_unreconciled,
                'currency_id': line_currency_id,
            }
            price -= rs['amount']
            #in case a corresponding move_line hasn't been found, we now try to assign the voucher amount
            #on existing invoices: we split voucher amount by most old first, but only for lines in the same currency
            if not move_lines_found:
                if currency_id == line_currency_id:
                    if line.credit:
                        amount = min(amount_unreconciled, abs(total_debit))
                        rs['amount'] = amount
                        total_debit -= amount
                    else:
                        amount = min(amount_unreconciled, abs(total_credit))
                        rs['amount'] = amount
                        total_credit -= amount

            if rs['amount_unreconciled'] == rs['amount']:
                rs['reconcile'] = True

            if rs['type'] == 'cr':
                default['value']['line_cr_ids'].append(rs)
            else:
                default['value']['line_dr_ids'].append(rs)
                
        for data in default['value'].keys():
            for value in default['value'][data]:
                if value['type']=='cr':
                    debit=value['amount_original']
                    credit=debit-value['amount_unreconciled']
                    
                else:
                    # Here Customer Refunds , or Customer Excess Amount is Recorded..
                    credit=value['amount_original']
                    debit=credit-value['amount_unreconciled']
                value.update({'debit':debit,'credit':credit,'result':debit-credit})
                for ele in ['amount_unreconciled','move_line_id','type','amount_original','amount']:
                    value.pop(ele)

                #Writing the Fields to Table........
                payment_display.create(cr, uid,value,context=context)
                
        return True


    def get_customer_table_html(self, cr, uid, ids, context=None):
        """ Build the html tables to be included in emails send to partners,
            when reminding them their overdue invoices.
            :param ids: [id] of the partner for whom we are building the tables
            :rtype: string
        """
        from report import r3x_customer_statement_print_report as r3x_customer_statement_print

        assert len(ids) == 1
        if context is None:
            context = {}
        partner = self.browse(cr, uid, ids[0], context=context)
        #copy the context to not change global context. Overwrite it because _() looks for the lang in local variable 'context'.
        #Set the language to use = the partner language
        context = dict(context, lang=partner.lang)
        followup_table = ''
        if partner.unreconciled_aml_ids:
            company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
            current_date = fields.date.context_today(self, cr, uid, context=context)

            rml_parse = r3x_customer_statement_print.report_rappel(cr, uid, "followup_rml_parser")

            final_res = rml_parse._lines_get_with_partner(partner,company.id)

            for currency_dict in final_res:
                currency = currency_dict.get('line', [{'currency_id': company.currency_id}])[0]['currency_id']
                followup_table += '''
                <table border="1" width=100%% cellpadding="1" cellspacing="0">
                <tr>
                    <td><center><b>''' + _("Invoice Date") + '''</b></center></td>
                    <td><center><b>''' + _("Invoice No") + '''</b></center></td>
                    <td><center><b>''' + _("Due Date") + '''</b></center></td>
                    <td><center><b>''' + _("Invoices") + " (%s)" % (currency.symbol) + '''</b></center></td>
                    <td><center><b>''' + _("Payments") + " (%s)" % (currency.symbol) + '''</b></center></td>
                    <td><center><b>''' + _("Balance") + " (%s)" % (currency.symbol) + '''</b></center></td>
                </tr>
                '''
                total = 0
                for aml in currency_dict['line']:
                    block = aml['blocked'] and 'X' or ' '
                    total = total+aml['balance']
                    strbegin = "<TD><center>"
                    strend = "</center></TD>"
                    date = aml['date_maturity'] or aml['date']
                    if date <= current_date and (aml['debit'] - aml['credit'])> 0:
                        strbegin ="<TD><B><center>"
                        strend = "</center></B></TD>"
                    # Modifying the Date Fomrat to dd/mm/yyyy
                    dt=aml['date'].split('-')
                    ndt=dt[-1]+'-'+dt[1]+'-'+dt[0]
                    xdt=date.split('-')
                    mdt=xdt[-1]+'-'+xdt[1]+'-'+xdt[0]
                    followup_table +="<TR>" + strbegin + str(ndt) + strend + strbegin + aml['name'] + strend +strbegin + str(mdt) + strend + strbegin + str(rml_parse.formatLang(aml['debit'], dp='Account', currency_obj=currency)) + strend  + strbegin + str(rml_parse.formatLang(aml['credit'], dp='Account', currency_obj=currency)) + strend + strbegin + str(rml_parse.formatLang(aml['balance'], dp='Account', currency_obj=currency)) + strend + "</TR>"
                overdue_bal=0
                total = rml_parse.formatLang(total, dp='Account', currency_obj=currency)
                overdue_bal = rml_parse.formatLang(partner.payment_amount_overdue, dp='Account', currency_obj=currency)
                followup_table += '''<tr> </tr>
                                </table>
                                <center><B>''' + _("Total Balance") + ''' : %s</B> </center>'''%total
                followup_table +='''<center><B>''' + _("Total OverDue Balance") + ''' : %s</B> </center>''' %overdue_bal

                # Adding Periods Here in the Email Functionality...............
                followup_table += '''
                <table border="1" width=100%% cellpadding="1" cellspacing="0">
                <tr>
                    <td><center><b>''' + _("Older") + '''</b></center></td>
                    <td><center><b>''' + _("Period3") + '''</b></center></td>
                    <td><center><b>''' + _("Period2") + '''</b></center></td>
                    <td><center><b>''' + _("Period1") + '''</b></center></td>
                    <td><center><b>''' + _("Current") + '''</b></center></td>
                    <td><center><b>''' + _("Not Due") + '''</b></center></td>
                    <td><center><b>''' + _("Total") + '''</b></center></td>
                </tr>
                '''
        strbegin="<td><center>"
        strend="</center></td>"
        aml=final_res[0].values()[0][0]
        
        followup_table +="<TR>" +\
                          strbegin + str(rml_parse.formatLang(aml['older'], dp='Account', currency_obj=currency)) + strend  +\
                          strbegin +str(rml_parse.formatLang(aml['period3'], dp='Account', currency_obj=currency)) + strend +\
                          strbegin +str(rml_parse.formatLang(aml['period2'], dp='Account', currency_obj=currency)) + strend +\
                          strbegin +str(rml_parse.formatLang(aml['period1'], dp='Account', currency_obj=currency)) + strend +\
                          strbegin +str(rml_parse.formatLang(aml['current'], dp='Account', currency_obj=currency)) + strend +\
                          strbegin +str(rml_parse.formatLang(aml['direction'], dp='Account', currency_obj=currency)) + strend +\
                          strbegin +str(rml_parse.formatLang(aml['total'], dp='Account', currency_obj=currency)) + strend +\
                          "</TR></table>"
        followup_table+="<br></br>"
        return followup_table


class account_payment_display_credit(osv.osv):
    _name="account.payment.display.credit"

    _columns={
              'partner_id': fields.integer('partner_id'),
              'account_id': fields.many2one('account.account', 'Account', required=True, ondelete="cascade", domain=[('type','<>','view'), ('type', '<>', 'closed')], select=2),
              'move_id':fields.integer('move_id'),
              'reconcile_id':fields.char('reconcile_id',size=64),
              'state': fields.selection([('draft','Unbalanced'), ('valid','Balanced')], 'Status', readonly=True),
              'date_maturity': fields.date('Due date', select=True ,help="This field is used for payable and receivable journal entries. You can put the limit date for the payment of this line."),
              'invoice_date': fields.char('invoice date', size=64),
              'invoice_no': fields.char('invoice no',size=20),
              'reference':fields.char('Reference',size=200),
              'date':fields.date('Effective Date'),
              'ref': fields.char('Reference', size=64),
              'due_date':fields.date('Due date'),
              'debit':fields.float('debit'),
              'credit':fields.float('Credit'),
              'result':fields.float('Balance'),
              'company_id': fields.related('account_id', 'company_id', type='many2one', relation='res.company',
                            string='Company', store=True, readonly=True),
              'currency_id': fields.many2one('res.currency', 'Currency', help="The optional other currency if it is a multi-currency entry."),
              'blocked':fields.boolean('blocked'),
              }

    _order='date asc'