# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    state = fields.Selection(
        selection_add=[("to_approve", "À valider"), ("sale",)],
        ondelete={"to_approve": "set default"},
    )

    esselami_max_discount = fields.Float(
        string="Remise max (%)",
        compute="_compute_esselami_max_discount",
        store=True,
        help="Remise la plus élevée accordée sur les lignes de ce devis.",
    )
    esselami_discount_approved = fields.Boolean(
        string="Remise validée",
        copy=False,
        readonly=True,
    )
    esselami_estimated_ship_date = fields.Date(
        string="Expédition estimée",
        compute="_compute_esselami_estimated_ship_date",
        store=True,
        help="Date d'expédition estimée : la plus tardive des lignes, "
             "calculée à partir des délais de fabrication.",
    )

    # ------------------------------------------------------------------
    # Champs calculés
    # ------------------------------------------------------------------
    @api.depends("order_line.discount")
    def _compute_esselami_max_discount(self):
        for order in self:
            order.esselami_max_discount = max(
                order.order_line.mapped("discount") or [0.0]
            )

    @api.depends("order_line.esselami_lead_time_days", "date_order")
    def _compute_esselami_estimated_ship_date(self):
        for order in self:
            max_days = max(
                order.order_line.mapped("esselami_lead_time_days") or [0]
            )
            if not order.date_order or not max_days:
                order.esselami_estimated_ship_date = False
            else:
                order.esselami_estimated_ship_date = (
                    order.date_order + relativedelta(days=max_days)
                ).date()

    # ------------------------------------------------------------------
    # Workflow de validation
    # ------------------------------------------------------------------
    def _get_discount_threshold(self):
        self.ensure_one()
        param = self.env["ir.config_parameter"].sudo().get_param(
            "esselami_custom.discount_approval_threshold", default="15.0"
        )
        try:
            return float(param)
        except (TypeError, ValueError):
            return 15.0

    def _needs_discount_approval(self):
        self.ensure_one()
        if self.esselami_discount_approved:
            return False
        return self.esselami_max_discount > self._get_discount_threshold()

    def action_confirm(self):
        """Les devis au-dessus du seuil passent en validation, les autres
        sont confirmés normalement.
        """
        to_approve = self.filtered(
            lambda order: order.state in ("draft", "sent")
            and order._needs_discount_approval()
        )
        if to_approve:
            to_approve._request_discount_approval()

        remaining = self - to_approve
        return super(SaleOrder, remaining).action_confirm() if remaining else True

    def _request_discount_approval(self):
        """Passe les devis en `to_approve` et crée une activité pour le valideur."""
        approver_group = self.env.ref(
            "esselami_custom.group_discount_approver", raise_if_not_found=False
        )
        approvers = approver_group.user_ids if approver_group else self.env["res.users"]

        self.write({"state": "to_approve"})
        for order in self:
            user = approvers[:1] or order.user_id or self.env.user
            order.activity_schedule(
                "mail.mail_activity_data_todo",
                user_id=user.id,
                summary=_("Validation de remise : %s", order.name),
                note=_(
                    "Remise de %(discount).2f %% demandée, au-dessus du seuil "
                    "de %(threshold).2f %%.",
                    discount=order.esselami_max_discount,
                    threshold=order._get_discount_threshold(),
                ),
            )

    def action_approve_discount(self):
        approver_group = self.env.ref(
            "esselami_custom.group_discount_approver", raise_if_not_found=False
        )
        if approver_group and not self.env.user.has_group(
            "esselami_custom.group_discount_approver"
        ):
            raise UserError(
                _("Vous n'avez pas le droit de valider une remise exceptionnelle.")
            )

        orders = self.filtered(lambda order: order.state == "to_approve")
        if not orders:
            return True

        # Le devis repasse en brouillon : c'est l'état attendu par la
        # confirmation standard.
        orders.write({"esselami_discount_approved": True, "state": "draft"})
        orders.activity_feedback(["mail.mail_activity_data_todo"])
        return orders.action_confirm()

    def action_refuse_discount(self):
        self.activity_unlink(["mail.mail_activity_data_todo"])
        self.write({"state": "draft"})
        for order in self:
            order.message_post(
                body=_("Remise refusée, le devis repasse en brouillon.")
            )
        return True
