.PHONY: docker-run up down logs status tutor-bootstrap student-bootstrap tutor-magic-link student-magic-link remove-tutor remove-student publish

export CONFIRM EMAIL

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

tutor-bootstrap student-bootstrap:
	@test -n "$$EMAIL" || (echo "Usage: make $@ EMAIL=$(word 1,$(subst -, ,$@))@example.com" >&2; exit 2)
	docker compose exec app python -m app.account_commands bootstrap "$(word 1,$(subst -, ,$@))" "$$EMAIL"

tutor-magic-link student-magic-link:
	@test -n "$$EMAIL" || (echo "Usage: make $@ EMAIL=$(word 1,$(subst -, ,$@))@example.com" >&2; exit 2)
	docker compose exec app python -m app.account_commands magic-link "$(word 1,$(subst -, ,$@))" "$$EMAIL"

remove-tutor remove-student:
	@test -n "$$EMAIL" || (echo "Usage: make $@ EMAIL=$(word 2,$(subst -, ,$@))@example.com CONFIRM=$@" >&2; exit 2)
	@test "$$CONFIRM" = "$@" || (echo "Usage: make $@ EMAIL=$(word 2,$(subst -, ,$@))@example.com CONFIRM=$@" >&2; exit 2)
	docker compose exec app python -m app.account_commands remove "$(word 2,$(subst -, ,$@))" "$$EMAIL"

publish:
	./scripts/publish-image.sh
