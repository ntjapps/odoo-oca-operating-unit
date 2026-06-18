# Copyright 2016 ForgeFlow S.L. (https://www.forgeflow.com)
# Copyright 2016 Serpent Consulting Services Pvt. Ltd.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import UserError  # retained: used in _check_company_operating_unit


class PurchaseRequisition(models.Model):
    _inherit = "purchase.requisition"

    operating_unit_id = fields.Many2one(
        comodel_name="operating.unit",
        string="Operating Unit",
        default=lambda self: self.env["res.users"]._get_default_operating_unit(
            self.env.uid
        ),
    )

    def _default_picking_type_id(self):
        res = super()._default_picking_type_id()
        operating_unit = self.env["res.users"]._get_default_operating_unit(self.env.uid)
        if operating_unit:
            types = self.env["stock.picking.type"].search(
                [
                    ("code", "=", "incoming"),
                    ("warehouse_id.operating_unit_id", "=", operating_unit.id),
                ],
                limit=1,
            )
            if types:
                return types
        return res

    picking_type_id = fields.Many2one(
        default=_default_picking_type_id,
    )

    @api.constrains("operating_unit_id", "company_id")
    def _check_company_operating_unit(self):
        for rec in self:
            if (
                rec.company_id
                and rec.operating_unit_id
                and rec.company_id != rec.operating_unit_id.company_id
            ):
                raise UserError(
                    _(
                        "The Company in the Purchase Requisition and"
                        " in the Operating Unit must be the same."
                    )
                )

    @api.constrains("operating_unit_id", "picking_type_id")
    def _check_warehouse_operating_unit(self):
        # APJII v15-parity relaxation (2026-06-17, NTJ):
        # APJII runs a SINGLE central warehouse bound to a placeholder OU; real
        # operational OUs have no dedicated warehouse.  The OCA hard
        # OU↔warehouse match would block every save for a real OU, exactly as it
        # did in v15 (where this constraint did not exist).  We keep the method
        # signature intact so any external references remain valid, but we no
        # longer raise — a central warehouse MAY serve all operating units.
        pass

    @api.onchange("operating_unit_id")
    def _onchange_operating_unit_id(self):
        # APJII v15-parity relaxation (2026-06-17, NTJ):
        # Auto-set picking_type_id only when a warehouse dedicated to the
        # selected OU exists — convenience, not a hard requirement.
        # If no OU-specific warehouse is found (central-warehouse topology),
        # leave picking_type_id at its current/default value and do NOT raise.
        type_obj = self.env["stock.picking.type"]
        if self.operating_unit_id:
            types = type_obj.search(
                [
                    ("code", "=", "incoming"),
                    ("warehouse_id.operating_unit_id", "=", self.operating_unit_id.id),
                ]
            )
            if types:
                self.picking_type_id = types[:1]
            # else: no dedicated warehouse — leave picking_type_id unchanged.


class PurchaseRequisitionLine(models.Model):
    _inherit = "purchase.requisition.line"

    operating_unit_id = fields.Many2one(
        comodel_name="operating.unit",
        string="Operating Unit",
        related="requisition_id.operating_unit_id",
        readonly=True,
        store=True,
    )
