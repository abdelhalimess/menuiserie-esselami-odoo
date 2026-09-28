# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    esselami_discount_threshold = fields.Float(
        string="Seuil de validation des remises (%)",
        default=15.0,
        config_parameter="esselami_custom.discount_approval_threshold",
        help="Au-delà de ce pourcentage, un devis doit être validé par un "
             "responsable avant confirmation.",
    )
    esselami_daily_capacity = fields.Float(
        string="Capacité atelier (unités / jour)",
        default=5.0,
        config_parameter="esselami_custom.daily_workshop_capacity",
        help="Utilisée pour estimer le délai de fabrication sur les devis.",
    )
