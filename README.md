# Menuiserie ESSELAMI — module Odoo 19

Module Odoo 19 pour une menuiserie fictive qui fabrique du mobilier sur mesure
pour les professionnels (Ventes, Fabrication, Stock, Achats).

## Fonctionnalités

- **Délai de fabrication sur le devis** : calculé par ligne à partir de la
  nomenclature et de la capacité de l'atelier, avec une date d'expédition
  estimée sur la commande.
- **Validation des remises** : au-delà d'un seuil (15 % par défaut), le devis
  passe à l'état « À valider » et doit être approuvé par un responsable.
- **Ruptures de composants** : les composants manquants sont signalés sur
  l'ordre de fabrication, qui propose de générer les demandes de prix par
  fournisseur.
- **Bon de livraison** : ajout de la référence commande et de la date
  d'installation prévue.
- **Tableau de bord Direction** : OF en retard, ruptures, livraisons en
  retard, devis à valider, impayés et devis en cours.

Le seuil de remise et la capacité de l'atelier se règlent dans
*Ventes > Configuration > Paramètres*.

## Lancer le projet

```bash
docker compose up -d   # Odoo 19 + PostgreSQL 16
```

Créer une base nommée `esselami` sur http://localhost:8069, puis :

```bash
make install   # installe le module
make test      # lance les tests
```

## Structure

```
esselami_custom/
├── models/        # ventes, fabrication, paramètres, tableau de bord
├── views/
├── report/        # bon de livraison
├── security/      # groupes et règle d'accès
├── data/          # paramètres par défaut
├── static/src/    # composant OWL du tableau de bord
└── tests/
```
