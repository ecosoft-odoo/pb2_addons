# -*- coding: utf-8 -*-
from openerp import models, fields, api, tools
from openerp.exceptions import ValidationError
from datetime import datetime 


class RPTBudgetActual(models.TransientModel):
    _name = 'rpt.budget.actual'
    _inherit = 'report.budget.common.multi'
    
    
    purchase_id = fields.Many2one(
        'purchase.order',
        string='Purchase Order',
    )
    results = fields.Many2many(
        'rpt.budget.actual.line',
        string='Results',
        compute='_compute_results',
    )
    
    
    
    @api.multi
    def _compute_results(self):
        self.ensure_one()
        dom = []
        section_ids = []
        project_ids = []
        invest_construction_phase_ids = []
        invest_asset_ids = []
        
        Result = self.env['rpt.budget.actual.line']
        
        """if self.chartfield_ids:
            chartfield = self.chartfield_ids
            
            section_ids = self._get_chartfield_ids(chartfield, 'sc:')
            project_ids = self._get_chartfield_ids(chartfield, 'pj:')
            invest_construction_phase_ids = self._get_chartfield_ids(chartfield, 'cp:')
            invest_asset_ids = self._get_chartfield_ids(chartfield, 'ia:')
          
        if self.report_type != 'all':
            dom += [('budget_view', '=', self.report_type)]
        if self.date_report:
            dom += [('order_date', '=', str((datetime.strptime(str(self.date_report), '%Y-%m-%d')).strftime("%d/%m/%Y")))]
        if self.fiscalyear_id:
            dom += [('fiscalyear_id', '=', self.fiscalyear_id.id)]
        if self.org_id:
            dom += [('operating_unit_id.org_id', '=', self.org_id.id)]
        if self.sector_id:
            dom += [('sector_code', '=', self.sector_id.code)]
        if self.subsector_id:
            dom += [('subsector_code', '=', self.subsector_id.code)]
        if self.division_id:
            dom += [('division_code', '=', self.division_id.code)]
        if self.section_id:
            section_ids.append(self.section_id.id)
        if self.section_program_id:
            dom += [('section_program_id', '=', self.section_program_id.id)]
        if self.invest_asset_id:
            invest_asset_ids.append(self.invest_asset_id.id)
        if self.activity_group_id:
            dom += [('activity_group_id', '=', self.activity_group_id.id)]
        if self.activity_id:
            dom += [('activity_rpt_id', '=', self.activity_id.id)]
        if self.functional_area_id:
            dom += [('functional_area_id', '=', self.functional_area_id.id)]
        if self.program_group_id:
            dom += [('program_group_id', '=', self.program_group_id.id)]
        if self.program_id:
            dom += [('program_id', '=', self.program_id.id)]
        if self.project_group_id:
            dom += [('project_group_id', '=', self.project_group_id.id)]
        if self.project_id:
            project_ids.append(self.project_id.id)
        if self.invest_construction_id:
            dom += [('invest_construction_id', '=', self.invest_construction_id.id)]
        if self.purchase_id:
            dom += [('purchase_id', '=', self.purchase_id.id)]
            
        if len(section_ids) > 0:
            dom += [('section_id', 'in', section_ids)]
        if len(project_ids) > 0:
            dom += [('project_id', 'in', project_ids)]
        if len(invest_construction_phase_ids) > 0:
            dom += [('invest_construction_phase_id', 'in', invest_construction_phase_ids)]
        if len(invest_asset_ids) > 0:
            dom += [('invest_asset_id', 'in', invest_asset_ids)]
        """
        self.results = Result.search(dom, limit=5)
        print '\n Actual Results: '+str(self.results)
    
    
    @api.multi
    def run_jasper_report(self, data):
        self.ensure_one()
        
        data = {}
        data['parameters'] = {}
        #data['parameters']['ids'] = self.id
        ids = []
        for rec in self.results:
            ids.append(rec.id)
        data['parameters']['ids'] = ids
        data['parameters']['report_type'] = ''
        data['parameters']['fiscal_year'] = self.fiscalyear_id.name or ''
        data['parameters']['org'] = self.org_id and self.org_id.operating_unit_id.name or ''
        data['parameters']['po_document'] = self.purchase_id and self.purchase_id.name or ''
        data['parameters']['order_date'] = ''
        data['parameters']['budget_overview'] = self.chart_view or ''
        data['parameters']['budget_method'] = self.budget_method or ''
        data['parameters']['run_by'] = self.create_uid.partner_id.name or ''
        data['parameters']['run_date'] = str((datetime.strptime(str(self.create_date), '%Y-%m-%d %H:%M:%S')).strftime("%d/%m/%Y"))
        
        report_ids = 'pabi_budget_report.rpt_budget_actual_jasper_report'
        
        return super(RPTBudgetActual, self).run_jasper_report(data, report_ids)
    
        
       
