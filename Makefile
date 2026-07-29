.PHONY: docker-run up down logs status bootstrap login-link publish

export EMAIL

up:
	docker compose up -d

docker-run:
	docker compose up --build --pull never

down:
	docker compose down

logs:
	docker compose logs -f

status:
	docker compose ps

bootstrap:
	@test -n "$$EMAIL" || (echo "Usage: make bootstrap EMAIL=tutor@example.com" >&2; exit 2)
	docker compose exec app python -m app.bootstrap_tutor "$$EMAIL"

login-link:
	docker compose exec app python -m app.generate_tutor_login_link

publish:
	./scripts/publish-image.sh
