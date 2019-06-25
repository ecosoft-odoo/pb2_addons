# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp import tools

REFERENCE_SELECT = [('account.voucher', 'Receipt'),
                    ('interface.account.entry', 'Account Interface'),
                    ('account.tax.detail', 'Adjustment'),
                    ]

class AccountMove(models.Model):
    _inherit = 'account.move'

    preprint_number = fields.Char(
        string='Preprint Number',
        compute='_compute_preprint_number',
    )

    @api.multi
    def _compute_preprint_number(self):
        for move in self:
            if move.doctype == 'receipt':
                Fund = self.env['account.voucher'] 
                domain = ([('move_id', '=', move.id)])
                lines = Fund.search(domain)
                move.preprint_number = lines.number_preprint
            if move.doctype == 'interface_account': 
                Fund = self.env['interface.account.entry'] 
                domain = ([('move_id', '=', move.id)])
                lines = Fund.search(domain)
                move.preprint_number = lines.preprint_number
            if move.doctype == 'adjustment': 
                Fund = self.env['account.tax.detail'] 
                domain = ([('ref_move_id', '=', move.id),('amount', '=', 0)])
                lines = Fund.search(domain)
                move.preprint_number = lines.invoice_number                                        

class Accountmovepreprint(models.Model):
    _name = 'account.move.preprint'    
    #_auto = False    

    move_id = fields.Many2one(
        'account.move',
        string='Document No',
    )
    name = fields.Char(
        string='Preprint Number',
        readonly=True,
    )
    org_id = fields.Many2one(
        'res.org',
        string='Org',
    )
    
class AccountMovePrePrintView(models.AbstractModel):
    """ Contrast to normal view, this will be used as mock temp table only """
    _name = 'account.move.preprint.view'
    _inherit = 'account.move'
    
    number_preprint = fields.Char(
        string='Preprint Number',
    )
    org_id = fields.Many2one(
        'res.org',
        string='Org',
    )
    amount = fields.Float(
        string='Amount',
    )
    base = fields.Float(
        string='Base Code Amount',
    )
    taxbranch_id = fields.Many2one(
        'res.taxbranch',
        string='Tax Branch',
    )
    
class XLSXReportGlProject(models.TransientModel):
    _name = 'xlsx.report.preprint.receipt'
    _inherit = 'report.account.common'

    postingdate_start = fields.Date(
        string='Start Posting Date',
    )
    postingdate_end = fields.Date(
        string='End Posting Date',
    )
    org_ids = fields.Many2many(
        'res.org',
        string='Org',
    )
    move_id = fields.Many2many(
        'account.move',
        string='Document No',
        domain=[('doctype','in',['adjustment','receipt','interface_account'])]
    )
