# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError


class AccountVoucher(models.Model):
    _inherit = 'account.voucher'

    @api.multi
    def proforma_voucher(self):
        result = super(AccountVoucher, self).proforma_voucher()
        #for voucher in self:
            #raise ValidationError(_('--- %s ---') % str(voucher.line_cr_ids[0].move_line_id.move_id.document_id.source_document_id.name))
        print '--------------Test POS Validate Payments-----------------'
        for voucher in self:
            if voucher.line_ids and \
                voucher.line_ids[0].move_line_id and \
                voucher.line_ids[0].move_line_id.move_id.document and \
                'DV' in voucher.line_ids[0].move_line_id.move_id.document and \
                voucher.line_ids[0].move_line_id.move_id.document_id and \
                voucher.line_ids[0].move_line_id.move_id.document_id.source_document_id and \
                'POS' in voucher.line_ids[0].move_line_id.move_id.document_id.source_document_id.name:
                picking = self.env['stock.picking'].search([('origin','=',voucher.line_ids[0].move_line_id.move_id.document_id.source_document_id.name)])
                for pick in picking:
                    pick.validate_picking()
        return result

