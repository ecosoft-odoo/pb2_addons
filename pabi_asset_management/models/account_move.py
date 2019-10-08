# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    ref = fields.Char(index=True)
    narration = fields.Text(index=True)

    @api.model
    def create(self, vals):
        # Case stock picking with force journal_id
        if self._context.get('overwrite_journal_id', False):
            vals['journal_id'] = self._context['overwrite_journal_id']
        elif self._context.get('active_model', False) == 'stock.picking':
            if 'journal_id' in vals:
                picking_id = self._context.get('active_id', False)
                picking = self.env['stock.picking'].browse(picking_id)
                if picking.asset_journal_id:  # If asset, use asset journal
                    vals['journal_id'] = picking.asset_journal_id.id
        # Move name to '/'
        if self._context.get('overwrite_move_name', False):
            vals['name'] = '/'
        results = super(AccountMove, self).create(vals)
        if 'STJ' in results.name:
            for line in results.line_id:
                line._get_detail_move_line()
        
        return results


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    asset_id = fields.Many2one(
        'account.asset',
        index=True,  # Add index
    )
    stock_move_id = fields.Many2one(
        'stock.move',
        string='Stock Move',
        readonly=True,
        help="When account is created by a stock move (anglo saxon).",
    )
    parent_asset_id = fields.Many2one(
        'account.asset',
        string='Parent Asset',
        readonly=True,
        help="If in purchase order line, parent asset is specified.",
    )
    
    @api.model
    def _prepare_asset_vals(self, move_line):
        sequence = move_line.product_id.sequence_id
        if not sequence:
            raise ValidationError(_('No asset sequence setup!'))
        code = self.env['ir.sequence'].next_by_id(sequence.id)
        vals = {
            'product_id': move_line.product_id.id,
            'move_id': move_line.stock_move_id.id,
            'asset_purchase_method_id':
            # Case direct receive, chosen by user in stock.picking
            move_line.stock_move_id.picking_id.asset_purchase_method_id.id or
            # Case Asset Transfer, inherit from source asset
            self._context.get('asset_purchase_method_id', False) or
            # Normal case, start from PR, link back to original document
            move_line.stock_move_id.purchase_line_id.quo_line_id.
            requisition_line_id.requisition_id.purchase_method_id.
            asset_purchase_method_id.id,
            'parent_id': move_line.parent_asset_id.id,
            'code': code,
            # Budget Source, from 4 structure
            'section_id': move_line.section_id.id,
            'project_id': move_line.project_id.id,
            'invest_asset_id': move_line.invest_asset_id.id,
            'invest_construction_phase_id':
            move_line.invest_construction_phase_id.id,
            # Owner
            # - project -> project
            # - section -> section
            # - invest_asset, invest_construction_phase -> section
            'owner_section_id': move_line.section_id.id or
            move_line.invest_construction_id.pm_section_id.id or
            move_line.invest_asset_id.owner_section_id.id,
            'owner_project_id': move_line.project_id.id,
            # Buildings
            'building_id': move_line.stock_move_id.building_id.id,
            'floor_id': move_line.stock_move_id.floor_id.id,
            'room_id': move_line.stock_move_id.room_id.id,
            'responsible_user_id':
            move_line.stock_move_id.responsible_user_id.id,
        }
        # With context data about the installment
        if self._context.get('work_acceptance_id', False):
            installment = self._context.get('installment', False)
            num_installment = self._context.get('num_installment', False)
            vals.update({'installment': installment,
                         'num_installment': num_installment,
                         })
        # --
        if not (vals['section_id'] or vals['project_id'] or
                vals['invest_asset_id'] or
                vals['invest_construction_phase_id']):
            raise ValidationError(
                _('Source of budget is not specified!'))
        if not (vals['owner_section_id'] or vals['owner_project_id']):
            raise ValidationError(
                _('Project/Section owner of asset not specified!'))
        return vals
    
    @api.multi
    def _get_record_chartfield(self, chartfield):
        search = False
        if chartfield:
            chartfield_id = self.env['chartfield.view'].browse(chartfield)
            
            if chartfield_id:
                if chartfield_id.type == 'pj:':
                    search = self.env['res.project'].search([['id','=',chartfield_id.res_id]])
                if chartfield_id.type == 'sc:':
                    search = self.env['res.section'].search([['id','=',chartfield_id.res_id]])
                if chartfield_id.type == 'cp:':
                    search = self.env['res.invest.construction.phase'].search([['id','=',chartfield_id.res_id]])
                if chartfield_id.type == 'pc:':
                    search = self.env['res.personnel.costcenter'].search([['id','=',chartfield_id.res_id]])
                if chartfield_id.type == 'ia:':
                    search = self.env['res.invest.asset'].search([['id','=',chartfield_id.res_id]])
                
        return search
    
    @api.multi
    def _get_detail_asset_move_line(self):
        for rec in self:
            if rec.asset_id and (not rec.taxbranch_id or not rec.chartfield_id):
                move_line_ids = self.env['account.move.line'].search([('asset_id','=',rec.asset_id.id),
                                                                      ('move_id','=',rec.move_id.id),
                                                                      ('taxbranch_id','!=',False),
                                                                      ('id','!=',rec.id)], limit=1)
                if not move_line_ids:
                    chartfield_id = rec.asset_id.owner_section_id \
                                    or rec.asset_id.owner_project_id \
                                    or rec.asset_id.owner_invest_asset_id \
                                    or rec.asset_id.owner_invest_construction_phase_id \
                                    or False
                    if chartfield_id:
                        rec.update({
                                    'costcenter_id': chartfield_id.costcenter_id.id,
                                    'org_id': chartfield_id.org_id.id,
                                    'fund_id': rec.asset_id.fund_id.id,
                                    'taxbranch_id': rec.asset_id.taxbranch_id.id,
                                    'section_id': rec.asset_id.owner_section_id.id,
                                    'project_id': rec.asset_id.owner_project_id.id,
                                    'invest_asset_id': rec.asset_id.owner_invest_asset_id.id,
                                    'invest_construction_phase_id': rec.asset_id.owner_invest_construction_phase_id.id
                        })
                else:
                    rec.update({
                                'costcenter_id': move_line_ids.costcenter_id.id,
                                'chartfield_id': move_line_ids.chartfield_id.id,
                                'org_id': move_line_ids.org_id.id,
                                'fund_id': move_line_ids.fund_id.id,
                                'taxbranch_id': move_line_ids.taxbranch_id.id
                    })
                    
            if rec.asset_id:
                if rec.section_id and rec.asset_id.owner_section_id and rec.section_id != rec.asset_id.owner_section_id:
                    rec.section_id = rec.asset_id.owner_section_id.id
                if rec.project_id and rec.asset_id.owner_project_id and rec.project_id != rec.asset_id.owner_project_id:
                    rec.project_id = rec.asset_id.owner_project_id.id
                if rec.invest_asset_id and rec.asset_id.owner_invest_asset_id and rec.invest_asset_id != rec.asset_id.owner_invest_asset_id:
                    rec.invest_asset_id = rec.asset_id.owner_invest_asset_id.id
                if rec.invest_construction_phase_id and rec.asset_id.owner_invest_construction_phase_id \
                        and rec.invest_construction_phase_id != rec.asset_id.owner_invest_construction_phase_id:
                    rec.invest_construction_phase_id = rec.asset_id.owner_invest_construction_phase_id.id
                    
                if rec.costcenter_id and rec.chartfield_id.costcenter_id.id and rec.costcenter_id != rec.chartfield_id.costcenter_id.id:
                    rec.costcenter_id = rec.chartfield_id.costcenter_id.id
    
    @api.multi
    def _get_detail_move_line(self):
        if self.document_id:
            if not self.chartfield_id:
                search = self.search([['move_id','=',self.move_id.id],
                                      #['costcenter_id','!=',False],
                                      #['org_id','!=',False]
                                      ['id','!=',self.id],
                                      ['chartfield_id','!=',False]],limit=1)
                if search:
                    self.chartfield_id = search.chartfield_id.id
                    self.costcenter_id = search.costcenter_id.id
                    self.org_id = search.org_id.id
                    self.fund_id = search.fund_id.id
                else:
                    search = self.search([['move_id','!=',self.move_id.id],
                                          ['document_id','=',self.document_id.id],
                                          ['product_id','=',self.product_id.id],
                                          #['chartfield_id','!=',False],
                                          ['docline_seq','=',self.docline_seq]],limit=1)
                    if search:
                        self.chartfield_id = search.chartfield_id.id
                        self.costcenter_id = search.costcenter_id.id
                        self.org_id = search.org_id.id
                        self.fund_id = search.fund_id.id
                        
            else:
                search = self.search([['move_id','=',self.move_id.id],['chartfield_id','=',False]])

                for rec in search:
                    rec.write({
                                'costcenter_id':self.costcenter_id.id,
                                'org_id':self.org_id.id,
                                'fund_id':self.fund_id.id,
                                'chartfield_id':self.chartfield_id.id
                        })
        
    @api.multi
    def _get_detail_chartfield(self, chartfield_id):
        chartfield, costcenter, org, fund = False, False, False, False
        
        search = self._get_record_chartfield(chartfield_id)
        if search:
            costcenter = search.costcenter_id.id
            org = search.org_id.id
            fund = search.fund_ids and search.fund_ids[0].id or False
            
        return {
                'chartfield_id':search,
                'costcenter_id':costcenter,
                'org_id':org,
                'fund_id':fund
            }
        
    @api.multi
    def _get_column_chartfield(self, move_id):
        chartfield, costcenter, org, fund = False, False, False, False
        search = self.env['account.move.line'].search([['move_id','=',move_id],
                                                       ['costcenter_id','!=',False],
                                                       ['org_id','!=',False]],limit=1)
        if search:
            chartfield = search.chartfield_id.id
            costcenter = search.costcenter_id.id
            org = search.org_id.id
            fund = search.fund_id.id
        
        return {
                'chartfield_id':chartfield,
                'costcenter_id':costcenter,
                'org_id':org,
                'fund_id':fund
            }
    
    @api.model
    def create(self, vals):
        if vals.get('chartfield_id') and not vals.get('costcenter_id'):# and not vals.get('costcenter_id'):# and not vals.get('org_id'):
            get_chartfield = self._get_detail_chartfield(vals.get('chartfield_id'))
            vals['costcenter_id'] = get_chartfield['costcenter_id']
            vals['org_id'] = get_chartfield['org_id']
            if not vals.get('fund_id'):
                vals['fund_id'] = get_chartfield['fund_id']
            
        move_line = super(AccountMoveLine, self).create(vals)
        if move_line.asset_id and (move_line.asset_id.code or '/') == '/':
            if move_line.asset_profile_id and move_line.asset_id:
                vals = self._prepare_asset_vals(move_line)
                move_line.asset_id.write(vals)
                # Asset must have account_analytic_id, if not exists
                if not move_line.asset_id.account_analytic_id:
                    Analytic = self.env['account.analytic.account']
                    move_line.asset_id.account_analytic_id = \
                        Analytic.create_matched_analytic(move_line.asset_id)
        if move_line.document_id:
            search_picking = self.env['stock.picking'].search([['id','=',move_line.document_id.id],'|',['origin','like','POS'],['origin','like','SR']])
            if search_picking:
                move_line._get_detail_move_line()
        return move_line
    
    
    @api.multi
    def write(self, vals, check=True, update_check=True):
        if vals.get('chartfield_id') and not vals.get('costcenter_id'):
            search = self._get_record_chartfield(vals.get('chartfield_id'))
            if search:
                vals['costcenter_id'] = search.costcenter_id.id
                vals['org_id'] = search.org_id.id
                
        res = super(AccountMoveLine, self).write(vals, check=check, update_check=True)
        return res
