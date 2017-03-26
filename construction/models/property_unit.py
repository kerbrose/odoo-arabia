# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 All Rights Reserved
#
# Created on Mar 13, 2017
#
# @author: kerbrose (Khaled Said)
# kerbrose  __hotmail__
###############################################

from odoo import api, models, fields

class PropertyUnit(models.Model):
    _inherit = 'mail.thread'
    _name = 'property.unit'
    _description = 'Information about the residential units'
    _order = 'name asc'
    
    
    name = fields.Char('Name')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', 'Company')