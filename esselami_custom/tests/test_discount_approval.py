# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import UserError


@tagged("post_install", "-at_install")
class TestDiscountApproval(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["ir.config_parameter"].sudo().set_param(
            "esselami_custom.discount_approval_threshold", "15.0"
        )
        cls.partner = cls.env["res.partner"].create({"name": "Client Remise"})
        # Produit de service : la confirmation ne déclenche ni stock ni
        # fabrication, le test reste centré sur le workflow de validation.
        cls.product = cls.env["product.product"].create({
            "name": "Pose sur site",
            "type": "service",
            "list_price": 500.0,
        })

    def _make_order(self, discount):
        return self.env["sale.order"].create({
            "partner_id": self.partner.id,
            "order_line": [(0, 0, {
                "product_id": self.product.id,
                "product_uom_qty": 1,
                "discount": discount,
            })],
        })

    def _make_approver(self):
        return self.env["res.users"].create({
            "name": "Responsable remises",
            "login": "valideur_esselami_test",
            "group_ids": [(6, 0, [
                self.env.ref("esselami_custom.group_discount_approver").id,
            ])],
        })

    def test_small_discount_confirms_normally(self):
        order = self._make_order(10.0)
        order.action_confirm()
        self.assertEqual(order.state, "sale")

    def test_large_discount_requires_approval(self):
        approver = self._make_approver()
        order = self._make_order(25.0)
        order.action_confirm()
        self.assertEqual(order.state, "to_approve")
        self.assertEqual(order.activity_ids.user_id, approver)

    def test_approval_then_confirm(self):
        approver = self._make_approver()
        order = self._make_order(25.0)
        order.action_confirm()
        order.with_user(approver).action_approve_discount()
        self.assertEqual(order.state, "sale")
        self.assertTrue(order.esselami_discount_approved)

    def test_refusal_returns_to_draft(self):
        order = self._make_order(25.0)
        order.action_confirm()
        order.action_refuse_discount()
        self.assertEqual(order.state, "draft")

    def test_batch_confirm_only_blocks_concerned_orders(self):
        """Une confirmation en lot ne bloque que le devis concerné."""
        ok_order = self._make_order(5.0)
        ko_order = self._make_order(30.0)
        (ok_order | ko_order).action_confirm()
        self.assertEqual(ok_order.state, "sale")
        self.assertEqual(ko_order.state, "to_approve")

    def test_approver_right_is_enforced(self):
        order = self._make_order(25.0)
        order.action_confirm()
        salesman = self.env["res.users"].create({
            "name": "Commercial simple",
            "login": "commercial_esselami_test",
            "group_ids": [(6, 0, [
                self.env.ref("sales_team.group_sale_salesman").id,
            ])],
        })
        with self.assertRaises(UserError):
            order.with_user(salesman).action_approve_discount()

    def test_to_approve_hidden_from_other_salesmen(self):
        order = self._make_order(25.0)
        order.action_confirm()
        colleague = self.env["res.users"].create({
            "name": "Autre commercial",
            "login": "collegue_esselami_test",
            "group_ids": [(6, 0, [
                self.env.ref("sales_team.group_sale_salesman_all_leads").id,
            ])],
        })
        visible = self.env["sale.order"].with_user(colleague).search(
            [("id", "=", order.id)]
        )
        self.assertFalse(visible)