#     results = fields.Many2many(
#         'account.move',
#         string='Results',
#         compute='_compute_results',
#         help='Use compute fields, so there is nothing store in database',
#     )
    results = fields.Many2many(
        'account.move.preprint.view',
        string='Results',
        compute='_compute_results',
        help='Use compute fields, so there is nothing store in database',
    )
    preprint_number = fields.Many2many(
        'account.move.preprint',
        string='Preprint Number',
    )

    @api.onchange('preprint_number')
    def create_data_preprint (self):
        self.env.cr.execute("SELECT COUNT(*) from account_move_preprint ")
        result=self.env.cr.fetchone()
        if result[0]==0:
            self.create_account_move_preprint()
        else:
            self.env.cr.execute(
                """
                select COUNT(*) from (SELECT m.id as move_id,pre.number_preprint as name,org.org_id as org_id
                    from account_move m
                    LEFT JOIN 
                        ( 
                        select c.move_id,c.number_preprint from
                        (select account_move.id as move_id,account_voucher.number_preprint as number_preprint
                        from account_move 
                        LEFT JOIN account_voucher on account_voucher.move_id = account_move."id"
                        UNION 
                        select account_move.id as move_id,interface_account_entry.preprint_number as number_preprint
                        from account_move 
                        LEFT JOIN interface_account_entry on interface_account_entry.move_id = account_move."id"
                        UNION 
                        select account_move.id as move_id,account_tax_detail.number_preprint as number_preprint
                        from account_move 
                        LEFT JOIN account_tax_detail on account_tax_detail.ref_move_id = account_move."id"
                        )as c
                        where c.number_preprint!=''
                        ) pre ON m.id = pre.move_id
                    LEFT JOIN 
                        (
                        SELECT DISTINCT m.id,m.name,l.org_id
                        from account_move m
                        LEFT JOIN account_move_line l ON l.move_id = m.id
                        where m.doctype in ('receipt','interface_account') and l.org_id != 0
                        ) org on org."id" = m."id"
                    where m.doctype in ('adjustment','receipt','interface_account') and pre.number_preprint!=''
                ) as count_update
                """
                )
            check = self.env.cr.fetchone()
            if result[0]!=check[0]:
                self.delete_account_move_preprint()
                self.create_account_move_preprint()

    def delete_account_move_preprint(self):
        self.env.cr.execute("DELETE FROM account_move_preprint")


    def create_account_move_preprint(self):
        self.env.cr.execute(
                """
                INSERT INTO account_move_preprint (
                     move_id,name,org_id)
                    (SELECT m.id as move_id,pre.number_preprint as name,org.org_id as org_id
                    from account_move m
                    LEFT JOIN 
                        ( 
                        select c.move_id,c.number_preprint from
                        (select account_move.id as move_id,account_voucher.number_preprint as number_preprint
                        from account_move 
                        LEFT JOIN account_voucher on account_voucher.move_id = account_move."id"
                        UNION 
                        select account_move.id as move_id,interface_account_entry.preprint_number as number_preprint
                        from account_move 
                        LEFT JOIN interface_account_entry on interface_account_entry.move_id = account_move."id"
                        UNION 
                        select account_move.id as move_id,account_tax_detail.number_preprint as number_preprint
                        from account_move 
                        LEFT JOIN account_tax_detail on account_tax_detail.ref_move_id = account_move."id"
                        )as c
                        where c.number_preprint!=''
                        ) pre ON m.id = pre.move_id
                    LEFT JOIN 
                        (
                        SELECT DISTINCT m.id,m.name,l.org_id
                        from account_move m
                        LEFT JOIN account_move_line l ON l.move_id = m.id
                        where m.doctype in ('receipt','interface_account') and l.org_id != 0
                        ) org on org."id" = m."id"
                    where m.doctype in ('adjustment','receipt','interface_account') and pre.number_preprint!=''
                    )
                """
        )    

