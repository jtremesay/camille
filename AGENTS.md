# Camille contributor guidelines

## Project direction

Camille is a work-in-progress, multi-user AI assistant built with Django and
Pydantic AI. Each user owns their agents, personalities, AI providers, models,
and API keys, and enables the capabilities they want per agent. Mattermost is
the next planned transport integration.

The `v6` branch is useful for understanding previously supported behavior,
especially Mattermost, user linking, conversations, model providers, memories,
credentials, file handling, and capabilities. Treat it as a product reference,
not as code or architecture to copy blindly: `v7` is an intentional redesign
and currently implements only a subset of that behavior.

## Architecture

- `src/camille/models/` — domain models, one module per concern
  (`profile.py`, `agent.py`, `ai.py`, `google.py`, `openai.py`, `tavily.py`,
  `exa.py`). Re-export public models from `models/__init__.py`.
- `src/camille/ai.py` — composition root. `create_pai_agent()` translates a
  stored `Agent` into a Pydantic AI agent by assembling tools and capabilities.
  Keep it declarative: no transport logic, no persistence, no I/O beyond
  building provider clients.
- `src/camille/capabilities/` — project-specific Pydantic AI capabilities
  (currently `PersonalityCapability`). Keep each capability independently
  composable and testable, and never couple a generic capability to a
  transport.
- `src/camille/management/commands/` — operational entry points such as
  `sandbox`, used to exercise an agent from the CLI.
- `src/pydanticai_django/` — reusable Django persistence adapter for Pydantic AI
  step persistence (run records, step events, tool effects, continuable
  snapshots). It must stay decoupled from Camille's domain models. It is not
  currently listed in `INSTALLED_APPS`; wire it up deliberately when run
  persistence is actually needed.
- Transport adapters (Mattermost, web) must stay separate from agent
  construction, domain logic, and provider/model selection. They supply user
  and conversation context; they do not decide which model or tools to use.

## Multi-user invariants

User isolation is a core requirement. Every domain object is owned by a Django
`User`, and every reference between two owned objects must stay within one
user.

- Scope reads and writes by the owning user; do not fetch globally and rely on
  a later authorization check.
- Validate ownership in `clean()` for every FK between user-owned objects, and
  raise `ValidationError`. See `Agent.clean()` and `Profile.clean()`.
- Add tests for both directions of each new relation: same-user accepted,
  another user's object rejected.
- Keep provider, model, and credential selection explicit and per-user. Never
  add a global credential or provider fallback that could cross users.
- Resolution order for an agent's model is agent-level first, then
  `Profile.default_model`, then an explicit error. Preserve this
  per-user-only fallback chain.
- For group conversations, distinguish agent owner, message author,
  participants, and conversation scope instead of collapsing them into one
  user.

## Model conventions

New user-owned models follow a consistent shape:

- `uuid` primary key using `uuid7`, `editable=False`;
- `created_at` / `updated_at` timestamps;
- a `user` FK with `on_delete=CASCADE` and explicit `related_name` /
  `related_query_name`;
- a human-readable `name` with `unique_together = ("user", "name")`;
- `__str__` returning the name.

Other rules:

- Use `CASCADE` for data wholly owned by its parent, and `SET_NULL` for
  optional references whose target may disappear (agent model, personality,
  API keys, profile defaults).
- Slugs and `AutoSlugField` were intentionally removed; select objects by
  `(user, name)` and do not reintroduce slug fields.
- Create migrations for every schema change, and test data migrations that
  backfill or transform rows.
- Register new models in `src/camille/admin.py` with ownership and stable
  identifiers in `list_display` / `search_fields`.

## Providers, models, and secrets

- `AIProvider`, `AIModel`, and `AIImageModel` are polymorphic
  (`django-polymorphic`) base models. Concrete backends subclass them and
  implement `get_instance()`, returning the matching Pydantic AI object.
- A concrete model must validate in `clean()` that its provider is the matching
  concrete provider type, in addition to the shared ownership check.
- Adding a backend means: a provider subclass, a model subclass, an image-model
  subclass when supported, migrations, admin registration, and tests.
- Store every credential and API key at rest in `EncryptedCharField`
  (`django-fernet-encrypted-fields`), following the provider, Tavily, and Exa
  models.
- Never log, serialize, or expose credential values, and never commit real
  keys.

## Capabilities and tools

Agent features are opt-in per agent with a `<feature>_enabled` boolean, plus an
optional per-user FK when the feature needs a credential or a model.

When adding a capability or tool:

1. add the flag and any owned FK to `Agent`, with ownership validation in
   `clean()`;
2. wire it in `create_pai_agent()`, raising an explicit `ValueError` when the
   feature is enabled but its credential or model is missing;
3. register it in the admin and cover it with tests, including the
   enabled-but-misconfigured failure path.

Prefer Pydantic AI's built-in tools and capabilities over bespoke
implementations. Keep local workarounds for upstream bugs small, commented with
the upstream issue, and isolated (see `MyDDGS` in `src/camille/ai.py`).

## Mattermost

When reintroducing Mattermost, consult the `v6` branch for expected behavior,
particularly:

- WebSocket event consumption and HTTP API interaction;
- bot/self/system-message filtering;
- secure Mattermost-to-Django user linking;
- per-channel conversation history and multi-user context;
- file ingestion, generated-file upload, and typing indicators;
- clear user-facing errors for unlinked users and failed runs.

Implement these incrementally behind a transport boundary with focused tests.
Do not assume a `v6` behavior exists in `v7` until it has been deliberately
ported and tested.

## Development workflow

The project targets Python 3.14+ and uses `uv`, `just`, Django's test runner,
and coverage. Do not swap these tools without an explicit project decision.

Common commands:

```bash
just makemigrations
just migrate
just runserver
just test
just buildimage
```

For focused tests, use Django's test labels:

```bash
uv run camille test tests.test_models
uv run camille test tests.test_ai
```

Known rough edges, since this is WIP:

- The test suite uses Django's test runner through `uv run camille test tests`.
  Keep model tests aligned with the current schema: slugs were removed, names
  are unique per user, and agents require an explicitly assigned or
  profile-default model.
- `just test` uses `--parallel=auto`, which can fail while serializing
  tracebacks. Fall back to `uv run camille test tests` when diagnosing.
- `src/camille/settings.py` holds development defaults: inline `SECRET_KEY` and
  `SALT_KEY`, `DEBUG = True`, empty `ALLOWED_HOSTS`, and local SQLite. These are
  not production patterns; move them to environment-driven configuration before
  any deployment.

## Change requirements

- Treat current APIs as WIP: inspect callers, migrations, and tests before
  extending or renaming anything.
- Prefer small, explicit interfaces over prematurely recreating all of `v6`.
- Add tests for new behavior, failure paths, ownership boundaries, and
  persistence semantics, using Django `TestCase` and `tests/helpers.py`.
- Keep model changes, their migrations, admin updates, and tests in the same
  change.
- Run the narrowest relevant tests first, then the full suite for changes that
  affect shared models, settings, persistence, or agent construction.
- Regularly compare this file with the codebase while working. If its
  architecture, invariants, commands, or stated project direction have
  materially diverged from the implementation, update `AGENTS.md` in the same
  change instead of preserving stale guidance.
