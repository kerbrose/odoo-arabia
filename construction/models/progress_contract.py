# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 All Rights Reserved
#
# Created on Mar 14, 2017
#
# @author: kerbrose (Khaled Said)
# kerbrose  __hotmail__
###############################################

from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_is_zero, float_compare
from odoo.exceptions import UserError, AccessError
from odoo.tools.misc import formatLang
from odoo.addons.base.res.res_partner import WARNING_MESSAGE, WARNING_HELP
import odoo.addons.decimal_precision as dp

class ProgressContract(models.Model):
    _name = 'progress.contract'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = "Progress Contract"
    _order = 'date_order desc, id desc'
    
    READONLY_STATES = {
        'confirm': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }
    
    @api.depends('contract_line.price_subtotal')
    def _amount_all(self):
        for contract in self:
            amount_total = 0.0
            for line in contract.contract_line:
                amount_total += line.price_subtotal 
            contract.update({
                'amount_total': amount_total,
            })
    
    account_analytic_id = analytic_id = fields.Many2one('account.analytic.account',
                                  string='Project',
                                  states=READONLY_STATES,
                                  )
    
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all')
    
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, states=READONLY_STATES, default=lambda self: self.env.user.company_id.id)
    
    contract_line = fields.One2many('progress.contract.line', 'contract_id', string='Contract Lines', states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True)
    
    currency_id = fields.Many2one('res.currency', 'Currency', required=True, states=READONLY_STATES,\
        default=lambda self: self.env.user.company_id.currency_id.id)
    
    date_order = fields.Datetime('Contract Date', required=True, states=READONLY_STATES, index=True, copy=False, default=fields.Datetime.now)
    
    name = fields.Char('Contract Reference', required=True, index=True, copy=False, default='New')
    
    notes = fields.Text('Terms and Conditions')
    
    origin = fields.Char('Source Document', copy=False)
    
    partner_id = fields.Many2one('res.partner', string='Contractor', required=True, states=READONLY_STATES, change_default=True, track_visibility='always')
    
    partner_ref = fields.Char('Contractor Reference', copy=False,)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True, index=True, copy=False, default='draft', track_visibility='onchange')
    
    
    @api.multi
    def button_cancel(self):
        for contract in self:
#             for inv in order.invoice_ids:
#                 if inv and inv.state not in ('cancel', 'draft'):
#                     raise UserError(_("Unable to cancel this purchase order. You must first cancel related vendor bills."))
            if contract.state in ['draft']:
                return True
            if contract.user_has_groups('construction.group_senior_engineer'):
                self.write({'state': 'cancel'})
        return True

    
    @api.multi
    def button_confirm(self):
        for contract in self:
            if contract.state not in ['draft']:
                continue
            if not contract.user_has_groups('construction.group_senior_engineer'):
                continue
            if contract.user_has_groups('construction.group_senior_engineer'):
                contract.write({'state': 'confirm'})
        return True
    
    
    @api.multi
    def button_done(self):
        self.write({'state': 'done'})
        
    
    @api.multi
    def button_draft(self):
        self.write({'state': 'draft'})
        return {}
    
    @api.multi
    def button_unlock(self):
        self.write({'state': 'confirm'})
        
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('progress.contract') or '/'
        return super(ProgressContract, self).create(vals)
    
class ProgressContractLine(models.Model):
    _name = 'progress.contract.line'
    _description = 'Progress Contract Line'
    
    READONLY_STATES = {
        'confirm': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }
    
    @api.depends('product_qty', 'price_unit')
    def _compute_amount(self):
        for line in self:
            line.update({
                'price_subtotal': (line.price_unit * line.product_qty),
            })
    
    @api.depends('invoice_lines.invoice_id.state')
    def _compute_qty_invoiced(self):
        for line in self:
            qty = 0.0
#             for inv_line in line.invoice_lines:
#                 if inv_line.invoice_id.state not in ['cancel']:
#                     qty += inv_line.uom_id._compute_quantity(inv_line.quantity, line.product_uom)
            line.qty_invoiced = qty
    
    @api.depends('contract_id.state')
    def _compute_qty_received(self):
        for line in self:
            line.qty_received = 0.0
