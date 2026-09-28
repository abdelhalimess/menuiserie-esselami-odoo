# -*- coding: utf-8 -*-
{
    "name": "Menuiserie ESSELAMI - Spécifique",
    "version": "19.0.1.0.0",
    "category": "Sales/Sales",
    "summary": "Spécifique métier Menuiserie ESSELAMI : délai de fabrication, "
               "validation des remises, contrôle des composants, tableau de bord.",
    "author": "Abdelhalim Esselami",
    "license": "LGPL-3",
    "depends": [
        "sale_management",
        "sale_stock",
        "mrp",
        "purchase",
        "stock",
        "account",
    ],
    "data": [
        "security/esselami_security.xml",
    ],
    "installable": True,
    "application": False,
}
