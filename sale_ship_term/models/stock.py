# Copyright 2021-2022 Sodexis
# License OPL-1 (See LICENSE file for full copyright and licensing details).

from odoo import models, fields


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    def _get_ship_terms(self):
        res = []
        shipping_options = [('prepaid_add', 'Prepaid & Add'),
                 ('collect', 'Collect'),
                 ('free', 'Free'),
                 ('thirdparty', 'Bill 3rd party'),
                 ('cod', 'C.O.D.')]
        for option in shipping_options:
            if self.env['ir.config_parameter'].sudo().get_param(option[0]):
                res.append(option)
        return res

    shipping_term = fields.Selection(_get_ship_terms , string='Shipping Terms')
    third_party_billing_id = fields.Many2one('res.partner', string='3rd party billing')
    carrier_account = fields.Char(string='Carrier Account')
    cod_amount = fields.Float(string='C.O.D Amount', copy=False, readonly=True)

    def _add_delivery_cost_to_so(self):
        self.ensure_one()
        if self.shipping_term != 'free' and self.sale_id and self.carrier_id:
            super()._add_delivery_cost_to_so()
        add_tracking = self.env['ir.config_parameter'].sudo().get_param('sale_ship_term.add_tracking')
        carrier_price = self.carrier_price * (1.0 + (float(self.carrier_id.margin) / 100.0))
        if add_tracking and self.sale_id and self.carrier_id and self.carrier_id.invoice_policy == 'real':
            delivery_lines = self.sale_id.order_line.filtered(lambda l: l.is_delivery and l.product_id == self.carrier_id.product_id and self.carrier_tracking_ref and 'Tracking Number(s)' not in l.name)
            if not delivery_lines:
                delivery_lines = [self.sale_id._create_delivery_line(self.carrier_id, carrier_price)]
            delivery_line = delivery_lines[0]
            if self.shipping_term == 'free':
                carrier_price = 0.0
            delivery_line[0].write({
                'price_unit': carrier_price,
                # remove the estimated price from the description
                'name': self.carrier_id.with_context(lang=self.partner_id.lang).name,
            })
        delivery_lines = self.sale_id.order_line.filtered(lambda l: l.is_delivery and round(l.price_unit,2) == round(carrier_price,2) and l.product_id == self.carrier_id.product_id and 'Tracking Number(s)' not in l.name)
        delivery_line = delivery_lines[0]
        if delivery_lines and self.carrier_tracking_ref:
            if ',' in self.carrier_tracking_ref:
                delivery_line.name += ' \n(Tracking Number(s): ' + self.carrier_tracking_ref.replace(",",", ") + ')'
            else :
                delivery_line.name += ' \nTracking Number(s): ' + self.carrier_tracking_ref

    def cancel_shipment(self):
        carrier_tracking_ref = self.carrier_tracking_ref
        super().cancel_shipment()
        add_tracking = self.env['ir.config_parameter'].sudo().get_param('sale_ship_term.add_tracking')
        for picking in self:
            if carrier_tracking_ref and add_tracking and picking.sale_id:
                delivery_line = picking.sale_id.order_line.filtered(lambda l: l.is_delivery and l.product_id == picking.carrier_id.product_id and carrier_tracking_ref in l.name)
                render_context = {
                    'picking': picking,
                    'carrier_name': picking.carrier_id.name,
                    'shipping_cost': delivery_line.price_unit,
                    'tracking_number': carrier_tracking_ref,
                }
                picking.sale_id._activity_schedule_with_view('mail.mail_activity_data_warning',
                user_id=picking.sale_id.user_id.id or self.env.uid,
                views_or_xmlid='sale_ship_term.exception_shipment_cancel',
                render_context=render_context
                )