# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 All Rights Reserved
#
# Created on Mar 19, 2017
#
# @author: kerbrose (Khaled Said)
# kerbrose  __hotmail__
###############################################

from odoo import api, models, fields

class ProgressContractLine(models.Model):
    _name = 'progress.contract.line'
    _inherit = 'purchase.order.line'
    _description = 'Progress Contract Line'
    
    order_id = fields.Many2one('progress.contract', string='Order Reference', index=True, required=True, ondelete='cascade')