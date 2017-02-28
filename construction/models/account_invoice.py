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
from odoo.exceptions import UserError

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    
    analytic_id = fields.Many2one('account.analytic.account', string='Project',
                                       required=True, states={'draft': [('readonly', False)]},
                                       )


    @api.multi
    def line_get_convert(self, line, part):
        line_id = line.get('invl_id', False)
        line_value = super(AccountInvoice, self).line_get_convert(line, part)
        line_value['csi_mf_id'] = self.env['account.invoice.line'].browse(line_id).csi_mf_id.id
        return line_value