from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from rich.console import RenderableType
from rich.panel import Panel
from rich.table import Table


class SyncStatus(Enum):
    CREATED = "Created"
    SKIPPED = "Skipped"
    ERROR = "Error"
    NO_ACTION = "No Action"

    __STYLES__ = {
        CREATED: "green",
        SKIPPED: "yellow",
        ERROR: "red",
        NO_ACTION: "blue",
    }


@dataclass
class SyncResult:
    status: SyncStatus
    src: Path | str | None = None
    dest: Path | str | None = None
    message: str | None = None


class SyncResults(list[SyncResult]):
    def get_status_counts(self) -> dict[SyncStatus, int]:
        counts: dict[SyncStatus, int] = {status: 0 for status in SyncStatus}

        for result in self:
            counts[result.status] += 1

        return counts

    def render_summary(self) -> RenderableType:
        counts = self.get_status_counts()

        return Panel(
            f"[bold]Total:[/bold] {len(self)}\n"
            f"[green]Created:[/green] {counts[SyncStatus.CREATED]}\n"
            f"[yellow]Skipped:[/yellow] {counts[SyncStatus.SKIPPED]}\n"
            f"[red]Error:[/red] {counts[SyncStatus.ERROR]}\n"
            f"[blue]No Action:[/blue] {counts[SyncStatus.NO_ACTION]}",
            title="Sync Summary",
            expand=False,
        )

    def render_results(self) -> RenderableType:
        table = Table(title="Sync Results")

        table.add_column("Status", style="bold")
        table.add_column("Source", style="bold")
        table.add_column("Destination", style="bold")
        table.add_column("Message")

        for result in self:
            style = SyncStatus.__STYLES__.get(result.status.value, "white")
            table.add_row(
                f"[{style}]{result.status.value}[/{style}]",
                self.format_path(result.src),
                self.format_path(result.dest),
                result.message or "",
            )

        return table

    @classmethod
    def format_path(cls, path: Path | str | None) -> str:
        if path is None:
            return ""

        if isinstance(path, Path):
            path = path.expanduser().absolute()

            if path.is_relative_to(Path.cwd()):
                return f"[link={path.as_uri()}]./{path.relative_to(Path.cwd()).as_posix()}[/link]"
            if path.is_relative_to(Path.home()):
                return f"[link={path.as_uri()}]~/{path.relative_to(Path.home()).as_posix()}[/link]"

            return f"[link={path.as_uri()}]{str(path.as_posix())}[/link]"

        return str(path)
