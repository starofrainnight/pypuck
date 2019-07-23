#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Console script for pypuck."""

import click
import pycurl
import os.path
from attrdict import AttrDict


@click.command()
def main(**kwargs):
    """Console script for pypuck."""

    kwargs = AttrDict(kwargs)

    url = "https://github.com/winpython/winpython/releases/download/1.11.20181031/Winpython64-3.7.1.0Zero.exe"
    proxy = "%s://%s:%s" % ("socks5", "127.0.0.1", "11086")
    curl = pycurl.Curl()
    try:
        curl.setopt(pycurl.URL, url)
        file = open(os.path.basename(url), "wb")
        curl.setopt(pycurl.WRITEFUNCTION, file.write)
        curl.setopt(pycurl.FOLLOWLOCATION, 1)
        curl.setopt(pycurl.HEADER, True)
        curl.setopt(pycurl.NOPROGRESS, 0)
        curl.setopt(pycurl.SSL_VERIFYPEER, False)
        curl.setopt(pycurl.SSL_VERIFYHOST, False)
        curl.setopt(pycurl.VERBOSE, 1)
        curl.setopt(pycurl.PROXY, proxy)
        curl.setopt(
            pycurl.USERAGENT,
            "Mozilla/5.2 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50324)",
        )
        curl.perform()
    finally:
        curl.close()


if __name__ == "__main__":
    main()
