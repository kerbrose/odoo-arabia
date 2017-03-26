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

class ProgressBill(models.Model):
    _name = 'progress.bill'
    _inherit = 'account.invoice'
    _description = "Progress Bill"
    _order = "date_invoice desc, number desc, id desc"
    
    
    invoice_line_ids = fields.One2many('progress.bill.line',
                                       'invoice_id',
                                       string='Invoice Lines',
                                       oldname='invoice_line',
                                       readonly=True,
                                       states={'draft': [('readonly', False)]},
                                       copy=True,
                                       )
    number_default = fields.Integer(string="Number", default=1)


    
