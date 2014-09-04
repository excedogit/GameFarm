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
from datetime import datetime
from dateutil.relativedelta import relativedelta
from collections import defaultdict
from openerp.osv import osv, fields
from openerp.tools.translate import _

from openerp import pooler
from openerp.report import report_sxw

class report_rappel(report_sxw.rml_parse):
    _name = "r3x_customer_statement.report.rappel"

    def __init__(self, cr, uid, name, context=None):
        super(report_rappel, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'ids_to_objects': self._ids_to_objects,
            'getLines': self._lines_get,
            'get_text': self._get_text
        })
        self.cr=cr
        self.uid=uid
        self.context=context

    def _ids_to_objects(self, ids):
        pool = pooler.get_pool(self.cr.dbname)
        all_lines = []
        
        for line in pool.get('r3x_customer_statement.stat.by.partner').browse(self.cr, self.uid, ids):
            if line not in all_lines:
                all_lines.append(line)
        return all_lines

    def _lines_get(self, stat_by_partner_line):
        return self._lines_get_with_partner(stat_by_partner_line.partner_id, stat_by_partner_line.company_id.id)

    def _lines_get_with_partner(self,partner,company_id):
        pool = pooler.get_pool(self.cr.dbname)
        moveline_obj = pool.get('account.payment.display.credit')
        moveline_ids = moveline_obj.search(self.cr, self.uid, [
                            ('partner_id', '=', partner.id),
                            ('account_id.type', '=', 'receivable'),
                            ('reconcile_id', '=', False),
                            ('state', '!=', 'draft'),
                            ('company_id', '=', company_id),
                        ])

        lines_per_currency = defaultdict(list)
        previous_cumm = 0
        data = self._get_payment_term_and_period_length(self.cr,self.uid,partner,self.context)
        data.update({'partner_id':partner.id})
        dictionary=self.get_lines_without_filter(data,partner,self.context)[0]

        for val,line in enumerate(moveline_obj.browse(self.cr, self.uid, moveline_ids)):
            currency = line.currency_id or line.company_id.currency_id
            period1=0;period2=0;period3=0;period4=0;older=0
            if val == 0:
                amount = line.debit - line.credit
                previous_cumm = amount
            else:
                amount = line.debit - line.credit + previous_cumm
                previous_cumm = amount

            line_data = {
                'payment_amount_overdue':partner.payment_amount_overdue,
                'name': line.invoice_no,
                'ref': line.ref,
                'date': line.date,
                'date_maturity': line.date_maturity,
                'debit':line.debit,
                'credit':line.credit,
                'balance': line.debit-line.credit,
                'total_balance':previous_cumm,
                'blocked': line.blocked,
                'currency_id': currency,
                'current':dictionary[str(4)],
                'period1':dictionary[str(1)],
                'period2':dictionary[str(2)],
                'period3':dictionary[str(3)],
                'older':dictionary[str(0)],
                'direction':dictionary['direction'],
                'total':dictionary['total']
            }
            lines_per_currency[currency].append(line_data)
        return [{'line': lines} for lines in lines_per_currency.values()]


    def _get_payment_term_and_period_length(self,cursor,uid,partner_id,context):
        res={}
        period_length=0

        partner_obj= self.pool.get('ir.property')
        filter_ids = partner_obj.search(cursor, uid, [('res_id','=',"res.partner,%s"%partner_id.id),('name','=','property_payment_term')])

        payment_term_ids = partner_obj.browse(cursor,uid,filter_ids)[0]

        payment_obj=self.pool.get('account.payment.term.line')
        payment_id = payment_obj.search(cursor,uid,[('payment_id','=',payment_term_ids.value_reference.id)])

        payname_obj=self.pool.get('account.payment.term')
        payname = payname_obj.browse(cursor,uid,payment_term_ids.value_reference.id)
        
        res['payment_term_id']=payment_term_ids.value_reference.id
        res['payment_name']=payname.name
        period_length=payment_obj.browse(cursor,uid,payment_id[0],context).days
        
                    #Code for Payment Item ids..
        if period_length == 0:
            period_length=payment_obj.browse(cursor,uid,payment_id[0],context).days2

        date_start = fields.date.context_today(self,cursor,uid,context=context)
        start = datetime.strptime(date_start, "%Y-%m-%d")

        res['date_from'] = date_start
        for i in range(5)[::-1]:
            stop = start - relativedelta(days=period_length)
            res[str(i)] = {
                'name': (i!=0 and (str((5-(i+1)) * period_length) + '-' + str((5-i) * period_length)) or ('+'+str(4 * period_length))),
                'stop': start.strftime('%Y-%m-%d'),
                'start': (i!=0 and stop.strftime('%Y-%m-%d') or False),
                }
            start = stop - relativedelta(days=1)

        res[str(0)]['name']="Older"
        res[str(1)]['name']="Period1"
        res[str(2)]['name']="Period2"
        res[str(3)]['name']="Period3"
        res[str(4)]['name']="Current"
        return res

    def _get_text(self, stat_line, followup_id, context=None):

        if context is None:
            context = {}
        context.update({'lang': stat_line.partner_id.lang})

        #look into the lines of the partner that already have a followup level, and take the description of the higher level for which it is available
        default_text = ''
        partner_line_ids = pooler.get_pool(self.cr.dbname).get('account.move.line').search(self.cr, self.uid, [('partner_id','=',stat_line.partner_id.id),('reconcile_id','=',False),('company_id','=',stat_line.company_id.id),('blocked','=',False),('state','!=','draft'),('debit','!=',False),('account_id.type','=','receivable'),('followup_line_id','!=',False)])
        partner_max_delay = 0
        partner_max_text = ''
        for i in pooler.get_pool(self.cr.dbname).get('account.move.line').browse(self.cr, self.uid, partner_line_ids, context=context):
            if i.followup_line_id.delay > partner_max_delay and i.followup_line_id.description:
                partner_max_delay = i.followup_line_id.delay
                partner_max_text = i.followup_line_id.description
        text = partner_max_delay and partner_max_text or default_text
        if text:
            text = text % {
                'partner_name': stat_line.partner_id.name,
                'date': time.strftime('%Y-%m-%d'),
                'company_name': stat_line.company_id.name,
                'user_signature': pooler.get_pool(self.cr.dbname).get('res.users').browse(self.cr, self.uid, self.uid, context).signature or '',
            }
        text="Please find the enclosed statement attached"
        return text


