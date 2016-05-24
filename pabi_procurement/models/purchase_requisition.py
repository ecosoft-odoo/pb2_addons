# -*- coding: utf-8 -*-
import openerp
import base64
import time
import re
from openerp import api, fields, models, _
import openerp.addons.decimal_precision as dp
from openerp.exceptions import Warning as UserError
from openerp.tools import float_compare


class PurchaseRequisition(models.Model):
    _inherit = "purchase.requisition"

    _STATES = [
        ('draft', 'Draft'),
        ('in_progress', 'Confirmed'),
        ('verify', 'To Verify'),
        ('rejected', 'Rejected'),
        ('open', 'Bid Selection'),
        ('done', 'PO Created'),
        ('cancel', 'Cancelled'),
    ]

    state = fields.Selection(
        _STATES,
        string='Status',
        track_visibility='onchange',
        required=True,
        copy=False,
    )
    purchase_type_id = fields.Many2one(
        'purchase.type',
        string='Type',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    objective = fields.Text(
        string='Objective',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    description = fields.Text(
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    total_budget_value = fields.Float(
        string='Total Budget Value',
        default=0.0,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    purchase_prototype_id = fields.Many2one(
        'purchase.prototype',
        string='Prototype',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    purchase_method_id = fields.Many2one(
        'purchase.method',
        string='Method',
        readonly=True,
        states={'draft': [('readonly', False)]},
        track_visibility='onchange',
    )
    purchase_price_range_id = fields.Many2one(
        'purchase.price.range',
        string='Price Range',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    purchase_condition_id = fields.Many2one(
        'purchase.condition',
        string='Condition',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    purchase_confidential_id = fields.Many2one(
        'purchase.confidential',
        string='Confidential',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    confidential_detail = fields.Text(
        string='Confidential Detail',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    currency_rate = fields.Float(
        string='Rate',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    committee_ids = fields.One2many(
        'purchase.requisition.committee',
        'requisition_id',
        string='Committee',
        readonly=False,
    )
    attachment_ids = fields.One2many(
        'purchase.requisition.attachment',
        'requisition_id',
        string='Attach Files',
    )
    amount_untaxed = fields.Float(
        string='Untaxed Amount',
        compute='_compute_amount',
        store=True,
        readonly=True,
        default=0.0,
    )
    amount_tax = fields.Float(
        string='Taxes',
        compute='_compute_amount',
        store=True,
        readonly=True,
        default=0.0,
    )
    amount_total = fields.Float(
        string='Total',
        compute='_compute_amount',
        store=True,
        readonly=True,
        default=0.0,
    )
    request_uid = fields.Many2one(
        'res.users',
        string='PR. Requested by',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    assign_uid = fields.Many2one(
        'res.users',
        string='PR. Approver',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    date_approve = fields.Date(
        string='PR. Approved Date',
        readonly=True,
        states={'draft': [('readonly', False)]},
        help="Date when the request has been approved",
    )
    request_ref_id = fields.Many2one(
        'purchase.request',
        string='PR Reference',
        copy=False,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    verify_uid = fields.Many2one(
        'res.users',
        string='Verified by',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    date_verify = fields.Date(
        string='Verified Date',
        readonly=True,
        states={'draft': [('readonly', False)]},
        help="Date when the request has been verified",
    )
    date_doc_approve = fields.Date(
        string='Date of Approval',
        readonly=True,
        states={'draft': [('readonly', False)]},
        help="Date of the order has been approved ",
    )
    doc_approve_uid = fields.Many2one(
        'res.users',
        string='Approver',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    doc_no = fields.Char(
        string='No.',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    doc_header = fields.Text(
        string='Header',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    doc_footer = fields.Text(
        string='Footer',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    reject_reason_txt = fields.Char(
        string="Rejected Reason",
        readonly=True,
        copy=False,
    )
    is_central_purchase = fields.Boolean(
        string='Central Purchase',
        readonly=True,
        states={'draft': [('readonly', False)]},
        default=False,
    )
    exclusive = fields.Selection(
        default='exclusive',
    )
    name = fields.Char(
        default=lambda self:
        self.env['ir.sequence'].get('purchase.requisition'),
    )

    @api.one
    @api.depends('line_ids.price_subtotal', 'line_ids.tax_ids')
    def _compute_amount(self):
        amount_untaxed = 0.0
        amount_tax = 0.0
        for line in self.line_ids:
            taxes = line.tax_ids.compute_all(line.price_unit, line.product_qty,
                                             product=line.product_id)
            amount_tax += sum([tax['amount'] for tax in taxes['taxes']])
            amount_untaxed += taxes['total']
        self.amount_untaxed = amount_untaxed
        self.amount_tax = amount_tax
        self.amount_total = amount_untaxed + amount_tax

    @api.onchange('is_central_purchase')
    def _onchange_is_central_purchase(self):
        domain = []
        if self.is_central_purchase:
            self.exclusive = 'multiple'
            self.multiple_rfq_per_supplier = True
            domain = []
        else:
            self.exclusive = 'exclusive'
            self.multiple_rfq_per_supplier = False
            domain = self.env['operating.unit']._ou_domain()
        return {'domain': {'operating_unit_id': domain}}

    @api.model
    def open_price_comparison(self, ids):
        window_obj = self.env["ir.actions.act_window"]
        res = window_obj.for_xml_id('purchase', 'purchase_line_form_action2')
        pur_line_ids = []
        po_recs = self.browse(ids)
        for po_rec in po_recs:
            pur_line_ids = po_rec.purchase_ids._ids
        res['context'] = self._context
        res['domain'] = [('order_id', 'in', pur_line_ids)]
        return res

    @api.multi
    def by_pass_approve(self):
        po_obj = self.env["purchase.order"]
        po_obj.action_button_convert_to_order()
        print 'by-pass requisition'
        return True

    @api.model
    def _prepare_committee_line(self, line, order_id):
        return {
            'order_id': order_id,
            'name': line.name,
            'sequence': line.sequence,
            'position': line.position,
            'committee_type_id': line.committee_type_id.id,
        }

    @api.model
    def _prepare_order_committees(self, order_id):
        committees = []
        for line in self.committee_ids:
            committee_line = self._prepare_committee_line(line,
                                                          order_id)
            committees.append([0, False, committee_line])
        return committees

    @api.multi
    def make_purchase_order(self, partner_id):
        res = super(PurchaseRequisition, self).\
            make_purchase_order(partner_id)
        Order = self.env['purchase.order']
        for order_id in res.itervalues():
            orders = Order.search([('id', '=', order_id)])
            for order in orders:
                order.write({
                    'committee_ids': self._prepare_order_committees(order_id),
                    'verify_uid': self.verify_uid.id,
                    'date_verify': self.date_verify,
                    'doc_no': self.doc_no,
                    'fine_rate': 0.1,
                })
        return res

    @api.model
    def _prepare_purchase_order(self, requisition, supplier):
        res = super(PurchaseRequisition, self).\
            _prepare_purchase_order(requisition, supplier)
        res.update({
            'requesting_operating_unit_id': requisition.operating_unit_id.id,
        })
        # Case central purchase, use selected OU
        if self._context.get('sel_operating_unit_id', False):
            operating_unit_id = self._context.get('sel_operating_unit_id')
            picking_type_id = self._context.get('sel_picking_type_id')
            location_id = self._context.get('sel_location_id')
            res.update({
                'operating_unit_id': operating_unit_id,
                'picking_type_id': picking_type_id,
                'location_id': location_id,
            })
        return res

    @api.model
    def _prepare_purchase_order_line(self, requisition, requisition_line,
                                     purchase_id, supplier):
        res = super(PurchaseRequisition, self).\
            _prepare_purchase_order_line(requisition, requisition_line,
                                         purchase_id, supplier)
        # Always use price and tax_ids from pr_line (NOT from product)
        res.update({
            'name': requisition_line.product_name,
            'price_unit': requisition_line.price_unit,
            'taxes_id': [(6, 0, requisition_line.tax_ids.ids)],
        })
        return res

    @api.multi
    def _check_product_type(self):
        self.ensure_one()
        if len(self.line_ids) == 0:
            raise UserError(
                _('Product line cannot be empty.')
            )
        types = [(l.product_id.type in ('product', 'consu') and
                  'stock' or
                  l.product_id.type) for l in self.line_ids]
        if len(list(set(types))) > 1:
            raise UserError(
                _('All products must be of the same type')
            )
        return True

    @api.multi
    def to_verify(self):
        assert len(self) == 1, \
            'This option should only be used for a single id at a time.'
        self._check_product_type()
        self.state = 'verify'
        return True

    @api.multi
    def rejected(self):
        assert len(self) == 1, \
            'This option should only be used for a single id at a time.'
        self.signal_workflow('rejected')
        self.state = 'rejected'

    @api.multi
    def send_pbweb_requisition(self):
        PWInterface = self.env['purchase.web.interface']
        PWInterface.send_pbweb_requisition(self)
        return True

    @api.multi
    def set_verification_info(self):
        assert len(self) == 1, \
            'This option should only be used for a single id at a time.'
        self.print_call_for_bid_form()
        self.write({
            'verify_uid': self._uid,
            'date_verify': fields.date.today(),
        })
        for order in self.purchase_ids:
            if order.state != 'cancel':
                order.write({
                    'verify_uid': self._uid,
                    'date_verify': fields.date.today(),
                })
        return True

    @api.multi
    def tender_done(self, context):
        # ensure the tender to be done in PABIWeb confirmation.
        res = False
        for requisition in self:
            if requisition.state == 'open':
                res = super(PurchaseRequisition, self).tender_done(context)
        return res

    @api.model
    def done_order(self, af_info):
        # {
        #     'name': 'TE00017',
        #     'approve_uid': '002241',
        #     'action' : 'C1' or 'W2'
        #     'file_name': 'TE00017.pdf',
        #     'file_url': 'aaaaas.pdf',
        # }
        user = self.env['res.users']
        res = {}
        requisition = self.search([('name', '=', af_info['name'])])
        uid = user.search([('login', '=', af_info['approve_uid'])])
        if len(requisition) == 1:
            if af_info['action'] == 'C1':
                att_file = []
                try:
                    attachments = {
                        'requisition_id': requisition.id,
                        'name': af_info['file_name'],
                        'file_url': af_info['file_url'],
                    }
                    att_file.append([0, False, attachments])
                    for order in requisition.purchase_ids:
                        if order.order_type == 'quotation' \
                                and order.state not in ('draft', 'cancel'):
                            requisition.write({
                                'doc_approve_uid': uid.id,
                                'date_doc_approve': fields.date.today(),
                                'attachment_ids': att_file,
                            })
                            order.action_button_convert_to_order()
                            if order.state2 != 'done' or order.state != 'done':
                                order.write({
                                    'state': 'done',
                                    'state2': 'done',
                                    'doc_approve_uid': uid.id,
                                    'date_doc_approve': fields.date.today(),
                                })
                    if requisition.state != 'done':
                        requisition.tender_done()
                    res.update({
                        'is_success': True,
                        'result': True,
                    })
                except Exception, e:
                    res.update({
                        'is_success': False,
                        'result': False,
                        'messages': _(str(e)),
                    })
        else:
            res.update({
                'is_success': False,
                'result': False,
                'messages': 'Cannot assign done state to Call for Bids.',
            })
        return res

    @api.multi
    def wkf_validate_vs_quotation(self):
        """ Case Central Purchase, quotation amount should not exceed """
        decimal_prec = self.env['decimal.precision']
        precision = decimal_prec.precision_get('Account')
        for requisition in self:
            if not requisition.is_central_purchase:
                continue
            total = sum([o.amount_total for o in requisition.purchase_ids])
            if float_compare(total, requisition.amount_total,
                             precision) == 1:
                raise UserError(
                    _('Total quotation amount exceed Call for Bid amount')
                )
        return True

    @api.multi
    def print_call_for_bid_form(self):
        self.ensure_one()
        Report = self.env['ir.actions.report.xml']
        matching_reports = Report.search([
            ('model', '=', self._name),
            ('report_type', '=', 'qweb-pdf'),
            ('report_name', '=',
             'purchase_requisition.report_purchaserequisitions')],)
        if matching_reports:
            report = matching_reports[0]
            result, _ = openerp.report.render_report(self._cr, self._uid,
                                                     [self.id],
                                                     report.report_name,
                                                     {'model': self._name})
            eval_context = {'time': time, 'object': self}
            if not report.attachment or not eval(report.attachment,
                                                 eval_context):
                # no auto-saving of report as attachment, need to do manually
                result = base64.b64encode(result)
                file_name = self.name_get()[0][1]
                file_name = re.sub(r'[^a-zA-Z0-9_-]', '_', file_name)
                file_name += ".pdf"
                self.env['ir.attachment'].create({'name': file_name,
                                                  'datas': result,
                                                  'datas_fname': file_name,
                                                  'res_model': self._name,
                                                  'res_id': self.id,
                                                  'type': 'binary'})


class PurchaseRequisitionLine(models.Model):
    _inherit = "purchase.requisition.line"

    price_unit = fields.Float(
        string='Unit Price',
    )
    price_standard = fields.Float(
        string='Standard Price',
    )
    fixed_asset = fields.Boolean(
        string='Fixed Asset',
        default=False,
    )
    price_subtotal = fields.Float(
        string='Sub Total',
        compute="_compute_price_subtotal",
        store=True,
        digits_compute=dp.get_precision('Account')
    )
    tax_ids = fields.Many2many(
        'account.tax',
        'purchase_requisition_taxes_rel',
        'requisition_line_id',
        'tax_id',
        string='Taxes',
        readonly=False,  # TODO: readonly=True
    )
    order_line_id = fields.Many2one(
        'purchase.order.line',
        string='Purchase Order Line'
    )
    product_name = fields.Char(
        string='Description',
    )

    @api.multi
    def onchange_product_id(self, product_id, product_uom_id,
                            parent_analytic_account, analytic_account,
                            parent_date, date):
        res = super(PurchaseRequisitionLine, self).\
            onchange_product_id(product_id, product_uom_id,
                                parent_analytic_account, analytic_account,
                                parent_date, date)
        if 'value' in res:
            if 'product_qty' in res['value']:
                del res['value']['product_qty']
            if 'product_uom_id' in res['value']:
                del res['value']['product_uom_id']
        return res

    @api.multi
    @api.depends('product_qty', 'price_unit', 'tax_ids')
    def _compute_price_subtotal(self):
        tax_amount = 0.0
        for line in self:
            amount_untaxed = line.product_qty * line.price_unit
            for line_tax in line.tax_ids:
                if line_tax.type == 'percent':
                    tax_amount += line.product_qty * (
                        line.price_unit * line_tax.amount
                    )
                elif line_tax.type == 'fixed':
                    tax_amount += line.product_qty * (
                        line.price_unit + line_tax.amount
                    )
            cur = line.requisition_id.currency_id
            line.price_subtotal = cur.round(amount_untaxed + tax_amount)


class PurchaseRequisitionAttachment(models.Model):
    _name = 'purchase.requisition.attachment'
    _description = 'Purchase Requisition Attachment'

    requisition_id = fields.Many2one(
        'purchase.requisition',
        string='Purchase Requisition',
    )
    name = fields.Char(
        string='File Name',
    )
    description = fields.Char(
        string='File Description',
    )
    file_url = fields.Char(
        string='File Url',
    )
    file = fields.Binary(
        string='File',
    )


class PurchaseRequisitionCommittee(models.Model):
    _name = 'purchase.requisition.committee'
    _description = 'Purchase Requisition Committee'
    _order = 'sequence, id'

    requisition_id = fields.Many2one(
        'purchase.requisition',
        string='Purchase Requisition',
    )
    sequence = fields.Integer(
        string='Sequence',
        default=1,
    )
    name = fields.Char(
        string='Name',
    )
    position = fields.Char(
        string='Position',
    )
    committee_type_id = fields.Many2one(
        'purchase.committee.type',
        string='Type',
    )
