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
            "python-*/*.txt",
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

    def _cpu_bits_text(self, bits):
        if bits is None:
            if self.is_64bits_system():
                return "64"
            else:
                return "32"
        else:
            return str(bits)

    def _cpu_arch(self, cpu_bits=None):
        return "x" + self._cpu_bits_text(cpu_bits)

    def download_winpython_core(self, cpu_bits=None):
        # `~` will be expanded as winpython-dir/settings
        cache_dir = os.path.expanduser("~/.pypuck/cache")
        os.makedirs(cache_dir, exist_ok=True)

        winpython_cpu = self._cpu_bits_text(cpu_bits)
        if winpython_cpu == "64":
            sha256_value = "7e95875b3217429b54939d45d69f87b6f2013a6cbd2e08b52429b466785bdba2"  # noqa
        else:
            sha256_value = "f63295ee104790e80ca1a7e67274d57f1a22aa33dce5850bd9f3464b709739d6"  # noqa

        # Latest winpython won't so mature for all packages

        url = (
            "https://github.com/winpython/winpython/releases/download/4.3.20210620/Winpython%s-3.8.10.0dot.exe"  # noqa
            % winpython_cpu
        )
        file_name = os.path.basename(url)
        if "=" in file_name:
            after_equal_index = file_name.index("=") + 1
            file_name = file_name[after_equal_index:]
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

    def pack(self, work_dir, archive_file):
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
            script_entry = os.path.join(work_dir, script_path.stem + ".bat")
            with open(script_entry, "w") as f:
                f.write(script_content.format(target_exe))

    def build(self, cpu_bits=None):
        if not os.path.exists("setup.py"):
            raise FileNotFoundError("setup.py not found!")

        file_path = self.download_winpython_core(cpu_bits)

        build_dir = "./build"
        work_dir = os.path.join(build_dir, "work")
        dist_dir = os.path.join(os.curdir, "dist")

        work_dir = os.path.realpath(work_dir).replace("/", os.sep)
        dist_dir = os.path.realpath(dist_dir).replace("/", os.sep)

        # Rebuild build dir
        shutil.rmtree(build_dir, ignore_errors=True)

        # FIXME: (On Windows) Seems if we call other function on the same
        # directory after rmtree(), it will failed to permisson problems. We
        # have to wait for a while, after that function before doing any
        # action.
        time.sleep(3)

        os.makedirs(work_dir, exist_ok=True)
        os.makedirs(dist_dir, exist_ok=True)

        click.echo("Silent install winpython to build cache ...")

        click.echo("work_dir: %s" % work_dir)

        # Downloaded python 3.6.8.0 package is an 7zip package, we just extract
        # it to target directory.
        cmd = '7z x %s -y -o"%s"'
        cmd = cmd % (file_path, work_dir)
        p = run(cmd, shell=True)

        click.echo("Clone pip settings of this python environment ...")

        # Change the work dir if it have more one level folder
        inner_dirs = glob.glob(os.path.join(work_dir, "WPy*"))
        if len(inner_dirs) > 0:
            work_dir = os.path.join(work_dir, inner_dirs[0])

        my_pip_dir = os.path.expanduser("~/pip")
        working_pip_dir = os.path.join(work_dir, "settings", "pip")
        if os.path.exists(my_pip_dir):
            shutil.copytree(my_pip_dir, working_pip_dir)

        click.echo("Install requirements ...")

        # First install the setup.py on local directory (just for the
        # requirements ...)
        #
        # pip have better depenences resolver than just install by setup.py
        p = run(
            'cmd /C ""%s\\scripts\\env.bat" & python -m pip install ."'
            % work_dir,
            shell=True,
        )

        click.echo("Setup result: %s" % p.returncode)

        p = run(
            'cmd /C ""%s\\scripts\\env.bat" & python setup.py --name"'
            % work_dir,
            shell=True,
            stdout=PIPE,
        )

        package_name = p.stdout.decode().strip()

        click.echo("Got package name : %s" % package_name)

        p = run(
            'cmd /C ""%s\\scripts\\env.bat" & python setup.py --version"'
            % work_dir,
            shell=True,
            stdout=PIPE,
        )

        package_version = p.stdout.decode().strip()
        click.echo("Got package version : %s" % package_version)

        click.echo("Uninstall package %s ..." % package_name)

        # Uninstall the package specificly, then reinstall it for get it's
        # scripts snapshot
        p = run(
            'cmd /C "'
            '"%s\\scripts\\env.bat" & python -m pip uninstall -y %s'
            '"' % (work_dir, package_name),
            shell=True,
        )

        # FIXME: (On Windows) The files not be deleted after uninstall, we
        # should wait for a while
        time.sleep(3)

        click.echo("Get snapshot of scripts...")

        before_scripts_snapshot = self.get_scripts_snapshot(work_dir)

        click.echo("Install again (capture generated scripts)...")

        p = run(
            'cmd /C ""%s\\scripts\\env.bat" & python -m pip install ."'
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

        click.echo("Remove pip settings of working python environment ...")

        shutil.rmtree(working_pip_dir, ignore_errors=True)

        dist_file_path = os.path.join(
            dist_dir,
            "%s-%s-%s-bin.zip"
            % (package_name, package_version, self._cpu_arch(cpu_bits)),
        )

        # Remove the dist file if already exists
        try:
            os.remove(dist_file_path)
        except OSError:
            pass

        # FIXME: (On Windows) Wait for a while, for those dir/file remove
        # operations ...
        time.sleep(3)

        self.pack(work_dir, dist_file_path)

        click.echo("Generated package : %s !" % dist_file_path)
        click.echo("Done!")
