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

{
    'name': 'Account Banking EFT File Export',
    'version': '1.4',
    'author': 'EXCEDO TECHNOLOGY AND SOLUTIONS',
    'website': '',
    'category': 'Account Banking',
    'depends': ['account_banking_payment','account_voucher'],
    'data': [
        'eft_export_view.xml',
        'wizard/export_eft_wizard_view.xml',
        'data/banking_export_eft.xml',
        'security/ir.model.access.csv',
    ],
    'description': '''
    Module to export payment orders .
    This module uses the account_banking logic.
    ''',
    'installable': True,
}
