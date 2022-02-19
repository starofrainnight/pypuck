#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Console script for pypuck."""

import click
from attrdict import AttrDict
from .pypuck import PyPuck


@click.group()
def main():
    """Console script for pypuck."""
    pass


@main.command()
@click.option(
    "--cpu-bits", "-c", type=click.Choice(["32", "64", ""]), default=""
)
def build(**kwargs):
    """Build the distribution
    """

    kwargs = AttrDict(kwargs)
    app = PyPuck()
    if len(kwargs.cpu_bits) <= 0:
        app.build()
    else:
        app.build(int(kwargs.cpu_bits))


if __name__ == "__main__":
    main()
