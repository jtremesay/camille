# Camille contributor guidelines

## Project direction

Camille is a work-in-progress, multi-user AI assistant built with Django and
Pydantic AI. The long-term goal is to let each user configure their own agents,
personalities, providers, credentials, memories, and capabilities. Mattermost
is the next planned transport integration.

The `v6` branch is useful for understanding previously supported behavior,
especially Mattermost, user linking, conversations, model providers, memories,
credentials, file handling, and capabilities. Treat it as a product reference,
not as code or architecture to copy blindly: `v7` is an intentional redesign
and currently implements only a subset of that behavior.

## Architecture

- Keep Django domain models and application code in `src/camille/`.
- Keep Pydantic AI persistence concerns in `src/pydanticai_django/`. Do not
  couple this package to Camille-specific users, agents, or transports.
- Keep transport adapters such as Mattermost separate from agent construction,
  domain logic, and model/provider selection.
- Implement agent features as independently composable and testable
  capabilities. Do not make a generic capability depend directly on a
  transport.
- Pass explicit user, conversation, and transport context to agents and tools.
  Avoid process-global or implicitly shared mutable state.
- Persist AI runs and resumable execution through `pydanticai_django` rather
  than adding ad hoc persistence to transports.

## Multi-user invariants

User isolation is a core requirement.

- Every customizable or sensitive object must have an explicit owner.
- Scope reads and writes by the authenticated/current user; do not fetch an
  object globally and rely only on a later authorization check.
- Validate ownership for every relation between user-owned objects. Follow the
  existing model `clean()` pattern and test both same-user success and
  cross-user rejection.
- Never share credentials, memories, agent configuration, conversation state,
  or provider settings between users unless the feature explicitly models and
  authorizes sharing.
- Keep provider and credential selection explicit and per-user. Never introduce
  a global credential fallback that could cross tenant boundaries.
- For group conversations, distinguish the agent owner, message author,
  participants, and conversation scope instead of treating them as one user.

## Django and data conventions

- Use the Django ORM and migrations for persistent state.
- Use UUIDv7 primary keys for new Camille-owned entities unless there is a
  documented reason not to.
- Use `CASCADE` for data wholly owned by its parent and `SET_NULL` for optional
  references whose target may be removed.
- Preserve human-readable, user-scoped slugs where entities are selected by
  name.
- Create and test data migrations for backfills or transformations.
- Register relevant domain models in the Django admin with useful ownership
  and stable-identifier search fields.
- Do not treat the current development settings, inline secret key, SQLite
  configuration, or enabled debug mode as production-ready patterns.

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

The project requires Python 3.14 or newer and uses `uv`, `just`, Django's test
runner, and coverage. Do not replace these tools without an explicit project
decision.

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

## Change requirements

- Treat current APIs as WIP: inspect callers and tests before extending or
  renaming them.
- Prefer small, explicit interfaces over prematurely recreating all of `v6`.
- Add tests for new behavior, failure paths, ownership boundaries, and
  persistence semantics.
- Use Django `TestCase`/`unittest` style and existing test helpers.
- Run the narrowest relevant tests first, then `just test` for changes that
  affect shared models, settings, persistence, or agent construction.
- Keep migrations and their tests in the same change as model updates.
- Update this file when the architecture or standard workflow materially
  changes.
