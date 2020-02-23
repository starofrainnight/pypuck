# -*- coding: utf-8 -*-

"""Main module."""

import os
import time
import glob
import os.path
import click
import requests
import hashlib
import shutil
import pathlib
from subprocess import run, PIPE
from requests import Timeout, ConnectTimeout, ConnectionError
from .exceptions import DownloadError, FileVerificationError


class PyPuck(object):
    def __init__(self, *args, **kwargs):
        pass

    def is_64bits_system(self):
        import struct

        return struct.calcsize("P") * 8 == 64

    def _download_once(self, url, outfile, is_resume):
        user_agent = "Mozilla/5.2 "
        user_agent += "("
        user_agent += "compatible; "
        user_agent += "MSIE 6.0; "
        user_agent += "Windows NT 5.1; "
        user_agent += "SV1; "
        user_agent += ".NET CLR 1.1.4322; "
        user_agent += ".NET CLR 2.0.50324"
        user_agent += ")"
        headers = {"user-agent": user_agent}

        got_size = 0
        if is_resume:
            got_size = os.fstat(outfile.fileno()).st_size
            headers["Range"] = "bytes=%s-" % got_size

        response = requests.get(
            url,
            headers=headers,
            stream=True,
            allow_redirects=True,
            timeout=10,
            verify=False,
        )

        for chunk in response.iter_content(chunk_size=1024):
            if not chunk:
                # filter out keep-alive new chunks
                continue

            outfile.write(chunk)
            got_size += len(chunk)
            click.echo("*", nl=False)
            outfile.flush()

    def download_file(self, url, outfile_path):
        mode = "wb"
        is_resume = False
        max_failed = 99
        failed = 0

        click.echo("Downloading : ", nl=False)
        while True:
            try:
                with open(outfile_path, mode) as f:
                    self._download_once(url, f, is_resume=is_resume)
                    click.echo("... Done!")
                    return
            except (Timeout, ConnectTimeout, ConnectionError):
                failed += 1

                if failed >= max_failed:
                    break

                is_resume = True
                mode = "ab"

                time.sleep(5)  # Try after 5 seconds
                click.echo("Try again ...")

        # Failed to dowload the file
        raise DownloadError()

    def tidy_winpython(self, target_dir):
        """Remove all winpython files that we don't needs for package our
        application.
        """

        patterns = [
            "*.exe",
            "unins*.dat",
            "notebooks/docs",
            "python-*/include",
            "python-*/libs",
            "python-*/Doc",
            "**/__pycache__",
        ]

        for pattern in patterns:
            iter_paths = glob.iglob(
                os.path.join(target_dir, pattern), recursive=True
            )

            for apath in iter_paths:
                if os.path.isfile(apath):
                    try:
                        os.remove(apath)
                    except OSError:
                        pass
                elif os.path.isdir(apath):
                    shutil.rmtree(apath, ignore_errors=True)

    def download_winpython_core(self):
        # Fixed `~` will be expanded as local-dir/settings
        cache_dir = "%s%s/.pypuck/cache" % (
            os.environ["HOMEDRIVE"],
            os.environ["HOMEPATH"],
        )
        os.makedirs(cache_dir, exist_ok=True)

        if self.is_64bits_system():
            winpython_cpu = "64"
            sha256_value = "8a821f16657e673c49de0f70fbe610dff3a0da4117bec33103700a15807380ee"  # noqa
        else:
            winpython_cpu = "32"
            sha256_value = "2982466f05e8bde7f850925f533a1fa529b84fe000f0cd0642cd4375f8a795c4"  # noqa

        # Latest winpython won't so mature for all packages
        url = (
            "https://bintray.com/starofrainnight/binpkgs/download_file?file_path=WinPython%s-3.6.8.0Zero-7z.exe"  # noqa
            % winpython_cpu
        )
        file_name = os.path.basename(url)
        file_name = file_name[file_name.index("=")+1:]
        file_path = os.path.join(cache_dir, file_name)

        if (
            os.path.exists(file_path)
            and hashlib.sha256(open(file_path, "rb").read())
            .hexdigest()
            .lower()
            == sha256_value
        ):
            click.echo("Winpython core exists.")
            return file_path

        self.download_file(url, file_path)

        if (
            os.path.exists(file_path)
            and hashlib.sha256(open(file_path, "rb").read())
            .hexdigest()
            .lower()
            == sha256_value
        ):
            click.echo("Winpython core download successed!")
            return file_path

        raise FileVerificationError(
            "Failed to verify downloaded winpython binary from %s" % url
        )

    def pack(self, work_dir, to_dir):
        archive_file = os.path.join(to_dir, "dist.zip")

        # Remove the old archive first, otherwise 7z will append files
        # into the old archive!
        try:
            os.remove(archive_file)
        except OSError:
            pass

        run('7z a "%s" .' % archive_file, shell=True, cwd=work_dir)

    def get_scripts_snapshot(self, work_dir):
        return glob.glob(os.path.join(work_dir, "python-*/Scripts/*.exe"))

    def create_script_entries(self, work_dir, scripts):
        scripts = list(scripts)
        script_content = """@echo off
setlocal
call "%~dp0scripts/env.bat"
"%~dp0{}" %*
endlocal
"""

        for script in scripts:
            script_path = pathlib.Path(script)
            target_exe = os.fspath(script_path.relative_to(work_dir))
            script_content.format(target_exe)
            script_entry = os.path.join(work_dir, script_path.stem + ".bat")
            with open(script_entry, "w") as f:
                f.write(script_content.format(target_exe))

    def build(self):
        if not os.path.exists("setup.py"):
            raise FileNotFoundError("setup.py not found!")

        file_path = self.download_winpython_core()

        build_dir = "./build"
        work_dir = os.path.join(build_dir, "work")
        dist_dir = os.path.join(build_dir, "dist")

        work_dir = os.path.realpath(work_dir).replace("/", os.sep)
        dist_dir = os.path.realpath(dist_dir).replace("/", os.sep)

        # Rebuild build dir
        shutil.rmtree(build_dir, ignore_errors=True)
        os.makedirs(work_dir, exist_ok=True)
        os.makedirs(dist_dir, exist_ok=True)

        click.echo("Silent install winpython to build cache ...")

        click.echo("work_dir: %s" % work_dir)

        # Downloaded python 3.6.8.0 package is an 7zip package, we just extract
        # it to target directory.
        cmd = '7z x %s -y -o"%s"'
        cmd = cmd % (file_path, work_dir)
        p = run(cmd, shell=True)

        click.echo("Install requirements ...")

        # First install the setup.py on local directory (just for the
        # requirements ...)
        p = run(
            'cmd /C "call "%s\\scripts\\env.bat" & python setup.py install"'
            % work_dir,
            shell=True,
        )

        click.echo("Setup result: %s" % p.returncode)

        p = run(
            'cmd /C "call "%s\\scripts\\env.bat" & python setup.py --name"'
            % work_dir,
            shell=True,
            stdout=PIPE,
        )

        package_name = p.stdout.decode().strip()

        click.echo("Got package name : %s" % package_name)

        click.echo("Uninstall package %s ..." % package_name)

        # Uninstall the package specificly, then reinstall it for get it's
        # scripts snapshot
        p = run(
            'cmd /C "'
            'call "%s\\scripts\\env.bat" & python -m pip uninstall -y %s'
            '"' % (work_dir, package_name),
            shell=True,
        )

        click.echo("Get snapshot of scripts...")

        before_scripts_snapshot = self.get_scripts_snapshot(work_dir)

        click.echo("Install again (capture generated scripts)...")

        p = run(
            'cmd /C "call "%s\\scripts\\env.bat" & python setup.py install"'
            % work_dir,
            shell=True,
        )

        after_scripts_snapshot = self.get_scripts_snapshot(work_dir)

        click.echo("Ensure python movable...")

        # Use echo to skip the "PAUSE" in that script!
        run(
            'cmd /C echo | call "%s\\scripts\\make_winpython_movable.bat"'
            % work_dir,
            shell=True,
        )

        click.echo("Remove unused binaries...")

        self.tidy_winpython(work_dir)

        scripts = set(after_scripts_snapshot) - set(before_scripts_snapshot)

        click.echo("Captured scripts: %s" % scripts)

        click.echo("Create script entries ...")

        self.create_script_entries(work_dir, scripts)

        click.echo("Packing distribution ...")

        self.pack(work_dir, dist_dir)

        click.echo("Done!")
