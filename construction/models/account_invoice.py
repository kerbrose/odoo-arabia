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

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    
    analytic_id = fields.Many2one('account.analytic.account', string='Project',
                                       required=True, states={'draft': [('readonly', False)]},
                                       )

