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

from account_banking import record
from account_banking.parsers import convert

__all__ = ['DirectDebitBatch', 'PaymentsBatch', 'DirectDebit', 'Payment',
           'DirectDebitFile', 'PaymentsFile', 'SalaryPaymentsFile',
           'SalaryPaymentOrder', 'PaymentOrder', 'DirectDebitOrder',
           'OrdersFile',
          ]

class SWIFTField(record.Field):
    '''
    A SWIFTField does not assume 'ascii' data. It actively converts data to
    SWIFT-specs.
    '''
    def __init__(self, *args, **kwargs):
        kwargs['cast'] = convert.to_swift
        super(SWIFTField, self).__init__(*args, **kwargs)

    #def take(self, buffer):
    #    return convert.to_swift(super(SWIFTField, self).take(buffer))

    #def format(self, value):
    #    return convert.to_swift(super(SWIFTField, self).format(value))

class SWIFTFieldNoLeadingWhitespace(SWIFTField):
    def format(self, value):
        return super(SWIFTFieldNoLeadingWhitespace, self).format(
            self.cast(value).lstrip())

def eleven_test(s):
    '''
    Dutch eleven-test for validating 9-long local bank account numbers.
    '''
    r = 0
    l = len(s)
    for i,c in enumerate(s):
        r += (l-i) * int(c)
    return (r % 11) == 0

def chunk(str, length):
    '''
    Split a string in equal sized substrings of length <length>
    '''
    while str:
        yield str[:length]
        str = str[length:]

class HeaderRecord(record.Record): #{{{
    '''ClieOp3 header record'''
    _fields = [
#         record.Filler('recordcode', 4, '0001'),
        record.Filler('recordcode', 1, '0'),
        record.Filler('variantcode', 1, 'A'),
        record.DateField('creation_date', '%d%m%y', auto=True),
        record.Filler('filename', 8, 'CLIEOP03'),
        SWIFTField('sender_id', 5),
        record.Field('file_id', 4),
        record.Field('duplicatecode', 1),
        record.Filler('filler', 21),
    ]

    def __init__(self, id='1', seqno=1, duplicate=False):
        super(HeaderRecord, self).__init__()
        self.sender_id = id or ''
        self.file_id = '%02d%02d' % (self.creation_date.day, seqno)
        self.duplicatecode = duplicate and '2' or '1'
#}}}

class FooterRecord(record.Record):
    '''ClieOp3 footer record'''
    _fields = [
        record.Filler('recordcode', 4, '9999'),
        record.Filler('variantcode', 1, 'A'),
        record.Filler('filler', 45),
    ]

class BatchHeaderRecord(record.Record):
    '''Header record preceding new batches'''
    _fields = [
        record.Filler('recordcode', 4, '0010'),
        record.Field('variantcode', 1),
        record.Field('transactiongroup', 2),
        record.NumberField('accountno_sender', 10),
        record.NumberField('batch_tracer', 4),
        record.Filler('currency_order', 3, 'EUR'),
        SWIFTField('batch_id', 16),
        record.Filler('filler', 10),
    ]

class BatchFooterRecord(record.Record):
    '''Closing record for batches'''
    _fields = [
        record.Filler('recordcode', 4, '9990'),
        record.Filler('variantcode', 1, 'A'),
        record.NumberField('total_amount', 18),
        record.NumberField('total_accountnos', 10),
        record.NumberField('nr_posts', 7),
        record.Filler('filler', 10),
    ]

class FixedMessageRecord(record.Record):
    '''Fixed message'''
    _fields = [
        record.Filler('recordcode', 4, '0020'),
        record.Filler('variantcode', 1, 'A'),
        SWIFTField('fixed_message', 32),
        record.Filler('filler', 13),
    ]

class SenderRecord(record.Record):
    '''Ordering party'''
    _fields = [
        record.Field('NAWcode', 1),
        record.DateField('preferred_execution_date', '%d%m%y', auto=True),
        SWIFTField('name_sender', 35),
        record.Field('testcode', 1),
    ]

class TransactionRecord(record.Record):
    '''Transaction'''
    _fields = [
        record.Filler('recordcode', 4, '0100'),
        record.Filler('variantcode', 1, 'A'),
        record.NumberField('transactiontype', 4),
        record.NumberField('amount', 12),
        record.NumberField('accountno_payer', 10),
        record.NumberField('accountno_beneficiary', 10),
        record.Filler('filler', 9),
    ]

