# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

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
