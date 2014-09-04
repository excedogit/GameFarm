# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Excedo Technologies & Solutions (<http:www.exced.in>).
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
{
    'name' : 'Ru3ix Customer Statement',
    'version' : '1.6',
    'author' : 'Excedo Technolgies & Solutions',
    'category' :'Account Statement',
    'description' : """Print Individual Account Statement.
                       Display Account Statement in Customer.
                       Added New Page Customer Statement in Customers Menu.
                       Send Email to Individual Customers.
                    """,
    'depends': ['account','mail','account_followup',
                'account_financial_report_webkit','email_template'
                ],
    'data': ['view/r3x_customer_account_statement_view.xml',
             'view/r3x_mass_email_view.xml',
             'view/r3x_customer_account_statement_data.xml',
             'view/r3x_account_followup_customer_extenstion.xml',
             'wizard/r3x_customer_statement_print_view.xml',
             'security/r3x_customer_statement_followup_security.xml',
             'security/ir.model.access.csv',
             ],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
