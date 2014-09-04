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

{
    'name' : 'Account voucher reconcile option',
    'version' : '1.0',
    'author' : 'Omkar Pakki',
    'summary': 'Send Invoices and Track Payments',
    'description': """
            This Module will uncheck all the full reconcile transactions in Account Voucher , By default
            this works with a check box.
            The checkbox was default checked , If we uncheck then it will un check all the existing checked options.
            else
             If it is unchecked it will reflect the previous changes...
    """,
    'category': 'Accounting & Finance',
    'sequence': 4,
    'website' : 'http://www.excedo.com',
    'images' : [],
    'depends' : ['account_voucher'],
    'demo' : [],
    'data' : ['account_voucher_reconcile_option.xml',],
    'test' : [],
    'auto_install': False,
    'application': True,
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
