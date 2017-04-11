# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 All Rights Reserved
#
# Created on Apr 5, 2017
#
# @author: kerbrose (Khaled Said)
# kerbrose  __hotmail__
###############################################

from odoo import api, models, fields

import odoo.addons.decimal_precision as dp

class ProgressInvoice(models.Model):
    _name = 'progress.invoice'
    _inherit = ['mail.thread']
    _inherits = {'account.invoice': 'account_invoice_id'}
    _description = "Progress Invoice"
    _order = "date desc, number desc, id desc"
    
    READONLY_STATES = {
        'open': [('readonly', True)],
        'approved': [('readonly', True)],
        'running': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }
    
    @api.model
    def _default_journal(self):
        company_id = self._context.get('company_id', self.env.user.company_id.id)
        domain = [
            ('type', '=', 'purchase'),
            ('company_id', '=', company_id),
        ]
        return self.env['account.journal'].search(domain, limit=1)
    
    account_invoice_id = fields.Many2one('account.invoice', required=True, ondelete='restrict')
    
    journal_id = fields.Many2one('account.journal', string='Journal', required=True, readonly=True,
                                 states=READONLY_STATES, default=_default_journal, domain="[('type', 'in', 'purchase'")
    
    number = fields.Integer(string='Number', required=True, states=READONLY_STATES)
    
    progress_invoice_line_ids = fields.One2many('progress.invoice.line', 'bill_id', string='Bill Lines', readonly=True, states=READONLY_STATES, copy=True)
    
    state = fields.Selection([
            ('draft','Draft'),
            ('open', 'Confirmed'),
            ('approved', 'Approved'),
            ('running', 'Running'),
            ('done', 'Done'),
            ('cancel', 'Cancelled'),
        ], string='Status', readonly=True, index=True, copy=False, default='draft', track_visibility='onchange')
    
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('progress.invoice') or '/'
        return super(ProgressInvoice, self.with_context(mail_create_nolog=True)).create(vals)