#             if line.order_id.state not in ['purchase', 'done']:
#                 line.qty_received = 0.0
#                 continue
#             if line.product_id.type not in ['consu', 'product']:
#                 line.qty_received = line.product_qty
#                 continue
#             total = 0.0
#             for move in line.move_ids:
#                 if move.state == 'done':
#                     if move.product_uom != line.product_uom:
#                         total += move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom)
#                     else:
#                         total += move.product_uom_qty
#             line.qty_received = total

    
    account_analytic_id = fields.Many2one('account.analytic.account', string='Project')
    
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')
    
    csi_mf_id = fields.Many2one('construction.master.format',
                                string='CSI MF',
                                states=READONLY_STATES,
                                )
    
    currency_id = fields.Many2one(related='contract_id.currency_id', store=True, string='Currency', readonly=True)
    
    company_id = fields.Many2one('res.company', related='contract_id.company_id', string='Company', store=True, readonly=True)
        
    contract_id = fields.Many2one('progress.contract', string='Contract Reference', index=True, required=True, ondelete='cascade')
    
    date_order = fields.Datetime(related='contract_id.date_order', string='Order Date', readonly=True)
    
    date_planned = fields.Datetime(string='Scheduled Date', required=True, index=True)
    
    #invoice_lines = fields.One2many('account.invoice.line', 'progress_line_id', string="Bill Lines", readonly=True, copy=False)
    
    name = fields.Text(string='Description', required=True)
    
    partner_id = fields.Many2one('res.partner', related='contract_id.partner_id', string='Partner', readonly=True, store=True)
    
    price_subtotal = fields.Monetary(compute='_compute_amount', string='Total', store=True)
    
    price_unit = fields.Float(string='Unit Price', required=True, digits=dp.get_precision('Product Price'))
    
    product_id = fields.Many2one('product.product', string='Product', domain=[('purchase_ok', '=', True), ('type', '=', 'service')], change_default=True, required=True)
    
    product_qty = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True)
    
    product_uom = fields.Many2one('product.uom', string='Product Unit of Measure', required=True)

    # Replace by invoiced Qty
    #qty_invoiced = fields.Float(compute='_compute_qty_invoiced', string="Billed Qty", store=True)
    
    #qty_received = fields.Float(compute='_compute_qty_received', string="Received Qty", store=True)
        
    sequence = fields.Integer(string='Sequence', default=10)
    
    state = fields.Selection(related='contract_id.state', store=True)
    
    @api.model
    def _get_date_planned(self, seller, pc=False):
        """Return the datetime value to use as Schedule Date (``date_planned``) for
           PC Lines that correspond to the given product.seller_ids,
           when ordered at `date_order_str`.

           :param browse_record | False product: product.product, used to
               determine delivery delay thanks to the selected seller field (if False, default delay = 0)
           :param browse_record | False po: purchase.order, necessary only if
               the PO line is not yet attached to a PO.
           :rtype: datetime
           :return: desired Schedule Date for the PO line
        """
        date_order = pc.date_order if pc else self.contract_id.date_order
        if date_order:
            return datetime.strptime(date_order, DEFAULT_SERVER_DATETIME_FORMAT) + relativedelta(days=seller.delay if seller else 0)
        else:
            return datetime.today() + relativedelta(days=seller.delay if seller else 0)
    @api.onchange('product_id')
    def _onchange_product_id(self):
        result = {}
        if not self.product_id:
            return result

        # Reset date, price and quantity since _onchange_quantity will provide default values
        self.date_planned = datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        self.price_unit = self.product_qty = 0.0
        self.product_uom = self.product_id.uom_po_id or self.product_id.uom_id
        result['domain'] = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}

        product_lang = self.product_id.with_context({
            'lang': self.partner_id.lang,
            'partner_id': self.partner_id.id,
        })
        self.name = product_lang.display_name
        if product_lang.description_purchase:
            self.name += '\n' + product_lang.description_purchase

        if self.env.uid == SUPERUSER_ID:
            company_id = self.env.user.company_id.id

        self._onchange_quantity()

        return result
    
    @api.onchange('product_id')
    def _onchange_product_id_warning(self):
        if not self.product_id:
            return
        warning = {}
        title = False
        message = False

        product_info = self.product_id

        if product_info.purchase_line_warn != 'no-message':
            title = _("Warning for %s") % product_info.name
            message = product_info.purchase_line_warn_msg
            warning['title'] = title
            warning['message'] = message
            if product_info.purchase_line_warn == 'block':
                self.product_id = False
            return {'warning': warning}
        return {}

    @api.onchange('product_qty')
    def _onchange_product_qty(self):
        if (self.state == 'confirm') and self.product_id.type in ['consu'] and self.product_qty < self._origin.product_qty:
            warning_mess = {
                'title': _('Ordered quantity decreased!'),
                'message' : _('You are decreasing the ordered quantity!\nYou must update the quantities on the reception and/or bills.'),
            }
            return {'warning': warning_mess}
        
    @api.onchange('product_qty', 'product_uom')
    def _onchange_quantity(self):
        if not self.product_id:
            return

        seller = self.product_id._select_seller(
            partner_id=self.partner_id,
            quantity=self.product_qty,
            date=self.contract_id.date_order and self.contract_id.date_order[:10],
            uom_id=self.product_uom)

        if seller or not self.date_planned:
            self.date_planned = self._get_date_planned(seller).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        if not seller:
            return

        price_unit = 0.0
        if price_unit and seller and self.contract_id.currency_id and seller.currency_id != self.contract_id.currency_id:
            price_unit = seller.currency_id.compute(price_unit, self.contract_id.currency_id)

        if seller and self.product_uom and seller.product_uom != self.product_uom:
            price_unit = seller.product_uom._compute_price(price_unit, self.product_uom)

        self.price_unit = price_unit


    
    def _suggest_quantity(self):
        '''
        Suggest a minimal quantity based on the seller
        '''
        if not self.product_id:
            return

        seller_min_qty = self.product_id.seller_ids\
            .filtered(lambda r: r.name == self.contract_id.partner_id)\
            .sorted(key=lambda r: r.min_qty)
        if seller_min_qty:
            self.product_qty = seller_min_qty[0].min_qty or 1.0
            self.product_uom = seller_min_qty[0].product_uom
        else:
            self.product_qty = 1.0
    
    @api.multi
    def unlink(self):
        for line in self:
            if line.contract_id.state in ['confirm', 'done']:
                raise UserError(_('Cannot delete a progress contract line which is in state \'%s\'.') %(line.state,))
        return super(ProgressContractLine, self).unlink()



