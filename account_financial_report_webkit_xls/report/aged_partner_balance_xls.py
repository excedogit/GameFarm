# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2013 Noviat nv/sa (www.noviat.com). All rights reserved.
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

from __future__ import division

import xlwt
import time
import account_financial_report_webkit
from datetime import datetime
from openerp.report import report_sxw
from openerp.addons.report_xls.report_xls import report_xls
from openerp.addons.report_xls.utils import rowcol_to_cell
from openerp.addons.account_financial_report_webkit.report.aged_partner_balance import AccountAgedTrialBalanceWebkit
from openerp.tools.translate import _

from openerp import pooler
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT

def make_ranges(top, offset):
    """Return sorted days ranges

    :param top: maximum overdue day
    :param offset: offset for ranges

    :returns: list of sorted ranges tuples in days
              eg. [(-100000, 0), (0, offset), (offset, n*offset), ... (top, 100000)]
    """
    ranges = [(n, min(n + offset, top)) for n in xrange(0, top, offset)]
    ranges.insert(0, (-100000000000, 0))
    ranges.append((top, 100000000000))
    return ranges

#list of overdue ranges
RANGES = make_ranges(120, 30)


def make_ranges_titles():
    """Generates title to be used by mako"""
    titles = [_('Not Due')]
    titles += [_(u'Overdue ≤ %s d.') % x[1] for x in RANGES[1:-1]]
    titles.append(_('Older'))
    return titles

#list of overdue ranges title
RANGES_TITLES = make_ranges_titles()

#list of payable journal types
REC_PAY_TYPE = ('purchase', 'sale')
#list of refund payable type

REFUND_TYPE = ('purchase_refund', 'sale_refund')

INV_TYPE = REC_PAY_TYPE + REFUND_TYPE
PAYMENT_IDS=[]
PAYMENT_NAMES=[]


