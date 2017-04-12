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
    
    READONLY_STATES = {
        'open': [('readonly', True)],
        'approved': [('readonly', True)],
        'running': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }
    
    @api.one
    @api.depends('name')
    def _compute_amount(self):
        #self.amount_net = 0.0
        self.amount_current_to_be_paid = 0.0
        #self.amount_previous_current_net = 0.0
        #self.money_retention_total = 0.0
        #self.amount_total = 0.0
        self.previous_paid_total = 0.0
        #self.previous_amount_total = 0.0

    @api.one
    @api.depends('progress_bill_line_ids')
    def _compute_amounts(self):
        self.amount_current_total = 0.0
        self.amount_total = 0.0
        self.amount_total_penalty = 0.0
        for line in self.progress_bill_line_ids:
            self.amount_current_total += line.price_subtotal 
            self.amount_total += line.price_total
            self.amount_total_penalty += line.discount_total
            

    @api.one
    @api.depends('number', 'contract_id')
    def _compute_amount_previous_total(self):
        self.amount_previous_total = 0.0
        previous_bill_number = Int(self.number) - 1
        if previous_bill_number == 0:
            self.amount_previous_total = 0.0
        else:
            for bill in self.contract_id.progress_bill_ids:
                if bill.number == previous_bill_number:
                    self.amount_previous_total == bill.amount_total
    
    @api.one
    @api.depends('amount_current_total', 'amount_total')
    def _compute_money_retention(self):
        # TODO: need not hard code the money retention value
        self.money_retention_current = float(self.amount_current_total * 0.05)
        self.money_retention_total = float(self.amount_total * 0.05)
        
        
        
    
    
    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id
    
    account_analytic_id = fields.Many2one('account.analytic.account', string='Project', required=True, states=READONLY_STATES)
    
    account_invoice_id = fields.Many2one('account.invoice', string='bill', required=True, ondelete='restrict')
    
    amount_current_total = fields.Monetary(string='Current Bill Net', store=True, readonly=True, compute='_compute_amounts')
    
    amount_current_to_be_paid = fields.Monetary(string='Payment', store=True, readonly=True, compute='_compute_amount')
    
    amount_previous_current_net = fields.Monetary(string='Current Bill Net', store=True, readonly=True, compute='_compute_amount')
    
    amount_previous_total = fields.Monetary(string='Total Amount of Previous Bill', store=True, readonly=True, compute='_compute_amount_previous_total')
    
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_compute_amounts')
    
    amount_total_penalty = fields.Monetary(string='Penalities', store=True, readonly=True, compute='_compute_amounts')
    
    comment = fields.Text('Additional Information', readonly=True, states=READONLY_STATES)
    
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Company Currency", readonly=True)
    
    company_id = fields.Many2one('res.company', string='Company', change_default=True, required=True, readonly=True, states=READONLY_STATES,
                                 default=lambda self: self.env['res.company']._company_default_get())
    
    contract_id = fields.Many2one('progress.contract', string='Add Purchase Order')
    
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, readonly=True, states=READONLY_STATES,
                                  default=_default_currency, track_visibility='always')
    
    date = fields.Date(string='Date', copy=False, required=True, states=READONLY_STATES)
    
    final_bill = fields.Boolean(string='Final Bill')
    
    last_bill = fields.Boolean(string='Last Bill')
    
    money_retention_current = fields.Monetary(string='Money Retention', store=True, readonly=True, compute='_compute_money_retention')
    
    money_retention_total = fields.Monetary(string='Total Money Retention', store=True, readonly=True, compute='_compute_money_retention')
    
    number = fields.Integer(string='Number', required=True, states=READONLY_STATES)
    
    origin = fields.Char(string='Source Document', readonly=True, states={'draft': [('readonly', False)]})
    
    partner_id = fields.Many2one('res.partner', string='Partner', change_default=True, required=True, states=READONLY_STATES, track_visibility='always')
    
    previous_paid_total = fields.Monetary(string='Total Previously', store=True, readonly=True, compute='_compute_amount')
    
    progress_bill_line_ids = fields.One2many('progress.bill.line', 'bill_id', string='Bill Lines', readonly=True, states=READONLY_STATES, copy=True)
    
    reference = fields.Char(string='Contractor Reference', readonly=True, states=READONLY_STATES)
    
    state = fields.Selection([
            ('draft','Draft'),
            ('open', 'Confirmed'),
            ('approved', 'Approved'),
            ('running', 'Running'),
            ('done', 'Done'),
            ('cancel', 'Cancelled'),
        ], string='Status', readonly=True, index=True, copy=False, default='draft', track_visibility='onchange')
    
    
    def _prepare_progress_bill_line_from_pc_line(self, pc_line):
        qty = pc_line.product_qty - pc_line.qty_invoiced
        
        if float_compare(qty, 0.0, precision_rounding=pc_line.product_uom.rounding) <= 0:
            qty = 0.0
        
        progress_bill_line = self.env['progress.bill.line']
        data = {
            'contract_line_id': pc_line.id,
            'name': pc_line.contract_id.name+': '+pc_line.name,
            'origin': pc_line.contract_id.name,
            'product_uom': pc_line.product_uom.id,
            'product_id': pc_line.product_id.id,
            'price_unit': pc_line.contract_id.currency_id.compute(pc_line.price_unit, self.currency_id, round=False),
            'qty_accepted': pc_line.product_qty,
            'qty_previous': pc_line.qty_invoiced,
            'quantity': 0.0,
            'discount': 0.0,
            'csi_mf_id': pc_line.csi_mf_id,
        }
        return data
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('progress.bill') or '/'
        return super(ProgressBill, self.with_context(mail_create_nolog=True)).create(vals)
    
    @api.multi
    def action_generate_account_invoice(self):
        for progress_bill in self:
            AccountInvoice = self.env['account.invoice']
            journal = self.env['account.journal'].search([('code', '=', 'PRJ')], limit=1)
            invoice_vals = {'parnter_id': self.partner_id.id,
                            'account_id': self.partner_id.property_account_payable_id.id,
                            'journal_id': journal,
                            }
            invoice_lines = []
            for line in progress_bill:
                invoice_lines.append([0, False, {'account_analytic_id':progress_bill.account_analytic_id.id,
                                                 'product_id': line.product_id.id,
                                                 'csi_mf_id': line.csi_mf_id.id,
                                                 'name': line.name,
                                                 'partner_id': progress_bill.partner_id.id,
                                                 'account_id': journal.default_debit_account_id.id,
                                                 'quantity': line.quantity,
                                                 'price_unit': line.price_unit,
                                                 'uom_id': line.product_uom.id,
                                                 }])
            invoice_vals.update({'invoice_line_ids': invoice_lines})
            invoice_id = AccountInvoice.create(invoice_vals)
            action = self.env.ref('account.action_invoice_tree2')
            result = action.read()[0]
 
            result['domain'] = "[('id', '=', " + str(invoice_id.id) + ")]"
        
        return result
    
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
        self.number = self.contract_id.progress_bill_count
        return {}


