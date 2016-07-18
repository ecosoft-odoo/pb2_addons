# -*- coding: utf-8 -*-

from openerp import models, fields
import time


class account_voucher(models.Model):

    _inherit = 'account.voucher'

    # Customer Payment
    date_cheque = fields.Date(
        string='Cheque Date',
        default=lambda *a: time.strftime('%Y-%m-%d'),
    )
    number_cheque = fields.Char(
        string='Cheque No.',
        size=64,
    )
    bank_cheque = fields.Char(
        string='Bank',
        size=64,
    )
    branch_cheque = fields.Char(
        string='Bank Branch',
        size=64,
    )
    # Supplier Payment
    date_value = fields.Date(
        string='Value Date',  # bank transfer date
        readonly=True,
        states={'draft': [('readonly', False)]},
        required=True,
    )

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
