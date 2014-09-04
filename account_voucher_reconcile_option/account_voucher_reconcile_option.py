from openerp.osv import fields, osv


class account_reconcile(osv.osv):
   _name = 'account.voucher'
   _inherit = ['account.voucher',]

   _columns = {
       'reconcile1': fields.boolean('Full Reconcile'),
   }

   def onchange_reconcile(self, cr, uid, ids,reconcile1,line_cr_ids, line_dr_ids, amount, payment_rate, partner_id, journal_id, currency_id,type, date, payment_rate_currency_id, company_id,context):
        print "On change for Function",amount
        vals = {}
        cr_list = []
        dr_list = []
        amount_val=0.0

        if reconcile1:
            reconcile = True
        else:
            reconcile = False

        if line_cr_ids:
            for line in line_cr_ids:
                 if line[2]:
                     if reconcile ==False:
					       line[2].update({'reconcile': reconcile,'amount': amount_val})
					       cr_list.append(line[2])
                     else:
                           line[2].update({'reconcile':reconcile})
                           cr_data = self.pool.get('account.voucher').onchange_amount( cr, uid, ids,amount, payment_rate, partner_id, journal_id, currency_id,type, date, payment_rate_currency_id, company_id,context)
                           cr_data.update({'reconcile':reconcile})
                           return (cr_data)
        if line_dr_ids:
            for line in line_dr_ids:
                    if reconcile==False:
                        if line[2]:
					       line[2].update({'reconcile': reconcile,'amount': amount_val})
					       dr_list.append(line[2])
                    else:
                        line[2].update({'reconcile':reconcile})
                        dr_data = self.pool.get('account.voucher').onchange_amount( cr, uid, ids,amount, payment_rate, partner_id, journal_id, currency_id,type, date, payment_rate_currency_id, company_id,context)
                        dr_data.update({'reconcile':reconcile})
                        return (dr_data)

        vals.update({'line_cr_ids': cr_list, 'line_dr_ids': dr_list})
        return {'value': vals}

   _defaults = {
       'reconcile1': True,
   }

account_reconcile()

