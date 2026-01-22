from pydantic_ai import RunContext

from camille.ai.deps import Deps
from camille.ai.schemas import ProfileSchema


def user_profile_context(ctx: RunContext[Deps]) -> str:
    profile_schema = ProfileSchema.from_orm(ctx.deps.profile)
    return f"""\
You are talking with:

```json
{profile_schema.model_dump_json()}
```
"""
