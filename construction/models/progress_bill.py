# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 All Rights Reserved
#
# Created on Mar 13, 2017
#
# @author: kerbrose (Khaled Said)
# kerbrose  __hotmail__
###############################################

import json
from lxml import etree
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.tools import float_is_zero, float_compare
from odoo.tools.misc import formatLang

from odoo.exceptions import UserError, RedirectWarning, ValidationError

import odoo.addons.decimal_precision as dp
import logging

_logger = logging.getLogger(__name__)

# mapping invoice type to journal type
TYPE2JOURNAL = {
    'out_invoice': 'sale',
    'in_invoice': 'purchase',
    'out_refund': 'sale',
    'in_refund': 'purchase',
}

# mapping invoice type to refund type
TYPE2REFUND = {
    'out_invoice': 'out_refund',        # Customer Invoice
    'in_invoice': 'in_refund',          # Vendor Bill
    'out_refund': 'out_invoice',        # Customer Refund
    'in_refund': 'in_invoice',          # Vendor Refund
}

MAGIC_COLUMNS = ('id', 'create_uid', 'create_date', 'write_uid', 'write_date')


class ProgressBill(models.Model):
    _name = 'progress.bill'
    _inherit = ['mail.thread']
    _description = "Progress Invoice"
    _order = "date desc, number desc, id desc"
    
    @api.one
    @api.depends('name')
    def _compute_amount(self):
        self.amount_untaxed = 0.0
        self.amount_tax = 0.0
        self.amount_total = 0.0
    
    @api.model
    def _default_currency(self):
        journal = self._default_journal()
        return self.env.user.company_id.currency_id
    
    amount_net = fields.Monetary(string='Current Bill Net', store=True,
                                 readonly=True, compute='_compute_amount')
    
    amount_current_to_be_paid = fields.Monetary(string='Payment', store=True,
                                                readonly=True, compute='_compute_amount')
    
    amount_previous_current_net = fields.Monetary(string='Current Bill Net', store=True,
                                                  readonly=True, compute='_compute_amount')
    
    money_retention_total = fields.Monetary(string='Total Money Retention', store=True,
                                            readonly=True, compute='_compute_amount')
    
    amount_total = fields.Monetary(string='Total', store=True,
                                   readonly=True, compute='_compute_amount')
    
    comment = fields.Text('Additional Information', readonly=True, states={'draft': [('readonly', False)]})
    
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Company Currency", readonly=True)
    
    company_id = fields.Many2one('res.company', string='Company', change_default=True,
                                 required=True, readonly=True, states={'draft': [('readonly', False)]},
                                 default=lambda self: self.env['res.company']._company_default_get())
    
    contract_id = fields.Many2one('progress.contract', string='Add Purchase Order',
                                  help='Encoding help. When selected, the associated purchase order lines are added to the vendor bill. Several PO can be selected.')
    
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  readonly=True, states={'draft': [('readonly', False)]},
                                  default=_default_currency, track_visibility='always')
    
    date = fields.Date(string='Date', copy=False,
                       help="Keep empty to use the invoice date.",
                       readonly=True, states={'draft': [('readonly', False)]})
    
    money_retention_total = fields.Monetary(string='Total Money Retention', store=True,
                                            readonly=True, compute='_compute_amount')
    
    name = fields.Char(string='Reference/Description', index=True, readonly=True,
                       states={'draft': [('readonly', False)]}, copy=False,
                       help='The name that will be used on account move lines')
    
    number = fields.Integer(string='Number', required=True, default=lambda self: self._get_default_number)
    
    origin = fields.Char(string='Source Document',
                         help="Reference of the document that produced this invoice.",
                         readonly=True, states={'draft': [('readonly', False)]})
    
    partner_id = fields.Many2one('res.partner', string='Partner', change_default=True,
                                 required=True, readonly=True, states={'draft': [('readonly', False)]},
                                 track_visibility='always')
    
    payment_penalty_total = fields.Monetary(string='Total Penalties', store=True,
                                            readonly=True, compute='_compute_amount')
    
    previous_paid_total = fields.Monetary(string='Total Previously', store=True,
                                          readonly=True, compute='_compute_amount')
    
    previous_amount_total = fields.Monetary(string='Total Amount of Previous Bill', store=True,
                                            readonly=True, compute='_compute_amount')
    
    progress_line_ids = fields.One2many('progress.bill.line', 'bill_id', string='Bill Lines',
                                        readonly=True, states={'draft': [('readonly', False)]}, copy=True)
    
    reference = fields.Char(string='Contractor Reference',
                            help="The partner reference of this invoice.",
                            readonly=True, states={'draft': [('readonly', False)]})

class ProgressBillLine(models.Model):
    _name = "progress.bill.line"
    _description = "Bill Line"
    _order = "bill_id,sequence,id"
    
    account_id = fields.Many2one('account.account', string='Account',
                                 required=True, domain=[('deprecated', '=', False)],
                                 default=_default_account,
                                 help="The income or expense account related to the selected product.")
    
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')
    
    bill_line_tax_ids = fields.Many2many('account.tax', 'account_invoice_line_tax',
                                            'invoice_line_id', 'tax_id',
                                            string='Taxes', 
                                            domain=[('type_tax_use','!=','none'), '|', ('active', '=', False), ('active', '=', True)],
                                            )
    
    company_currency_id = fields.Many2one('res.currency', related='bill_id.company_currency_id', readonly=True)
    
    company_id = fields.Many2one('res.company', string='Company', related='bill_id.company_id',
                                 store=True, readonly=True)
    
    contract_id = fields.Many2one('progress.contract', related='contract_line_id.contract_id', string='Progress Contract', store=False, readonly=True,
                                  help='Associated Purchase Order. Filled in automatically when a PO is chosen on the vendor bill.')
    
    contract_line_id = fields.Many2one('progress.contract.line', 'Progress Contract Line', ondelete='set null', index=True, readonly=True)
    
    currency_id = fields.Many2one('res.currency', related='bill_id.currency_id', store=True)
    
    name = fields.Text(string='Description', required=True)
    
    origin = fields.Char(string='Source Document',
        help="Reference of the document that produced this invoice.")
    
    bill_id = fields.Many2one('progress.bill', string='Bill Reference',
                              ondelete='cascade', index=True)
    
    discount = fields.Float(string='Discount', digits=dp.get_precision('Discount'),
                            default=0.0)
    
    partner_id = fields.Many2one('res.partner', string='Partner',
                                 related='bill_id.partner_id', store=True, readonly=True)
    
    price_subtotal = fields.Monetary(string='Amount', store=True,
                                     readonly=True, compute='_compute_price')
    
    price_subtotal_signed = fields.Monetary(string='Amount Signed', currency_field='company_currency_id',
                                            store=True, readonly=True, compute='_compute_price',
                                            help="Total amount in the currency of the company, negative for credit notes.")
    
    price_unit = fields.Float(string='Unit Price', required=True, digits=dp.get_precision('Product Price'))
    
    product_id = fields.Many2one('product.product', string='Product',
                                 domain=[('purchase_ok', '=', True), ('type', '=', 'service')],
                                 ondelete='restrict', index=True)
    
    quantity = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'),
                            required=True, default=1)
    
    sequence = fields.Integer(default=10,
                              help="Gives the sequence of this line when displaying the invoice.")
    
    uom_id = fields.Many2one('product.uom', string='Unit of Measure',
                             ondelete='set null', index=True,)
    