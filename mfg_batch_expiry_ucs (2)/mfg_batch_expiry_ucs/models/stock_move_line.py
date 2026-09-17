# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import datetime

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    # Kept store=True for solid database persistence
    x_studio_manufacturing_date = fields.Date(
        string="Manufacturing Date",
        compute='_compute_x_studio_manufacturing_date',
        store=True,
        readonly=False
    )

    @api.depends('lot_id', 'lot_id.x_studio_manufacturing_date', 'quant_id', 'quant_id.lot_id.x_studio_manufacturing_date')
    def _compute_x_studio_manufacturing_date(self):
        for line in self:
            # We only overwrite or calculate if lot_id/quant_id has a value.
            # This prevents Odoo from resetting/clearing manual user input on incoming receipts.
            if line.lot_id:
                line.x_studio_manufacturing_date = line.lot_id.x_studio_manufacturing_date
            elif line.quant_id and line.quant_id.lot_id:
                line.x_studio_manufacturing_date = line.quant_id.lot_id.x_studio_manufacturing_date

    @api.onchange('lot_id', 'quant_id')
    def _onchange_lot_or_quant_id(self):
        if self.lot_id:
            self.x_studio_manufacturing_date = self.lot_id.x_studio_manufacturing_date
        elif self.quant_id and self.quant_id.lot_id:
            self.x_studio_manufacturing_date = self.quant_id.lot_id.x_studio_manufacturing_date

    @api.depends('x_studio_manufacturing_date', 'product_id', 'lot_id.expiration_date', 'picking_id.scheduled_date', 'quant_id')
    def _compute_expiration_date(self):
        super(StockMoveLine, self)._compute_expiration_date()
        for move_line in self:
            if move_line.x_studio_manufacturing_date and move_line.product_id.use_expiration_date and move_line.product_id.expiration_time:
                mfg_datetime = fields.Datetime.to_datetime(move_line.x_studio_manufacturing_date)
                move_line.expiration_date = mfg_datetime + datetime.timedelta(days=move_line.product_id.expiration_time)

    def _prepare_new_lot_vals(self):
        vals = super(StockMoveLine, self)._prepare_new_lot_vals()
        if self.x_studio_manufacturing_date:
            vals['x_studio_manufacturing_date'] = self.x_studio_manufacturing_date
        if self.expiration_date:
            vals['expiration_date'] = self.expiration_date
        if self.picking_id and self.picking_id.partner_id:
            vals['x_studio_bulk_manufacturer'] = self.picking_id.partner_id.id
        return vals

    def _action_done(self):
        for ml in self:
            if ml.product_id.tracking != 'none' and ml.quantity > 0 and not ml.x_studio_manufacturing_date:
                if ml.picking_id and ml.picking_id.picking_type_id.code == 'incoming':
                    raise UserError(_("Manufacturing Date is required for tracked product %s on incoming receipts.") % ml.product_id.display_name)
        
        res = super(StockMoveLine, self)._action_done()

        # ml.exists() handles records deleted during super()
        for ml in self.exists():
            if ml.lot_id and ml.product_id.tracking != 'none':
                lot_vals = {}
                if ml.x_studio_manufacturing_date:
                    lot_vals['x_studio_manufacturing_date'] = ml.x_studio_manufacturing_date
                if ml.expiration_date:
                    lot_vals['expiration_date'] = ml.expiration_date
                if ml.picking_id and ml.picking_id.partner_id:
                    lot_vals['x_studio_bulk_manufacturer'] = ml.picking_id.partner_id.id
                
                lot_vals = {k: v for k, v in lot_vals.items() if ml.lot_id[k] != v}
                if lot_vals:
                    ml.lot_id.write(lot_vals)
        return res
