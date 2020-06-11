# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import ValidationError


class PabiRegister_iCash(models.Model):
    _name = 'pabi.register.icash'
    _inherit = ['mail.thread']

    name = fields.Char(
        'Register number',
        track_visibility='onchange',
    )
    service_type = fields.Selection(
        [('direct', 'DIRECT'),('smart', 'SMART')],
        'Service Type',
        track_visibility='onchange',
    )
    export_date = fields.Date(
        'Register export date',
        #default=fields.Date.context_today,
        track_visibility='onchange',
    )
    state = fields.Selection(
        [('draft', 'Draft'),
         ('exported', 'Exported'),
         ('cancel', 'Cancelled')],
        string='Status',
        default='draft',
        readonly=True,
        track_visibility='onchange',
    )
    line_ids = fields.One2many(
        'pabi.register.icash.line',
        'register_id',
        'Supplier Account'
    )
    line_filter = fields.Char(
        string='Filter',
        readonly=True,
        states={'draft': [('readonly', False)]},
        help="More filter. You can use complex search with comma and between.",
    )

    @api.model
    def create(self, vals):
        vals['state'] = 'draft'
        vals['name'] = self.env['ir.sequence'].next_by_code('register.icash')
        res = super(PabiRegister_iCash, self).create(vals)
        #res._create_register_icash_line()
        return res

    @api.multi
    def write(self, vals):
        res = super(PabiRegister_iCash, self).write(vals)
        """if 'service_type' in vals:
            self.line_ids.unlink()
            self._create_register_icash_line()"""
        return res

    @api.multi
    def _create_register_icash_line(self, domain=None):
        self.ensure_one()
        RegisterLineObj = self.env['pabi.register.icash.line']
        PartnerBankObj = self.env['res.partner.bank']
        if domain is None:
            domain = []
        domain.append(('is_register','!=',True))

        if self.line_ids:
            ids = self.line_ids.mapped('partner_bank_id').ids
            domain.append(('id', 'not in', ids))
        if self.service_type == 'direct':
            domain.append(('bank.abbrev', '=', 'BBL'))
        if self.service_type == 'smart':
            domain.append(('bank.abbrev', '!=', 'BBL'))

        parner_bank_search = PartnerBankObj.search(domain)

        for line in parner_bank_search:
            register_line = RegisterLineObj.new()
            register_line.partner_bank_id = line
            register_line.beneficiary_code = 'NSTDA_%s' % line.acc_number
            register_line.account_number = line.acc_number
            register_line.owner_name_en = line.owner_name_en
            register_line.partner_searchkey = line.partner_id.search_key
            register_line.partner_name = line.partner_id.name
            register_line.partner_email_accountant = line.partner_id.email_accountant
            self.line_ids += register_line
            """RegisterLineObj.create({'register_id': self.id,
                                    'partner_bank_id': line.id,
                                    'beneficiary_code': 'NSTDA_%s' % line.acc_number,
                                    'account_number': line.acc_number,
                                    'owner_name_en': line.owner_name_en,
                                    'partner_searchkey': line.partner_id.search_key,
                                    'partner_name': line.partner_id.name,
                                    'partner_email_accountant': line.partner_id.email_accountant,
                                    })"""

    @api.onchange('line_filter')
    def _onchange_compute_register_icash_line(self):
        if self.line_filter:
            acc_number = self.line_filter.split(',')
            acc_number = [x.strip() for x in acc_number]
            acc_number = tuple(acc_number)
            domain = [('acc_number', 'in', acc_number)]

            self._create_register_icash_line(domain)

    @api.onchange('service_type')
    def _onchange_service_type(self):
        self.line_ids = False

    @api.multi
    def _check_record_registered(self):
        self.ensure_one()
        registered_ids = self.line_ids.filtered(
            lambda l: l.partner_bank_id.is_register == True).mapped('beneficiary_code')
        if registered_ids:
            raise ValidationError('Record Registered\n%s' % str(tuple(registered_ids)))

    @api.multi
    def register_cancel(self):
        self.state = 'cancel'

    @api.multi
    def reload(self):
        self.line_ids.onchange_partner_bank_id()

    @api.multi
    def generate_record(self):
        self._create_register_icash_line()


class PabiRegister_iCashLine(models.Model):
    _name = 'pabi.register.icash.line'

    register_id = fields.Many2one(
        'pabi.register.icash'
    )
    partner_bank_id = fields.Many2one(
        'res.partner.bank'
    )
    beneficiary_code = fields.Char(
        'Beneficiary Code'
    )
    account_number = fields.Char(
        'Account Number'
    )
    owner_name_en = fields.Char(
        'Account Ower Name En'
    )
    partner_searchkey = fields.Char(
        'Partner Search Key'
    )
    partner_name = fields.Char(
        'Partner Name'
    )
    partner_email_accountant = fields.Char(
        'Email Account'
    )

    @api.onchange('partner_bank_id')
    def onchange_partner_bank_id(self):
        for rec in self:
            if rec.register_id.state == 'draft' and rec.partner_bank_id:
                rec.beneficiary_code = 'NSTDA_%s' % rec.partner_bank_id.acc_number
                rec.account_number = rec.partner_bank_id.acc_number
                rec.owner_name_en = rec.partner_bank_id.owner_name_en
                rec.partner_searchkey = rec.partner_bank_id.partner_id.search_key
                rec.partner_name = rec.partner_bank_id.partner_id.name
                rec.partner_email_accountant = rec.partner_bank_id.partner_id.email_accountant
