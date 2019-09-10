# -*- coding: utf-8 -*-
import time
from openerp import fields, models, api
from openerp.tools.float_utils import float_compare
import logging

_logger = logging.getLogger(__name__)


class ProjectBalanceCarryForward(models.Model):
    _name = 'project.balance.carry.forward'

    name = fields.Char(
        string='Name',
        readonly=True,
        size=500,
    )
    from_fiscalyear_id = fields.Many2one(
        'account.fiscalyear',
        string='From Fiscal Year',
        readonly=True,
        required=True,
        states={'draft': [('readonly', False)]},
    )
    to_fiscalyear_id = fields.Many2one(
        'account.fiscalyear',
        string='To Fiscal Year',
        readonly=True,
        required=True,
        states={'draft': [('readonly', False)]},
    )
    line_ids = fields.One2many(
        'project.balance.carry.forward.line',
        'carry_forward_id',
        string='Carry Forward Lines',
        readonly=True,
        copy=False,
        states={'draft': [('readonly', False)]},
    )
    state = fields.Selection(
        [('draft', 'Draft'),
         ('done', 'Done')],
        string='Status',
        default='draft',
        readonly=True,
    )
    amount_total = fields.Float(
        string='Total Amount',
        compute='_compute_amount_total',
    )

    @api.multi
    def _compute_amount_total(self):
        for rec in self:
            rec.amount_total = sum(rec.line_ids.mapped('balance_amount'))

    @api.model
    def default_get(self, fields):
        res = super(ProjectBalanceCarryForward, self).default_get(fields)
        Fiscal = self.env['account.fiscalyear']
        if not res.get('fiscalyear_id', False):
            fiscals = Fiscal.search([
                ('date_start', '>', time.strftime('%Y-%m-%d'))],
                order='date_start')
            if fiscals:
                res['from_fiscalyear_id'] = Fiscal.find()
                res['to_fiscalyear_id'] = fiscals[0].id
        return res

    @api.multi
    def write(self, vals):
        res = super(ProjectBalanceCarryForward, self).write(vals)
        if 'from_fiscalyear_id' in vals:
            self.compute_projects()
        return res

    @api.model
    def create(self, vals):
        res = super(ProjectBalanceCarryForward, self).create(vals)
        res.name = '{:03d}'.format(res.id)
        res.compute_projects()
        return res

    @api.multi
    def compute_projects(self):
        self.ensure_one()
        self.line_ids.unlink()
        """ This method, list all projects with, budget balance > 0 """
        where_ext = ''
        if self.from_fiscalyear_id.control_ext_charge_only:
            where_ext = "and charge_type = 'external'"
        sql = """
            select a.project_id, a.program_id, a.balance_amount
            from (
                select project_id, program_id,
                sum(released_amount - amount_actual) balance_amount
                from budget_monitor_report
                where budget_method = 'expense'
                and project_id is not null
                and fiscalyear_id = %s
                %s
                and (coalesce(released_amount, 0.0) != 0.0
                     or coalesce(amount_actual, 0.0) != 0.0)
                group by project_id,  program_id
            ) a
                inner join res_project prj
                    on prj.id = a.project_id
                    and prj.state = 'approve'
            where a.balance_amount > 0.0
        """ % (self.from_fiscalyear_id.id, where_ext)
        self._cr.execute(sql)
        projects = [(0, 0, project) for project in self._cr.dictfetchall()]
        self.write({'line_ids': projects})

    @api.multi
    def action_carry_forward(self):
        """ For each project, inject the balance amount to the released amount
        in related account.budget.line """
        BudgetLine = self.env['account.budget.line']
        for rec in self:
            fiscalyear = rec.to_fiscalyear_id
            for line in rec.line_ids:
                _logger.info("fiscalyear: %s", str(fiscalyear.id))
                _logger.info("project_id: %s", str(line.project_id.id))
                budget_lines = BudgetLine.search(
                    [('fiscalyear_id', '=', fiscalyear.id),
                     ('project_id', '=', line.project_id.id),
                     ('charge_type', '=', 'external'),
                     ('budget_method', '=', 'expense')])
                _logger.info("budget_lines: %s", str(budget_lines))
                if len(budget_lines) == 1:
                    budget_lines.released_amount = line.balance_amount
                    _logger.info("balance_amount: %s", str(line.balance_amount))
                    line.write({'state': 'success'})
                elif not budget_lines:
                    line.write({'reason': '1',
                                'state': 'fail'})
                elif len(budget_lines) > 1:
                    line.write({'reason': '2',
                                'state': 'fail'})
                _logger.info("state: %s", str(line.state))
                
        # update project released amount
        fiscalyear = self.to_fiscalyear_id
        for line in self.line_ids:
            project = line.project_id
            self.update_project_released_amount(project, fiscalyear, line.balance_amount)

        self.write({'state': 'done'})

    def update_project_released_amount(self, project, fiscalyear, balance_amount):
        budget_plans = project.budget_plan_ids.filtered(lambda l: l.fiscalyear_id == fiscalyear 
                                                        and l.budget_method=='expense' 
                                                        and l.charge_type=='external')
        if not budget_plans:
            raise ValidationError(
                _('Not allow to release budget for project without plan!'))
             
        update_vals = []
        for budget_plan in budget_plans:
            if float_compare(balance_amount, budget_plan.planned_amount, 2) == 1:
                update = {'released_amount': budget_plan.planned_amount}
                balance_amount -= budget_plan.planned_amount
                update_vals.append((1, budget_plan.id, update))
            else:
                update = {'released_amount': balance_amount}
                balance_amount = 0.0
                update_vals.append((1, budget_plan.id, update))
                break
        if update_vals:
            project.write({'budget_plan_ids': update_vals})

        return True





























class ProjectBalanceCarryForwardLine(models.Model):
    _name = 'project.balance.carry.forward.line'
    _order = 'program_id'

    carry_forward_id = fields.Many2one(
        'project.balance.carry.forward',
        string='Carry Over',
        index=True,
        ondelete='cascade',
    )
    program_id = fields.Many2one(
        'res.program',
        string='Program',
    )
    project_id = fields.Many2one(
        'res.project',
        string='Project',
    )
    balance_amount = fields.Float(
        string='Amount to Carry Forward',
    )
    state = fields.Selection(
        [('draft', 'Draft'),
         ('success', 'Successful'),
         ('fail', 'Failed')],
        string='Status',
        readonly=True,
        default='draft',
        help="Whether the amount has been carried as released amount "
        "in target fiscal year release",
    )
    reason = fields.Selection(
        [('1', 'No project in budget line on target fiscalyear'),
         ('2', '> 1 budget line for the same project on target fiscalyear')],
        string='Reason',
        readonly=True,
        help="Reason for failed carry forward",
    )
