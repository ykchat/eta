from eta.models import Operator
from eta.context import Context

async def update_operators(context: Context) -> list[Operator]:

    operators: list[Operator] = []
    for source_id in context.source_ids():
        provider = await context.provider(source_id)
        operators_from_source = await provider.get_operators()
        context.static_db().save_operators(source_id, operators_from_source)
        operators.extend(operators_from_source)

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