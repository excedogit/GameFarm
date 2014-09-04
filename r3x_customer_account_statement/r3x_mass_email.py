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
import base64
from openerp.osv import osv, orm, fields
from openerp import SUPERUSER_ID
from openerp.tools.translate import _
from openerp.addons.account_financial_report_webkit.report.webkit_parser_header_fix import HeaderFooterTextWebKitParser
from openerp.addons.account_financial_report_webkit.report.open_invoices import PartnersOpenInvoicesWebkit


class open_invoices_webkit_wizard(orm.TransientModel):
    _inherit = 'open.invoices.webkit'

    _columns = {
        'filter_by_payment': fields.many2one('account.payment.term','Filter by Payment Term',store=True),
        'email_template':fields.many2one('email.template','Email Template'),
        'report_print':fields.selection([(1,'Print All'),(2,'Only No Email'),(3,'None')])
            }
    
    _defaults={
               'report_print':3,
               }

    def filter_data(self, cr, uid, ids, context=None):
        """
            Filter Data Button should Filter the Data Basing on Payment Filter Option.
            It will retrieve the data from ir.property table and store the values in the table
            open_invoices_webkit_res_partner_rel.
        """
        partner_obj= self.pool.get('ir.property')
        filter_ids = partner_obj.search(cr, uid, [('value_reference','=',"account.payment.term,%s"%context.get('filter_by_payment','')),('name','=','property_payment_term')])
        payment_term_ids = partner_obj.browse(cr,uid,filter_ids,context)

        view_id = self.pool.get('ir.ui.view').search(cr,uid,[('model','=','open.invoices.webkit')])
        if payment_term_ids:
            for partner_id in payment_term_ids:
                if partner_id.res_id.payment_amount_due <= 0:
                    pass
                else:
                    company_id = self.pool.get('res.partner').search(cr,uid,[('id','=',partner_id.res_id.id),('is_company','=',True),('supplier','=',False)])
                    if company_id:
                        cr.execute('select open_invoices_webkit_id from open_invoices_webkit_res_partner_rel where open_invoices_webkit_id = %s and res_partner_id = %s'%(ids[0],partner_id.res_id.id))
                        data= cr.fetchall()
                        if data:
                            cr.execute('delete from open_invoices_webkit_res_partner_rel where open_invoices_webkit_id = %s and res_partner_id = %s'%(ids[0],partner_id.res_id.id))
                        cr.execute('insert into open_invoices_webkit_res_partner_rel(open_invoices_webkit_id,res_partner_id) values(%s,%s)'%(ids[0],partner_id.res_id.id))
            return {
             'name':_("open.invoices.webkit"),
             'view_mode': 'form',
             'view_id': [view_id[-1]],
             'view_type': 'form',
             'res_model': 'open.invoices.webkit',
             'res_id': ids[0],
             'type': 'ir.actions.act_window',
             'nodestroy': True,
             'target': 'new',
             'domain': '[]',
             'context': context,
             }

        else:
            return {
             'name':_("open.invoices.webkit"),
             'view_mode': 'form',
             'view_id': [view_id[0]],
             'view_type': 'form',
             'res_model': 'open.invoices.webkit',
             'res_id': ids[0],
             'type': 'ir.actions.act_window',
             'nodestroy': True,
             'target': 'new',
             'domain': '[]',
             'context': context,
             }

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


            
    def custom_send_email(self, cr, uid, ids, context=None):
        # Added the Functionality for Email
        """
            Custom Email Module Returns the List of All the Customers Existed in the
            open_invoices_webkit_res_partner_rel table basing on the open_invoices_webkit_id.

            Call the Module Email Template and Send the mail using the Function send_mail.
        """
        from report import r3x_customer_statement_print_report as r3x_customer_statement_print

        if context is None:
                context = {}

        template_obj=self.pool.get('open.invoices.webkit').browse(cr, uid, ids, context=context)
        company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id

        template_id=""
        payment_id=""
        result_selection=""
        with_email=""
        for element in template_obj:
                template_id=element.email_template.id
                payment_id = element.filter_by_payment
                result_selection=element.result_selection
                report_print=element.report_print

        if template_id and result_selection=="customer":

            context = context or {}
            res_obj=self.pool.get('res.partner')
            mail_mail = self.pool.get('mail.mail')

            cr.execute("select res_partner_id from open_invoices_webkit_res_partner_rel where open_invoices_webkit_id=%s"%ids[0])
            payment_elements =[r[0] for r in cr.fetchall()]
            if len(payment_elements)==0:
                raise osv.except_osv(_('Error!'),
                        _('Please Select Single Customer'))
                
            mtp =self.pool.get('email.template')
            for payment_ids in payment_elements:
                # Functions Calling Here to Verify That Values Exist Or Not.

                assert len(ids) == 1
                if context is None:
                    context = {}
                partner = res_obj.browse(cr, uid, payment_ids, context=context)
                #copy the context to not change global context.
                #Overwrite it because _() looks for the lang in local variable 'context'.
                #Set the language to use = the partner language
                context = dict(context, lang=partner.lang)
                followup_table = ''
                if partner.unreconciled_aml_ids:
                    company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
                    current_date = fields.date.context_today(self, cr, uid, context=context)
                    rml_parse = r3x_customer_statement_print.report_rappel(cr, uid, "followup_rml_parser")
                    final_res = rml_parse._lines_get_with_partner(partner, company.id)
                    # Returns a Disctionary With Payment Values.........
                    if final_res:
                        # Retrieving the Template
                        mail_template_id = self.pool.get('ir.model.data').get_object_reference(cr, uid,
                                                    'r3x_customer_account_statement', 'email_template_customer_account_statement')

                        mtp.send_mail(cr, uid, mail_template_id[1], payment_ids, context=context)
   
            # Functionality to Print the Report of the Partners
            tup_partner_ids=tuple(payment_elements)
            if len(tup_partner_ids) == 1:
                cr.execute("select id from res_partner where email IS NULL and id = %s"%tup_partner_ids[0])
                email_not_exists=cr.fetchall()
            
            else:
                cr.execute("select id from res_partner where email IS NULL and id in %s"%str(tup_partner_ids))
                email_not_exists=cr.fetchall()
            
            company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
            wizard_partner_ids = [ids[0] * 10000 + company_id]
            
            followup_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id

            data = {
                    'date': fields.date.today(),
                    'followup_id': followup_id,
                    }

            if report_print == 1:
                # Importing Customer Statement and Updating the Customer Statement Total For 
                partner_ids=[]
                for element in payment_elements:
                    res_obj=self.pool.get('res.partner')
                    id_browse=res_obj.browse(cr,uid,element,context)
                    self.display_screen(cr,uid,[element],context)
                    partner_ids.append(element * 10000 + company_id)

                if partner_ids:
                    data['partner_ids']=partner_ids                
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
                else:
                    return {'type': 'ir.actions.act_window_close'}
                
            elif report_print == 2:
                if len(email_not_exists) <=1:
                    payment_elements=email_not_exists[0]
                else:
                    payment_elements=reduce(list.__add__,map(list,email_not_exists))
                
                partner_ids=[]
                for element in payment_elements:
                    res_obj=self.pool.get('res.partner')
                    id_browse=res_obj.browse(cr,uid,element,context)
                    self.display_screen(cr,uid,[element],context)
                    partner_ids.append(element * 10000 + company_id)
                
                if partner_ids:
                    data['partner_ids']=partner_ids
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
                else:
                    return {'type': 'ir.actions.act_window_close'}
                
            else:
                return {'type': 'ir.actions.act_window_close'}

        else:
            if template_id and result_selection!="customer":
                raise osv.except_osv(_('Error!'),
                        _('Partners Should Be Receivabe Accounts'))
            else:
                raise osv.except_osv(_('Error!'),
                        _('Email Template Not Defined'))
