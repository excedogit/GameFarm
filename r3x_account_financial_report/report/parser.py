# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2013 Excedo Technologies & Solutions (www.excedo.in). All rights reserved.
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
from openerp.addons.account_financial_report.report.parser import account_balance as new_aged_trial_report
from openerp.tools.translate import _
from openerp import pooler
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT



class account_balance_xls(report_xls):

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
        #Relacing This Line................

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

    def print_columns_title(self, _p, data, row_position):  # Fill in a row with the titles of the columns for the invoice lines: Date - Period - Entry -...
        if data['form']['original_name'] == 'afr.1cols':
            c_specs = [
                       ('code', 1, 0, 'text', _('Code'),None,style_yellow_bold),
                       ('name',1,0,'text',_('Account'),None,style_yellow_bold),
                       ('balance', 1, 0, 'text', _('Balance'),None,style_yellow_bold),
                       ]
        
        if data['form']['original_name'] == 'afr.2cols':
            c_specs = [
                       ('code', 1, 0, 'text', _('CODE'),None,style_yellow_bold),
                       ('name',1,0,'text',_('ACCOUNT'),None,style_yellow_bold),
                       ('debit', 1, 0, 'text', _('DEBIT'),None,style_yellow_bold),
                       ('credit', 1, 0, 'text', _('CREDIT'),None,style_yellow_bold),
                       ]
        
        if data['form']['original_name']=='afr.4cols':
            c_specs = [
                       ('code', 1, 0, 'text', _('CODE'),None,style_yellow_bold),
                       ('name',1,0,'text',_('ACCOUNT'),None,style_yellow_bold),
                       ('balanceinit', 1, 0, 'text', _('INITIAL'),None,style_yellow_bold),
                       ('debit', 1, 0, 'text', _('DEBIT'),None,style_yellow_bold),
                       ('credit', 1, 0, 'text', _('CREDIT'),None,style_yellow_bold),
                       ('balance', 1, 0, 'text', _('BALANCE'),None,style_yellow_bold),
                       ]

        if data['form']['original_name']=='afr.5cols':
            c_specs = [
                       ('code', 1, 0, 'text', _('CODE'),None,style_yellow_bold),
                       ('name',1,0,'text',_('ACCOUNT'),None,style_yellow_bold),
                       ('balanceinit', 1, 0, 'text', _('InIT.BAL.'),None,style_yellow_bold),
                       ('debit', 1, 0, 'text', _('DEBIT'),None,style_yellow_bold),
                       ('credit', 1, 0, 'text', _('CREDIT'),None,style_yellow_bold),
                       ('period', 1, 0, 'text', _('PERIOD'),None,style_yellow_bold),
                       ('ytd', 1, 0, 'text', _('YTD'),None,style_yellow_bold),
                       ]

        if data['form']['original_name']=='afr.qtrcols':
            c_specs = [
                       ('code', 1, 0, 'text', _('CODE'),None,style_yellow_bold),
                       ('name',1,0,'text',_('ACCOUNT'),None,style_yellow_bold),
                       ('q1',1,0, 'text', _('Q1'), None,style_yellow_bold),
                       ('q2',1,0, 'text', _('Q2'), None,style_yellow_bold),
                       ('q3',1,0, 'text', _('Q3'), None,style_yellow_bold),
                       ('q4',1,0, 'text', _('Q4'), None,style_yellow_bold),
                       ('ytd',1,0,'text', _('YTD'),None,style_yellow_bold),
                       ]

        if data['form']['original_name']=='afr.13cols':
            c_specs = [
                       ('code', 1, 0, 'text', _('CODE'),None,style_yellow_bold),
                       ('name',1,0,'text',_('ACCOUNT'),None,style_yellow_bold),
                       ('q1',1,0, 'text', _('01'), None,style_yellow_bold),
                       ('q2',1,0, 'text', _('02'), None,style_yellow_bold),
                       ('q3',1,0, 'text', _('03'), None,style_yellow_bold),
                       ('q4',1,0, 'text', _('04'), None,style_yellow_bold),
                       ('q5',1,0, 'text', _('05'), None,style_yellow_bold),
                       ('q6',1,0, 'text', _('06'), None,style_yellow_bold),
                       ('q7',1,0, 'text', _('07'), None,style_yellow_bold),
                       ('q8',1,0, 'text', _('08'), None,style_yellow_bold),
                       ('q9',1,0, 'text', _('09'), None,style_yellow_bold),
                       ('q10',1,0, 'text', _('10'), None,style_yellow_bold),
                       ('q11',1,0, 'text', _('11'), None,style_yellow_bold),
                       ('q12',1,0, 'text', _('12'), None,style_yellow_bold),
                       ('ytd',1,0,'text', _('YTD'),None,style_yellow_bold),
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
        
        if line['original_name'] == 'afr.1cols':
            if 'bold_req' in line.keys():
                c_specs = [
                           ('code',1,0,'text','',None,style_yellow_bold),
                           ('name', 1, 0, 'text',line.get('name')or '',None,style_yellow_bold),
                           ('balance', 1, 0, 'number', line.get('balance') or 0.0, None,style_yellow_bold),
                           ]
            else:
                c_specs = [
                           ('code',1,0,'text',line.get('code')or ' -'),
                           ('name', 1, 0, 'text',line.get('name')or '' ),
                           ('balance', 1, 0, 'number', line.get('balance') or 0.0, None, style_line_decimal),
                           ]

        if line['original_name'] == 'afr.2cols':
            if 'bold_req' in line.keys():
                c_specs = [
                           ('code',1,0,'text','',None,style_yellow_bold),
                           ('name', 1, 0, 'text',line.get('name')or '',None,style_yellow_bold),
                           ('debit', 1, 0, 'number', line.get('debit') or 0.0, None, style_yellow_bold),
                           ('credit', 1, 0, 'number', line.get('credit') or 0.0, None, style_yellow_bold),
                           ]
            else:
                c_specs = [
                           ('code',1,0,'text',line.get('code')or ' -'),
                           ('name', 1, 0, 'text',line.get('name')or '' ),
                           ('debit', 1, 0, 'number', line.get('debit') or 0.0, None, style_line_decimal),
                           ('credit', 1, 0, 'number', line.get('credit') or 0.0, None, style_line_decimal),
                           ]

        if line['original_name'] == 'afr.4cols':
            if 'bold_req' in line.keys():
                c_specs = [
                           ('code',1,0,'text','',None,style_yellow_bold),
                           ('name', 1, 0, 'text',line.get('name')or '',None,style_yellow_bold),
                           ('balanceinit', 1, 0, 'number', line.get('balanceinit') or 0.0, None, style_yellow_bold),
                           ('debit', 1, 0, 'number', line.get('debit') or 0.0, None, style_yellow_bold),
                           ('credit', 1, 0, 'number', line.get('credit') or 0.0, None, style_yellow_bold),
                           ('balance', 1, 0, 'number', line.get('balance') or 0.0, None, style_yellow_bold),
                           ]
            else:
                c_specs = [
                           ('code',1,0,'text',line.get('code')or ' -'),
                           ('name', 1, 0, 'text',line.get('name')or '' ),
                           ('balanceinit', 1, 0, 'number', line.get('balanceinit') or 0.0, None, style_line_decimal),
                           ('debit', 1, 0, 'number', line.get('debit') or 0.0, None, style_line_decimal),
                           ('credit', 1, 0, 'number', line.get('credit') or 0.0, None, style_line_decimal),
                           ('balance', 1, 0, 'number', line.get('balance') or 0.0, None, style_line_decimal),
                           ]

        if line['original_name'] == 'afr.5cols':
            if 'bold_req' in line.keys():
                c_specs = [
                           ('code',1,0,'text','',None,style_yellow_bold),
                           ('name', 1, 0, 'text',line.get('name')or '',None,style_yellow_bold),
                           ('balanceinit', 1, 0, 'number', line.get('balanceinit') or 0.0, None, style_yellow_bold),
                           ('debit', 1, 0, 'number', line.get('debit') or 0.0, None, style_yellow_bold),
                           ('credit', 1, 0, 'number', line.get('credit') or 0.0, None, style_yellow_bold),
                           ('ytd', 1, 0, 'number', line.get('ytd') or 0.0, None, style_yellow_bold),
                           ('balance', 1, 0, 'number', line.get('balance') or 0.0, None, style_yellow_bold),
                           ]
            else:
                c_specs = [
                           ('code',1,0,'text',line.get('code')or ' -'),
                           ('name', 1, 0, 'text',line.get('name')or '' ),
                           ('balanceinit', 1, 0, 'number', line.get('balanceinit') or 0.0, None, style_line_decimal),
                           ('debit', 1, 0, 'number', line.get('debit') or 0.0, None, style_line_decimal),
                           ('credit', 1, 0, 'number', line.get('credit') or 0.0, None, style_line_decimal),
                           ('ytd', 1, 0, 'number', line.get('ytd') or 0.0, None, style_line_decimal),
                           ('balance', 1, 0, 'number', line.get('balance') or 0.0, None, style_line_decimal),
                           ]

        if line['original_name'] == 'afr.qtrcols':
            if 'bold_req' in line.keys():
                c_specs = [
                           ('code',1,0,'text','',None,style_yellow_bold),
                           ('name', 1, 0, 'text',line.get('name')or '',None,style_yellow_bold),
                           ('q1', 1, 0, 'number', line.get('bal1') or 0.0, None, style_yellow_bold),
                           ('q2', 1, 0, 'number', line.get('bal2') or 0.0, None, style_yellow_bold),
                           ('q3', 1, 0, 'number', line.get('bal3') or 0.0, None, style_yellow_bold),
                           ('q4', 1, 0, 'number', line.get('bal4') or 0.0, None, style_yellow_bold),
                           ('ytd', 1, 0, 'number', line.get('bal5') or 0.0, None, style_yellow_bold),
                           ]
            else:
                c_specs = [
                           ('code',1,0,'text',line.get('code')or ' -'),
                           ('name', 1, 0, 'text',line.get('name')or ''),
                           ('q1', 1, 0, 'number', line.get('bal1') or 0.0, None, style_line_decimal),
                           ('q2', 1, 0, 'number', line.get('bal2') or 0.0, None, style_line_decimal),
                           ('q3', 1, 0, 'number', line.get('bal3') or 0.0, None, style_line_decimal),
                           ('q4', 1, 0, 'number', line.get('bal4') or 0.0, None, style_line_decimal),
                           ('ytd', 1, 0, 'number', line.get('bal5') or 0.0, None, style_line_decimal),
                           ]

        if line['original_name'] == 'afr.13cols':
            if 'bold_req' in line.keys():
                c_specs = [
                           ('code',1,0,'text','',None,style_yellow_bold),
                           ('name', 1, 0, 'text',line.get('name')or '',None,style_yellow_bold),
                           ('q1', 1, 0, 'number', line.get('bal1') or 0.0, None, style_yellow_bold),
                           ('q2', 1, 0, 'number', line.get('bal2') or 0.0, None, style_yellow_bold),
                           ('q3', 1, 0, 'number', line.get('bal3') or 0.0, None, style_yellow_bold),
                           ('q4', 1, 0, 'number', line.get('bal4') or 0.0, None, style_yellow_bold),
                           ('q5', 1, 0, 'number', line.get('bal5') or 0.0, None, style_yellow_bold),
                           ('q6', 1, 0, 'number', line.get('bal6') or 0.0, None, style_yellow_bold),
                           ('q7', 1, 0, 'number', line.get('bal7') or 0.0, None, style_yellow_bold),
                           ('q8', 1, 0, 'number', line.get('bal8') or 0.0, None, style_yellow_bold),
                           ('q9', 1, 0, 'number', line.get('bal9') or 0.0, None, style_yellow_bold),
                           ('q10', 1, 0, 'number', line.get('bal10') or 0.0, None, style_yellow_bold),
                           ('q11', 1, 0, 'number', line.get('bal11') or 0.0, None, style_yellow_bold),
                           ('q12', 1, 0, 'number', line.get('bal12') or 0.0, None, style_yellow_bold),
                           ('ytd', 1, 0, 'number', line.get('bal13') or 0.0, None, style_yellow_bold),
                           ]
            else:
                c_specs = [
                           ('code',1,0,'text',line.get('code')or ' -'),
                           ('name', 1, 0, 'text',line.get('name')or ''),
                           ('q1', 1, 0, 'number', line.get('bal1') or 0.0, None, style_line_decimal),
                           ('q2', 1, 0, 'number', line.get('bal2') or 0.0, None, style_line_decimal),
                           ('q3', 1, 0, 'number', line.get('bal3') or 0.0, None, style_line_decimal),
                           ('q4', 1, 0, 'number', line.get('bal4') or 0.0, None, style_line_decimal),
                           ('q5', 1, 0, 'number', line.get('bal5') or 0.0, None, style_line_decimal),
                           ('q6', 1, 0, 'number', line.get('bal6') or 0.0, None, style_line_decimal),
                           ('q7', 1, 0, 'number', line.get('bal7') or 0.0, None, style_line_decimal),
                           ('q8', 1, 0, 'number', line.get('bal8') or 0.0, None, style_line_decimal),
                           ('q9', 1, 0, 'number', line.get('bal9') or 0.0, None, style_line_decimal),
                           ('q10', 1, 0, 'number', line.get('bal10') or 0.0, None, style_line_decimal),
                           ('q11', 1, 0, 'number', line.get('bal11') or 0.0, None, style_line_decimal),
                           ('q12', 1, 0, 'number', line.get('bal12') or 0.0, None, style_line_decimal),
                           ('ytd', 1, 0, 'number', line.get('bal13') or 0.0, None, style_line_decimal),
                           ]

        row_data = self.xls_row_template(c_specs, [x[0] for x in c_specs])
        row_position = self.xls_write_row(ws, row_position, row_data, style_line_default)
        return row_position

    def print_ledger_lines(self, row_pos, lines_data, _xs, xlwt, _p, data): # export the invoice AR/AP lines

            row_start_account = row_pos

            row_start_account = row_pos
            res_obj = self.pool.get('ir.property')

            row_pos = self.print_empty_row(row_pos)
            row_pos = self.print_columns_title(_p, data, row_pos)

            line_number=1
            for acc in lines_data:
                line_number = 0
                balance=0
                line={}

                if 'bold_req' in acc.keys():
                    line['bold_req']=acc['bold_req']

                if 'code' in acc.keys():
                    line['code']=acc['code']        
                
                if 'balance' in acc.keys():
                    line['balance'] = acc['balance']
                    
                line['total']=acc['total']
                line['name'] = acc['name']
                line['label']=acc['label']
                line['original_name']=data['form']['original_name']

                if data['form']['original_name']=='afr.13cols':
                    line['bal1']=acc['bal1']
                    line['bal2']=acc['bal2']
                    line['bal3']=acc['bal3']
                    line['bal4']=acc['bal4']
                    line['bal5']=acc['bal5']                    
                    line['bal6']=acc['bal6']
                    line['bal7']=acc['bal7']
                    line['bal8']=acc['bal8']
                    line['bal9']=acc['bal9']
                    line['bal10']=acc['bal10']
                    line['bal11']=acc['bal11']
                    line['bal12']=acc['bal12']
                    line['bal13']=acc['bal13']
                
                if data['form']['original_name']=='afr.qtrcols':
                    line['bal1']=acc['bal1']
                    line['bal2']=acc['bal2']
                    line['bal3']=acc['bal3']
                    line['bal4']=acc['bal4']
                    line['bal5']=acc['bal5']
                else:

                    if 'credit' in acc.keys():
                        line['credit']=acc['credit']
                    
                    if 'debit' in acc.keys():
                        line['debit']=acc['debit']
                    
                    if 'balanceinit' in acc.keys():
                        line['balanceinit']=acc['balanceinit']
                    
                    if 'ytd' in acc.keys():
                        line['ytd']=acc['ytd']
                    
                    if 'type' in acc.keys():
                        line['type']=acc['type']
                
                row_pos_start = row_pos
                row_pos = self.print_lines(row_pos, acc, line, _p, data, line_number)
                line_number += 1

            return row_pos

    def special_period(self, periods):
        period_obj = self.pool.get('account.period')
        period_brw = period_obj.browse(self.cr, self.uid, periods)
        period_counter = [True for i in period_brw if not i.special]
        if not period_counter:
            return True
        return False

    def exchange(self, from_amount):
        if self.from_currency_id == self.to_currency_id:
            return from_amount
        curr_obj = self.pool.get('res.currency')
        return curr_obj.compute(self.cr, self.uid, self.from_currency_id, self.to_currency_id, from_amount)

    def get_company_accounts(self, company_id, acc='credit'):
        rc_obj = self.pool.get('res.company')
        if acc == 'credit':
            return [brw.id for brw in rc_obj.browse(self.cr, self.uid, company_id).credit_account_ids]
        else:
            return [brw.id for brw in rc_obj.browse(self.cr, self.uid, company_id).debit_account_ids]

    def get_company_currency(self, company_id):
        rc_obj = self.pool.get('res.company')
        return rc_obj.browse(self.cr, self.uid, company_id).currency_id.id

    def lines(self,form,level=0):
     #   print "Testing the FOrm Omi... In Xls :::", form
        self.context=form['context']
        """
        Returns all the data needed for the report lines
        (account info plus debit/credit/balance in the selected period
        and the full year)
        """
        account_obj = self.pool.get('account.account')
        period_obj = self.pool.get('account.period')
        fiscalyear_obj = self.pool.get('account.fiscalyear')

        def _get_children_and_consol(cr, uid, ids, level, context={}, change_sign=False):
            aa_obj = self.pool.get('account.account')
            ids2 = []
            for aa_brw in aa_obj.browse(cr, uid, ids, context):
                if aa_brw.child_id and aa_brw.level < level and aa_brw.type != 'consolidation':
                    if not change_sign:
                        ids2.append([aa_brw.id, True, False, aa_brw])
                    ids2 += _get_children_and_consol(cr, uid, [
                                                     x.id for x in aa_brw.child_id], level, context, change_sign=change_sign)
                    if change_sign:
                        ids2.append(aa_brw.id)
                    else:
                        ids2.append([aa_brw.id, False, True, aa_brw])
                else:
                    if change_sign:
                        ids2.append(aa_brw.id)
                    else:
                        ids2.append([aa_brw.id, True, True, aa_brw])
            #print "Testing Omkar ... in _get_children_and_consol",ids2
            return ids2

        #######################################################################
        # CONTEXT FOR ENDIND BALANCE                                                #
        #######################################################################
        def _ctx_end(ctx):
            ctx_end = ctx
            ctx_end['filter'] = form.get('filter', 'all')
            ctx_end['fiscalyear'] = fiscalyear.id
            #~ ctx_end['periods'] = period_obj.search(self.cr, self.uid, [('fiscalyear_id','=',fiscalyear.id),('special','=',False)])

            if ctx_end['filter'] not in ['bydate', 'none']:
                special = self.special_period(form['periods'])
            else:
                special = False

            if form['filter'] in ['byperiod', 'all']:
                if special:
                    ctx_end['periods'] = period_obj.search(self.cr, self.uid, [(
                        'id', 'in', form['periods'] or ctx_end.get('periods', False))])
                else:
                    ctx_end['periods'] = period_obj.search(self.cr, self.uid, [('id', 'in', form[
                                                           'periods'] or ctx_end.get('periods', False)), ('special', '=', False)])

            if form['filter'] in ['bydate', 'all', 'none']:
                ctx_end['date_from'] = form['date_from']
                ctx_end['date_to'] = form['date_to']
            return ctx_end.copy()

        def missing_period(ctx_init):

            ctx_init['fiscalyear'] = fiscalyear_obj.search(self.cr, self.uid, [('date_stop', '<', fiscalyear.date_start)], order='date_stop') and \
                fiscalyear_obj.search(self.cr, self.uid, [(
                                                          'date_stop', '<', fiscalyear.date_start)], order='date_stop')[-1] or []
            ctx_init['periods'] = period_obj.search(self.cr, self.uid, [(
                'fiscalyear_id', '=', ctx_init['fiscalyear']), ('date_stop', '<', fiscalyear.date_start)])
            return ctx_init
        #######################################################################
        # CONTEXT FOR INITIAL BALANCE                                               #
        #######################################################################

        def _ctx_init(ctx):
            ctx_init = self.context.copy()
            ctx_init['filter'] = form.get('filter', 'all')
            ctx_init['fiscalyear'] = fiscalyear.id

            if form['filter'] in ['byperiod', 'all']:
                ctx_init['periods'] = form['periods']
                if not ctx_init['periods']:
                    ctx_init = missing_period(ctx_init.copy())
                date_start = min([period.date_start for period in period_obj.browse(
                    self.cr, self.uid, ctx_init['periods'])])
                ctx_init['periods'] = period_obj.search(self.cr, self.uid, [(
                    'fiscalyear_id', '=', fiscalyear.id), ('date_stop', '<=', date_start)])
            elif form['filter'] in ['bydate']:
                ctx_init['date_from'] = fiscalyear.date_start
                ctx_init['date_to'] = form['date_from']
                ctx_init['periods'] = period_obj.search(self.cr, self.uid, [(
                    'fiscalyear_id', '=', fiscalyear.id), ('date_stop', '<=', ctx_init['date_to'])])
            elif form['filter'] == 'none':
                ctx_init['periods'] = period_obj.search(self.cr, self.uid, [(
                    'fiscalyear_id', '=', fiscalyear.id), ('special', '=', True)])
                date_start = min([period.date_start for period in period_obj.browse(
                    self.cr, self.uid, ctx_init['periods'])])
                ctx_init['periods'] = period_obj.search(self.cr, self.uid, [(
                    'fiscalyear_id', '=', fiscalyear.id), ('date_start', '<=', date_start), ('special', '=', True)])

            return ctx_init.copy()

        def z(n):
            return abs(n) < 0.005 and 0.0 or n

        self.context['state'] = form['target_move'] or 'posted'

        self.from_currency_id = self.get_company_currency(form['company_id'] and type(form[
                                                          'company_id']) in (list, tuple) and form['company_id'][0] or form['company_id'])
        if not form['currency_id']:
            self.to_currency_id = self.from_currency_id
        else:
            self.to_currency_id = form['currency_id'] and type(form['currency_id']) in (
                list, tuple) and form['currency_id'][0] or form['currency_id']

        if 'account_list' in form and form['account_list']:
            account_ids = form['account_list']
            account_list = form['account_list']
            del form['account_list']

        credit_account_ids = self.get_company_accounts(form['company_id'] and type(form[
                                                       'company_id']) in (list, tuple) and form['company_id'][0] or form['company_id'], 'credit')

        debit_account_ids = self.get_company_accounts(form['company_id'] and type(form[
                                                      'company_id']) in (list, tuple) and form['company_id'][0] or form['company_id'], 'debit')


        if form.get('fiscalyear'):
            if type(form.get('fiscalyear')) in (list, tuple):
                fiscalyear = form['fiscalyear'] and form['fiscalyear'][0]
            elif type(form.get('fiscalyear')) in (int,):
                fiscalyear = form['fiscalyear']
        fiscalyear = fiscalyear_obj.browse(self.cr, self.uid, fiscalyear)

        ################################################################
        # Get the accounts                                             #
        ################################################################
        all_account_ids = _get_children_and_consol(
            self.cr, self.uid, account_ids, 100, self.context)

        account_ids = _get_children_and_consol(self.cr, self.uid, account_ids, form[
                                               'display_account_level'] and form['display_account_level'] or 100, self.context)

        credit_account_ids = _get_children_and_consol(
            self.cr, self.uid, credit_account_ids, 100, self.context, change_sign=True)

        debit_account_ids = _get_children_and_consol(
            self.cr, self.uid, debit_account_ids, 100, self.context, change_sign=True)

        credit_account_ids = list(set(
            credit_account_ids) - set(debit_account_ids))
        #
        # Generate the report lines (checking each account)
        #

        tot_check = False

        if not form['periods']:
            form['periods'] = period_obj.search(self.cr, self.uid, [(
                'fiscalyear_id', '=', fiscalyear.id), ('special', '=', False)], order='date_start asc')
            if not form['periods']:
                raise osv.except_osv(_('UserError'), _(
                    'The Selected Fiscal Year Does not have Regular Periods'))

        if form['columns'] == 'qtr':
            period_ids = period_obj.search(self.cr, self.uid, [(
                'fiscalyear_id', '=', fiscalyear.id), ('special', '=', False)], order='date_start asc')
            a = 0
            l = []
            p = []
            for x in period_ids:
                a += 1
                if a < 3:
                        l.append(x)
                else:
                        l.append(x)
                        p.append(l)
                        l = []
                        a = 0
            tot_bal1 = 0.0
            tot_bal2 = 0.0
            tot_bal3 = 0.0
            tot_bal4 = 0.0
            tot_bal5 = 0.0
        elif form['columns'] == 'thirteen':
            period_ids = period_obj.search(self.cr, self.uid, [(
                'fiscalyear_id', '=', fiscalyear.id), ('special', '=', False)], order='date_start asc')
            tot_bal1 = 0.0
            tot_bal1 = 0.0
            tot_bal2 = 0.0
            tot_bal3 = 0.0
            tot_bal4 = 0.0
            tot_bal5 = 0.0
            tot_bal6 = 0.0
            tot_bal7 = 0.0
            tot_bal8 = 0.0
            tot_bal9 = 0.0
            tot_bal10 = 0.0
            tot_bal11 = 0.0
            tot_bal12 = 0.0
            tot_bal13 = 0.0
        else:
            ctx_end = _ctx_end(self.context.copy())
            tot_bin = 0.0
            tot_deb = 0.0
            tot_crd = 0.0
            tot_ytd = 0.0
            tot_eje = 0.0

        res = {}
        result_acc = []
        tot = {}

        ###############################################################
        # Calculations of credit, debit and balance,
        # without repeating operations.
        ###############################################################

        account_black_ids = account_obj.search(self.cr, self.uid, (
                                               [('id', 'in', [i[0] for i in all_account_ids]),
                                                ('type', 'not in',
                                                 ('view', 'consolidation'))]))

        account_not_black_ids = account_obj.search(self.cr, self.uid, ([('id', 'in', [
                                                   i[0] for i in all_account_ids]), ('type', '=', 'view')]))

        acc_cons_ids = account_obj.search(self.cr, self.uid, ([('id', 'in', [
            i[0] for i in all_account_ids]), ('type', 'in', ('consolidation',))]))

        account_consol_ids = acc_cons_ids and account_obj._get_children_and_consol(
            self.cr, self.uid, acc_cons_ids) or []

        account_black_ids += account_obj.search(self.cr, self.uid, (
            [('id', 'in', account_consol_ids),
             ('type', 'not in',
              ('view', 'consolidation'))]))

        account_black_ids = list(set(account_black_ids))

        c_account_not_black_ids = account_obj.search(self.cr, self.uid, ([
            ('id', 'in',
             account_consol_ids),
            ('type', '=', 'view')]))
        delete_cons = False
        if c_account_not_black_ids:
            delete_cons = set(account_not_black_ids) & set(
                c_account_not_black_ids) and True or False
            account_not_black_ids = list(
                set(account_not_black_ids) - set(c_account_not_black_ids))

        # This could be done quickly with a sql sentence
        account_not_black = account_obj.browse(
            self.cr, self.uid, account_not_black_ids)
        account_not_black.sort(key=lambda x: x.level)
        account_not_black.reverse()
        account_not_black_ids = [i.id for i in account_not_black]

        c_account_not_black = account_obj.browse(
            self.cr, self.uid, c_account_not_black_ids)
        c_account_not_black.sort(key=lambda x: x.level)
        c_account_not_black.reverse()
        c_account_not_black_ids = [i.id for i in c_account_not_black]

        if delete_cons:
            account_not_black_ids = c_account_not_black_ids + \
                account_not_black_ids
            account_not_black = c_account_not_black + account_not_black
        else:
            acc_cons_brw = account_obj.browse(
                self.cr, self.uid, acc_cons_ids)
            acc_cons_brw.sort(key=lambda x: x.level)
            acc_cons_brw.reverse()
            acc_cons_ids = [i.id for i in acc_cons_brw]

            account_not_black_ids = c_account_not_black_ids + \
                acc_cons_ids + account_not_black_ids
            account_not_black = c_account_not_black + \
                acc_cons_brw + account_not_black

        all_account_period = {}  # All accounts per period

        # Iteration limit depending on the number of columns
        if form['columns'] == 'thirteen':
            limit = 13
        elif form['columns'] == 'qtr':
            limit = 5
        else:
            limit = 1

        for p_act in range(limit):
            if limit != 1:
                if p_act == limit - 1:
                    form['periods'] = period_ids
                else:
                    if form['columns'] == 'thirteen':
                        form['periods'] = [period_ids[p_act]]
                    elif form['columns'] == 'qtr':
                        form['periods'] = p[p_act]

            if form['inf_type'] == 'IS':
                ctx_to_use = _ctx_end(self.context.copy())
            else:
                ctx_i = _ctx_init(self.context.copy())
                ctx_to_use = _ctx_end(self.context.copy())

            account_black = account_obj.browse(
                self.cr, self.uid, account_black_ids, ctx_to_use)

            if form['inf_type'] == 'BS':
                account_black_init = account_obj.browse(
                    self.cr, self.uid, account_black_ids, ctx_i)

            #~ Black
            dict_black = {}
            for i in account_black:
                d = i.debit
                c = i.credit
                dict_black[i.id] = {
                    'obj': i,
                    'debit': d,
                    'credit': c,
                    'balance': d - c
                }
                if form['inf_type'] == 'BS':
                    dict_black.get(i.id)['balanceinit'] = 0.0

            # If the report is a balance sheet
            # Balanceinit values are added to the dictionary
            if form['inf_type'] == 'BS':
                for i in account_black_init:
                    dict_black.get(i.id)['balanceinit'] = i.balance

            #~ Not black
            dict_not_black = {}
            for i in account_not_black:
                dict_not_black[i.id] = {
                    'obj': i, 'debit': 0.0, 'credit': 0.0, 'balance': 0.0}
                if form['inf_type'] == 'BS':
                    dict_not_black.get(i.id)['balanceinit'] = 0.0

            all_account = dict_black.copy(
            )  # It makes a copy because they modify

            for acc_id in account_not_black_ids:
                acc_childs = dict_not_black.get(acc_id).get('obj').type == 'view' \
                    and dict_not_black.get(acc_id).get('obj').child_id \
                    or dict_not_black.get(acc_id).get('obj').child_consol_ids
                for child_id in acc_childs:
                    if child_id.type == 'consolidation' and delete_cons:
                        continue
                    dict_not_black.get(acc_id)['debit'] += all_account.get(
                        child_id.id).get('debit')
                    dict_not_black.get(acc_id)['credit'] += all_account.get(
                        child_id.id).get('credit')
                    dict_not_black.get(acc_id)['balance'] += all_account.get(
                        child_id.id).get('balance')
                    if form['inf_type'] == 'BS':
                        dict_not_black.get(acc_id)['balanceinit'] += all_account.get(
                            child_id.id).get('balanceinit')
                all_account[acc_id] = dict_not_black[acc_id]

            if p_act == limit - 1:
                all_account_period['all'] = all_account
            else:
                if form['columns'] == 'thirteen':
                    all_account_period[p_act] = all_account
                elif form['columns'] == 'qtr':
                    all_account_period[p_act] = all_account

        ###############################################################
        # End of the calculations of credit, debit and balance
        #
        ###############################################################

        for aa_id in account_ids:
            #print"AA_ID:", aa_id[-1].name
            id = aa_id[0]
            if aa_id[3].type == 'consolidation' and delete_cons:
                continue
            #
            # Check if we need to include this level
            #
            if not form['display_account_level'] or aa_id[3].level <= form['display_account_level']:
                #print "Here is the Name As Per Guess::::::::::::::::::::", aa_id[3].name.upper()
                res = {
                    'id': id,
                    'type': aa_id[3].type,
                    'code': aa_id[3].code,
                    'name': (aa_id[2] and not aa_id[1]) and 'TOTAL %s' % (aa_id[3].name.upper()) or aa_id[3].name,
                    'parent_id': aa_id[3].parent_id and aa_id[3].parent_id.id,
                    'level': aa_id[3].level,
                    'label': aa_id[1],
                    'total': aa_id[2],
                    'change_sign': credit_account_ids and (id in credit_account_ids and -1 or 1) or 1
                }
                if res['name'] == "TOTAL %s" % (aa_id[3].name.upper()):
                    res.update({'bold_req':True})

                if form['columns'] == 'qtr':
                    for pn in range(1, 5):

                        if form['inf_type'] == 'IS':
                            d, c, b = map(z, [
                                          all_account_period.get(pn - 1).get(id).get('debit', 0.0), all_account_period.get(pn - 1).get(id).get('credit', 0.0), all_account_period.get(pn - 1).get(id).get('balance', 0.0)])
                            res.update({
                                'dbr%s' % pn: self.exchange(d),
                                'cdr%s' % pn: self.exchange(c),
                                'bal%s' % pn: self.exchange(b),
                            })
                        else:
                            i, d, c = map(z, [
                                          all_account_period.get(pn - 1).get(id).get('balanceinit', 0.0), all_account_period.get(pn - 1).get(id).get('debit', 0.0), all_account_period.get(pn - 1).get(id).get('credit', 0.0)])
                            b = z(i + d - c)
                            res.update({
                                'dbr%s' % pn: self.exchange(d),
                                'cdr%s' % pn: self.exchange(c),
                                'bal%s' % pn: self.exchange(b),
                            })

                    if form['inf_type'] == 'IS':
                        d, c, b = map(z, [
                                      all_account_period.get('all').get(id).get('debit', 0.0), all_account_period.get('all').get(id).get('credit', 0.0), all_account_period.get('all').get(id).get('balance')])
                        res.update({
                            'dbr5': self.exchange(d),
                            'cdr5': self.exchange(c),
                            'bal5': self.exchange(b),
                        })
                    else:
                        i, d, c = map(z, [
                                      all_account_period.get('all').get(id).get('balanceinit', 0.0), all_account_period.get('all').get(id).get('debit', 0.0), all_account_period.get('all').get(id).get('credit', 0.0)])
                        b = z(i + d - c)
                        res.update({
                            'dbr5': self.exchange(d),
                            'cdr5': self.exchange(c),
                            'bal5': self.exchange(b),
                        })

                elif form['columns'] == 'thirteen':
                    pn = 1
                    for p_num in range(12):

                        if form['inf_type'] == 'IS':
                            d, c, b = map(z, [
                                          all_account_period.get(p_num).get(id).get('debit', 0.0), all_account_period.get(p_num).get(id).get('credit', 0.0), all_account_period.get(p_num).get(id).get('balance', 0.0)])
                            res.update({
                                'dbr%s' % pn: self.exchange(d),
                                'cdr%s' % pn: self.exchange(c),
                                'bal%s' % pn: self.exchange(b),
                            })
                        else:
                            i, d, c = map(z, [
                                          all_account_period.get(p_num).get(id).get('balanceinit', 0.0), all_account_period.get(p_num).get(id).get('debit', 0.0), all_account_period.get(p_num).get(id).get('credit', 0.0)])
                            b = z(i + d - c)
                            res.update({
                                'dbr%s' % pn: self.exchange(d),
                                'cdr%s' % pn: self.exchange(c),
                                'bal%s' % pn: self.exchange(b),
                            })

                        pn += 1

                    if form['inf_type'] == 'IS':
                        d, c, b = map(z, [
                                      all_account_period.get('all').get(id).get('debit', 0.0), all_account_period.get('all').get(id).get('credit', 0.0), all_account_period.get('all').get(id).get('balance', 0.0)])
                        res.update({
                            'dbr13': self.exchange(d),
                            'cdr13': self.exchange(c),
                            'bal13': self.exchange(b),
                        })
                    else:
                        i, d, c = map(z, [
                                      all_account_period.get('all').get(id).get('balanceinit', 0.0), all_account_period.get('all').get(id).get('debit', 0.0), all_account_period.get('all').get(id).get('credit', 0.0)])
                        b = z(i + d - c)
                        res.update({
                            'dbr13': self.exchange(d),
                            'cdr13': self.exchange(c),
                            'bal13': self.exchange(b),
                        })

                else:
                    
                    i, d, c = map(z, [
                                  all_account_period.get('all').get(id).get('balanceinit', 0.0), all_account_period.get('all').get(id).get('debit', 0.0), all_account_period.get('all').get(id).get('credit', 0.0)])
                    b = z(i + d - c)
                    res.update({
                        'balanceinit': self.exchange(i),
                        'debit': self.exchange(d),
                        'credit': self.exchange(c),
                        'ytd': self.exchange(d - c),
                    })

                    if form['inf_type'] == 'IS' and form['columns'] == 'one':
                        res.update({
                            'balance': self.exchange(d - c),
                        })
                    else:
                        res.update({
                            'balance': self.exchange(b),
                        })

                #
                # Check whether we must include this line in the report or not
                #
                to_include = False

                if form['columns'] in ('thirteen', 'qtr'):
                    to_test = [False]
                    if form['display_account'] == 'mov' and aa_id[3].parent_id:
                        # Include accounts with movements
                        for x in range(pn - 1):
                            to_test.append(res.get(
                                'dbr%s' % x, 0.0) >= 0.005 and True or False)
                            to_test.append(res.get(
                                'cdr%s' % x, 0.0) >= 0.005 and True or False)
                        if any(to_test):
                            to_include = True

                    elif form['display_account'] == 'bal' and aa_id[3].parent_id:
                        # Include accounts with balance
                        for x in range(pn - 1):
                            to_test.append(res.get(
                                'bal%s' % x, 0.0) >= 0.005 and True or False)
                        if any(to_test):
                            to_include = True

                    elif form['display_account'] == 'bal_mov' and aa_id[3].parent_id:
                        # Include accounts with balance or movements
                        for x in range(pn - 1):
                            to_test.append(res.get(
                                'bal%s' % x, 0.0) >= 0.005 and True or False)
                            to_test.append(res.get(
                                'dbr%s' % x, 0.0) >= 0.005 and True or False)
                            to_test.append(res.get(
                                'cdr%s' % x, 0.0) >= 0.005 and True or False)
                        if any(to_test):
                            to_include = True
                    else:
                        # Include all accounts
                        to_include = True

                else:

                    if form['display_account'] == 'mov' and aa_id[3].parent_id:
                        # Include accounts with movements
                        if abs(d) >= 0.005 or abs(c) >= 0.005:
                            to_include = True
                    elif form['display_account'] == 'bal' and aa_id[3].parent_id:
                        # Include accounts with balance
                        if abs(b) >= 0.005:
                            to_include = True
                    elif form['display_account'] == 'bal_mov' and aa_id[3].parent_id:
                        # Include accounts with balance or movements
                        if abs(b) >= 0.005 or abs(d) >= 0.005 or abs(c) >= 0.005:
                            to_include = True
                    else:
                        # Include all accounts
                        to_include = True

                #~ ANALYTIC LEDGER
                if to_include and form['analytic_ledger'] and form['columns'] == 'four' and form['inf_type'] == 'BS' and res['type'] in ('other', 'liquidity', 'receivable', 'payable'):
                    res['mayor'] = self._get_analytic_ledger(res, ctx=ctx_end)
                elif to_include and form['journal_ledger'] and form['columns'] == 'four' and form['inf_type'] == 'BS' and res['type'] in ('other', 'liquidity', 'receivable', 'payable'):
                    res['journal'] = self._get_journal_ledger(res, ctx=ctx_end)
                elif to_include and form['partner_balance'] and form['columns'] == 'four' and form['inf_type'] == 'BS' and res['type'] in ('other', 'liquidity', 'receivable', 'payable'):
                    res['partner'] = self._get_partner_balance(
                        res, ctx_i['periods'], ctx=ctx_end)
                else:
                    res['mayor'] = []

                if to_include:
                    result_acc.append(res)
                    #
                    # Check whether we must sumarize this line in the report or not
                    #
                    if form['tot_check'] and (res['id'] in account_list) and (res['id'] not in tot):
                        if form['columns'] == 'qtr':
                            tot_check = True
                            tot[res['id']] = True
                            tot_bal1 += res.get('bal1', 0.0)
                            tot_bal2 += res.get('bal2', 0.0)
                            tot_bal3 += res.get('bal3', 0.0)
                            tot_bal4 += res.get('bal4', 0.0)
                            tot_bal5 += res.get('bal5', 0.0)

                        elif form['columns'] == 'thirteen':
                            tot_check = True
                            tot[res['id']] = True
                            tot_bal1 += res.get('bal1', 0.0)
                            tot_bal2 += res.get('bal2', 0.0)
                            tot_bal3 += res.get('bal3', 0.0)
                            tot_bal4 += res.get('bal4', 0.0)
                            tot_bal5 += res.get('bal5', 0.0)
                            tot_bal6 += res.get('bal6', 0.0)
                            tot_bal7 += res.get('bal7', 0.0)
                            tot_bal8 += res.get('bal8', 0.0)
                            tot_bal9 += res.get('bal9', 0.0)
                            tot_bal10 += res.get('bal10', 0.0)
                            tot_bal11 += res.get('bal11', 0.0)
                            tot_bal12 += res.get('bal12', 0.0)
                            tot_bal13 += res.get('bal13', 0.0)
                        else:
                            tot_check = True
                            tot[res['id']] = True
                            tot_bin += res['balanceinit']
                            tot_deb += res['debit']
                            tot_crd += res['credit']
                            tot_ytd += res['ytd']
                            tot_eje += res['balance']

        if tot_check:
            str_label = form['lab_str']
            res2 = {
                'bold_req':True,
                'type': 'view',
                'name': 'TOTAL %s' % (str_label),
                'label': False,
                'total': True,
            }
            if form['columns'] == 'qtr':
                res2.update(dict(
                            bal1=z(tot_bal1),
                            bal2=z(tot_bal2),
                            bal3=z(tot_bal3),
                            bal4=z(tot_bal4),
                            bal5=z(tot_bal5),))
            elif form['columns'] == 'thirteen':
                res2.update(dict(
                            bal1=z(tot_bal1),
                            bal2=z(tot_bal2),
                            bal3=z(tot_bal3),
                            bal4=z(tot_bal4),
                            bal5=z(tot_bal5),
                            bal6=z(tot_bal6),
                            bal7=z(tot_bal7),
                            bal8=z(tot_bal8),
                            bal9=z(tot_bal9),
                            bal10=z(tot_bal10),
                            bal11=z(tot_bal11),
                            bal12=z(tot_bal12),
                            bal13=z(tot_bal13),))

            else:
                res2.update({
                    'balanceinit': tot_bin,
                    'debit': tot_deb,
                    'credit': tot_crd,
                    'ytd': tot_ytd,
                    'balance': tot_eje,
                })
            result_acc.append(res2)
        return result_acc

#### Added Functions From Acount Partner Balance................................

    def report_name(self,form):
        if form['original_name']=='afr.1cols':
            return 'End Balance'
        if form['original_name']=='afr.2cols':
            return 'Debit - Credit'
        if form['original_name']=='afr.4cols':
            return 'Initial - Debit - Credit - YTD'
        if form['original_name']=='afr.5cols':
            return 'Initial - Debit - Credit - Period - YTD'
        if form['original_name']=='afr.qtrcols':
            return "4 QTR's - YTD"
        if form['original_name']=='afr.13cols':
            return '12 Months - YTD'
        

    def generate_xls_report(self, _p, _xs, data, objects, wb): # main function
        # Initializations
        _p.update({'report_name':self.report_name(data['form'])})
        
        self.global_initializations(wb,_p, xlwt, _xs, objects, data)
        row_pos = 0

        row_pos = self.print_title(_p, row_pos)

        ws.set_horz_split_pos(row_pos)

        lines_data = list(self.lines(data['form']))

        row_pos = self.print_ledger_lines(row_pos, lines_data , _xs, xlwt, _p, data)
        row_pos += 1

account_balance_xls('report.afr.account_financial_report_balance_full_xls', 'wizard.report', parser=new_aged_trial_report)
