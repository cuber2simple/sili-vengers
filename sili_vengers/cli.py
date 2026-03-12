#!/usr/bin/env python3
"""Sili-vengers CLI - Multi-agent orchestration for Claude Code"""

import click
from sili_vengers.commands.init_cmd import init
from sili_vengers.commands.start_cmd import start
from sili_vengers.commands.resume_cmd import resume
from sili_vengers.commands.stop_cmd import stop
from sili_vengers.commands.crew_cmd import crew
from sili_vengers.commands.status_cmd import status
from sili_vengers.commands.agents_cmd import agents
from sili_vengers.commands.task_cmd import task
from sili_vengers.commands.log_cmd import log


def _get_version():
    try:
        from importlib.metadata import version
        return version("sili-vengers")
    except Exception:
        return "unknown"


@click.group()
@click.version_option(version=_get_version(), prog_name="sili-vengers")
def cli():
    """
    ⚡ Sili-vengers - Multi-agent Claude Code orchestration

    Your AI crew, assembled and ready.
    """
    pass


cli.add_command(init)
cli.add_command(start)
cli.add_command(resume)
cli.add_command(stop)
cli.add_command(crew)
cli.add_command(status)
cli.add_command(agents)
cli.add_command(task)
cli.add_command(log)


if __name__ == "__main__":
    cli()
