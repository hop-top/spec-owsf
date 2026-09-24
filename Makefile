SPEC_DIR := specs/v1.0
SCHEMA_CORE := $(SPEC_DIR)/schemas/core.schema.json
SCHEMA_AGENT_LOOP := $(SPEC_DIR)/schemas/profiles/agent-loop.schema.json
SCHEMA_HOOKS := $(SPEC_DIR)/schemas/profiles/hooks.schema.json
EXAMPLES := $(wildcard $(SPEC_DIR)/examples/*.json)
FIXTURE := tools/testdata/sample-session.jsonl

.PHONY: ci lint-schemas validate-examples validate-profiles converter lint-md hooks check-tools

ci: lint-schemas validate-examples validate-profiles converter

## lint-schemas: JSON syntax of every published schema
lint-schemas:
	@for s in $(SCHEMA_CORE) $(SCHEMA_AGENT_LOOP) $(SCHEMA_HOOKS); do \
		jq . "$$s" >/dev/null || exit 1; \
		echo "ok   $$s"; \
	done

## validate-examples: core schema + semantic validation for every example
validate-examples:
	@test -n "$(EXAMPLES)" || { echo "no examples found in $(SPEC_DIR)/examples/" >&2; exit 1; }
	@for f in $(EXAMPLES); do \
		echo "validating $$f"; \
		jq . "$$f" >/dev/null || exit 1; \
		check-jsonschema --schemafile $(SCHEMA_CORE) "$$f" || exit 1; \
		python3 scripts/validate_owsf_semantics.py "$$f" || exit 1; \
	done

## validate-profiles: profile schemas, including the composition case
validate-profiles:
	check-jsonschema --schemafile $(SCHEMA_AGENT_LOOP) \
		$(SPEC_DIR)/examples/agent-loop-owsf.json \
		$(SPEC_DIR)/examples/claude-code-session-owsf.json
	check-jsonschema --schemafile $(SCHEMA_HOOKS) \
		$(SPEC_DIR)/examples/hooks-owsf.json
	check-jsonschema --schemafile $(SCHEMA_AGENT_LOOP) \
		$(SPEC_DIR)/examples/hooks-owsf.json

## converter: determinism against the committed example + byte-identical round-trip
converter:
	@tmp="$$(mktemp -d)"; \
	python3 tools/convert_claude_jsonl.py $(FIXTURE) -o "$$tmp/artifact.json" && \
	diff "$$tmp/artifact.json" $(SPEC_DIR)/examples/claude-code-session-owsf.json && \
	python3 tools/convert_claude_jsonl.py --reverse "$$tmp/artifact.json" -o "$$tmp/roundtrip.jsonl" && \
	cmp "$$tmp/roundtrip.jsonl" $(FIXTURE); \
	rc=$$?; rm -rf "$$tmp"; exit $$rc

## lint-md: markdown lint (requires npx)
lint-md:
	npx --yes markdownlint-cli2

## hooks: route git hooks at .githooks/
hooks:
	git config core.hooksPath .githooks
	@echo "core.hooksPath -> .githooks"

## check-tools: report which required tools are missing
check-tools:
	@for t in jq python3 check-jsonschema; do \
		command -v "$$t" >/dev/null 2>&1 && echo "ok      $$t" || echo "MISSING $$t"; \
	done