# Adding Function For Partner Balance............................

    def get_lines_without_filter(self,data,form,context):
        """
            # Function used to retrieve the data from the Periods based on Dates.
        """
        self.total_account = []
        obj_move = self.pool.get('account.move.line')
        self.query = obj_move._query_get(self.cr, self.uid, obj='l', context=context)
        self.direction_selection = "past"
        self.target_move = "posted"
        self.date_from = data.get('date_from', time.strftime('%Y-%m-%d'))
        self.ACCOUNT_TYPE = ['receivable']

        res = []
        move_state = ['draft','posted']
        if self.target_move == 'posted':
            move_state = ['posted']

        self.cr.execute('select id,name from res_partner where id=%s'%data['partner_id'])
        partners = self.cr.dictfetchall()
        ## mise a 0 du total
        for i in range(7):
            self.total_account.append(0)
        #
        # Build a string like (1,2,3) for easy use in SQL query
        partner_ids = [x['id'] for x in partners]
        if not partner_ids:
            return []
        # This dictionary will store the debit-credit for all partners, using partner_id as key.

        totals = {}
        self.cr.execute('SELECT l.partner_id, SUM(l.debit-l.credit) \
                    FROM account_move_line AS l, account_account, account_move am \
                    WHERE (l.account_id = account_account.id) AND (l.move_id=am.id) \
                    AND (am.state IN %s)\
                    AND (account_account.type IN %s)\
                    AND (l.partner_id IN %s)\
                    AND ((l.reconcile_id IS NULL)\
                    OR (l.reconcile_id IN (SELECT recon.id FROM account_move_reconcile AS recon WHERE recon.create_date > %s )))\
                    AND ' + self.query + '\
                    AND account_account.active\
                    AND (l.date <= %s)\
                    GROUP BY l.partner_id ', (tuple(move_state), tuple(self.ACCOUNT_TYPE), tuple(partner_ids), self.date_from, self.date_from,))
        t = self.cr.fetchall()
        for i in t:
            totals[i[0]] = i[1]

        # This dictionary will store the future or past of all partners
        future_past = {}
        if self.direction_selection == 'future':
            self.cr.execute('SELECT l.partner_id, SUM(l.debit-l.credit) \
                        FROM account_move_line AS l, account_account, account_move am \
                        WHERE (l.account_id=account_account.id) AND (l.move_id=am.id) \
                        AND (am.state IN %s)\
                        AND (account_account.type IN %s)\
                        AND (COALESCE(l.date_maturity, l.date) < %s)\
                        AND (l.partner_id IN %s)\
                        AND ((l.reconcile_id IS NULL)\
                        OR (l.reconcile_id IN (SELECT recon.id FROM account_move_reconcile AS recon WHERE recon.create_date > %s )))\
                        AND '+ self.query + '\
                        AND account_account.active\
                    AND (l.date <= %s)\
                        GROUP BY l.partner_id', (tuple(move_state), tuple(self.ACCOUNT_TYPE), self.date_from, tuple(partner_ids),self.date_from, self.date_from,))
            t = self.cr.fetchall()
            for i in t:
                future_past[i[0]] = i[1]
        elif self.direction_selection == 'past': # Using elif so people could extend without this breaking
            self.cr.execute('SELECT l.partner_id, SUM(l.debit-l.credit) \
                    FROM account_move_line AS l, account_account, account_move am \
                    WHERE (l.account_id=account_account.id) AND (l.move_id=am.id)\
                        AND (am.state IN %s)\
                        AND (account_account.type IN %s)\
                        AND (COALESCE(l.date_maturity,l.date) > %s)\
                        AND (l.partner_id IN %s)\
                        AND ((l.reconcile_id IS NULL)\
                        OR (l.reconcile_id IN (SELECT recon.id FROM account_move_reconcile AS recon WHERE recon.create_date > %s )))\
                        AND '+ self.query + '\
                        AND account_account.active\
                    AND (l.date <= %s)\
                        GROUP BY l.partner_id', (tuple(move_state), tuple(self.ACCOUNT_TYPE), self.date_from, tuple(partner_ids), self.date_from, self.date_from,))
            t = self.cr.fetchall()
            for i in t:
                future_past[i[0]] = i[1]

        # Use one query per period and store results in history (a list variable)
        # Each history will contain: history[1] = {'<partner_id>': <partner_debit-credit>}
        history = []
        for i in range(5):
            args_list = (tuple(move_state), tuple(self.ACCOUNT_TYPE), tuple(partner_ids),self.date_from,)
            dates_query = '(COALESCE(l.date_maturity,l.date)'
            if data[str(i)]['start'] and data[str(i)]['stop']:
                dates_query += ' BETWEEN %s AND %s)'
                args_list += (data[str(i)]['start'], data[str(i)]['stop'])
            elif data[str(i)]['start']:
                dates_query += ' > %s)'
                args_list += (data[str(i)]['start'],)
            else:
                dates_query += ' < %s)'
                args_list += (data[str(i)]['stop'],)
            args_list += (self.date_from,)
            self.cr.execute('''SELECT l.partner_id, SUM(l.debit-l.credit)
                    FROM account_move_line AS l, account_account, account_move am
                    WHERE (l.account_id = account_account.id) AND (l.move_id=am.id)
                        AND (am.state IN %s)
                        AND (account_account.type IN %s)
                        AND (l.partner_id IN %s)
                        AND ((l.reconcile_id IS NULL)
                          OR (l.reconcile_id IN (SELECT recon.id FROM account_move_reconcile AS recon WHERE recon.create_date > %s )))
                        AND ''' + self.query + '''
                        AND account_account.active
                        AND ''' + dates_query + '''
                    AND (l.date <= %s)
                    GROUP BY l.partner_id''', args_list)
            t = self.cr.fetchall()
            d = {}
            for i in t:
                d[i[0]] = i[1]
            history.append(d)

        for partner in partners:
            values = {}
            ## If choise selection is in the future
            if self.direction_selection == 'future':
                # Query here is replaced by one query which gets the all the partners their 'before' value
                before = False
                if future_past.has_key(partner['id']):
                    before = [ future_past[partner['id']] ]
                self.total_account[6] = self.total_account[6] + (before and before[0] or 0.0)
                values['direction'] = before and before[0] or 0.0
            elif self.direction_selection == 'past': # Changed this so people could in the future create new direction_selections
                # Query here is replaced by one query which gets the all the partners their 'after' value
                after = False
                if future_past.has_key(partner['id']): # Making sure this partner actually was found by the query
                    after = [ future_past[partner['id']] ]

                self.total_account[6] = self.total_account[6] + (after and after[0] or 0.0)
                values['direction'] = after and after[0] or 0.0

            for i in range(5):
                during = False
                if history[i].has_key(partner['id']):
                    during = [ history[i][partner['id']] ]
                # Ajout du compteur
                self.total_account[(i)] = self.total_account[(i)] + (during and during[0] or 0)
                values[str(i)] = during and during[0] or 0.0
            total = False
            if totals.has_key( partner['id'] ):
                total = [ totals[partner['id']] ]
            values['total'] = total and total[0] or 0.0
            ## Add for total
            self.total_account[(i+1)] = self.total_account[(i+1)] + (total and total[0] or 0.0)
            values['name'] = partner['name']

            # Connnect to ir.property table to return the Values for the Payment Term................
            self.cr.execute("select value_reference from ir_property where name='property_payment_term' and res_id='res.partner,%s'    "%partner['id'])
            payment_term_val=self.cr.dictfetchall()
            if payment_term_val:
                payment_term_val=payment_term_val[0]

                self.cr.execute('select name from account_payment_term where id=%s'%payment_term_val['value_reference'].split(',')[-1])
                payment_term = self.cr.dictfetchall()[0]
                values['payment_term']=payment_term['name']
            else:
                values['payment_term']=""
            res.append(values)
        total = 0.0
        totals = {}
        for r in res:
            total += float(r['total'] or 0.0)
            for i in range(5)+['direction']:
                totals.setdefault(str(i), 0.0)
                totals[str(i)] += float(r[str(i)] or 0.0)
        return res


report_sxw.report_sxw('report.r3x_customer_statement_print',
        'r3x_customer_statement.stat.by.partner', 
        'addons/r3x_customer_account_statement/report/r3x_customer_statement_report.rml',
        parser=report_rappel)

# vim:expandtab:smartindent:tabstop=4:4softtabstop=4:shiftwidth=4: