.PHONY: up down logs ps rebuild pull deploy

up:
\tdocker compose up -d

down:
\tdocker compose down

logs:
\tdocker compose logs -f --tail=100

ps:
\tdocker compose ps

rebuild:
\tdocker compose build --no-cache web && docker compose up -d

pull:
\tgit pull --rebase

deploy: pull
\tdocker compose build web
\tdocker compose up -d
\tdocker compose logs -f --tail=50