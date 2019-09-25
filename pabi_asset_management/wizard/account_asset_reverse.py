# -*- coding: utf-8 -*-
from openerp import fields, models, api, _
from openerp.exceptions import ValidationError


class AccountAssetReverse(models.TransientModel):
    """For asset that wrongly received, this will simply reverse it
    (set removed with status = reversed, and set inactive)
    """
    _name = 'account.asset.reverse'

    target_status = fields.Many2one(
        'account.asset.status',
        string='Target Status',
        domain="[('map_state_removed', '=', 'removed')]",
        default=lambda self:
        self.env.ref('pabi_asset_management.asset_status_reverse', False),
        required=True,
        readonly=True,
    )
    note = fields.Text(
        string='Notes',
        size=1000,
    )
    void_date_remove = fields.Date(
        string='Asset Removal Date',
        default=fields.Date.today,
        required=True,
        copy=False,
    )
    void_account_residual_value_id = fields.Many2one(
        comodel_name='account.account',
        string='Residual Value Account',
        domain=[('type', '=', 'other')],
        required=True,
        default=lambda self: self.env['account.account'].search([('code','=','1214010002')])
    )
    void_posting_regime = fields.Selection(
        [('residual_value', _('Residual Value')),
         ('gain_loss_on_sale', _('Gain/Loss on Sale')),],
        string='Removal Entry Policy',
        required=True,
        default='residual_value',
        #default=lambda self: self._get_posting_regime(),
    )

    @api.multi
    def reverse(self):
        """ Reverse JE of the asset receipt, and set as removed """
        asset_ids = self._context.get('active_ids')
        Asset = self.env['account.asset']
        AccountMove = self.env['account.move']
        MoveLine = self.env['account.move.line']
        Purchase = self.env['purchase.order']
        for asset in Asset.browse(asset_ids):
            # All invoice related to this PO, must be cancelled state
            purchase = Purchase.search([('name', '=',
                                         asset.picking_id.group_id.name)])
            if purchase.invoice_ids.filtered(lambda l: l.state != 'cancel'):
                raise ValidationError(
                    _('This action is not allowed for this asset %s.\n'
                      'All invoices of %s must be cancelled to remove asset') %
                    (asset.display_name, purchase.name))
            if asset.state == 'removed':
                raise ValidationError(
                    _('Asset %s already been removed!') % (asset.code, ))
            move_lines = MoveLine.search([('asset_id', '=', asset.id)])
            move = move_lines.mapped('move_id')
            # Only asset with create asset JE can be reverse
            if len(move) != 1 or asset.value_depreciated > 0.0:
                raise ValidationError(
                    _('Wrong asset %s !\n'
                      'Only recently received asset can be reversed.\n'
                      'For asset with depreciation, use asset removal.') %
                    (asset.code, ))
            # Reverse entry
            move_dict = move.copy_data({})[0]
            move_dict['ref'] = _(u'%s / %s') % (asset.code,self.note)
            move_dict['journal_id'] = 417   #change Asset Journal => Asset Journal (No-Budget)
            for line in move_dict.get('line_id', []):
                line[2]['asset_profile_id'] = False
            move_dict = AccountMove._switch_move_dict_dr_cr(move_dict)
            ctx = {'allow_asset': True}
            rev_move = AccountMove.with_context(ctx).create(move_dict)
            AccountMove._reconcile_voided_entry([move.id, rev_move.id])
            rev_move.button_validate()
            # Set asset removed
            res = asset.open_entries()
            move_id = self.env['account.move'].search(res['domain'])
            for move in move_id:
                move.date = self.void_date_remove
                asset.date_remove = self.void_date_remove
                asset.note = self.note
                move.line_id._check_asset_move_line()
            asset.write({'status': self.target_status.id,
                         'state': 'removed'})
            asset.message_post(body=_('-- Void/Removed --\n%s') % self.note)
        return True