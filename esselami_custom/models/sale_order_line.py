# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    esselami_lead_time_days = fields.Integer(
        string="Délai fabrication (j)",
        compute="_compute_esselami_lead_time_days",
        store=True,
        help="Délai estimé de fabrication, calculé à partir de la nomenclature "
             "du produit et de la quantité commandée.",
    )

    @api.depends("product_id", "product_uom_qty", "company_id")
    def _compute_esselami_lead_time_days(self):
        """délai = délai de la nomenclature
                + quantité / capacité journalière de l'atelier (arrondi sup.)
        """
        capacity = self.env["ir.config_parameter"].sudo().get_param(
            "esselami_custom.daily_workshop_capacity", default="5"
        )
        try:
            capacity = max(float(capacity), 1.0)
        except (TypeError, ValueError):
            capacity = 5.0

        bom_model = self.env["mrp.bom"]
        for line in self:
            if not line.product_id or line.product_id.type == "service":
                line.esselami_lead_time_days = 0
                continue

            bom = bom_model._bom_find(
                line.product_id,
                company_id=line.company_id.id or line.order_id.company_id.id,
            ).get(line.product_id)

            if not bom:
                # Produit non fabriqué : délai de livraison du produit
                line.esselami_lead_time_days = int(
                    line.product_id.sale_delay or 0
                )
                continue

            base_days = int(bom.produce_delay or 0)
            qty_days = -(-line.product_uom_qty // capacity)  # ceil
            line.esselami_lead_time_days = base_days + int(qty_days)
