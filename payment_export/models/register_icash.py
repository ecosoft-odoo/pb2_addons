# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError
from datetime import datetime


class PabiRegister_iCash(models.Model):
    _name = 'pabi.register.icash'
    _inherit = ['mail.thread']
    _description = 'Pre-Register iCash'

    name = fields.Char(
        'Register number',
        track_visibility='onchange',
    )
    service_type = fields.Selection(
        [('direct', 'BBL DIRECT-DCB02'),('smart', 'BBL SMART-SMC06')],
        'Service Type',
        track_visibility='onchange',
    )
    export_date = fields.Datetime(
        'Register Date',
        #default=fields.Date.context_today,
        track_visibility='onchange',
    )
    state = fields.Selection(
        [('draft', 'Draft'),
         ('registered', 'Registered'),
         ('cancel', 'Cancelled')],
        string='Status',
        #default='draft',
        readonly=True,
        track_visibility='onchange',
    )
    nume_lines = fields.Float(
        'Num Lines',
        compute="_compute_num_line",
        store=True
    )
    line_ids = fields.One2many(
        'pabi.register.icash.line',
        'register_id',
        'Supplier Account',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    line_filter = fields.Char(
        string='Filter',
        readonly=True,
        #states={'draft': [('readonly', False)]},
        help="More filter. You can use complex search with comma and between.",
    )

    @api.multi
    @api.depends('line_ids')
    def _compute_num_line(self):
        for rec in self:
            rec.nume_lines = len(rec.line_ids)
    
    @api.multi
    def _check_access_config(self):
        Config = self.env['pabi.register.icash.config']
        user_id = Config.search([('user_id', '=', self._uid)])
        user_id = user_id.filtered(lambda l: l.perm_create == True)
        if not user_id:
            raise ValidationError('ไม่สามารถดำเนินการได้ อนุญาตให้เฉพาะผู้จัดการด้านจ่ายเท่านั้น')

    @api.model
    def create(self, vals):
        self._check_access_config()
        vals['state'] = 'draft'
        vals['name'] = self.env['ir.sequence'].next_by_code('register.icash')
        res = super(PabiRegister_iCash, self).create(vals)
        return res

    @api.multi
    def _create_register_icash_line(self, domain=None):
        self.ensure_one()
        RegisterLineObj = self.env['pabi.register.icash.line']
        PartnerBankObj = self.env['res.partner.bank']
        if domain is None:
            domain = []

        parner_bank_search = PartnerBankObj.search(domain)
        #parner_bank_search = parner_bank_search.filtered(lambda l: l.partner_id.active is True)

        for line in parner_bank_search:
            bank_branch = line.bank_branch.code
            if line.bank.abbrev != 'BBL':
                if line.bank.code == '030':
                    bank_branch = '0309990'
                if line.bank.code == '034':
                    bank_branch = '0340000'

                if line.bank.code == '033':
                    if len(line.acc_number) == 10:
                        account_number = '00' + line.acc_number[2:4] + '0' + line.acc_number[-6:]
                    
                    elif len(line.acc_number) == 12:
                        account_number = '00' + line.acc_number[-9:]
                        
                elif line.bank.code in ['066','067','069']:
                    account_number = '0' + line.acc_number[-10:]
                else:
                    account_number = ('00000000000' + line.acc_number)[-11:]
            else:
                account_number = line.acc_number.strip()
            
            register_line = RegisterLineObj.new()
            register_line.partner_bank_id = line
            register_line.beneficiary_code = 'NSTDA_%s' % account_number
            register_line.account_number = account_number
            register_line.owner_name_en = line.owner_name_en
            register_line.partner_searchkey = line.partner_id.search_key
            register_line.partner_name = line.partner_id.name
            register_line.partner_email_accountant = line.partner_id.email_accountant
            register_line.bank_branch_code = bank_branch
            self.line_ids += register_line
            
    @api.multi
    @api.depends('line_filter')
    def _check_data_partner_bank(self, domain=None):
        PartnerBankObj = self.env['res.partner.bank']
        
        if domain is not None:
            parner_bank_ids = PartnerBankObj.search(domain)
            #parner_bank_ids = parner_bank_ids.filtered(lambda l: l.partner_id.active is True)
            
            # Check len(acc_number) > 1
            """partner_banks = {}
            acc_number = parner_bank_ids.mapped('acc_number')
            for acc in acc_number:
                if len(parner_bank_ids.filtered(lambda l: l.acc_number == acc)) > 1:
                    partner_name = [x.partner_id.display_name for x in parner_bank_ids.filtered(lambda l: l.acc_number == acc)]
                    partner_banks[acc] = '\n'.join(partner_name)
            
            if partner_banks:
                text_error = [u'เลขที่บัญชี {}\n {}'.format(key, value) for key, value in partner_banks.iteritems()]
                text_error = '\n\n'.join(text_error)
                raise ValidationError(u'กรุณาตรวจสอบ ข้อมูลหลัก Accounting ซึ่งมีข้อมูลเลขที่บัญชีมากกว่า 1 partner ดังนี้ \n {}'.format(text_error))"""
            
            # Check email_accountant or owner_name_en is NULL
            parner_bank_ids = parner_bank_ids.filtered(lambda l: l.partner_id.email_accountant is False
                                                                or l.owner_name_en is False)
            
            if parner_bank_ids:
                partners = []
                for rec in parner_bank_ids:
                    partners.append(rec.partner_id.display_name)

                raise ValidationError(u'กรุณาใส่ข้อมูล Email Accountant, Account Name EN ของ Partner ต่อไปนี้ให้ครบถ้วน\n{}'.format('\n'.join(tuple(partners))))

    @api.multi
    def _get_domain_partner_bank(self):
        PartnerBank = self.env['res.partner.bank']
        domain = []
        if self.line_filter:
            acc_number = self.line_filter.split(',')
            acc_number = [x.strip() for x in acc_number]
            
            ids = []
            for number in acc_number:
                pb = PartnerBank.search([('acc_number','=',number),
                                         ('is_register', '!=', True),
                                         ('active','=',True)
                                         ], order="write_date DESC", limit=1)
                if pb:
                    ids.append(pb.id)
            if ids:
                domain = [('id', 'in', ids)]
                if self.line_ids:
                    ids = self.line_ids.mapped('partner_bank_id').ids
                    domain.append(('id', 'not in', ids))
                if self.service_type == 'direct':
                    domain.append(('bank.abbrev', '=', 'BBL'))
                if self.service_type == 'smart':
                    domain.append(('bank.abbrev', '!=', 'BBL'))
        return domain

    @api.onchange('line_filter')
    def _onchange_compute_register_icash_line(self):
        if self.line_filter:
            
            domain = self._get_domain_partner_bank()
            if domain:
                self._check_data_partner_bank(domain)
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
        domain = [('is_register', '!=', True),
                  ('active', '=', True),
                  ('partner_id.active', '=', True)]
        self._create_register_icash_line()
        
    @api.multi
    def register(self):
        PartnerBank = self.env['res.partner.bank']
        self._check_access_config()
        self._check_record_registered()
        self.write({'state': 'registered',
                    'export_date': datetime.now()})

        acc_number = self.line_ids.mapped('partner_bank_id')
        acc_number = acc_number.mapped('acc_number')
        parner_bank_ids = PartnerBank.search([('acc_number', 'in', acc_number),
                                              ('is_register', '!=', True)])
        for line in parner_bank_ids:
            line.write({'register_no': self.name,
                        'register_date': datetime.now(),
                        'is_register': True})


class PabiRegister_iCashLine(models.Model):
    _name = 'pabi.register.icash.line'
    _description = 'Pre-Register iCash Line'

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
    bank_branch_code = fields.Char(
        'Bank Branch Code'
    )

    @api.onchange('partner_bank_id')
    def onchange_partner_bank_id(self):
        for rec in self:
            if rec.register_id.state == 'draft' and rec.partner_bank_id:
                bank_branch = rec.partner_bank_id.bank_branch.code
                if rec.partner_bank_id.bank.abbrev != 'BBL':
                    if rec.partner_bank_id.bank.code == '030':
                        bank_branch = '0309990'
                    if rec.partner_bank_id.bank.code == '034':
                        bank_branch = '0340000'
                    
                    if rec.partner_bank_id.bank.code == '033':
                        if len(rec.partner_bank_id.acc_number.strip()) == 10:
                            account_number = '00' + rec.partner_bank_id.acc_number.strip()[2:4] +\
                                             '0' + rec.partner_bank_id.acc_number.strip()[-6:]
                        
                        elif len(rec.partner_bank_id.acc_number.strip()) == 12:
                            account_number = '00' + rec.partner_bank_id.acc_number.strip()[-9:]
                            
                    elif rec.partner_bank_id.bank.code in ['066','067','069']:
                        account_number = '0' + rec.partner_bank_id.acc_number.strip()[-10:]
                    else:
                        account_number = ('00000000000' + rec.partner_bank_id.acc_number.strip())[-11:]
                else:
                    account_number = rec.partner_bank_id.acc_number.strip()
                
                rec.beneficiary_code = 'NSTDA_%s' % account_number
                rec.account_number = account_number
                rec.owner_name_en = rec.partner_bank_id.owner_name_en
                rec.partner_searchkey = rec.partner_bank_id.partner_id.search_key
                rec.partner_name = rec.partner_bank_id.partner_id.name
                rec.partner_email_accountant = rec.partner_bank_id.partner_id.email_accountant
                rec.bank_branch_code = bank_branch


class PabiRegisterConfig(models.Model):
    _name = 'pabi.register.icash.config'
    _description = 'Pre-Register iCash Config'
    
    user_id = fields.Many2one(
        'res.users',
        'User'
    )
    perm_create = fields.Boolean(
        string='Create Access'
    )
