from typing import Annotated

import typer

from eta.cli import context, render
from eta import services

app = typer.Typer(
    help="Show bus arrival information.",
    add_completion=False, 
    no_args_is_help=True, 
    pretty_exceptions_show_locals=False
)

@app.command("search", help="Search by part of a name.")
@render.handle_errors
def search(
    query: Annotated[str | None, typer.Argument(help="Part of a name (all when omitted)")] = None,
    to_operator: Annotated[bool, typer.Option("--operator", help="Search operator")] = False,
) -> None:

    if not to_operator:
        render.console.print("[yellow]バス停の検索はまだありません。事業者を検索するときは --operator を付けてください[/]")
        raise typer.Exit(1)

    operators = context.call(services.get_operators, query)
    render.show_operators(operators, query)  

@app.command("update", help="Import local data.")
@render.handle_errors
def update(
    to_operator: Annotated[bool, typer.Option("--operator", help="Import operators")] = False,
) -> None:

    if not to_operator:
        render.console.print("[yellow]バス停の更新はまだありません。事業者を更新するときは --operator を付けてください[/]")
        raise typer.Exit(1)

    operators = context.call(services.update_operators)
    render.console.print(f"事業者を {len(operators)} 件取り込みました")