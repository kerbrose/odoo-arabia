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

class ProgressBillLine(models.Model):
    _inherit = 'account.invoice.line'
    _name = 'progress.bill.line'
    _description = 'Progress Bill Line'
    _order = "progress_bill_id,sequence,id"
    
    
    csi_mf_id = fields.Many2one('construction.master.format',
                                string='CSI MF',
                                states={'draft': [('readonly', False)]},
                                )
    invoice_id = fields.Many2one('progress.bill',
                                 string='Invoice Reference',
                                 ondelete='cascade',
                                 index=True
                                 )
    previous_pbl_id = fields.Many2one('progress.bill.line',
                                      string='Origin Line',
                                      ondelete='restrict',
                                      readonly=True,
                                      index=True,
                                      )

    quantity = fields.Float(string='Quantity',
                            digits=dp.get_precision('Product Unit of Measure'),
                            required=True,
                            default=0)
    quantity_previous = fields.Float(string='Previous Quantity',
                                     store=True,
                                     readonly=True,
                                     compute='_get_previous_quantity'
                                     )
    quantity_total = fields.Float(string='Quantity',
                                  digits=dp.get_precision('Product Unit of Measure'),
                            required=True,
                            default=1)
    
    @api.one
    @api.depends('previous_pbl_id')
    def _get_previous_quantity(self):
        self.quantity_previous = self.previous_pbl_id.quntity_total
        
    @api.onchange('quantity')
    def _onchange_quantity(self):
        self.quantity_total = self.quantity_previous + self.quantity

    @api.onchange('quantity_total')
    def _onchange_quantity_total(self):
        self.quantity = self.quantity_total - self.quantity_previous
    


    def _set_additional_fields(self, invoice):
        """ Some modules, such as Purchase, provide a feature to add automatically pre-filled
            invoice lines. However, these modules might not be aware of extra fields which are
            added by extensions of the accounting module.
            This method is intended to be overridden by these extensions, so that any new field can
            easily be auto-filled as well.
            :param invoice : account.invoice corresponding record
            :rtype line : account.invoice.line record
        """
        pass
