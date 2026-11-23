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

sources_app = typer.Typer(
    help="Manage data sources.",
    no_args_is_help=True
)
app.add_typer(sources_app, name="sources")

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
    target: Annotated[Target, typer.Argument(help="What to update")],
    source_id: Annotated[str | None, typer.Option("--source", help="Source to import (all when omitted)")] = None,
) -> None:

    match target:
        case Target.OPERATORS:
            operators = context.call(services.update_operators, source_id)
            render.console.print(f"事業者を {len(operators)} 件取り込みました")


@sources_app.command("list", help="List data sources.")
@render.handle_errors
def list_sources() -> None:

    sources = context.call(services.get_sources)
    render.show_sources(sources)