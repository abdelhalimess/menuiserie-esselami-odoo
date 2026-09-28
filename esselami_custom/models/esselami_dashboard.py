# -*- coding: utf-8 -*-
from odoo import api, fields, models


class EsselamiDashboard(models.AbstractModel):
    """Données du tableau de bord Direction, appelées par le composant OWL."""

    _name = "esselami.dashboard"
    _description = "Données du tableau de bord Direction"

    @api.model
    def get_dashboard_data(self):
        today = fields.Date.context_today(self)
        now = fields.Datetime.now()

        late_mo = self.env["mrp.production"].search_count([
            ("state", "in", ("confirmed", "progress")),
            ("date_start", "<", now),
        ])
        shortage_mo = self.env["mrp.production"].search_count([
            ("state", "in", ("confirmed", "progress")),
            ("components_availability_state", "in", ("late", "unavailable")),
        ])
        late_delivery = self.env["stock.picking"].search_count([
            ("picking_type_code", "=", "outgoing"),
            ("state", "in", ("assigned", "confirmed", "waiting")),
            ("scheduled_date", "<", now),
        ])
        to_approve = self.env["sale.order"].search_count([
            ("state", "=", "to_approve"),
        ])

        overdue_invoices = self.env["account.move"].search([
            ("move_type", "=", "out_invoice"),
            ("payment_state", "in", ("not_paid", "partial")),
            ("state", "=", "posted"),
            ("invoice_date_due", "<", today),
        ])

        pipeline = self.env["sale.order"]._read_group(
            domain=[("state", "in", ("draft", "sent"))],
            groupby=[],
            aggregates=["amount_total:sum"],
        )
        pipeline_total = pipeline[0][0] if pipeline else 0.0

        return {
            "currency": self.env.company.currency_id.symbol,
            "cards": [
                {
                    "key": "late_mo",
                    "label": "OF en retard",
                    "value": late_mo,
                    "tone": "danger" if late_mo else "ok",
                },
                {
                    "key": "shortage_mo",
                    "label": "OF avec composants manquants",
                    "value": shortage_mo,
                    "tone": "warning" if shortage_mo else "ok",
                },
                {
                    "key": "late_delivery",
                    "label": "Livraisons en retard",
                    "value": late_delivery,
                    "tone": "danger" if late_delivery else "ok",
                },
                {
                    "key": "to_approve",
                    "label": "Devis à valider",
                    "value": to_approve,
                    "tone": "warning" if to_approve else "ok",
                },
                {
                    "key": "overdue_amount",
                    "label": "Impayés échus",
                    "value": round(
                        sum(overdue_invoices.mapped("amount_residual")), 2
                    ),
                    "is_amount": True,
                    "tone": "danger" if overdue_invoices else "ok",
                },
                {
                    "key": "pipeline",
                    "label": "Devis en cours",
                    "value": round(pipeline_total or 0.0, 2),
                    "is_amount": True,
                    "tone": "ok",
                },
            ],
        }