class NamePayerRecord(record.Record):
    '''Name payer'''
    _fields = [
        record.Filler('recordcode', 4, '1111'),
        record.Filler('variantcode', 1, 'B'),
        SWIFTField('name', 35),
        record.Filler('filler', 10),
    ]

class PaymentReferenceRecord(record.Record):
    '''Payment reference'''
    _fields = [
        record.Filler('recordcode', 4, '0150'),
        record.Filler('variantcode', 1, 'A'),
        SWIFTFieldNoLeadingWhitespace('paymentreference', 16),
        record.Filler('filler', 29),
    ]

class DescriptionRecord(record.Record):
    '''Description'''
    _fields = [
        record.Filler('recordcode', 4, '0160'),
        record.Filler('variantcode', 1, 'A'),
        SWIFTField('description', 32),
        record.Filler('filler', 13),
    ]

class NameBeneficiaryRecord(record.Record):
    '''Name receiving party'''
    _fields = [
        record.Filler('recordcode', 4, '0170'),
        record.Filler('variantcode', 1, 'B'),
        SWIFTField('name', 35),
        record.Filler('filler', 10),
    ]

class OrderRecord(record.Record):
    '''Order details'''
    _fields = [
        record.Filler('recordcode', 6, 'KAE092'),
        SWIFTField('name_transactioncode', 18),
        record.NumberField('total_amount', 13),
        record.Field('accountno_sender', 10),
        record.NumberField('total_accountnos', 5),
        record.NumberField('nr_posts', 6),
        record.Field('identification', 6),
        record.DateField('preferred_execution_date', '%y%m%d'),
        record.Field('batch_medium', 18),
        record.Filler('currency', 3, 'EUR'),
        record.Field('testcode', 1),
    ]
    def __init__(self, *args, **kwargs):
        super(OrderRecord, self).__init__(*args, **kwargs)
        self.batch_medium = 'DATACOM'
        self.name_transactioncode = self._transactioncode

class SalaryPaymentOrder(OrderRecord):
    '''Salary payment batch record'''
    _transactioncode = 'SALARIS'

class PaymentOrder(OrderRecord):
    '''Payment batch record'''
    _transactioncode = 'CREDBET'

class DirectDebitOrder(OrderRecord):
    '''Direct debit payments batch record'''
    _transactioncode = 'INCASSO'

class Optional(object):
    '''Auxilliary class to handle optional records'''
    def __init__(self, klass, max=1):
        self._klass = klass
        self._max = max
        self._guts = []

    def __setattr__(self, attr, value):
        '''Check for number of records'''
        if attr[0] == '_':
            super(Optional, self).__setattr__(attr, value)
        else:
            if self._guts and len(self._guts) > self._max:
                raise ValueError, 'Only %d lines are allowed' % self._max
            newitem = self._klass()
            setattr(newitem, attr, value)
            self._guts.append(newitem)

    def __len__(self):
        '''Return actual contents'''
        return len(self._guts)

    def length(self, attr):
        '''Return length of optional record'''
        res = [x for x in self._klass._fields if x.name == attr]
        if res:
            return res[0].length
        raise AttributeError(attr)

    def __getattr__(self, attr):
        '''Only return if used'''
        if attr[0] == '_':
            return super(Optional, self).__getattr__(attr)
        return [getattr(x, attr) for x in self._guts]

    def __iter__(self):
        '''Make sure to adapt'''
        return self._guts.__iter__()

class OrdersFile(object):
    '''A payment orders file'''
    def __init__(self, *args, **kwargs):
        self.orders = []

    @property
    def rawdata(self):
        '''
        Return a writeable file content object
        '''
        return ' '.join(self.orders)

class Transaction(object):
    '''Generic transaction class'''
    def __init__(self, type_=0, name=None, reference=None, messages=[],
                 accountno_beneficiary=None, accountno_payer=None,
                 amount=0,bank_bic='',partner_bank_no=None, ref='', acc_number='',acc_owner='',partner_bank_bic='',reference_no=''
                ):
        self.transaction = TransactionRecord()
        self.reference_no = reference_no
        self.ref = ref
        self.partner_bank_bic =partner_bank_bic
        self.acc_number = acc_number
        self.acc_owner = acc_owner
        self.bank_bic = bank_bic
        self.partner_bank_no = partner_bank_no
        self.paymentreference = Optional(PaymentReferenceRecord)
        self.description = Optional(DescriptionRecord, 4)
        self.transaction.transactiontype = type_
        # Remove Postbank account marker 'P'
        self.transaction.accountno_beneficiary = accountno_beneficiary.replace('P', '0')
        self.transaction.accountno_payer = accountno_payer.replace('P', '0')
        self.transaction.amount = int(round(amount * 100))
        if reference:
            self.paymentreference.paymentreference = reference
        # Allow long message lines to redistribute over multiple message
        # records
        for msg in chunk(''.join(messages),
                           self.description.length('description')
                        ):
            try:
                self.description.description = msg
            except ValueError:
                break
        self.name = name


