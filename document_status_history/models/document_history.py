# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp import tools


class AuditlogLogLine(models.Model):
    _inherit = 'auditlog.log.line'

    difference_value = fields.Text(
        string="Difference Value",
        compute="_compute_difference_value_text",
        store=False,
    )
    difference_value_text = fields.Text(
        string="Difference Value Text",
        compute="_compute_difference_value_text",
        store=False,
    )

    @api.multi
    def _compute_difference_value_text(self):
        for rec in self:
            if rec.field_name != 'groups_id':
                continue
            old_values = []
            new_values = []
            old_values = eval(rec.old_value_text)
            new_values = eval(rec.new_value_text)
            diff = list(
                set(old_values).union(set(new_values)) -
                set(old_values).intersection(set(new_values))
            )
            add = []
            remove = []
            rec.difference_value = diff
            for val in diff:
                if val in new_values:
                    text = val
                    add.append(text)
                else:
                    text = val
                    remove.append(text)
            if add:
                rec.difference_value_text = "ADD ---> %s" % add
            if remove:
                rec.difference_value_text = "Remove ---> %s" % remove
            if add and remove:
                rec.difference_value_text = "ADD ---> %s,\nRemove ---> %s" \
                                            % (add, remove)

    @api.model
    def create(self, vals):
        if vals.get('field_id', False):
            field = self.env['ir.model.fields'].browse(vals['field_id'])
            if field.ttype == 'selection' and field.name == 'state':
                state_labels =\
                    dict(self.env[field.model_id.model].
                         fields_get(['state'])['state']['selection'])
                vals['new_value'] = state_labels[vals['new_value']]
        res = super(AuditlogLogLine, self).create(vals)
        return res


class DocumentAuditlogLogLine(models.Model):
    _name = 'document.auditlog.log.line'
    _auto = False
    _order = 'date'

    status = fields.Char(
        string=u'Status',
        size=500,
    )
    status_text = fields.Char(
        string=u'Status Text',
        size=500,
    )
    user_id = fields.Many2one(
        'res.users',
        string=u"Changed By",
    )
    model_id = fields.Many2one(
        'ir.model',
        string=u"Model",
    )
    res_id = fields.Integer(u"Resource ID")
    date = fields.Datetime(
        string=u'Changed Date',
    )
    field_id = fields.Many2one(
        'ir.model.fields',
        ondelete='cascade',
        string=u"Field",
    )

    def _get_sql_view(self):
        sql_view = """
            SELECT
                logline.id as id,
                logline.new_value as status,
                logline.new_value_text as status_text,
                log.user_id as user_id,
                log.model_id as model_id,
                log.res_id as res_id,
                log.create_date as date,
                logline.field_id as field_id
            FROM
                auditlog_log_line as logline
            JOIN auditlog_log log
                ON (log.id = logline.log_id)
            JOIN ir_model_fields field
                ON (field.id = logline.field_id)
            WHERE field.name = 'state'
        """
        return sql_view

    def init(self, cr):
        tools.drop_view_if_exists(cr, self._table)
        cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" %
                   (self._table, self._get_sql_view(), ))


class LogCommon(object):

    auditlog_line_ids = fields.Many2many(
        'document.auditlog.log.line',
        compute='_compute_log_lines',
        string="Status History",
    )

    @api.multi
    def _compute_log_lines(self):
        for record in self:
            if isinstance(record.id, int):
                self._cr.execute("""
                    SELECT
                        logline.id
                    FROM
                        document_auditlog_log_line logline
                    JOIN ir_model as model
                        ON (model.id = logline.model_id)
                    WHERE
                        model.model = %s AND
                        logline.res_id = %s
                """, (self._name, record.id))
                result = self._cr.fetchall()
                line_ids = [r[0] for r in result]
                record.auditlog_line_ids = [(6, 0, line_ids)]