#     @api.multi
#     def _compute_results(self):
#         self.ensure_one()
#         Result = self.env['account.move']
#         dom = []
#         domain=[]
#         if self.period_start_id:
#             dom += [('date', '>=', self.period_start_id.date_start)]
#         if self.period_end_id:
#             dom += [('date', '<=', self.period_end_id.date_stop)]
#         if self.date_start:
#             dom += [('date', '>=', self.date_start)]
#         if self.date_end:
#             dom += [('date', '<=', self.date_end)]
#         if self.postingdate_start:
#             dom += [('date', '>=', self.postingdate_start)]
#         if self.postingdate_end:
#             dom += [('date', '<=', self.postingdate_end)]
#         if self.move_id:
#             domain += [('move_id', 'in', self.move_id.ids)]
#         if self.org_ids:
#             domain += [('org_id', 'in', self.org_ids.ids)]
#         if self.preprint_number:
#             domain += [('id', 'in', self.preprint_number.ids)]
#         if domain:
#             preprint=self.env['account.move.preprint'].search(domain)
#             dom += [('id', 'in', [x.move_id.id for x in preprint])]
# 
#         self.results = Result.with_context(active=False).search(dom)
    @api.model
    def _domain_to_where_str(self, domain):
        """ Helper Function for better performance """
        where_dom = [" %s %s %s " % (x[0], x[1], isinstance(x[2], basestring)
                     and "'%s'" % x[2] or x[2]) for x in domain]
        where_str = 'and'.join(where_dom)
        return where_str
    
    @api.multi
    def _compute_results(self):
        self.ensure_one()
        dom = []
        if self.period_start_id:
            dom += [('date', '>=', self.period_start_id.date_start)]
        if self.period_end_id:
            dom += [('date', '<=', self.period_end_id.date_stop)]
        if self.date_start:
            dom += [('date', '>=', self.date_start)]
        if self.date_end:
            dom += [('date', '<=', self.date_end)]
        if self.postingdate_start:
            dom += [('date', '>=', self.postingdate_start)]
        if self.postingdate_end:
            dom += [('date', '<=', self.postingdate_end)]
        
        #prefix
        if self.move_id:
            dom += [('id', 'in', self.move_id.ids)]
        if self.org_ids:
            dom += [('org_id', 'in', self.org_ids.ids)]
        if self.preprint_number:
            dom += [('id', 'in', self.preprint_number.ids)]
        
        whr_depreciation = ""   
        where_str = self._domain_to_where_str(dom) 
        if where_str:
            where_str = ' and '+ where_str
        
        self._cr.execute("""
                    SELECT m.*,pre.number_preprint as number_preprint,org.org_id as org_id,pre.amount,pre.base,pre.taxbranch_id
                    from account_move m
                    LEFT JOIN 
                        ( 
                        --Search move_id and number_preprint
                        select c.move_id,c.number_preprint,c.amount,c.base,c.taxbranch_id from
                        (
                        -- RC
                        select account_move.id as move_id,account_voucher.number_preprint as number_preprint,
                                account_tax_detail.amount,account_tax_detail.base as base,account_tax_detail.taxbranch_id
                            from account_move 
                            LEFT JOIN account_voucher on account_voucher.move_id = account_move."id"
                            INNER JOIN account_tax_detail on account_tax_detail.ref_move_id = account_move."id"
                            WHERE account_tax_detail.doc_type = 'sale'
                        UNION 
                        -- IA
                        select account_move.id as move_id,interface_account_entry.preprint_number as number_preprint,
                                account_tax_detail.amount,account_tax_detail.base as base,account_tax_detail.taxbranch_id
                            from account_move 
                            LEFT JOIN interface_account_entry on interface_account_entry.move_id = account_move."id"
                            LEFT JOIN account_move_line on account_move_line.move_id = account_move.id
                            INNER JOIN account_tax_detail on account_tax_detail.move_line_id = account_move_line.id
                            WHERE account_tax_detail.doc_type = 'sale'
                        UNION 
                        --CV
                            select account_move.id as move_id,account_tax_detail.number_preprint as number_preprint,
                                    account_tax_detail.amount,account_tax_detail.base as base,account_tax_detail.taxbranch_id
                            from account_move 
                            LEFT JOIN account_tax_detail on account_tax_detail.ref_move_id = account_move."id"
                            WHERE account_tax_detail.doc_type = 'sale'
                        )as c
                        where c.number_preprint!=''
                        ) pre ON m.id = pre.move_id
                    -- Search org
                    LEFT JOIN 
                        (
                        SELECT DISTINCT m.id,m.name,l.org_id
                        from account_move m
                        LEFT JOIN account_move_line l ON l.move_id = m.id
                        where m.doctype in ('receipt','interface_account') and l.org_id != 0
                        ) org on org."id" = m."id"
                    where m.doctype in ('adjustment','receipt','interface_account') and pre.number_preprint!=''
                  
        """  + where_str + ' order by pre.number_preprint ' )     
        
        results = self._cr.dictfetchall()
        ReportLine = self.env['account.move.preprint.view']
        for line in results:
            self.results += ReportLine.new(line)
        return True
         