class DirectDebit(Transaction):
    '''Direct Debit Payment transaction'''
    def __init__(self, *args, **kwargs):
        reknr = kwargs['accountno_payer']
        kwargs['type_'] = len(reknr.lstrip('0')) <= 7 and 1002 or 1001
        super(DirectDebit, self).__init__(*args, **kwargs)

    @property
    def rawdata(self):
        '''
        Return self as writeable file content object
        '''
        items = []
        if self.name:
            items.append(str(1) + str(self.bank_bic) + '-' + str(self.partner_bank_no))
            items.append(str(self.name))
            items.append('00000000')
            part_bank = str(self.partner_bank_bic)
            part_bank = part_bank[0:3] + '-' + part_bank[3:]
            acc_number = self.acc_number[0:3].strip()+'-'+self.acc_number[3:]

            return ''.join(
                           [str(1)] + [str(part_bank).ljust(7)[0:7]] + [str(self.partner_bank_no).rjust(9)[0:10]] + \
                           [''.ljust(1)] + ['50'] +[str("%010d" % (int(self.transaction and self.transaction.amount or 0)))] +\
                           [str(self.name ).ljust(32)[0:32]] + [''.ljust(0)] + [str(self.reference_no).ljust(18)[0:18]] + \
                           [str(acc_number)[0:16]] + [str(self.acc_owner).ljust(16)[0:16]] +   ['00000000']  + ['\n'])

class Payment(Transaction):
    '''Payment transaction'''
    def __init__(self, *args, **kwargs):
        reknr = kwargs['accountno_beneficiary']
        if len(reknr.lstrip('0')) > 7:
            if not eleven_test(reknr):
                raise ValueError, '%s is not a valid bank account' % reknr
        kwargs['type_'] = 5
        self.name = NameBeneficiaryRecord()
        super(Payment, self).__init__(*args, **kwargs)

    @property
    def rawdata(self):
        '''
        Return self as writeable file content object
        '''
        items = [str(self.transaction)]
        for reference in self.paymentreference:
            items.append(str(reference))
        for description in self.description:
            items.append(str(description))
        if self.name:
            items.append(str(self.name))
        return ''.join(items)

class SalaryPayment(Payment):
    '''Salary Payment transaction'''
    def __init__(self, *args, **kwargs):
        reknr = kwargs['accountno_beneficiary']
        kwargs['type_'] = len(reknr.lstrip('0')) <= 7 and 3 or 8
        super(SalaryPayment, self).__init__(*args, **kwargs)

class Batch(object):
    '''Generic batch class'''
    transactionclass = None

    def __init__(self, sender, rekeningnr, execution_date=None,
                 test=True, messages=[], transactiongroup=None,bank_bic='',accountno_sender='',
                 batch_tracer=1, batch_id=''
                ):
        self.accountno_sender = accountno_sender
        self.header = BatchHeaderRecord()
        self.bank_bic = bank_bic
        self.fixed_message = Optional(FixedMessageRecord, 4)
        self.sender = SenderRecord()
        self.footer = BatchFooterRecord()
        self.header.variantcode = batch_id and 'C' or 'B'
        self.header.transactiongroup = transactiongroup
        self.header.batch_tracer = batch_tracer
        self.header.batch_id = batch_id or ''
        self.header.accountno_sender = rekeningnr
        self.sender.name_sender = sender
        self.sender.preferred_execution_date = execution_date
        self.sender.NAWcode = 1
        self.sender.testcode = test and 'T' or 'P'
        self.transactions = []
        for message in messages:
            self.fixed_message.fixed_message = message

    @property
    def nr_posts(self):
        '''nr of posts'''
        return len(self.transactions)

    @property
    def total_amount(self):
        '''total amount transferred'''
        return reduce(lambda x,y: x + int(y.transaction and y.transaction.amount or 0),self.transactions, 0 )

    @property
    def total_accountnos(self):
        '''check number on account numbers'''
        return reduce(lambda x,y:
                          x + int(y.transaction.accountno_payer) + \
                          int(y.transaction.accountno_beneficiary),
                      self.transactions, 0
                     )

    @property
    def rawdata(self):
        '''
        Return self as writeable file content object
        '''
        self.bank_bic = self.bank_bic
        self.footer.nr_posts = self.nr_posts
        self.footer.total_amount = self.total_amount
        self.footer.total_accountnos = self.total_accountnos
        lines = []
        lines += [
            ''.join([x.rawdata for x in self.transactions]),
        ]
        return ''.join(lines)

    def transaction(self, *args, **kwargs):
        '''generic factory method'''
        retval = self.transactionclass(*args, **kwargs)
        self.transactions.append(retval)
        return retval

