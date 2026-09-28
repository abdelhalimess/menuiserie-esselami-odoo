/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Layout } from "@web/search/layout";

/**
 * Tableau de bord Direction : affiche les indicateurs renvoyés par
 * esselami.dashboard.get_dashboard_data.
 */
export class EsselamiDashboard extends Component {
    static template = "esselami_custom.Dashboard";
    static components = { Layout };
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({ cards: [], loading: true, error: null });

        onWillStart(async () => {
            await this.loadData();
        });
    }

    async loadData() {
        this.state.loading = true;
        try {
            const data = await this.orm.call(
                "esselami.dashboard",
                "get_dashboard_data",
                []
            );
            this.state.cards = data.cards;
            this.state.currency = data.currency;
            this.state.error = null;
        } catch (error) {
            this.state.error = error.message || "Chargement impossible";
        } finally {
            this.state.loading = false;
        }
    }

    formatValue(card) {
        if (!card.is_amount) {
            return card.value;
        }
        return `${card.value.toLocaleString("fr-FR", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        })} ${this.state.currency || ""}`;
    }

    /** Ouvre la liste correspondant à la carte cliquée. */
    onCardClick(card) {
        const targets = {
            late_mo: {
                name: "OF en retard",
                res_model: "mrp.production",
                domain: [
                    ["state", "in", ["confirmed", "progress"]],
                    ["date_start", "<", new Date().toISOString().slice(0, 19).replace("T", " ")],
                ],
            },
            late_delivery: {
                name: "Livraisons en retard",
                res_model: "stock.picking",
                domain: [
                    ["picking_type_code", "=", "outgoing"],
                    ["state", "in", ["assigned", "confirmed", "waiting"]],
                ],
            },
            to_approve: {
                name: "Devis à valider",
                res_model: "sale.order",
                domain: [["state", "=", "to_approve"]],
            },
            overdue_amount: {
                name: "Factures impayées",
                res_model: "account.move",
                domain: [
                    ["move_type", "=", "out_invoice"],
                    ["payment_state", "in", ["not_paid", "partial"]],
                    ["state", "=", "posted"],
                ],
            },
        };
        const target = targets[card.key];
        if (!target) {
            return;
        }
        this.action.doAction({
            type: "ir.actions.act_window",
            name: target.name,
            res_model: target.res_model,
            domain: target.domain,
            views: [[false, "list"], [false, "form"]],
        });
    }
}

registry.category("actions").add("esselami_dashboard", EsselamiDashboard);
