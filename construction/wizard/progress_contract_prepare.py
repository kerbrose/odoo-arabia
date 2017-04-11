# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 All Rights Reserved
#
# Created on Apr 9, 2017
#
# @author: kerbrose (Khaled Said)
# kerbrose  __hotmail__
###############################################

from odoo import api, fields, models
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class ProgressContractPrepare(models.TransientModel):
    _name = 'progress.contract.prepare'
    _description = "Prepare progress contracts from bill of quantity"
    
    @api.model
    def default_get(self, fields):
        res = super(ProgressContractPrepare, self).default_get(fields)
        active_id = self.env.context.get('active_id')
        if self.env.context.get('active_model') == 'quantity.bill' and active_id:
            res['boq_id'] = active_id
        return res
    
    boq_id = fields.Many2one('quantity.bill', string="Bill of Quantity")
    
    csi_target = fields.Many2one('construction.master.format', string="CSI", required=True,)
    
    partner_id = fields.Many2one('res.partner', string='Contractor', required=True,)
    
    
    @api.multi
    def generate_progress_contract(self):
        for wizard in self:
            PROGRESSCONTRACT = self.env['progress.contract']
            lines = wizard.boq_id.quantity_bill_lines.filtered(lambda x: x.csi_mf_id == wizard.csi_target)
            contract_lines = []
            date_planned = datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            for line in lines:
                contract_lines.append([0, False, {'account_analytic_id':wizard.boq_id.project_name.id,
                                                  'boq_line_id': line.id,
                                                  'csi_mf_id': line.csi_mf_id.id,
                                                  'name': line.name,
                                                  'partner_id': wizard.partner_id.id,
                                                  'product_qty': line.quantity,
                                                  'price_unit': line.price_unit,
                                                  'product_uom': line.uom_id.id,
                                                  'date_planned': date_planned,
                                                  }]) 
            progress_contract = {
                'partner_id': wizard.partner_id.id,
                'account_analytic_id': wizard.boq_id.project_name.id,
                'contract_line': contract_lines,
                }
            contract = PROGRESSCONTRACT.create(progress_contract)
            action = self.env.ref('construction.contract_progress_bill_action')
            result = action.read()[0]
            result['active_model'] = 'progress.contract'
            result['res_model'] = 'progress.contract'
            result['domain'] = "[('id', '=', " + str(contract.id) + ")]"
        return result


