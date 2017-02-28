# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 All Rights Reserved
#
# Created on Feb 28, 2017
#
# @author: kerbrose (Khaled Said)
# kerbrose  __hotmail__
###############################################

from odoo import api, models, fields

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    
    csi_mf_id = fields.Many2one('construction.master.format',
                                string='CSI MF',
                                required=False,
                                )