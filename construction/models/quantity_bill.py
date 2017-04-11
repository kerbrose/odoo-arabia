# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 All Rights Reserved
#
# Created on Apr 6, 2017
#
# @author: kerbrose (Khaled Said)
# kerbrose  __hotmail__
###############################################

from odoo import api, models, fields
import odoo.addons.decimal_precision as dp

class QuantityBill(models.Model):
    _name = 'quantity.bill'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _inherits = {'account.analytic.account' : 'project_name'}
    _description = "Bill of Quantity"
    _order = 'date desc, id desc'
    
    READONLY_STATES = {
        'confirm': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }
    
    LINES_STATES = {
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }
    
    @api.one
    @api.depends('quantity_bill_lines')
    def _compute_amounts(self):
        for line in self.quantity_bill_lines:
            self.amount_total += line.price_subtotal
    
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_compute_amounts')
    
    date = fields.Datetime('Contract Date', required=True, states=READONLY_STATES, index=True, copy=False, default=fields.Datetime.now)
    
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, states=READONLY_STATES, default=lambda self: self.env.user.company_id.id)
    
    currency_id = fields.Many2one('res.currency', 'Currency', required=True, states=READONLY_STATES,\
        default=lambda self: self.env.user.company_id.currency_id.id)
    
    project_name = fields.Many2one('account.analytic.account', required=True, ondelete='restrict')
    
    quantity_bill_lines = fields.One2many('quantity.bill.line', 'quantity_bill_id', string='BOQ Lines', states=LINES_STATES, copy=True)
    
    seq = fields.Char('BOQ Ref.', required=True, index=True, copy=False, default='New')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True, index=True, copy=False, default='draft', track_visibility='onchange')
    
    @api.multi
    def button_confirm(self):
        for boq in self:
            if boq.state != 'draft':
                continue
            if not boq.user_has_groups('construction.group_senior_engineer'):
                continue
            if boq.user_has_groups('construction.group_senior_engineer'):
                boq.write({'state': 'confirm'})
        return True
    
    @api.multi
    def button_done(self):
        for boq in self:
            if boq.user_has_groups('construction.group_senior_engineer'):
                boq.write({'state':'done'})
        return True
    
    @api.multi
    def button_draft(self):
        for boq in self:
            if boq.user_has_groups(''):
                boq.write({'state':'draft'})
        return True
    
    @api.multi
    def button_cancel(self):
        for boq in self:
            if boq.user_has_groups('construction.group_senior_engineer'):
                boq.write({'state':'cancel'})
        return True
    
    @api.model
    def create(self, vals):
        if vals.get('seq', 'New') == 'New':
            vals['seq'] = self.env['ir.sequence'].next_by_code('quantity.bill') or '/'
        return super(QuantityBill, self).create(vals)
    

class QuantityBillLines(models.Model):
    _name = "quantity.bill.line"
    _description = 'Qunatity Bill Lines'

    @api.depends('quantity', 'price_unit')
    def _compute_amount(self):
        for line in self:
            line.update({
                'price_subtotal': float(line.price_unit * line.quantity),
            })
     
    csi_mf_id = fields.Many2one('construction.master.format', string='CSI MF', required=True)
      
    currency_id = fields.Many2one(related='quantity_bill_id.currency_id', store=True, string='Currency', readonly=True)

    company_id = fields.Many2one('res.company', related='quantity_bill_id.company_id', string='Company', store=True, readonly=True)
  
    quantity_bill_id = fields.Many2one('quantity.bill', string='BOQ Ref.', index=True, required=True, ondelete='cascade')
     
    date_order = fields.Datetime(related='quantity_bill_id.date', string='Order Date', readonly=True)
    
    name = fields.Text(string='Description', required=True)
  
    price_subtotal = fields.Monetary(compute='_compute_amount', string='Total', store=True)
    
    price_unit = fields.Float(string='Unit Price', required=True)
    
    quantity = fields.Float(string='Quantity', required=True)
    
    uom_id = fields.Many2one('product.uom', string='UOM', required=True)

    progress_contract_lines = fields.One2many('progress.contract.line', 'boq_line_id', string="Service Lines", readonly=True, copy=False)
   
    purchase_order_line = fields.One2many('purchase.order.line', 'quntity_bill_line_id', readonly=True, copy=False)

    sequence = fields.Integer(string='Sequence', default=10)
    
    state = fields.Selection(related='quantity_bill_id.state', store=True)
     
    @api.multi
    def unlink(self):
        for line in self:
            if line.quantity_bill_id.state in ['confirm', 'done']:
                raise UserError(_('Cannot delete a progress contract line which is in state \'%s\'.') %(line.state,))
        return super(ProgressContractLine, self).unlink()
 


