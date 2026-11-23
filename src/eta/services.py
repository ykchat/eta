from eta.models import Source, Operator
from eta.context import Context
from eta.errors import SourceNotFoundError

async def get_sources(context: Context) -> list[Source]:

    sources_by_id = {source.id: source for source in context.static_db().get_sources()}

    return [sources_by_id.get(id, Source(id=id)) for id in context.source_ids()]

def matches(operator: Operator, query: str) -> bool:

    query = query.casefold()
    targets = (operator.title("ja"), operator.title("en"), operator.name)

    return any(query in target.casefold() for target in targets if target)

async def get_operators(context: Context, query: str | None) -> list[Operator]:

    operators = context.static_db().get_operators()

    if not query:
        return operators

    return [operator for operator in operators if matches(operator, query)]

async def update_operators(context: Context, source_id: str | None = None) -> list[Operator]:

    source_ids = context.source_ids()

    if source_id is not None:
        if source_id not in source_ids:
            raise SourceNotFoundError(f"{source_id} not found (choose from {', '.join(source_ids)})")
        source_ids = [source_id]

    operators: list[Operator] = []
    for id in source_ids:
        provider = await context.provider(id)
        operators_from_source = await provider.get_operators()
        context.static_db().save_operators(id, operators_from_source)
        operators.extend(operators_from_source)

    return operators