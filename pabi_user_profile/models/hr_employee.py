# -*- coding: utf-8 -*-
from openerp import fields, models, api


class ResourceResource(models.Model):
    _inherit = 'resource.resource'

    name = fields.Char(
        required=False,
    )

class HREmployee(models.Model):
    _inherit = 'hr.employee'

    name = fields.Char(
        compute='_compute_name',
        store=False,  # Do not store as it will be difficult to manage
    )
    title_id = fields.Many2one(
        'res.partner.title',
        string='Title',
    )
    first_name = fields.Char(
        string='First Name',
        translate=True,
        size=500,
    )
    mid_name = fields.Char(
        string='Middle Name',
        translate=True,
        size=500,
    )
    last_name = fields.Char(
        string='Last Name',
        translate=True,
        size=500,
    )
    employee_code = fields.Char(
        string='Employee ID.',
        size=100,
    )
    section_id = fields.Many2one(
        'res.section',
        string='Section',
    )
    section_assign_ids = fields.Many2many(
        'res.section',
        'section_employee_rel',
        'employee_id', 'section_id',
        string='Section Assignment',
    )
    org_id = fields.Many2one(
        'res.org',
        related='section_id.org_id',
        string='Org',
        readonly=True,
        store=True,
    )
    org_ids = fields.Many2many(
        'res.org',
        'org_employee_rel',
        'employee_id', 'org_id',
        string='Additional Orgs',
        help="More Orgs that this employee have access to",
    )
    costcenter_id = fields.Many2one(
        'res.costcenter',
        related='section_id.costcenter_id',
        string='Cost Center',
        store=True,
    )
    position_id = fields.Many2one(
        'hr.position',
        string='Position',
    )
    position_management_id = fields.Many2one(
        'hr.position',
        string='Management Position',
    )
    is_management = fields.Boolean(
        string='Is Management',
    )
    status_id = fields.Many2one(
        'hr.status',
        string='Status',
    )
    #add by Karndarrat.ngm 20190301
    report_admin = fields.Boolean(
        string='Report Admin'
        ,default=False,store=True)
    section_rpt_ids = fields.Many2many(
        'res.section',
        'hr_section_rpt_rel',
        'employee_id',
        'section_id',
        string='Section')
    
    report_project = fields.Boolean(
        string='All Project'
        ,default=False,store=True)
    report_section = fields.Boolean(
        string='All Section'
        ,default=False,store=True)
    report_construction = fields.Boolean(
        string='All Investment construction'
        ,default=False,store=True)
    report_invest_asset = fields.Boolean(
        string='All Investment asset'
        ,default=False,store=True)
    report_project_ids = fields.Many2many(
        'res.org',
        'report_project_org_employee_rel',
        'employee_id', 'org_id',
        string='Project')
    report_section_ids = fields.Many2many(
        'res.org',
        'report_section_org_employee_rel',
        'employee_id', 'org_id',
        string='Section')
    report_construction_ids = fields.Many2many(
        'res.org',
        'report_construction_org_employee_rel',
        'employee_id', 'org_id',
        string='Investment Construction')
    report_invest_asset_ids = fields.Many2many(
        'res.org',
        'report_invest_asset_org_employee_rel',
        'employee_id', 'org_id',
        string='Investment Asset')
    @api.multi
    @api.depends('employee_code', 'title_id',
                 'first_name', 'mid_name', 'last_name',)
    def _compute_name(self):
        for rec in self:
            code = rec.employee_code and ('[%s] ' % rec.employee_code) or ''
            title = rec.title_id and ('%s ' % rec.title_id.name) or ''
            first_name = rec.first_name and ('%s ' % rec.first_name) or ''
            mid_name = rec.mid_name and ('%s ' % rec.mid_name) or ''
            last_name = rec.last_name and ('%s ' % rec.last_name) or ''
            rec.name = ("%s%s%s%s%s" % (code, title, first_name,
                                        mid_name, last_name)).strip()

    @api.multi
    def write(self, vals):
        res = super(HREmployee, self).write(vals)
        if 'org_ids' in vals or 'section_id' in vals:
            for employee in self:
                employee.user_id.write({})  # Write to clear cache
        if 'user_id' in vals:
            self.mapped('user_id')._compute_operating_unit()
        return res

    # Kitti U. Remove this otherwise, can't update Related user on Employee
    # @Poon, will you have any other problem?
    #     user_id = fields.Many2one(
    #         'res.users',
    #         related='resource_id.user_id',
    #         string='User',
    #         store=True,
    #     )
