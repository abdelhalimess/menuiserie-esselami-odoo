# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    """Détection des composants en rupture et génération des achats."""

    _inherit = "mrp.production"

    esselami_missing_component_ids = fields.Many2many(
        comodel_name="product.product",
        string="Composants en rupture",
        compute="_compute_esselami_missing_components",
        help="Composants dont le stock libre est insuffisant pour cet OF.",
    )
    esselami_has_shortage = fields.Boolean(
        string="Rupture détectée",
        compute="_compute_esselami_missing_components",
    )

    @api.depends("move_raw_ids.product_id", "move_raw_ids.product_uom_qty", "state")
    def _compute_esselami_missing_components(self):
        for production in self:
            missing = production._get_component_shortage()
            production.esselami_missing_component_ids = [
                (6, 0, list(missing.keys()))
            ]
            production.esselami_has_shortage = bool(missing)

    def _get_component_shortage(self):
        """Retourne {product_id: quantité manquante} pour cet OF."""
        self.ensure_one()
        shortage = {}
        for move in self.move_raw_ids:
            product = move.product_id
            if not product or product.type != "consu" or not product.is_storable:
                continue
            available = product.with_company(self.company_id).free_qty
            missing = move.product_uom_qty - available
            if missing > 0:
                shortage[product.id] = missing
        return shortage

    def action_confirm(self):
        res = super().action_confirm()
        for production in self:
            shortage = production._get_component_shortage()
            if not shortage:
                continue
            products = self.env["product.product"].browse(shortage.keys())
            lines = "".join(
                "<li>%s : %s manquant(s)</li>"
                % (product.display_name, round(shortage[product.id], 2))
                for product in products
            )
            production.message_post(
                body=_(
                    "<p><b>Composants en rupture pour cet ordre de "
                    "fabrication :</b></p><ul>%s</ul>",
                    lines,
                )
            )
        return res

    def action_create_purchase_from_shortage(self):
        """Crée une demande de prix par fournisseur (selon les seller_ids)."""
        self.ensure_one()
        shortage = self._get_component_shortage()
        if not shortage:
            raise UserError(_("Aucun composant en rupture sur cet ordre."))

        purchase_by_vendor = {}
        without_vendor = self.env["product.product"]

        for product in self.env["product.product"].browse(shortage.keys()):
            seller = product._select_seller(quantity=shortage[product.id])
            if not seller:
                without_vendor |= product
                continue
            purchase_by_vendor.setdefault(seller.partner_id, []).append(
                (product, shortage[product.id], seller)
            )

        created = self.env["purchase.order"]
        for vendor, items in purchase_by_vendor.items():
            order = self.env["purchase.order"].create({
                "partner_id": vendor.id,
                "company_id": self.company_id.id,
                "origin": self.name,
                "order_line": [
                    (0, 0, {
                        "product_id": product.id,
                        "product_qty": qty,
                        "product_uom_id": product.uom_id.id,
                        "price_unit": seller.price,
                        "date_planned": fields.Datetime.now(),
                        "name": product.display_name,
                    })
                    for product, qty, seller in items
                ],
            })
            created |= order

        if without_vendor:
            self.message_post(
                body=_(
                    "Aucun fournisseur défini pour : %s",
                    ", ".join(without_vendor.mapped("display_name")),
                )
            )

        action = self.env["ir.actions.actions"]._for_xml_id(
            "purchase.purchase_rfq"
        )
        action["domain"] = [("id", "in", created.ids)]
        return action