class open_invoices_xls(report_xls):
    column_sizes = [12,12,20,15,30,30,14,14,14,14,14,14,10]

    def global_initializations(self, wb, _p, xlwt, _xs, objects, data):
        # this procedure will initialise variables and Excel cell styles and return them as global ones
        global ws
        ws = wb.add_sheet(_p.report_name[:31])
        ws.panes_frozen = True
        ws.remove_splits = True
        ws.portrait = 0 # Landscape
        ws.fit_width_to_pages = 1
        ws.header_str = self.xls_headers['standard']
        ws.footer_str = self.xls_footers['standard']
        #-------------------------------------------------------
        global nbr_columns  #number of columns is 11 in case of normal report, 13 in case the option currency is selected and 12 in case of the regroup by currency option is checked
        group_lines = False
        
        if group_lines:
            nbr_columns = 12
        elif _p.amount_currency(data) and not group_lines:
            nbr_columns = 13
        else:
            nbr_columns = 11
        #-------------------------------------------------------
        global style_font12  #cell style for report title
        style_font12 = xlwt.easyxf(_xs['xls_title'])
        #-------------------------------------------------------
        global style_default
        style_default = xlwt.easyxf(_xs['borders_all'])
        #-------------------------------------------------------
        global style_default_italic
        style_default_italic = xlwt.easyxf(_xs['borders_all'] + _xs['italic'])
        #-------------------------------------------------------
        global style_bold
        style_bold = xlwt.easyxf(_xs['bold'] + _xs['borders_all'])
        #-------------------------------------------------------
        global style_bold_center
        style_bold_center = xlwt.easyxf(_xs['bold'] + _xs['borders_all'] + _xs['center'])
        #-------------------------------------------------------
        global style_bold_italic
        style_bold_italic = xlwt.easyxf(_xs['bold'] + _xs['borders_all'] + _xs['italic'])
        #-------------------------------------------------------
        global style_bold_italic_decimal
        style_bold_italic_decimal = xlwt.easyxf(_xs['bold'] + _xs['borders_all'] + _xs['italic'] + _xs['right'], num_format_str = report_xls.decimal_format)
        #-------------------------------------------------------
        global style_bold_blue
        style_bold_blue = xlwt.easyxf(_xs['bold'] + _xs['fill_blue'] + _xs['borders_all'] )
        #-------------------------------------------------------
        global style_bold_blue_italic_decimal
        style_bold_blue_italic_decimal = xlwt.easyxf(_xs['bold'] + _xs['fill_blue'] + _xs['borders_all'] + _xs['italic'], num_format_str = report_xls.decimal_format)
        #-------------------------------------------------------
        global style_bold_blue_center #cell style for header titles: 'Chart of accounts' - 'Fiscal year' ...
        style_bold_blue_center= xlwt.easyxf(_xs['bold'] + _xs['fill_blue'] + _xs['borders_all'] + _xs['center'])
        #-------------------------------------------------------
        global style_center #cell style for header data: 'Chart of accounts' - 'Fiscal year' ...
        style_center = xlwt.easyxf(_xs['borders_all'] + _xs['wrap'] + _xs['center'])
        #-------------------------------------------------------
        global style_yellow_bold #cell style for columns titles 'Date'- 'Period' - 'Entry'...
        style_yellow_bold = xlwt.easyxf(_xs['bold'] + _xs['fill'] + _xs['borders_all'])
        #-------------------------------------------------------
        global style_yellow_bold_right #cell style for columns titles 'Date'- 'Period' - 'Entry'...
        style_yellow_bold_right = xlwt.easyxf(_xs['bold'] + _xs['fill'] + _xs['borders_all'] + _xs['right'])
        #-------------------------------------------------------
        global style_right
        style_right = xlwt.easyxf(_xs['borders_all'] + _xs['right'])
        #-------------------------------------------------------
        global style_right_italic
        style_right_italic = xlwt.easyxf(_xs['borders_all'] + _xs['right'] + _xs['italic'])
        #-------------------------------------------------------
        global style_decimal
        style_decimal = xlwt.easyxf(_xs['borders_all'] + _xs['right'], num_format_str = report_xls.decimal_format)
        #-------------------------------------------------------
        global style_decimal_italic
        style_decimal_italic = xlwt.easyxf(_xs['borders_all'] + _xs['right'] + _xs['italic'], num_format_str = report_xls.decimal_format)
        #-------------------------------------------------------
        global style_date
        style_date = xlwt.easyxf(_xs['borders_all'] + _xs['left'], num_format_str = report_xls.date_format)
        #-------------------------------------------------------
        global style_date_italic
        style_date_italic = xlwt.easyxf(_xs['borders_all'] + _xs['left'] + _xs['italic'], num_format_str = report_xls.date_format)
        #-------------------------------------------------------
        global style_account_title, style_account_title_right, style_account_title_decimal
        cell_format = _xs['xls_title'] + _xs['bold'] + _xs['fill'] + _xs['borders_all']
        style_account_title = xlwt.easyxf(cell_format)
        style_account_title_right = xlwt.easyxf(cell_format + _xs['right'])
        style_account_title_decimal = xlwt.easyxf(cell_format + _xs['right'], num_format_str = report_xls.decimal_format)
        #-------------------------------------------------------
        global style_partner_row
        cell_format = _xs['bold']
        style_partner_row = xlwt.easyxf(cell_format)
        #-------------------------------------------------------
        global style_partner_cumul, style_partner_cumul_right, style_partner_cumul_center, style_partner_cumul_decimal
        cell_format = _xs['bold'] + _xs['fill'] + _xs['borders_all']
        style_partner_cumul = xlwt.easyxf(cell_format)
        style_partner_cumul_right = xlwt.easyxf(cell_format + _xs['right'])
        style_partner_cumul_center = xlwt.easyxf(cell_format + _xs['center'])
        style_partner_cumul_decimal = xlwt.easyxf(cell_format + _xs['right'], num_format_str = report_xls.decimal_format)

    def print_title(self, _p, row_position): # print the first line "OPEN INVOICE REPORT - db name - Currency
        report_name =  ' - '.join([_p.report_name.upper(), _p.company.partner_id.name, _p.company.currency_id.name])
        c_specs = [('report_name', nbr_columns, 0, 'text', report_name), ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_position = self.xls_write_row(ws, row_position, row_data, row_style=style_font12)
        return row_position

    def print_empty_row(self, row_position): #send an empty row to the Excel document
        c_sizes = self.column_sizes
        c_specs = [('empty%s'%i, 1, c_sizes[i], 'text', None) for i in range(0,len(c_sizes))]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_position = self.xls_write_row(ws, row_position, row_data, set_column_size=True)
        return row_position

    def print_header_titles(self, _p, data, row_position): #Fill in the titles of the header summary tables: Chart of account - Fiscal year - ...
        c_specs = [
            ('coa', 2, 0, 'text', _('Chart of Account'), None, style_bold_blue_center),
            ('fy', 2, 0, 'text', _('Fiscal Year'), None, style_bold_blue_center),
            ('df', 2, 0, 'text', _p.filter_form(data) == 'filter_date' and _('Dates Filter') or _('Periods Filter'), None, style_bold_blue_center),
            ('cd', 1 if nbr_columns == 11 else 2 , 0, 'text', _('Clearance Date'), None, style_bold_blue_center),
            ('af', 2, 0, 'text', _('Accounts Filter'), None, style_bold_blue_center),
            ('tm', 3 if nbr_columns == 13 else 2, 0, 'text', _('Target Moves'), None, style_bold_blue_center),
        ]       
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_position = self.xls_write_row(ws, row_position, row_data, row_style=style_bold_blue_center)
        return row_position
    
    
    def print_header_data(self, _p, data, row_position):   #Fill in the data of the header summary tables: Chart of account - Fiscal year - ...
        #print "Testing the Attributes ::::", dir(_p)
        c_specs = [
            ('coa', 2, 0, 'text', _p.chart_account.name, None, style_center),       
            ('fy', 2, 0, 'text', _p.fiscalyear.name if _p.fiscalyear else '-', None, style_center),
        ]
        df = _('From') + ': '
        if _p.filter_form(data) == 'filter_date':
            df += _p.start_date if _p.start_date else u'' 
        else:
            df += _p.start_period.name if _p.start_period else u''
        df += ' ' + _('To') + ': '
        if _p.filter_form(data) == 'filter_date':
            df += _p.stop_date if _p.stop_date else u''
        else:
            df += _p.stop_period.name if _p.stop_period else u''
        c_specs += [
            ('df', 2, 0, 'text', df, None, style_center),
            ('cd', 1 if nbr_columns == 11 else 2, 0, 'text', _p.date_until, None, style_center), #clearance date  
            ('af', 2, 0, 'text', _('Custom Filter') if _p.partner_ids else _p.display_partner_account(data), None, style_center),        
            ('tm', 3 if nbr_columns == 13 else 2, 0, 'text', _p.display_target_move(data), None, style_center),
        ]              
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_position = self.xls_write_row(ws, row_position, row_data, row_style=style_center)
        return row_position

    def print_columns_title(self, _p, data, row_position):  # Fill in a row with the titles of the columns for the invoice lines: Date - Period - Entry -...
        c_specs = [
            ('partners', 1, 0, 'text', _('Partner'),None,style_yellow_bold),
            ('code', 1, 0, 'text', _('Code'),None,style_yellow_bold),
            ('payment_term',1,0,'text',_('Payment Term'),None,style_yellow_bold),
            ('balance', 1, 0, 'text', _('balance'),None,style_yellow_bold),
            ('due', 1, 0, 'text', RANGES_TITLES[0],None,style_yellow_bold),
            ('od30', 1, 0, 'text', RANGES_TITLES[1],None,style_yellow_bold),
            ('od60', 1, 0, 'text',RANGES_TITLES[2],None,style_yellow_bold),
            ('od90', 1, 0, 'text',RANGES_TITLES[3],None,style_yellow_bold),
            ('od120', 1, 0, 'text',RANGES_TITLES[4],None,style_yellow_bold),
            ('older', 1, 0, 'text', RANGES_TITLES[5],None,style_yellow_bold),
            ('coments', 1, 0, 'text', _('Coments'),None,style_yellow_bold),
            ('payment_next_Action_date',1,0,'text',_('Next Action Date'),None,style_yellow_bold),
            
        ]
       
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_position = self.xls_write_row(ws, row_position, row_data, row_style=style_yellow_bold)
        return row_position

    def print_row_code_account(self,account, row_position, partner_name): # Fill in a row with the code and the name of an account + the partner name in case of currency regrouping
        c_specs = [ ('acc_title', nbr_columns, 0, 'text', ' - '.join([account.code, account.name])),  ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_position = self.xls_write_row(ws, row_position, row_data, style_account_title)
        return row_position+1

    def print_row_partner(self, row_position, partner_name):
        c_specs = [ ('partner', nbr_columns, 0, 'text', partner_name or _('No partner')),  ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_position = self.xls_write_row(ws, row_position, row_data, style_partner_row)
        return row_position

    def print_group_currency(self, row_position, curr, _p):
        c_specs = [ ('curr', nbr_columns, 0, 'text', curr or _p.company.currency_id.name),  ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_position = self.xls_write_row(ws, row_position, row_data, style_bold)
        return row_position

    def print_lines(self, row_position, account, line,_p, data, line_number): # Fill in rows of invoice line
        # Mako: <div class="act_as_row lines ${line.get('is_from_previous_periods') and 'open_invoice_previous_line' or ''} ${line.get('is_clearance_line') and 'clearance_line' or ''}">
        if line.get('is_from_previous_periods') or line.get('is_clearance_line'):
            style_line_default = style_default_italic
            style_line_right = style_right_italic
            style_line_date = style_date_italic
            style_line_decimal = style_decimal_italic
        else:
            style_line_default = style_default
            style_line_right = style_right
            style_line_date = style_date
            style_line_decimal = style_decimal
       
        c_specs = [
            ('partner_name', 1, 0, 'text',line.get('partner_name')or '' ),
            ('invoice_no', 1, 0, 'text',  line.get('ref')or '' ),
            ('payment_term',1,0,'text',line.get('payment_term')or ' -'),
            ('balance', 1, 0, 'number', line.get('balance') or 0.0, None, style_line_decimal),
            ('due',1,0,'number',line.get('due') or 0.0, None,style_line_decimal),
            ('od30',1,0,'number',line.get('od30') or 0.0, None,style_line_decimal),
            ('od60',1,0,'number',line.get('od60') or 0.0, None,style_line_decimal),
            ('od90',1,0,'number',line.get('od90') or 0.0, None,style_line_decimal),
            ('od120',1,0,'number',line.get('od120') or 0.0, None,style_line_decimal),
            ('older',1,0,'number',line.get('older') or 0.0, None,style_line_decimal),
            ('payment_note',1,0,'text',line.get('payment_note')or '  -'),
            ('payment_next_Action_date',1,0,'text',line.get('payment_next_Action_date')or '  -'),
     
        ]
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_position = self.xls_write_row(ws, row_position, row_data, style_line_default)
        return row_position
 

    def compute_aged_lines(self, partner_id, ledger_lines, data):
        """Add property aged_lines to accounts browse records

        contained in :attr:`objects` for a given partner

        :param: partner_id: current partner
        :param ledger_lines: generated by parent
                 :class:`.open_invoices.PartnersOpenInvoicesWebkit`

        :returns: dict of computed aged lines
                  eg {'balance': 1000.0,
                       'aged_lines': {(90, 120): 0.0, ...}

        """

        #print "Here is the Payment Term in Data Hope It Exists Here:::",data

        lines_to_age = self.filter_lines(partner_id, ledger_lines)
        res = {}
        end_date = self._get_end_date(data)
        aged_lines = dict.fromkeys(RANGES, 0.0)
        reconcile_lookup = self.get_reconcile_count_lookup(lines_to_age)
        res['aged_lines'] = aged_lines
        for line in lines_to_age:
            compute_method = self.get_compute_method(reconcile_lookup,
                                                     partner_id,
                                                     line)
            delay = compute_method(line, end_date, ledger_lines)
            classification = self.classify_line(partner_id, delay)
            aged_lines[classification] += line['debit'] - line['credit']
            #print "aged_lines in XLS:::::::", aged_lines
       
        self.compute_balance(res, aged_lines)
         
        return res
        
    def _get_end_date(self, data):
        """Retrieve end date to be used to compute delay.

        :param data: data dict send to report contains form dict

        :returns: end date to be used to compute overdue delay

        """
        end_date = None
        date_to = data['form']['date_to']
        period_to_id = data['form']['period_to']
        fiscal_to_id = data['form']['fiscalyear_id']
        if date_to:
            end_date = date_to
        elif period_to_id:
            period_to = self.pool['account.period'].browse(self.cr,
                                                           self.uid,
                                                           period_to_id)
            end_date = period_to.date_stop
        elif fiscal_to_id:
            fiscal_to = self.pool['account.fiscalyear'].browse(self.cr,
                                                               self.uid,
                                                               fiscal_to_id)
            end_date = fiscal_to.date_stop
        else:
            raise ValueError('End date and end period not available')
         
        return end_date
        
    def _compute_delay_from_key(self, key, line, end_date):
        """Compute overdue delay delta in days for line using attribute in key

        delta = end_date - date of key

        :param line: current ledger line
        :param key: date key to be used to compute delta
        :param end_date: end_date computed for wizard data

        :returns: delta in days
        """
        from_date = datetime.strptime(line[key], DEFAULT_SERVER_DATE_FORMAT)
        end_date = datetime.strptime(end_date, DEFAULT_SERVER_DATE_FORMAT)
        delta = end_date - from_date
       #print "delta of compute_delay_from_key ::::::::",delta
        
        return delta.days

    def compute_delay_from_maturity(self, line, end_date, ledger_lines):
        """Compute overdue delay delta in days for line using attribute in key

        delta = end_date - maturity date

        :param line: current ledger line
        :param end_date: end_date computed for wizard data
        :param ledger_lines: generated by parent
                 :class:`.open_invoices.PartnersOpenInvoicesWebkit`

        :returns: delta in days
        """
        
        return self._compute_delay_from_key('date_maturity',
                                            line,
                                            end_date)

    def compute_delay_from_date(self, line, end_date, ledger_lines):
        """Compute overdue delay delta in days for line using attribute in key

        delta = end_date - date

        :param line: current ledger line
        :param end_date: end_date computed for wizard data
        :param ledger_lines: generated by parent
                 :class:`.open_invoices.PartnersOpenInvoicesWebkit`

        :returns: delta in days
        """
         
        return self._compute_delay_from_key('ldate',
                                            line,
                                            end_date)

    def compute_delay_from_partial_rec(self, line, end_date, ledger_lines):
        """Compute overdue delay delta in days for the case where move line

        is related to a partial reconcile with more than one reconcile line

        :param line: current ledger line
        :param end_date: end_date computed for wizard data
        :param ledger_lines: generated by parent
                 :class:`.open_invoices.PartnersOpenInvoicesWebkit`

        :returns: delta in days
        """
       
        
        sale_lines = [x for x in ledger_lines if x['jtype'] in REC_PAY_TYPE and
                      line['rec_id'] == x['rec_id']]
     
        refund_lines = [x for x in ledger_lines if x['jtype'] in REFUND_TYPE and
                        line['rec_id'] == x['rec_id']]
      
        if len(sale_lines) == 1:
            reference_line = sale_lines[0]
        elif len(refund_lines) == 1:
            reference_line = refund_lines[0]
        else:
            reference_line = line
        key = 'date_maturity' if reference_line.get('date_maturity') else 'ldate'
        
        return self._compute_delay_from_key(key,
                                            reference_line,
                                            end_date)

    def get_compute_method(self, reconcile_lookup, partner_id, line):
        """Get the function that should compute the delay for a given line

        :param reconcile_lookup: dict of reconcile group by id and count
                                 {rec_id: count of line related to reconcile}
        :param partner_id: current partner_id
        :param line: current ledger line generated by parent
                     :class:`.open_invoices.PartnersOpenInvoicesWebkit`

        :returns: function bounded to :class:`.AccountAgedTrialBalanceWebkit`

        """
        if reconcile_lookup.get(line['rec_id'], 0.0) > 1:
            #print "reconcile_lookup details :::::::",reconcile_lookup
            return self.compute_delay_from_partial_rec
        elif line['jtype'] in INV_TYPE and line.get('date_maturity'):
            return self.compute_delay_from_maturity
        else:
            return self.compute_delay_from_date

    def line_is_valid(self, partner_id, line):
        """Predicate hook that allows to filter line to be treated

        :param partner_id: current partner_id
        :param line: current ledger line generated by parent
                     :class:`.open_invoices.PartnersOpenInvoicesWebkit`

        :returns: boolean True if line is allowed
        """
        #print "NUMBER-----14" 
        return True

    def filter_lines(self, partner_id, lines):
        """Filter ledger lines that have to be treated

        :param partner_id: current partner_id
        :param lines: ledger_lines related to current partner
                      and generated by parent
                      :class:`.open_invoices.PartnersOpenInvoicesWebkit`

        :returns: list of allowed lines

        """
        #print "[x for x in lines if self.line_is_valid(partner_id, x)]=====15"
        return [x for x in lines if self.line_is_valid(partner_id, x)]

    def classify_line(self, partner_id, overdue_days):
        """Return the overdue range for a given delay

        We loop from smaller range to higher
        This should be the most effective solution as generaly
        customer tend to have one or two month of delay

        :param overdue_days: delay in days
        :param partner_id: current partner_id

        :returns: the correct range in :const:`RANGES`

        """
        for drange in RANGES:
            if overdue_days <= drange[1]:
                return drange
        return drange

    def compute_balance(self, res, aged_lines):
        """Compute the total balance of aged line
        for given account"""
        res['balance'] = sum(aged_lines.values())
        #print "NUMBER-----17" 

    def compute_totals(self, aged_lines):
        """Compute the totals for an account

        :param aged_lines: dict of aged line taken from the
                           property added to account record

        :returns: dict of total {'balance':1000.00, (30, 60): 3000,...}

        """
        totals = {}
        totals['balance'] = sum(x.get('balance', 0.0) for
                                x in aged_lines)
        aged_ranges = [x.get('aged_lines', {}) for x in aged_lines]
        for drange in RANGES:
            totals[drange] = sum(x.get(drange, 0.0) for x in aged_ranges)
        
        return totals

    def compute_percents(self, totals):
        percents = {}
        base = totals['balance'] or 1.0
        for drange in RANGES:
            
            percents[drange] = (totals[drange] / base) * 100.0
           
        return percents

    def get_reconcile_count_lookup(self, lines):
        """Compute an lookup dict

        It contains has partial reconcile id as key and the count of lines
        related to the reconcile id

        :param: a list of ledger lines generated by parent
                :class:`.open_invoices.PartnersOpenInvoicesWebkit`

        :retuns: lookup dict {ṛec_id: count}

        """
       
        l_ids = tuple(x['id'] for x in lines)
        #print "values in l-ids in the aged partner::::::",l_ids
        sql = ("SELECT reconcile_partial_id, COUNT(*) FROM account_move_line"
               "   WHERE reconcile_partial_id IS NOT NULL"
               "   AND id in %s"
               "   GROUP BY reconcile_partial_id")
        self.cr.execute(sql, (l_ids,))
        res = self.cr.fetchall()
        #print "Res values in the aged partner::::::::20"
        return dict((x[0], x[1]) for x in res)
 
 
    def print_group_cumul_account(self,row_position, row_start_account, acc): 
        #print by account the totals of the credit and debit + balance calculation
        #This procedure will create  an Excel sumif function that will check in the column "label" for the "Cumulated Balance.." string and make a sum of the debit & credit data
        start_col = 4   #the text "Cumulated Balance on Partner starts in column 4 when selecting the option regroup by currency, 5 in  the other case

        c_specs = [
            
            ('partner_name', 1, 0, 'text',_('Total') ),      
            ('invoice_no', 1, 0, 'text', None ),
            ('payment_term', 1, 0, 'text', None),
            ('balance', 1, 0, 'number', acc.aged_totals['balance']  or 0.0, None, style_account_title_decimal),
            ('due',1,0,'number',acc.aged_totals[(-100000000000, 0)]  or 0.0, None,style_account_title_decimal),
            ('od30',1,0,'number',acc.aged_totals[(0, 30)]  or 0.0, None,style_account_title_decimal),
            ('od60',1,0,'number',acc.aged_totals[(30, 60)]  or 0.0, None,style_account_title_decimal),
            ('od90',1,0,'number',acc.aged_totals[(60, 90)]  or 0.0, None,style_account_title_decimal),
            ('od120',1,0,'number',acc.aged_totals[(90, 120)]  or 0.0, None,style_account_title_decimal),
            ('older',1,0,'number',acc.aged_totals[(120, 100000000000)]  or 0.0, None,style_account_title_decimal),                                   
        ]

       
        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_position = self.xls_write_row(ws, row_position, row_data,style_account_title)  
        return row_position+1
    

    def print_ledger_lines(self, row_pos, acc, _xs, xlwt, _p, data): # export the invoice AR/AP lines
        
        
        if acc.ledger_lines and acc.partners_order:
            row_start_account = row_pos 
            
            for part_id, partner_lines in acc.ledger_lines.items():
                aged_lines = self.compute_aged_lines(part_id,partner_lines,data)
                if aged_lines:
                   acc.aged_lines[part_id] = aged_lines
            
            acc.aged_totals = totals = self.compute_totals(acc.aged_lines.values())       
            acc.aged_percents = self.compute_percents(totals)
           
                #Free some memory
            #del(acc.ledger_lines) 
            row_start_account = row_pos
            res_obj = self.pool.get('ir.property')
            #res = res_obj.browse(cr,uid,ids,context=context)
            #print "RES_OBJ test------",res
            
            row_pos = self.print_row_code_account(acc, row_pos, data)
            row_pos = self.print_empty_row(row_pos)
            row_pos = self.print_columns_title(_p, data, row_pos)
            #print "acc.partner_order------:",aged_lines
            
            
            for partner_name, p_id, p_ref, p_name  in acc.partners_order:
                line_number = 0             
                balance=0
                line={}
                #print "Payment Term Here :::--->",data['form']['payment_info'][p_id]['payment_term']
                line['balance'] = acc.aged_lines[p_id]['balance']
                line['partner_name'] = partner_name
                line['payment_term']=data['form']['payment_info'][p_id]['payment_term']
                line['ref']= p_ref
                line['due']= acc.aged_lines[p_id]['aged_lines'][(-100000000000, 0)]
                line['od30']= acc.aged_lines[p_id]['aged_lines'][(0, 30)]
                line['od60']= acc.aged_lines[p_id]['aged_lines'][(30,60)]
                line['od90']= acc.aged_lines[p_id]['aged_lines'][(60, 90)]
                line['od120']= acc.aged_lines[p_id]['aged_lines'][(90, 120)]
                line['older']= acc.aged_lines[p_id]['aged_lines'][(120, 100000000000)]
                line['payment_next_Action_date']=data['form']['payment_info'][p_id]['payment_next_Action_date']
                line['payment_note']=data['form']['payment_info'][p_id]['payment_note']
                row_pos_start = row_pos
                row_pos = self.print_lines(row_pos, acc, line, _p, data, line_number)
                line_number += 1
                 
            self.print_group_cumul_account(row_pos, row_start_account, acc)    
        return row_pos

#### Added Functions From Acount Partner Balance................................

    def generate_xls_report(self, _p, _xs, data, objects, wb): # main function            
        # Initializations
        self.global_initializations(wb,_p, xlwt, _xs, objects, data)
        row_pos = 0
        # Print Title
        row_pos = self.print_title(_p, row_pos)
        # Print empty row to define column sizes
        row_pos = self.print_empty_row(row_pos)
        # Print Header Table titles (Fiscal Year - Accounts Filter - Periods Filter...)
        row_pos = self.print_header_titles(_p, data, row_pos)
        # Print Header Table data
        row_pos = self.print_header_data(_p, data, row_pos)
       
         # Print empty row to define column sizes
        ws.set_horz_split_pos(row_pos)         
        # Print empty row
        row_pos = self.print_empty_row(row_pos)
        
        for acc in objects:    
            acc.aged_lines = {}
            acc.agged_totals = {}
            acc.agged_percents = {}
            
           
            
            row_pos = self.print_ledger_lines(row_pos, acc , _xs, xlwt, _p, data)
           
            row_pos += 1 
            
           
open_invoices_xls('report.account.account_report_aged_partner_balance_xls', 'account.account', parser=AccountAgedTrialBalanceWebkit)
