# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestDashboard(TransactionCase):

    def test_dashboard_data_structure(self):
        data = self.env["esselami.dashboard"].get_dashboard_data()
        self.assertIn("currency", data)
        keys = [card["key"] for card in data["cards"]]
        self.assertEqual(
            keys,
            [
                "late_mo",
                "shortage_mo",
                "late_delivery",
                "to_approve",
                "overdue_amount",
                "pipeline",
            ],
        )
        for card in data["cards"]:
            self.assertIsNotNone(card["value"])
            self.assertIn(card["tone"], ("ok", "warning", "danger"))

    def test_to_approve_card_counts_pending_orders(self):
        partner = self.env["res.partner"].create({"name": "Client Tableau"})
        product = self.env["product.product"].create({
            "name": "Prestation",
            "type": "service",
            "list_price": 300.0,
        })
        before = self._card_value("to_approve")
        order = self.env["sale.order"].create({
            "partner_id": partner.id,
            "order_line": [(0, 0, {
                "product_id": product.id,
                "product_uom_qty": 1,
                "discount": 40.0,
            })],
        })
        order.action_confirm()
        self.assertEqual(order.state, "to_approve")
        self.assertEqual(self._card_value("to_approve"), before + 1)

    def _card_value(self, key):
        data = self.env["esselami.dashboard"].get_dashboard_data()
        return next(card["value"] for card in data["cards"] if card["key"] == key)
