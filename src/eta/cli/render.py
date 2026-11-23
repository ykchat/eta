import functools
from collections.abc import Callable

import httpx
import typer
from rich.console import Console
from rich.table import Table
from rich.markup import escape

from eta.models import Source, Operator
from eta.errors import ConfigError, SourceNotFoundError

console = Console()

def handle_errors[**P, T](command: Callable[P, T]) -> Callable[P, T]:

    @functools.wraps(command)    # 引数の情報(Typer が読む)を、元の関数から写す
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        try:
            return command(*args, **kwargs)
        except ConfigError as error:
            console.print(f"[red]{escape(str(error))}[/]")
            raise typer.Exit(1)
        except SourceNotFoundError as error:
            console.print(f"[red]{escape(str(error))}[/]")
            raise typer.Exit(1)
        except httpx.HTTPStatusError as error:
            console.print(f"[dim]{escape(str(error).splitlines()[0])}[/]")
            raise typer.Exit(1)
        except httpx.HTTPError as error:
            console.print(f"[red]接続に失敗しました ({type(error).__name__})[/]")
            console.print(f"[dim]{escape(str(error.request.url))}[/]")
            raise typer.Exit(1)

    return wrapper

def show_sources(sources: list[Source]) -> None:

    table = Table(
        title=f"取得元: {len(sources)} 件",
        title_justify="left",
        header_style="bold cyan",
    )
    table.add_column("取得元", style="bold")
    table.add_column("事業者数", justify="right")
    table.add_column("更新日時")

    for source in sources:
        updated_at = source.updated_at.astimezone().strftime("%Y-%m-%d %H:%M") if source.updated_at else "-"
        table.add_row(
            escape(source.id),
            str(source.operator_count),
            updated_at
        )

    console.print(table)

def show_operators(operators: list[Operator], query: str | None) -> None:

    if not operators:
        prefix = f"「{escape(query)}」に一致する" if query else ""
        console.print(f"[yellow]{prefix}事業者は見つかりません[/]")
        return

    table = Table(
        title=f"事業者: {len(operators)} 件",
        title_justify="left",
        header_style="bold cyan",
    )
    table.add_column("名前", style="bold")
    table.add_column("事業者")
    table.add_column("Operator", style="dim")

    for operator in operators:
        table.add_row(
            escape(operator.name),
            escape(operator.title("ja") or "-"),
            escape(operator.title("en") or "-"),
        )

    console.print(table)

