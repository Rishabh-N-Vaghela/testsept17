# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import datetime

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    # Set default to today's date so it is never empty on new MOs
    x_studio_manufacturing_date = fields.Date(
        string="Manufacturing Date",
        default=fields.Date.context_today
    )
    x_studio_bulk_lotserial_date = fields.Date(string="Bulk Expiry Date")

    @api.onchange('x_studio_manufacturing_date')
    def _onchange_manufacturing_date(self):
        if self.x_studio_manufacturing_date and self.product_id.use_expiration_date and self.product_id.expiration_time:
            self.x_studio_bulk_lotserial_date = self.x_studio_manufacturing_date + datetime.timedelta(days=self.product_id.expiration_time)

    @api.onchange('lot_producing_id')
    def _onchange_lot_producing_id(self):
        if self.lot_producing_id:
            self.x_studio_manufacturing_date = self.lot_producing_id.x_studio_manufacturing_date
            self.x_studio_bulk_lotserial_date = self.lot_producing_id.expiration_date.date() if self.lot_producing_id.expiration_date else False

    def _prepare_stock_lot_values(self):
        vals = super(MrpProduction, self)._prepare_stock_lot_values()
        earliest_expiry = False
        for move in self.move_raw_ids:
            for line in move.move_line_ids:
                if line.lot_id and line.lot_id.expiration_date:
                    if not earliest_expiry or line.lot_id.expiration_date < earliest_expiry:
                        earliest_expiry = line.lot_id.expiration_date
        if earliest_expiry:
            vals['name'] = earliest_expiry.strftime('%Y-%m-%d')
        
        if self.x_studio_manufacturing_date:
            vals['x_studio_manufacturing_date'] = self.x_studio_manufacturing_date
        if self.x_studio_bulk_lotserial_date:
            vals['expiration_date'] = fields.Datetime.to_datetime(self.x_studio_bulk_lotserial_date)
        
        # Copy Bulk Manufacturer to Lot on creation
        if self.x_studio_many2one_field_8jb_1jrfuhjph:
            vals['x_studio_bulk_manufacturer'] = self.x_studio_many2one_field_8jb_1jrfuhjph.id
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        records = super(MrpProduction, self).create(vals_list)
        for record in records:
            if record.lot_producing_id:
                record._sync_dates_to_lot()
        return records

    def write(self, vals):
        res = super(MrpProduction, self).write(vals)
        if 'x_studio_manufacturing_date' in vals or 'x_studio_bulk_lotserial_date' in vals or 'lot_producing_id' in vals or 'x_studio_many2one_field_8jb_1jrfuhjph' in vals:
            for record in self:
                if record.lot_producing_id:
                    record._sync_dates_to_lot()
        return res

    def _sync_dates_to_lot(self):
        self.ensure_one()
        lot_vals = {}
        if self.x_studio_manufacturing_date and self.x_studio_manufacturing_date != self.lot_producing_id.x_studio_manufacturing_date:
            lot_vals['x_studio_manufacturing_date'] = self.x_studio_manufacturing_date
        
        lot_expiry_date = self.lot_producing_id.expiration_date.date() if self.lot_producing_id.expiration_date else False
        if self.x_studio_bulk_lotserial_date and self.x_studio_bulk_lotserial_date != lot_expiry_date:
            lot_vals['expiration_date'] = fields.Datetime.to_datetime(self.x_studio_bulk_lotserial_date)
            
        # Sync Bulk Manufacturer
        if self.x_studio_many2one_field_8jb_1jrfuhjph and self.x_studio_many2one_field_8jb_1jrfuhjph != self.lot_producing_id.x_studio_bulk_manufacturer:
            lot_vals['x_studio_bulk_manufacturer'] = self.x_studio_many2one_field_8jb_1jrfuhjph.id

        if lot_vals:
            self.lot_producing_id.write(lot_vals)

    def button_mark_done(self):
        for production in self:
            # Instead of raising UserError, default it to today's date if empty
            if production.product_id.tracking != 'none' and not production.x_studio_manufacturing_date:
                production.x_studio_manufacturing_date = fields.Date.context_today(production)
                # Compute bulk expiry date as well
                if production.product_id.use_expiration_date and production.product_id.expiration_time:
                    production.x_studio_bulk_lotserial_date = production.x_studio_manufacturing_date + datetime.timedelta(days=production.product_id.expiration_time)
        return super(MrpProduction, self).button_mark_done()
