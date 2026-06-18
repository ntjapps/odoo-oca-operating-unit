# Copyright 2016 ForgeFlow S.L. (https://www.forgeflow.com)
# Copyright 2016 Serpent Consulting Services Pvt. Ltd.
# Copyright 2026 NTJ (https://www.ntj.co.id)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    picking_type_id = fields.Many2one(
        default=lambda self: self._jp_default_picking_type_ou(),
    )

    @api.model
    def _jp_default_picking_type_ou(self):
        """APJII v15-parity (NTJ 2026-06-17): prefer an incoming picking type whose
        warehouse belongs to the user's operating unit; otherwise fall back to core's
        company-based default so picking_type_id (the required "Deliver To" field) is
        NEVER left empty — which was blocking new RFQ saves when the single central
        warehouse isn't linked to the user's OU."""
        operating_unit = self.env["res.users"]._get_default_operating_unit(self.env.uid)
        if operating_unit:
            ptype = self.env["stock.picking.type"].search(
                [
                    ("code", "=", "incoming"),
                    ("warehouse_id.operating_unit_id", "=", operating_unit.id),
                ],
                limit=1,
            )
            if ptype:
                return ptype
        # Fallback: core purchase_stock default (company-based; returns Receipts) — never empty.
        return self._default_picking_type()

    @api.onchange("requisition_id")
    def _onchange_requisition_id(self):
        res = super()._onchange_requisition_id()
        if self.requisition_id:
            self.requesting_operating_unit_id = self.requisition_id.operating_unit_id
            self.operating_unit_id = self.requisition_id.operating_unit_id
        return res
