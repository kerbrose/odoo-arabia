# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 All Rights Reserved
#
# Created on Feb 20, 2017
#
# @author: kerbrose (Khaled Said)
# @contact: kerbrose  ==> hotmail  ==> com
#####################################

from odoo import api, models, fields

class ConstructionMasterFormat(models.Model):
    _name = 'construction.master.format'
    _parent_store = True
    
    child_ids = fields.One2many('construction.master.format',
                                'parent_id',
                                string = 'Child Categories')
    
    name = fields.Char('CSI Format')
    
    parent_id = fields.Many2one('construction.master.format',
                                string = 'Parent Category',
                                ondelete = 'restrict',
                                index = True
                                )
    
    parent_left = fields.Integer(index = True)
    
    parent_right = fields.Integer(index = True)
    
    @api.constrains('parent_id')
    def _check_hierarchy(self):
        if not self._check_recursion():
            raise models.ValidationError('Error! You cannot create recursive categories.')