# -*- coding: utf-8 -*-
{
    'name': "NSTDA :: PABI2 Internal Charge",
    'summary': "",
    'author': "Ecosoft",
    'website': "http://ecosoft.co.th",
    'category': 'Account',
    'version': '0.1.0',
    'depends': [
        'hr_expense_auto_invoice',
        'account_budget_activity',
        'pabi_budget_plan',
        'pabi_hr_expense',
        'pabi_utils',
    ],
    'data': [
        'data/account_data.xml',
        'data/groups.xml',
        'security/ir.model.access.csv',
        'security/security_rule.xml',
        'wizard/update_inrev_activity.xml',
        'wizard/validate_internal_charge.xml',
        'views/account_view.xml',
        'views/budget_plan_unit_view.xml',
        'views/hr_expense_view.xml',
        'views/account_budget_view.xml',
        'views/account_activity_view.xml',
        'workflow/hr_expense_workflow.xml',
    ],
    'demo': [
    ],
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
