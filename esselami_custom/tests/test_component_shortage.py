# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestComponentShortage(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.vendor = cls.env["res.partner"].create({"name": "Fournisseur Bois"})
        cls.component = cls.env["product.product"].create({
            "name": "Plateau hêtre",
            "is_storable": True,
            "seller_ids": [(0, 0, {
                "partner_id": cls.vendor.id,
                "price": 80.0,
            })],
        })
        cls.finished = cls.env["product.product"].create({
            "name": "Table réunion",
            "is_storable": True,
        })
        cls.bom = cls.env["mrp.bom"].create({
            "product_tmpl_id": cls.finished.product_tmpl_id.id,
            "product_qty": 1.0,
            "bom_line_ids": [(0, 0, {
                "product_id": cls.component.id,
                "product_qty": 4.0,
            })],
        })

    def _make_mo(self, qty=1):
        mo = self.env["mrp.production"].create({
            "product_id": self.finished.id,
            "product_qty": qty,
            "bom_id": self.bom.id,
        })
        mo.action_confirm()
        return mo

    def test_shortage_detected_when_no_stock(self):
        mo = self._make_mo()
        self.assertTrue(mo.esselami_has_shortage)
        self.assertIn(self.component, mo.esselami_missing_component_ids)

    def test_purchase_order_created_for_shortage(self):
        mo = self._make_mo()
        mo.action_create_purchase_from_shortage()
        purchase = self.env["purchase.order"].search([("origin", "=", mo.name)])
        self.assertEqual(len(purchase), 1)
        self.assertEqual(purchase.partner_id, self.vendor)
        self.assertEqual(purchase.order_line.product_id, self.component)
