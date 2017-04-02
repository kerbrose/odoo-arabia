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


class ProgressBill(models.Model):
    _name = 'progress.bill'
    _inherit = ['mail.thread']
    _description = "Progress Invoice"
    _order = "date desc, number desc, id desc"
    
    @api.one
    @api.depends('name')
    def _compute_amount(self):
        self.amount_net = 0.0
        self.amount_current_to_be_paid = 0.0
        self.amount_previous_current_net = 0.0
        self.money_retention_total = 0.0
        self.amount_total = 0.0
        self.payment_penalty_total = 0.0
        self.previous_paid_total = 0.0
        self.previous_amount_total = 0.0

#     @api.model
#     def default_get(self, vals):
#         result = super(ProgressBill, self).default_get(vals)
#         if self._context.get('default_contract_id'):
#             contract_id = int(self._context.get('default_contract_id'))
#             result.update({'contract_id': contract_id})
#         return result
        
    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id
    
    account_analytic_id = fields.Many2one('account.analytic.account', string='Project', required=True)
    
    amount_net = fields.Monetary(string='Current Bill Net', store=True,
                                 readonly=True, compute='_compute_amount')
    
    amount_current_to_be_paid = fields.Monetary(string='Payment', store=True,
                                                readonly=True, compute='_compute_amount')
    
    amount_previous_current_net = fields.Monetary(string='Current Bill Net', store=True,
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
    
    final_bill = fields.Boolean(string='Final Bill')
    
    last_bill = fields.Boolean(string='Last Bill')
    
    money_retention_total = fields.Monetary(string='Total Money Retention', store=True,
                                            readonly=True, compute='_compute_amount')
    
    name = fields.Char(string='Reference/Description', index=True, readonly=True,
                       states={'draft': [('readonly', False)]}, copy=False,
                       help='The name that will be used on account move lines')
    
    number = fields.Integer(string='Number', required=True, default=lambda self: self._get_default_number(),
                            readonly=True, states={'draft':[('readonly', False)]})
    
    origin = fields.Char(string='Source Document',
                         help="Reference of the document that produced this bill.",
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
    
    progress_bill_line_ids = fields.One2many('progress.bill.line', 'bill_id', string='Bill Lines',
                                        readonly=True, states={'draft': [('readonly', False)]}, copy=True)
    
    reference = fields.Char(string='Contractor Reference',
                            help="The partner reference of this invoice.",
                            readonly=True, states={'draft': [('readonly', False)]})
    
    state = fields.Selection([
            ('draft','Draft'),
            ('open', 'Confirmed'),
            ('approved', 'Approved'),
            ('running', 'Running'),
            ('done', 'Done'),
            ('cancel', 'Cancelled'),
        ], string='Status', index=True, readonly=True, default='draft',
        track_visibility='onchange', copy=False,
        help=" * The 'Draft' status is used when a user is creating a new and unconfirmed Invoice.\n"
             " * The 'Confirmed' status is used when the progress bill is approved by the engineers.\n"
             " * The 'Approved' status is used when it gets approved by Financial Department.\n"
             " * The 'Running' status is used when it is still in progress.\n"
             " * The 'done' status is set automatically when the final progress bill initiated.\n"
             " * The 'Cancelled' status is used when user cancel invoice.")
    
    @api.model
    def _get_default_number(self):
        """Return the progress bill number."""
        print self
        if not self.contract_id:
            return 1
        if self.contract_id:
            return self.contract_id.progress_bill_count + 1
    
    def _prepare_progress_bill_line_from_pc_line(self, pc_line):
        qty = pc_line.product_qty - pc_line.qty_invoiced
        
        if float_compare(qty, 0.0, precision_rounding=pc_line.product_uom.rounding) <= 0:
            qty = 0.0
        
        progress_bill_line = self.env['progress.bill.line']
        data = {
            'contract_line_id': pc_line.id,
            'name': pc_line.contract_id.name+': '+pc_line.name,
            'origin': pc_line.contract_id.origin,
            'product_uom': pc_line.product_uom.id,
            'product_id': pc_line.product_id.id,
            'price_unit': pc_line.contract_id.currency_id.compute(pc_line.price_unit, self.currency_id, round=False),
            'quantity': qty,
            'discount': 0.0,
            'csi_mf_id': pc_line.csi_mf_id,
        }
        return data
    
    @api.model
    def create(self, vals):
        print vals
        progress_bill = super(ProgressBill, self.with_context(mail_create_nolog=True)).create(vals)
        return invoice
    
    # Load all unsold PC lines
    @api.onchange('contract_id')
    def progress_bill_change(self):
        if not self.contract_id:
            return {}
        if not self.partner_id:
            self.partner_id = self.contract_id.partner_id.id
            self.account_analytic_id = self.contract_id.account_analytic_id

        new_lines = self.env['progress.bill.line']
        for line in self.contract_id.contract_line:
            # Load a PC line only once
            if line in self.progress_bill_line_ids.mapped('contract_line_id'):
                continue
            data = self._prepare_progress_bill_line_from_pc_line(line)
            new_line = new_lines.new(data)
            new_lines += new_line

        self.progress_bill_line_ids += new_lines
        if not self.origin:
            self.origin = ''
        self.origin += self.contract_id.name
        self.contract_id = False
        return {}


class ProgressBillLine(models.Model):
    _name = "progress.bill.line"
    _description = "Bill Line"
    _order = "bill_id,sequence,id"
    
    @api.one
    @api.depends('price_unit', 'discount', 'quantity')
    def _compute_price(self):
        price_subtotal = (self.price_unit * self.quantity) - self.discount
        self.price_subtotal = price_subtotal
    
    @api.one
    @api.depends('progress_percentage')
    def _compute_quantity(self):
        qty_total = (self.progress_percentage * self.qty_accepted)/100
        self.qty_total = qty_total
        self.quantity = qty_total - self.qty_previous
    

    @api.depends('contract_line_id')
    def _get_estimated_quantity(self):
        for line in self:
            line.qty_accepted = line.contract_line_id.product_qty
            
    @api.depends('contract_line_id')
    def _get_previous_quantity(self):
        for line in self:
            line.qty_previous = line.contract_line_id.qty_invoiced
    
    bill_id = fields.Many2one('progress.bill', string='Bill Reference',
                              ondelete='cascade', index=True)
    
    company_currency_id = fields.Many2one('res.currency', related='bill_id.company_currency_id', readonly=True)
    
    company_id = fields.Many2one('res.company', string='Company', related='bill_id.company_id',
                                 store=True, readonly=True)
    
    contract_id = fields.Many2one('progress.contract', related='contract_line_id.contract_id', string='Progress Contract', store=False, readonly=True,
                                  help='Associated Purchase Order. Filled in automatically when a PO is chosen on the vendor bill.')
    
    contract_line_id = fields.Many2one('progress.contract.line', 'Progress Contract Line', ondelete='set null', index=True, readonly=True)
    
    csi_mf_id = fields.Many2one('construction.master.format',
                                string='CSI MF',
                                ondelete='restrict',
                                )
    
    currency_id = fields.Many2one('res.currency', related='bill_id.currency_id', store=True)
    
    discount = fields.Float(string='Discount', digits=dp.get_precision('Discount'),
                            default=0.0)
    
    name = fields.Text(string='Description', required=True)
    
    origin = fields.Char(string='Source Document',
                         help="Reference of the document that produced this invoice.")
    
    partner_id = fields.Many2one('res.partner', string='Partner',
                                 related='bill_id.partner_id', store=True, readonly=True)
    
    price_subtotal = fields.Monetary(string='Amount', store=True,
                                     readonly=True, compute='_compute_price')
    
    price_unit = fields.Float(string='Unit Price', required=True, digits=dp.get_precision('Product Price'))
    
    product_id = fields.Many2one('product.product', string='Product',
                                 domain=[('purchase_ok', '=', True), ('type', '=', 'service')],
                                 ondelete='restrict', index=True)
    
    product_uom = fields.Many2one('product.uom', string='UOM',
                                  ondelete='set null', index=True,)
    
    progress_percentage = fields.Float(string='Progress Percentage', digits=(16,2))
    
    #current quantity
    quantity = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'),
                            required=True, compute='_compute_quantity')
    
    qty_accepted = fields.Float(string='Estimated Quantity', store=True, required=True,
                                compute='_get_estimated_quantity'
                                )
    
    qty_previous = fields.Float(string='Previous Quantity', required=True,
                                store=True, compute='_get_previous_quantity'
                                )
    
    qty_total = fields.Float(string='Total Quantity', digits=dp.get_precision('Product Unit of Measure'),
                             required=True, compute='_compute_quantity',
                             )
    
    sequence = fields.Integer(default=10,
                              help="Gives the sequence of this line when displaying the invoice.")
    

    @api.onchange('account_analytic_id')
    def _onchange_account_analytic_id(self):
        for line in self:
            if not line.account_analytic_id:
                analytic_id = self.bill_id.account_analytic_id
                self.account_analytic_id = analytic_id
    