class ProgressBillLine(models.Model):
    _name = "progress.bill.line"
    _description = "Bill Line"
    _order = "bill_id,sequence,id"
    
    @api.one
    @api.depends('price_unit', 'discount', 'quantity')
    def _compute_price(self):
        self.price_subtotal = float((self.price_unit * self.quantity) - self.discount)
        self.price_total = float((self.price_unit * self.qty_total) - self.discount_total - self.discount)

    @api.depends('contract_line_id')
    def _get_previous_defaults(self):
        for line in self:
            line.qty_accepted = line.contract_line_id.product_qty
            for previous_line in line.contract_line_id.progress_bill_lines:
                if previous_line.bill_id.id < line.bill_id.id and (previous_line.bill_id.state != 'cancel' or previous_line.bill_id.state != 'draft'):
                    line.qty_previous += previous_line.quantity
                    line.discount_total += previous_line.discount    
    
    bill_id = fields.Many2one('progress.bill', string='Bill Reference', ondelete='cascade', index=True)
    
    company_currency_id = fields.Many2one('res.currency', related='bill_id.company_currency_id', readonly=True)
    
    company_id = fields.Many2one('res.company', string='Company', related='bill_id.company_id', store=True, readonly=True)
    
    contract_id = fields.Many2one('progress.contract', related='contract_line_id.contract_id', string='Progress Contract', required=True, store=False, readonly=True)
    
    contract_line_id = fields.Many2one('progress.contract.line', 'Progress Contract Line', ondelete='set null', index=True, readonly=True)
    
    csi_mf_id = fields.Many2one('construction.master.format', string='CSI MF', ondelete='restrict')
    
    currency_id = fields.Many2one('res.currency', related='bill_id.currency_id', store=True)
    
    discount = fields.Float(string='Discount', digits=dp.get_precision('Discount'), default=0.0)
    
    discount_total = fields.Float(string='Total Penalties', required=True, store=True, compute='_get_previous_defaults')
    
    name = fields.Text(string='Description', required=True)
    
    origin = fields.Char(string='Source Document')
    
    partner_id = fields.Many2one('res.partner', string='Partner', related='bill_id.partner_id', store=True, readonly=True)
    
    price_subtotal = fields.Monetary(string='Current Amount', store=True, readonly=True, compute='_compute_price')
    
    price_total = fields.Monetary(string='Total Amount', store=True, readonly=True, compute='_compute_price')
    
    price_unit = fields.Float(string='Unit Price', required=True, digits=dp.get_precision('Product Price'))
    
    product_id = fields.Many2one('product.product', string='Product', domain=[('purchase_ok', '=', True), ('type', '=', 'service')],
                                 ondelete='restrict', index=True)
    
    product_uom = fields.Many2one('product.uom', string='UOM', ondelete='set null', index=True)
    
    progress_percentage = fields.Float(string='Progress Percentage', digits=(16,2))
    
    #current quantity
    quantity = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'), store=True, required=True)
    
    qty_accepted = fields.Float(string='Estimated Quantity', required=True, store=True, compute='_get_previous_defaults')
    
    qty_previous = fields.Float(string='Previous Quantity', required=True, store=True, compute='_get_previous_defaults')
    
    qty_total = fields.Float(string='Total Quantity', required=True, store=True, digits=dp.get_precision('Product Unit of Measure'))
    
    sequence = fields.Integer(default=10)
    

    @api.onchange('account_analytic_id')
    def _onchange_account_analytic_id(self):
        if not line.account_analytic_id:
            analytic_id = self.bill_id.account_analytic_id
            self.account_analytic_id = analytic_id


    @api.onchange('progress_percentage')
    def _onchange_progress_percentage(self):
        self.quantity = float((self.qty_accepted * self.progress_percentage / 100) - self.qty_previous)
        self.qty_total = float(self.qty_accepted * self.progress_percentage / 100)
        if self.quantity < 0:
            warning = {
                'title': _('Warning!'),
                'message': _('Quantity is not acceptable'),
                }
            return {'warning':warning}
    

    @api.onchange('quantity')
    def _onchange_quantity(self):
        qty_total = float(self.qty_previous + self.quantity)
        if self.qty_accepted != 0:
            self.progress_percentage = float(qty_total * 100 / self.qty_accepted)
        self.qty_total = qty_total
    

    @api.onchange('qty_total')
    def _onchange_qty_total(self):
        if self.qty_accepted != 0:
            self.progress_percentage = float((self.qty_total / self.qty_accepted) * 100 )
            self.quantity = float(self.qty_total - self.qty_previous)
            
