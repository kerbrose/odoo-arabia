# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 All Rights Reserved
#
# Created on Mar 6, 2017
#
# @author: kerbrose (Khaled Said)
# kerbrose  __hotmail__
###############################################

from odoo import api, models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    property_account_payable_id = fields.Many2one('account.account', company_dependent=True,
        string="Account Payable", oldname="property_account_payable",
        domain="['|', ('internal_type', '=', 'payable'), ('internal_type', '=', 'receivable'), ('deprecated', '=', False)]",
        help="This account will be used instead of the default one as the payable account for the current partner",
        required=True)
    property_account_receivable_id = fields.Many2one('account.account', company_dependent=True,
        string="Account Receivable", oldname="property_account_receivable",
        domain="['|', ('internal_type', '=', 'payable'), ('internal_type', '=', 'receivable'), ('deprecated', '=', False)]",
        help="This account will be used instead of the default one as the receivable account for the current partner",
        required=True)