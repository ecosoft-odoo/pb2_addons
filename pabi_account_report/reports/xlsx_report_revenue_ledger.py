# -*- coding: utf-8 -*-
from openerp import models, fields, api


class XLSXReportRevenueLedger(models.TransientModel):
    _name = 'xlsx.report.revenue.ledger'
    _inherit = 'report.account.common'

    account_ids = fields.Many2many(
        'account.account',
        string='Accounts',
    )
    line_filter = fields.Text(
        string='Filter',
        help="More filter. You can use complex search with comma and between.",
    )
    chartfield_ids = fields.Many2many(
        'chartfield.view',
        string='Budget',
        domain=[('model', '!=', 'res.personnel.costcenter')],
    )
    partner_ids = fields.Many2many(
        'res.partner',
        string='Customers',
    )
    count_chartfield = fields.Integer(
        compute='_compute_count_chartfield',
        string='Budget Count',
    )
    charge_type = fields.Selection(
        [('internal', 'Internal'),
         ('external', 'External')],
        string='Charge Type',
    )
    results = fields.Many2many(
        'pabi.common.account.report.view',
        string='Results',
        compute='_compute_results',
        help='Use compute fields, so there is nothing store in database',
    )

    @api.multi
    @api.depends('chartfield_ids')
    def _compute_count_chartfield(self):
        for rec in self:
            rec.count_chartfield = len(rec.chartfield_ids)

    @api.multi
    def _compute_results(self):
        """
        Solution
        1. Get from pabi.common.account.report.view
        2. Check account type is revenue
        """
        self.ensure_one()
        Result = self.env['pabi.common.account.report.view']
        dom = [('account_id.user_type.code', '=', 'Revenue')]
        if self.account_ids:
            dom += [('account_id', 'in', self.account_ids.ids)]
        if self.chartfield_ids:
            ChartfieldView = self.env['chartfield.view']
            chartfields = ChartfieldView.browse(self.chartfield_ids.ids)
            budgets = ['%s,%s' % (x.model, x.res_id) for x in chartfields]
            dom += [('budget', 'in', budgets)]
        if self.partner_ids:
            dom += [('partner_id', 'in', self.partner_ids.ids)]
        if self.charge_type:
            dom += [('charge_type', '=', self.charge_type)]
        if self.fiscalyear_start_id:
            dom += [('invoice_posting_date',
                    '>=', self.fiscalyear_start_id.date_start)]
        if self.fiscalyear_end_id:
            dom += [('invoice_posting_date',
                    '<=', self.fiscalyear_end_id.date_stop)]
        if self.period_start_id:
            dom += [('invoice_posting_date', '>=',
                     self.period_start_id.date_start)]
        if self.period_end_id:
            dom += [('invoice_posting_date', '<=',
                     self.period_end_id.date_stop)]
        if self.date_start:
            dom += [('invoice_posting_date', '>=', self.date_start)]
        if self.date_end:
            dom += [('invoice_posting_date', '<=', self.date_end)]
        self.results = Result.search(dom).sorted(
                       key=lambda l: (l.charge_type,
                                      l.account_id.code,
                                      l.activity_group_id.code,
                                      l.activity_id.code,
                                      l.period_id.fiscalyear_id.name,
                                      l.period_id.name))

    @api.onchange('line_filter')
    def _onchange_line_filter(self):
        self.chartfield_ids = []
        Chartfield = self.env['chartfield.view']
        dom = []
        if self.line_filter:
            codes = self.line_filter.split('\n')
            codes = [x.strip() for x in codes]
            codes = ','.join(codes)
            dom.append(('code', 'ilike', codes))
            self.chartfield_ids = Chartfield.search(dom, order='id')
