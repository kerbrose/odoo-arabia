# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 All Rights Reserved
#
# Created on Feb 27, 2017
#
# @author: kerbrose (Khaled Said)
# kerbrose  __hotmail__
###############################################

from odoo import api, models, fields

class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.model
    def _default_account_analytic_id(self):
        if self._context.get('analytic_id'):
            analytic_id = int(self._context.get('analytic_id'))
            analytic = self.env['account.analytic.account'].search([('id', '=', analytic_id)], limit=1)
            return analytic
        

    account_analytic_id = fields.Many2one('account.analytic.account',
                                          string='Analytic Account',
                                          default=_default_account_analytic_id,
                                          )
    csi_mf_id = fields.Many2one('construction.master.format',
                                string='CSI MF',
                                states={'draft': [('readonly', False)]},
                                )
    
    @api.onchange('account_analytic_id')
    def _onchange_account_analytic_id(self):
        analytic_id = self._context.get('analytic_id')
        account_analytic_id = self.env['account.analytic.account'].search([('id', '=', analytic_id)], limit=1)
        self.account_analytic_id = account_analytic_id

        

