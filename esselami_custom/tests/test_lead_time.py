# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestLeadTime(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["ir.config_parameter"].sudo().set_param(
            "esselami_custom.daily_workshop_capacity", "5"
        )
        cls.partner = cls.env["res.partner"].create({"name": "Client Test"})
        cls.component = cls.env["product.product"].create({
            "name": "Panneau chêne",
            "is_storable": True,
        })
        cls.finished = cls.env["product.product"].create({
            "name": "Comptoir sur mesure",
            "is_storable": True,
        })
        cls.bom = cls.env["mrp.bom"].create({
            "product_tmpl_id": cls.finished.product_tmpl_id.id,
            "product_qty": 1.0,
            "produce_delay": 3.0,
            "bom_line_ids": [(0, 0, {
                "product_id": cls.component.id,
                "product_qty": 2.0,
            })],
        })

    def _make_order(self, qty):
        return self.env["sale.order"].create({
            "partner_id": self.partner.id,
            "order_line": [(0, 0, {
                "product_id": self.finished.id,
                "product_uom_qty": qty,
            })],
        })

    def test_lead_time_uses_bom_delay(self):
        """3 j de nomenclature + 1 j pour 5 unités à capacité 5/j."""
        order = self._make_order(5)
        self.assertEqual(order.order_line.esselami_lead_time_days, 4)

    def test_lead_time_scales_with_quantity(self):
        """11 unités à capacité 5/j -> 3 jours d'atelier (arrondi sup)."""
        order = self._make_order(11)
        self.assertEqual(order.order_line.esselami_lead_time_days, 6)

    def test_estimated_ship_date_is_set(self):
        order = self._make_order(5)
        self.assertTrue(order.esselami_estimated_ship_date)
        self.assertGreater(
            order.esselami_estimated_ship_date, order.date_order.date()
        )

    def test_product_without_bom_falls_back_to_sale_delay(self):
        simple = self.env["product.product"].create({
            "name": "Poignée standard",
            "is_storable": True,
            "sale_delay": 7.0,
        })
        order = self.env["sale.order"].create({
            "partner_id": self.partner.id,
            "order_line": [(0, 0, {
                "product_id": simple.id,
                "product_uom_qty": 3,
            })],
        })
        self.assertEqual(order.order_line.esselami_lead_time_days, 7)