class RPTBudgetActualLine(models.Model):
    _name = 'rpt.budget.actual.line'
    _auto = False
    
    id = fields.Integer('doc date')
    doc_date = fields.Char('doc date')
    posting_date = fields.Char('posting date')
    document = fields.Char('document')
    amvl_item = fields.Integer('amvl item')
    amount = fields.Float('amount')
    detail = fields.Char('detail')
    ref_document = fields.Char('ref document')
    document_ref = fields.Char('document ref')
    #ref_document = fields.Char('ref document')
    schedule_date = fields.Char('schedule date')
    po_contract = fields.Char('po contract')
    contract_start_date = fields.Char('contract start date')
    contract_end_date = fields.Char('contract end date')
    product_category = fields.Char('product category')
    product_code = fields.Char('product code')
    product_name = fields.Char('product name')
    purchasing_method = fields.Char('purchasing method')
    activity_group = fields.Char('activity group')
    activity_group_name = fields.Char('activity group name')
    activity = fields.Char('activity')
    activity_name = fields.Char('activity name')
    activity_rpt = fields.Char('activity rpt')
    activity_rpt_name = fields.Char('activity rpt name')
    account_code = fields.Char('account code')
    account_name = fields.Char('account name')
    partner_code = fields.Char('partner code')
    partner_name = fields.Char('partner name')
    org_code = fields.Char('org code')
    org_name = fields.Char('org name')
    section = fields.Char('section')
    section_name = fields.Char('section name')
    costcenter = fields.Char('costcenter')
    costcenter_name = fields.Char('costcenter name')
    costcenter_used = fields.Char('costcenter used')
    costcenter_name_used = fields.Char('costcenter name used')
    mission = fields.Char('mission')
    functional_area = fields.Char('functional area')
    functional_area_name = fields.Char('functional area name')
    program_group = fields.Char('program group')
    program_group_name = fields.Char('program group name')
    program = fields.Char('program')
    program_name = fields.Char('program name')
    project_group = fields.Char('project group')
    propect_group_name = fields.Char('propect group name')
    master_plan_code = fields.Char('master plan code')
    master_plan_name = fields.Char('master plan name')
    project_type = fields.Char('project type')
    project_type_name = fields.Char('project type name')
    project_operation_code = fields.Char('project operation code')
    project_operation_name = fields.Char('project operation name')
    project_fund_code = fields.Char('project fund code')
    project_fund_name = fields.Char('project fund name')
    project_date_start = fields.Char('project date start')
    project_date_end = fields.Char('project date end')
    project_date_start_spending = fields.Char('project date start spending')
    project_date_end_spending = fields.Char('project date end spending')
    project_date_close = fields.Char('project date close')
    project_date_close_cond = fields.Char('project date close cond')
    pm = fields.Char('pm')
    pm_name = fields.Char('pm name')
    project_status = fields.Char('project status')
    sector = fields.Char('sector')
    sector_name = fields.Char('sector name')
    sub_sector = fields.Char('sub sector')
    sub_sector_name = fields.Char('sub sector name')
    division = fields.Char('division')
    division_name = fields.Char('division name')
    section_program = fields.Char('section program')
    section_program_name = fields.Char('section program name')
    project_c_code = fields.Char('project c code')
    project_c_name = fields.Char('project c name')
    project_c_date_start = fields.Char('project c date start')
    project_c_date_end = fields.Char('project c date end')
    project_c_date_expansion = fields.Char('project c date expansion')
    request_by = fields.Char('request by')
    request_by_name = fields.Char('request by name')
    approver = fields.Char('approver')
    approver_name = fields.Char('approver name')
    prepared_by = fields.Char('prepared by')
    prepared_by_name = fields.Char('prepared by name')
    fisyear = fields.Char('fisyear')
    period = fields.Char('period')
    budget_commit_type = fields.Char('budget commit type')
    charge_type = fields.Char('charge type')
    budget_method = fields.Char('budget method')
    doctype = fields.Char('doctype')
    budget_view = fields.Char('budget view')
    source_budget_code = fields.Char('source budget code')
    source_budget_name = fields.Char('source budget name')
    item = fields.Integer('item')
    

    def _get_sql_view(self):
        sql_view = """
    SELECT 
        ROW_NUMBER() over (order by document,fisyear) AS id,
        doc_date,
        posting_date,
        document,
        amvl_item,
        amount,
        detail,
        ref_document,
        document_ref,
        schedule_date,
        po_contract,
        contract_start_date,
        contract_end_date,
        product_category,
        product_code,
        product_name,
        purchasing_method,
        activity_group,
        activity_group_name,
        activity,
        activity_name,
        activity_rpt,
        activity_rpt_name,
        account_code,
        account_name,
        partner_code,
        partner_name,
        org_code,
        org_name,
        section,
        section_name,
        costcenter,
        costcenter_name,
        costcenter_used,
        costcenter_name_used,
        mission,
        functional_area,
        functional_area_name,
        program_group,
        program_group_name,
        program,
        program_name,
        project_group,
        propect_group_name,
        master_plan_code,
        master_plan_name,
        project_type,
        project_type_name,
        project_operation_code,
        project_operation_name,
        project_fund_code,
        project_fund_name,
        project_date_start,
        project_date_end,
        project_date_start_spending,
        project_date_end_spending,
        project_date_close,
        project_date_close_cond,
        pm,
        pm_name,
        project_status,
        sector,
        sector_name,
        sub_sector,
        sub_sector_name,
        division,
        division_name,
        section_program,
        section_program_name,
        project_c_code,
        project_c_name,
        project_c_date_start,
        project_c_date_end,
        project_c_date_expansion,
        request_by,
        request_by_name,
        approver,
        approver_name,
        prepared_by,
        prepared_by_name,
        fisyear,
        period,
        budget_commit_type,
        charge_type,
        budget_method,
        doctype,
        budget_view,
        source_budget_code,
        source_budget_name,
        item
    FROM issi_budget_summary_actual_view
        """
        return sql_view

    def init(self, cr):
        tools.drop_view_if_exists(cr, self._table)
        cr.execute("""CREATE OR REPLACE VIEW %s AS (%s)"""
                   % (self._table, self._get_sql_view()))
        
 
