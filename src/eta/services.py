from eta.models import Operator
from eta.context import Context

async def update_operators(context: Context) -> list[Operator]:

    provider = await context.provider()
    operators = await provider.get_operators()
    context.static_db().save_operators(operators)

    return operators

async def get_operators(context: Context, query: str | None) -> list[Operator]:

    operators = context.static_db().get_operators()

    if not query:
        return operators

    return [operator for operator in operators if matches(operator, query)]

def matches(operator: Operator, query: str) -> bool:

    query = query.casefold()
    targets = (operator.title("ja"), operator.title("en"), operator.name)

    return any(query in target.casefold() for target in targets if target) 