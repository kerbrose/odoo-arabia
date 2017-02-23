# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 All Rights Reserved
#
# Created on Feb 23, 2017
#
# @author: kerbrose (Khaled Said)
# kerbrose  __hotmail__
###############################################
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
    
    description = fields.Text('Description')
    
    name = fields.Char('CSI Format', translate=True)
    
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


    @api.multi
    def name_get(self):
        """ Return the categories' display name, including their direct
            parent by default.

            If ``context['partner_category_display']`` is ``'short'``, the short
            version of the category name (without the direct parent) is used.
            The default is the long version.
        """
        if self._context.get('csi_format_display') == 'short':
            return super(ConstructionMasterFormat, self).name_get()

        res = []
        for csi_format in self:
            names = []
            current = csi_format
            while current:
                names.append(current.name)
                current = current.parent_id
            res.append((csi_format.id, ' / '.join(reversed(names))))
        return res


    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            # Be sure name_search is symetric to name_get
            name = name.split(' / ')[-1]
            args = [('name', operator, name)] + args
        return self.search(args, limit=limit).name_get()
