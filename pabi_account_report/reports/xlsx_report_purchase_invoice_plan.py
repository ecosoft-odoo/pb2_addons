# -*- coding: utf-8 -*-
from openerp import models, fields, api


class XLSXReportPurchaseInvoicePlan(models.TransientModel):
    _name = 'xlsx.report.purchase.invoice.plan'
    _inherit = 'report.account.common'

    filter = fields.Selection(
        [('filter_no', 'No Filters'),
         ('filter_period', 'Periods')],
        string='Filter by',
        required=True,
        default='filter_no',
    )
    org_ids = fields.Many2many(
        'res.org',
        string='Org',
    )
    date_po_start = fields.Date(
        string='Start PO Date',
    )
    date_po_end = fields.Date(
        string='End PO Date',
    )
    purchase_ids = fields.Many2many(
        'purchase.order',
        string='Po Number',
    )
    contract_ids = fields.Many2many(
        'purchase.contract',
        string='Po Contract',
    )
    date_contract_action_start = fields.Date(
        string='Start Contract Action Date',
    )
    date_contract_action_end = fields.Date(
        string='End Contract Action Date',
    )
    invoice_plan = fields.Boolean(
        string='Invoice Plan',
        default=True,
    )
    po_not_closed = fields.Boolean(
        string='PO Not Closed',
        default=True,
    )
    no_finlease = fields.Boolean(
        string='No Finlease',
        default=True,
    )
    no_po_draft = fields.Boolean(
        string='No PO Draft',
        default=True,
    )
    filter_description = fields.Char(
        string='Filter',
        compute='_compute_filter_description',
    )
    account_ids = fields.Many2many(
        'account.account',
        string='Account',
    )
    line_filter = fields.Text(
        string='Filter',
        help="More filter. You can use complex search with comma and between.",
    )
    line_po_filter = fields.Text(
        string='Filter',
        help="More filter. You can use complex search with comma and between.",
    )
    line_ct_filter = fields.Text(
        string='Filter',
        help="More filter. You can use complex search with comma and between.",
    )
    line_acc_filter = fields.Text(
        string='Filter',
        help="More filter. You can use complex search with comma and between.",
    )
    chartfield_ids = fields.Many2many(
        'chartfield.view',
        string='Budget',
        domain=[('model', '!=', 'res.personnel.costcenter')],
    )
    results = fields.Many2many(
        'report.purchase.invoice.plan.view',
        string='Results',
        compute='_compute_results',
        help='Use compute fields, so there is nothing store in database',
    )
    
    @api.multi
    @api.depends('invoice_plan', 'po_not_closed', 'no_finlease', 'no_po_draft')
    def _compute_filter_description(self):
        for rec in self:
            filter_description = ''
            if rec.invoice_plan is True:
                filter_description = ' Invoice Plan,'
            if rec.po_not_closed:
                filter_description += ' PO Not Closed,'
            if rec.no_finlease:
                filter_description += ' No Finlease,'
            if rec.no_po_draft:
                filter_description += ' No Po Draft,'
            
            rec.filter_description = filter_description

    @api.onchange('line_filter')
    def _onchange_line_filter(self):
        self.chartfield_ids = []
        Chartfield = self.env['chartfield.view']
        if self.line_filter:
            codes = self.line_filter.split('\n')
            codes = [x.strip() for x in codes]
            #codes = ','.join(codes)
            codes = tuple(codes)
            dom = [('code', 'in', codes)]
            self.chartfield_ids = Chartfield.search(dom, order='id')
            print('\n Onchange Filter Budget: '+str(self.chartfield_ids))


    def get_domain_filter(self, fields, filters):
        dom = []
        n = 0
        codes = filters.replace(' ','').replace('\n',',').replace(',,',',').replace(',\n','').split(',')
        #codes = filters.split(',')
        codes = tuple(codes)
        #if '' in codes:
        #    codes.remove('')
        codes = [x.strip() for x in codes]
        """for rec in codes:
            n += 1
            if rec != '':
                if n != len(codes):
                    dom.append('|')
                dom.append((fields, 'ilike', rec))"""
        dom = [(fields, 'in', codes)]
        return dom

    @api.onchange('line_po_filter')
    def _onchange_line_po_filter(self):
        self.purchase_ids = []
        Purchase = self.env['purchase.order']
        if self.line_po_filter:
            dom = self.get_domain_filter('name', self.line_po_filter)
            self.purchase_ids = Purchase.search(dom, order='id')

    @api.onchange('line_ct_filter')
    def _onchange_line_ct_filter(self):
        self.contract_ids = []
        Contract = self.env['purchase.contract']
        dom = []
        if self.line_ct_filter:
            dom = self.get_domain_filter('poc_code', self.line_ct_filter)
            self.contract_ids = Contract.search(dom, order='id')

    @api.onchange('line_acc_filter')
    def _onchange_line_acc_filter(self):
        self.account_ids = []
        Account = self.env['account.account']
        dom = []
        if self.line_acc_filter:
            dom = self.get_domain_filter('code', self.line_acc_filter)
            self.account_ids = Account.search(dom, order='id')

    @api.model
    def _domain_to_where_str(self, domain):
        """ Helper Function for better performance """
        where_dom = [" %s %s %s " % (x[0], x[1], isinstance(x[2], basestring)
                     and "'%s'" % x[2] or x[2]) for x in domain]

        where_str = 'and'.join(where_dom)
        where_str = where_str.replace(',)', ')')
        return where_str

    @api.multi
    def get_model_chartfield(self):
        section = []
        project = []
        asset = []
        phase = []
        personnel = []

        for chartfield in self.chartfield_ids:
            if chartfield.model == 'res.section':
                section.append(chartfield.res_id)
            elif chartfield.model == 'res.project':
                project.append(chartfield.res_id)
            elif chartfield.model == 'res.invest.asset':
                asset.append(chartfield.res_id)
            elif chartfield.model == 'res.invest.construction.phase':
                phase.append(chartfield.res_id)
            elif chartfield.model == 'res.personnel.costcenter':
                personnel.append(chartfield.res_id)

        return {
                'section': section,
                'project': project,
                'asset': asset,
                'phase': phase,
                'personnel': personnel
            }

    @api.multi
    def get_where_str_chartfield(self):
        chartfield_dom = []
        
        chartfield = self.get_model_chartfield()
        if chartfield['section']:
            chartfield_dom += [('section_id','in',tuple(chartfield['section']))]
        if chartfield['project']:
            chartfield_dom += [('project_id','in',tuple(chartfield['project']))]
        if chartfield['asset']:
            chartfield_dom += [('invest_asset_id','in',tuple(chartfield['asset']))]
        if chartfield['phase']:
            chartfield_dom += [('invest_construction_phase_id','in',tuple(chartfield['phase']))]
        if chartfield['personnel']:
            chartfield_dom += [('personnel_costcenter_id','in',tuple(chartfield['personnel']))]
            
        where_dom = [" %s %s %s " % (x[0], x[1], isinstance(x[2], basestring)
                     and "'%s'" % x[2] or x[2]) for x in chartfield_dom]
        
        where_str = 'or'.join(where_dom)
        where_str = '(%s)' % where_str.replace(',)',')')
        return where_str

    @api.multi
    def _compute_results(self):
        #self.ensure_one()
        plan_ids = []
        chartfield_dom = ''
        where_acc = ''
        InvoicePlan = self.env['purchase.invoice.plan']
        Reports = self.env['report.purchase.invoice.plan.view']
        where_str = ''
        dom = []
        if self.org_ids:
            dom += [('org_id', 'in', tuple(self.org_ids.ids))]
        if self.purchase_ids:
            dom += [('purchase_id', 'in', tuple(self.purchase_ids.ids))]
        if self.contract_ids:
            dom += [('contract_id', 'in', tuple(self.contract_ids.ids))]
        if self.account_ids:
            dom += [('account_id', 'in', tuple(self.account_ids.ids))]

        if self.line_filter and not self.chartfield_ids:
            self.chartfield_ids = []
            Chartfield = self.env['chartfield.view']
            dom2 = []
            if self.line_filter:
                codes = self.line_filter.split('\n')
                codes = [x.strip() for x in codes]
                codes = tuple(codes)
                dom2.append(('code', 'in', codes))
                self.chartfield_ids = Chartfield.search(dom2, order='id')

        if self.chartfield_ids:
            chartfield_dom = self.get_where_str_chartfield()

        print('\n chartfield_dom: '+chartfield_dom)

        if self.date_po_start and not self.date_po_end:
            dom += [('date_order','=',self.date_po_start)]
        if self.date_po_start and self.date_po_end:
            dom += [('date_order','>=',self.date_po_start),('date_order','<=',self.date_po_end)]
        if self.date_start:
            dom += [('date_order','>=',self.date_start)]
        if self.date_end:
            dom += [('date_order','<=',self.date_end)]
        if self.period_start_id:
            dom += [('date_order','>=',self.period_start_id.date_start)]
        if self.period_end_id:
            dom += [('date_order','<=',self.period_end_id.date_stop)]
        if self.date_contract_action_start:
            dom += [('action_date','>=',self.date_contract_action_start)]
        if self.date_contract_action_end:
            dom += [('action_date','<=',self.date_contract_action_end)]
        if self.invoice_plan is True:
            dom += [('use_invoice_plan','=',True)]
        if self.po_not_closed is True:
            dom += [('technical_closed','!=',True)]
        if self.no_finlease is True:
            dom += [('is_fin_lease','!=',True)]
        if self.no_po_draft is True:
            dom += [('po_status','!=','draft')]
        
        if len(dom) > 0:
            where_str = self._domain_to_where_str(dom)
        if where_str != '' and chartfield_dom != '':
            where_str += 'and ' + chartfield_dom
        if where_str == '' and chartfield_dom != '':
            where_str = chartfield_dom
        if where_str != '':
            where_str = 'and %s' % where_str
        print 'where_str: '+where_str

        self._cr.execute("""
            select *,
                CASE 
                    WHEN new.use_invoice_plan = True 
                        THEN (select count(*) from purchase_invoice_plan pip
                            where pip.order_id = new.purchase_id
                                and pip.installment is not null
                            )
                    ELSE (select count(*) from account_invoice av
                            left join purchase_invoice_rel pi_r on pi_r.invoice_id = av.id
                        where pi_r.purchase_id = new.purchase_id and av.state <> 'cancel'
                        )
                END as no_of_installment,
                (CASE
                    WHEN new.use_invoice_plan = True
                        THEN (select sum(pip.invoice_amount) from purchase_invoice_plan pip
                             where pip.order_id = new.purchase_id and pip.state = 'draft'
                                and pip.date_invoice >=
                                    (select fis.date_start from account_fiscalyear fis
                                        where cast(NOW() as Date) between fis.date_start and fis.date_stop)
                                and pip.date_invoice <=
                                    (select fis.date_stop from account_fiscalyear fis
                                        where cast(NOW() as Date) between fis.date_start and fis.date_stop))
                    ELSE
                        (select sum(av.amount_total)
                         from account_invoice av
                            left join purchase_invoice_rel pi_r on pi_r.invoice_id = av.id
                         where pi_r.purchase_id = new.purchase_id and av.state = 'draft'
                            and av.date_invoice >=
                                (select fis.date_start from account_fiscalyear fis
                                    where cast(NOW() as Date) between fis.date_start and fis.date_stop)
                            and av.date_invoice <=
                                (select fis.date_stop from account_fiscalyear fis
                                    where cast(NOW() as Date) between fis.date_start and fis.date_stop))
                END)
                as amount_curr_fisyear,
                (CASE
                    WHEN new.use_invoice_plan = True
                        THEN (select sum(pip.invoice_amount) from purchase_invoice_plan pip
                             where pip.order_id = new.purchase_id and pip.state = 'draft'
                                and pip.date_invoice >=
                                    (select fis.date_start from account_fiscalyear fis
                                        where cast(NOW() + interval '1 year' as Date) between fis.date_start and fis.date_stop)
                                and pip.date_invoice <=
                                    (select fis.date_stop from account_fiscalyear fis
                                        where cast(NOW() + interval '1 year' as Date) between fis.date_start and fis.date_stop))
                    ELSE
                        (select sum(av.amount_total)
                         from account_invoice av
                            left join purchase_invoice_rel pi_r on pi_r.invoice_id = av.id
                         where pi_r.purchase_id = new.purchase_id and av.state = 'draft'
                            and av.date_invoice >=
                                (select fis.date_start from account_fiscalyear fis
                                    where cast(NOW() + interval '1 year' as Date) between fis.date_start and fis.date_stop)
                            and av.date_invoice <=
                                (select fis.date_stop from account_fiscalyear fis
                                    where cast(NOW() + interval '1 year' as Date) between fis.date_start and fis.date_stop))
                END)
                as amount_next_fisyear
             from (
                (select
                    ou.org_id as org_id, po.id as purchase_id, pct.id as contract_id, 
                    pip.id as inv_plan_id, av.id as invoice_id, avl.id as invoice_line_id,
                    av.purchase_billing_id as billing_id, pol.id as purchase_line_id,
                    po.state as po_status, po.order_type,
                    case
                        when prot.type in ('product','consu') then acc_st.id
                        when prot.type in ('service') then acc_exp.id
                        else null
                    end as account_id,
                    prod.id as product_id, po.partner_id as supplier_id,
                    fis.name as po_fiscalyear, ou.name as org, cast(po.date_order as date) as date_order,
                    po.name as po_number, pol.docline_seq, 
                    cast(pip.installment as varchar) as installment,
                    pct.action_date,
                    (select pe.id from account_period pe 
                        where pip.date_invoice between pe.date_start and pe.date_stop limit 1
                    ) as period_plan_id,
                    (select pe.id from account_period pe 
                        where av.date_invoice between pe.date_start and pe.date_stop limit 1
                    ) as period_kv_id,
                    case
                        when po.po_contract_type_id is not null then po_pct_t.name
                        else ''
                    end as po_contract_type,
                    ag.name as activity_group, 
                    rpt.name as activity_rpt,
                    case
                        when pol.section_id is not null then sec.code
                        when pol.project_id is not null then prj.code
                        when pol.invest_asset_id is not null then asset.code
                        when pol.invest_construction_phase_id is not null then phase.code
                        when pol.personnel_costcenter_id is not null then rpc.code
                        else ''
                    end as budget_code,
                    case
                        when pol.section_id is not null then sec.name
                        when pol.project_id is not null then prj.name
                        when pol.invest_asset_id is not null then asset.name
                        when pol.invest_construction_phase_id is not null then phase.name
                        when pol.personnel_costcenter_id is not null then rpc.name
                        else ''
                    end as budget_name,
                    pol.section_id,
                    pol.project_id,
                    pol.invest_asset_id,
                    pol.invest_construction_phase_id,
                    pol.personnel_costcenter_id,
                    fund.name as fund, fis.name as fiscal_year_by_invoice_plan,
                    cur_po.name as currency, 
                    (SELECT STRING_AGG(tax.description, ', ') AS tax 
                     FROM account_tax tax 
                         LEFT JOIN purchase_order_taxe pot ON pot.tax_id = tax.id
                     WHERE pot.ord_id = pol.id
                    ) AS taxes,
                     wa.name as wa_number, 
                    wa.date_accept as acceptance_date,
                    wal.to_receive_qty as plan_qty,
                    wal.price_unit_untaxed as plan_unit_price,
                    wal.price_subtotal as subtotal,
                    avl.price_subtotal as inv_amount,
                    case
                        when po.use_deposit is False and po.use_advance is False then ''
                        else ads.name
                    end as advance_deposit,
                    po.use_invoice_plan, po.technical_closed, po.is_fin_lease
                from purchase_order po
                    left join purchase_invoice_plan pip on pip.order_id = po.id
                    left join purchase_order_line pol on pol.id = pip.order_line_id
                    left join account_invoice av on av.id = pip.ref_invoice_id and av.state <> 'cancel'
                    left join account_invoice_line avl on avl.invoice_id = av.id
                         and (avl.purchase_line_id = pol.id or (avl.purchase_line_id is null and pip.order_line_id is null))
                    left join purchase_work_acceptance wa on wa.invoice_created = av.id and wa.state <> 'cancel'
                    left join purchase_work_acceptance_line wal 
                        on wal.acceptance_id = wa.id and wal.line_id = pol.id
                    left join account_fiscalyear fis on fis.id = pol.fiscalyear_id
                    left join purchase_contract pct on pct.id = po.contract_id
                    left join purchase_contract_type pct_t on pct_t.id = pct.contract_type_id
                    left join purchase_contract_type po_pct_t on po_pct_t.id = po.po_contract_type_id
                    left join account_activity_group ag on ag.id = pol.activity_group_id
                    left join account_activity rpt on rpt.id = pol.activity_rpt_id
                    left join product_product prod on prod.id = pol.product_id
                    left join product_template prot on prot.id = prod.product_tmpl_id
                    left join product_category cate on cate.id = prot.categ_id
                    left join ir_property ip_exp on ip_exp.res_id = concat('product.category,',cate.id)
                        and ip_exp.name = 'property_account_expense_categ'
                    left join account_account acc_exp on concat('account.account,',acc_exp.id) = ip_exp.value_reference
                    left join ir_property ip_st on ip_st.res_id = concat('product.category,',cate.id)
                        and ip_st.name = 'property_stock_valuation_account_id'
                    left join account_account acc_st on concat('account.account,',acc_st.id) = ip_st.value_reference
                    left join res_org org on org.id = pol.org_id
                    left join operating_unit ou on ou.id =
                        (select ouu.id from operating_unit ouu 
                         where (org.id is not null and ouu.id = org.operating_unit_id)
                            or (org.id is null and ouu.id = po.operating_unit_id))
                    left join res_fund fund on fund.id = pol.fund_id
                    left join res_section sec on sec.id = pol.section_id
                    left join res_project prj on prj.id = pol.project_id
                    left join res_invest_asset asset on asset.id = pol.invest_asset_id
                    left join res_invest_construction_phase phase on phase.id = pol.invest_construction_phase_id
                    left join res_personnel_costcenter rpc on rpc.id = pol.personnel_costcenter_id
                    left join purchase_billing pbil on pbil.id = av.purchase_billing_id
                    left join res_currency cur_po on cur_po.id = po.currency_id
                    left join res_currency cur_kv on cur_kv.id = av.currency_id
                    left join account_account ads on ads.id = po.account_deposit_supplier
                where pip.id is not null and (pip.order_line_id is null or pol.active = True)
                    and po.use_invoice_plan = True
                )
                union
                (select
                    org.id as org_id, po.id as purchase_id, pct.id as contract_id, 
                    pip.id as inv_plan_id, av.id as invoice_id, avl.id as invoice_line_id,
                    av.purchase_billing_id as billing_id, pol.id as purchase_line_id,
                    po.state as po_status, po.order_type,
                    case
                        when prot.type in ('product','consu') then acc_st.id
                        when prot.type in ('service') then acc_exp.id
                        else null
                    end as account_id,
                    prod.id as product_id, po.partner_id as supplier_id,
                    fis.name as po_fiscalyear, ou.name as org, cast(po.date_order as date) as date_order,
                    po.name as po_number, pol.docline_seq, 
                    cast(pip.installment as varchar) as installment,
                    pct.action_date,
                    (select pe.id from account_period pe 
                        where pip.date_invoice between pe.date_start and pe.date_stop limit 1
                    ) as period_plan_id,
                    (select pe.id from account_period pe 
                        where av.date_invoice between pe.date_start and pe.date_stop limit 1
                    ) as period_kv_id,
                    case
                        when po.po_contract_type_id is not null then po_pct_t.name
                        else ''
                    end as po_contract_type,
                    ag.name as activity_group, 
                    rpt.name as activity_rpt,
                    case
                        when pol.section_id is not null then sec.code
                        when pol.project_id is not null then prj.code
                        when pol.invest_asset_id is not null then asset.code
                        when pol.invest_construction_phase_id is not null then phase.code
                        when pol.personnel_costcenter_id is not null then rpc.code
                        else ''
                    end as budget_code,
                    case
                        when pol.section_id is not null then sec.name
                        when pol.project_id is not null then prj.name
                        when pol.invest_asset_id is not null then asset.name
                        when pol.invest_construction_phase_id is not null then phase.name
                        when pol.personnel_costcenter_id is not null then rpc.name
                        else ''
                    end as budget_name,
                    pol.section_id,
                    pol.project_id,
                    pol.invest_asset_id,
                    pol.invest_construction_phase_id,
                    pol.personnel_costcenter_id,
                    fund.name as fund, fis.name as fiscal_year_by_invoice_plan,
                    cur_po.name as currency, 
                    (SELECT STRING_AGG(tax.description, ', ') AS tax 
                     FROM account_tax tax 
                         LEFT JOIN purchase_order_taxe pot ON pot.tax_id = tax.id
                     WHERE pot.ord_id = pol.id
                    ) AS taxes,
                     wa.name as wa_number, 
                    wa.date_accept as acceptance_date,
                    wal.to_receive_qty as plan_qty,
                    wal.price_unit_untaxed as plan_unit_price,
                    wal.price_subtotal as subtotal,
                    avl.price_subtotal as inv_amount,
                    case
                        when po.use_deposit is False and po.use_advance is False then ''
                        else ads.name
                    end as advance_deposit,
                    po.use_invoice_plan, po.technical_closed, po.is_fin_lease
                from purchase_order po
                    left join purchase_order_line pol on pol.order_id = po.id
                    left join purchase_invoice_plan pip on pip.order_line_id = pol.id
                    left join account_invoice_line avl on avl.purchase_line_id = pol.id
                        and (select av2.state from account_invoice av2 where av2.id = avl.invoice_id) <> 'cancel'
                    left join account_invoice av on av.id = avl.invoice_id
                    left join purchase_work_acceptance wa on wa.invoice_created = av.id and wa.state <> 'cancel'
                    left join purchase_work_acceptance_line wal 
                        on wal.acceptance_id = wa.id and wal.line_id = pol.id
                    left join account_fiscalyear fis on fis.id = pol.fiscalyear_id
                    left join purchase_contract pct on pct.id = po.contract_id
                    left join purchase_contract_type pct_t on pct_t.id = pct.contract_type_id
                    left join purchase_contract_type po_pct_t on po_pct_t.id = po.po_contract_type_id
                    left join account_activity_group ag on ag.id = pol.activity_group_id
                    left join account_activity rpt on rpt.id = pol.activity_rpt_id
                    left join product_product prod on prod.id = pol.product_id
                    left join product_template prot on prot.id = prod.product_tmpl_id
                    left join product_category cate on cate.id = prot.categ_id
                    left join ir_property ip_exp on ip_exp.res_id = concat('product.category,',cate.id) 
                        and ip_exp.name = 'property_account_expense_categ'
                    left join account_account acc_exp on concat('account.account,',acc_exp.id) = ip_exp.value_reference
                    left join ir_property ip_st on ip_st.res_id = concat('product.category,',cate.id) 
                        and ip_st.name = 'property_stock_valuation_account_id'
                    left join account_account acc_st on concat('account.account,',acc_st.id) = ip_st.value_reference
                    left join res_org org on org.id = pol.org_id
                    left join operating_unit ou on ou.id = org.operating_unit_id
                    left join res_fund fund on fund.id = pol.fund_id
                    left join res_section sec on sec.id = pol.section_id
                    left join res_project prj on prj.id = pol.project_id
                    left join res_invest_asset asset on asset.id = pol.invest_asset_id
                    left join res_invest_construction_phase phase on phase.id = pol.invest_construction_phase_id
                    left join res_personnel_costcenter rpc on rpc.id = pol.personnel_costcenter_id
                    left join purchase_billing pbil on pbil.id = av.purchase_billing_id
                    left join res_currency cur_po on cur_po.id = po.currency_id
                    left join res_currency cur_kv on cur_kv.id = av.currency_id
                    left join account_account ads on ads.id = po.account_deposit_supplier
                where (pol.id is null or pol.active = True) and pip.id is null
                    and po.use_invoice_plan <> True
                )
            ) as new
            where po_status not in ('except_picking','except_invoice','cancel') 
                and order_type = 'purchase_order'
                %s 
            order by org_id, po_fiscalyear, date_order, po_number, docline_seq, installment
        """  % (where_str))

        invoice_plans = self._cr.dictfetchall()
        self.results = [Reports.new(line).id for line in invoice_plans]
        print 'results: '+str(self.results)
 

