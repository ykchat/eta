from enum import StrEnum
from typing import Annotated

import typer

from eta.cli import context, render
from eta import services

class Target(StrEnum):

    OPERATORS = "operators"

app = typer.Typer(
    help="Show bus arrival information.",
    add_completion=False, 
    no_args_is_help=True, 
    pretty_exceptions_show_locals=False
)

@app.command("search", help="Search by part of a name.")
@render.handle_errors
def search(
    target: Annotated[Target, typer.Argument(help="What to search")],
    query: Annotated[str | None, typer.Argument(help="Part of a name (all when omitted)")] = None,
) -> None:

    match target:
        case Target.OPERATORS:
            operators = context.call(services.get_operators, query)
            render.show_operators(operators, query)  

@app.command("update", help="Import local data.")
@render.handle_errors
def update(
    target: Annotated[Target, typer.Argument(help="What to search")],
) -> None:

    match target:
        case Target.OPERATORS:
            operators = context.call(services.update_operators)
            render.console.print(f"事業者を {len(operators)} 件取り込みました")