class DirectDebitBatch(Batch):
    '''Direct Debig Payment batch'''
    transactionclass = DirectDebit

class PaymentsBatch(Batch):
    '''Payment batch'''
    transactionclass = Payment

class SalaryBatch(Batch):
    '''Salary payment class'''
    transactionclass = SalaryPayment

class ClieOpFile(object):
    '''The grand unifying class'''
    def __init__(self, identification='1', execution_date=None,
                 name_sender='', accountno_sender='',banks_name='',eft_user_id='',bank='',no_of_orders='',bank_bic='',total_amount='',
                 test=False, seqno=1, **kwargs):
        self.header = HeaderRecord(id=identification, seqno=seqno)
        self.total_amount = total_amount
        self.footer = FooterRecord()
        self.batches = []
        self._execution_date = execution_date
        self.bank = bank
        self.bank_name = banks_name
        self.eft_user_id = eft_user_id
        self.no_of_orders = no_of_orders
        self.bank_bic = bank_bic
        self._identification = identification
        self._name_sender = name_sender
        self._accno_sender = accountno_sender
        self._test = test

    @property
    def rawdata(self):
        '''Return self as writeable file content object'''

        return ''.join(
            [str(0)] +[''.ljust(17)]+ ['01']  + [str(self.bank_name).ljust(3)[0:3]] + [''.ljust(7)] + [str(self._name_sender).ljust(26)[0:26]] + [str(self.eft_user_id ).ljust(6)[0:6]] + ['CR698'.ljust(11)] + [str(SenderRecord())]+[''.ljust(4)] + ['\n'] +
            [x.rawdata for x in self.batches] +
            ['7999-999'] + [''.ljust(12)]  + [str("%010d" % (int(round(self.total_amount * 100))))] + [str("%010d" % (int(round(self.total_amount * 100))))] + ['0000000000'] + [''.ljust(24)]   + [str(self.no_of_orders)] +[''.ljust(40)]
        )

    def batch(self, *args, **kwargs):
        '''Create batch'''
        kwargs['bank_bic'] = self.bank_bic
        kwargs['transactiongroup'] = self.transactiongroup
        kwargs['batch_tracer'] = len(self.batches) +1
        kwargs['execution_date'] = self._execution_date
        kwargs['test'] = self._test
        args = (self._name_sender, self._accno_sender)
        retval = self.batchclass(*args, **kwargs)
        self.batches.append(retval)
        return retval

    @property
    def order(self):
        '''Produce an order to go with the file'''
        total_accountnos = 0
        total_amount = 0
        nr_posts = 0
        for batch in self.batches:
            total_amount += batch.total_amount
            nr_posts += batch.nr_posts
        retval = self.orderclass()
        retval.identification = self._identification
        retval.accountno_sender = self._accno_sender
        retval.preferred_execution_date = self._execution_date
        retval.testcode = self._test and 'T' or 'P'
        retval.total_amount = total_amount
        retval.nr_posts = nr_posts
        retval.total_accountnos = total_accountnos
        return retval

class DirectDebitFile(ClieOpFile):
    '''Direct Debit Payments file'''
    transactiongroup = '10'
    batchclass = DirectDebitBatch
    orderclass = DirectDebitOrder

class PaymentsFile(ClieOpFile):
    '''Payments file'''
    transactiongroup = '00'
    batchclass = PaymentsBatch
    orderclass = PaymentOrder

class SalaryPaymentsFile(PaymentsFile):
    '''Salary Payments file'''
    batchclass = SalaryBatch
    orderclass = SalaryPaymentOrder

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

