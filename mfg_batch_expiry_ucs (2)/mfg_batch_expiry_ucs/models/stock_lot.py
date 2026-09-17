# -*- coding: utf-8 -*-
from odoo import api, fields, models
import datetime

class StockLot(models.Model):
    _inherit = 'stock.lot'

    x_studio_manufacturing_date = fields.Date(string="Manufacturing Date")
    x_studio_bulk_manufacturer = fields.Many2one('res.partner', string="Manufacturer")

    @api.depends('x_studio_manufacturing_date', 'product_id')
    def _compute_expiration_date(self):
        lots_with_mfg = self.filtered(lambda l: l.x_studio_manufacturing_date and l.product_id.use_expiration_date)
        lots_without_mfg = self - lots_with_mfg
        
        for lot in lots_with_mfg:
            duration = lot.product_id.product_tmpl_id.expiration_time or 0
            mfg_datetime = fields.Datetime.to_datetime(lot.x_studio_manufacturing_date)
            lot.expiration_date = mfg_datetime + datetime.timedelta(days=duration)
            
        if lots_without_mfg:
            super(StockLot, lots_without_mfg)._compute_expiration_date()

    def write(self, vals):
        res = super(StockLot, self).write(vals)
        if 'x_studio_manufacturing_date' in vals or 'expiration_date' in vals:
            for lot in self:
                productions = self.env['mrp.production'].search([('lot_producing_id', '=', lot.id)])
                for prod in productions:
                    prod_vals = {}
                    if 'x_studio_manufacturing_date' in vals:
                        prod_vals['x_studio_manufacturing_date'] = vals['x_studio_manufacturing_date']
                    if 'expiration_date' in vals:
                        # Convert datetime to date for x_studio_bulk_lotserial_date
                        expiry = vals['expiration_date']
                        if expiry:
                            prod_vals['x_studio_bulk_lotserial_date'] = fields.Datetime.to_datetime(expiry).date()
                        else:
                            prod_vals['x_studio_bulk_lotserial_date'] = False
                    prod_vals = {k: v for k, v in prod_vals.items() if prod[k] != v}
                    if prod_vals:
                        prod.write(prod_vals)
        return res