class ReportPurchaseInvoicePlanView(models.AbstractModel):
    _name = 'report.purchase.invoice.plan.view'
    # _auto = False

    org_id = fields.Many2one('res.org')
    purchase_id = fields.Many2one('purchase.order')
    contract_id = fields.Many2one('purchase.contract')
    account_id = fields.Many2one('account.account')
    inv_plan_id = fields.Many2one('purchase.invoice.plan')
    invoice_id = fields.Many2one('account.invoice')
    invoice_line_id = fields.Many2one('account.invoice.line')
    billing_id = fields.Many2one('purchase.billing')
    purchase_line_id = fields.Many2one('purchase.order.line')
    product_id = fields.Many2one('product.product')
    supplier_id = fields.Many2one('res.partner')
    period_plan_id = fields.Many2one('account.period')
    period_kv_id = fields.Many2one('account.period')
    po_fiscalyear = fields.Char()
    po_contract_type = fields.Char()
    activity_group = fields.Char()
    activity_rpt = fields.Char()
    budget_code = fields.Char()
    budget_name = fields.Char()
    fund = fields.Char()
    fiscal_year_by_invoice_plan = fields.Char()
    currency = fields.Char()
    taxes = fields.Char()
    wa_number = fields.Char()
    acceptance_date = fields.Date()
    plan_qty = fields.Char()
    plan_unit_price = fields.Char()
    subtotal = fields.Char()
    inv_amount = fields.Float()
    advance_deposit = fields.Char()
    installment = fields.Char()
    no_of_installment = fields.Integer()
    amount_curr_fisyear = fields.Float()
    amount_next_fisyear = fields.Float()
    amount_curr_fisyear_local = fields.Float(compute='_compute_amount_local')
    amount_next_fisyear_local = fields.Float(compute='_compute_amount_local')

    @api.multi
    @api.depends('amount_curr_fisyear','amount_next_fisyear')
    def _compute_amount_local(self):
        for rec in self:
            if rec.amount_curr_fisyear:
                rec.amount_curr_fisyear_local = rec.amount_curr_fisyear * rec.purchase_id.currency_rate
            if rec.amount_next_fisyear:
                rec.amount_next_fisyear_local = rec.amount_next_fisyear * rec.purchase_id.currency_rate
