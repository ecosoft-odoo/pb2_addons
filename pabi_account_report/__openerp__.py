# -*- coding: utf-8 -*-
{
    'name': 'NSTDA :: Accounting Reports',
    'version': '8.0.1.0.0',
    'category': 'Accounting & Finance',
    'description': """
""",
    'author': 'Kitti U.',
    'website': 'http://ecosoft.co.th',
    'depends': [
        'payment_export',
        'pabi_purchase_contract',
        'pabi_utils',
        'pabi_purchase_billing',
        'pabi_bank_statement_reconcile',
        'pabi_account',
        'pabi_th_tax_report',
        'pabi_reconcile_auto',
        'pabi_bank',
        'pabi_loan_receivable',
        'sale_invoice_plan',
        'report',
        'l10n_th_amount_text',
        'pabi_account_move_document_ref',
        'pabi_asset_management',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/menu.xml',
        'data/status_data.xml',
        'data/report_data.xml',
        'data/default_value.xml',
        'data/report_paperformat.xml',
        'xlsx_template/templates.xml',
        'xlsx_template/load_template.xml',
        # Payable Reports
        'reports/report_account_common.xml',
        'reports/xlsx_report_input_tax.xml',
        'reports/xlsx_report_partner_detail.xml',
        'reports/xlsx_report_pit_detail.xml',
        'reports/xlsx_report_advance_status.xml',
        'reports/xlsx_report_cheque_register.xml',
        'reports/xlsx_report_contract_collateral.xml',
        'reports/xlsx_report_advance_payment.xml',
        'reports/xlsx_report_payable_detail.xml',
        'reports/xlsx_report_payable_balance.xml',
        'reports/xlsx_report_purchase_billing.xml',
        'reports/xlsx_report_sla_supplier.xml',
        'reports/xlsx_report_sla_employee.xml',
        'reports/xlsx_report_sla_procurement.xml',
        'reports/xlsx_report_supplier_receipt_follow_up.xml',
        'reports/qweb_report_payable_confirmation_letter_template.xml',
        'reports/qweb_report_payable_confirmation_letter.xml',
        'reports/xlsx_report_purchase_invoice_plan.xml',
        #'reports/xlsx_report_purchase_no_invoice_plan.xml',
        # Receivable Reports
        'reports/xlsx_report_output_tax.xml',
        'reports/xlsx_report_cd_receivable_confirmation.xml',
        'reports/xlsx_report_cd_receivable_planning.xml',
        'reports/xlsx_report_sla_receipt.xml',
        'reports/xlsx_report_cd_receivable_balance_sheet_summary.xml',
        'reports/xlsx_report_cd_receivable_balance_sheet_detail.xml',
        'reports/xlsx_report_tax_exemption_receipt.xml',
        'reports/xlsx_report_receivable_before_due.xml',
        'reports/xlsx_report_receivable_detail.xml',
        'reports/xlsx_report_registrar_of_guarantee.xml',
        'reports/jasper_report_cd_receivable_payment_history.xml',
        'reports/jasper_report_cd_receivable_follow_up.xml',
        'reports/qweb_report_receivable_confirmation_letter_template.xml',
        'reports/qweb_report_receivable_confirmation_letter.xml',
        # GL Reports
        'reports/xlsx_report_expense_ledger.xml',
        'reports/xlsx_report_revenue_ledger.xml',
        'reports/xlsx_report_gl_allowance_doubtful_accounts.xml',
        # 'reports/xlsx_report_gl_expenditure.xml',
        'reports/xlsx_report_gl_project.xml',
        # Asset Reports
        'reports/asset_repair_report.xml',
        'reports/asset_register_report.xml',
        'reports/asset_estimate_report.xml',
        # PND Reports
        'reports/xlsx_report_pnd1.xml',
        #Preprint Receipt
        'reports/xlsx_report_preprint_receipt.xml',
        'reports/xlsx_report_pabi_employee_advance_report.xml',
        'reports/xlsx_report_cgd.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
