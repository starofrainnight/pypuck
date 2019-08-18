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
def build(**kwargs):
    """Build the distribution
    """

    kwargs = AttrDict(kwargs)
    app = PyPuck()
    app.build()


if __name__ == "__main__":
    main()
