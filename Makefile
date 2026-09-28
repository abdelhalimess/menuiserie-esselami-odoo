.PHONY: up down install upgrade test logs

DB ?= esselami

up:
	docker compose up -d

down:
	docker compose down

install:
	docker compose exec odoo odoo -d $(DB) -i esselami_custom --stop-after-init

upgrade:
	docker compose exec odoo odoo -d $(DB) -u esselami_custom --stop-after-init

test:
	docker compose exec odoo odoo -d $(DB) -u esselami_custom \
		--test-enable --test-tags /esselami_custom --stop-after-init \
		--http-port=8071

logs:
	docker compose logs -f odoo
