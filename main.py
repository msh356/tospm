#!/usr/bin/env python3
import sys
import os
import random
import subprocess
from debian import deb822
from pathlib import Path
import shutil
import zipfile

print("TOSPM - by msh356")

if len(sys.argv) < 3:
    exit("invalid arguments")

if sys.argv[1] == "deb":
    print("converting Debian (dpkg) package!")
    print("getting ready temporary directory...")
    tmpdirname = f"/tmp/tospm_{random.randint(0, 99999)}"
    os.makedirs(tmpdirname)
    print("unpacking...")
    subprocess.run(["dpkg-deb", "-x", sys.argv[2], tmpdirname + "/root"])
    subprocess.run(["dpkg-deb", "-e", sys.argv[2], tmpdirname + "/DEBIAN"])
    print("reading control file...")
    cfile = open(tmpdirname + "/DEBIAN/control")
    controlinfo = deb822.Deb822(cfile.read())
    cfile.close()
    print("--- BEGIN PACKAGE INFO ---")
    print(f"Name: {controlinfo['Package']}")
    print(f"Description: {controlinfo['Description']}")
    print(f"Version: {controlinfo['Version']}")
    print("--- END PACKAGE INFO ---")
    print("creating install script...")
    install_sh = f"""#!/bin/sh
set -e

echo "Made by TOSPM!"
echo "Installing {controlinfo['Package']}..."
    
if [ "$(id -u)" -ne 0 ]; then
    echo "Error: run as root"
    exit 1
fi

cp -a sources/* /

echo "Fixing permissions in bin directories..."
for dir in /bin /sbin /usr/bin /usr/sbin /usr/local/bin /usr/local/sbin; do
    if [ -d "$dir" ]; then
        find "$dir" -maxdepth 1 -type f -exec chmod +x {{}} + 2>/dev/null || true
    fi
done

echo "Installed {controlinfo['Package']} {controlinfo['Version']}"
"""
    os.makedirs(tmpdirname + "/package", exist_ok=True)
    open(tmpdirname + "/package/install.sh", "w").write(install_sh)
    print("written install.sh!")
    Path(tmpdirname + "/package/install.sh").chmod(0o755)
    print("set correct rights")
    print("copying tree...")
    src = Path(tmpdirname) / "root"
    dst = Path(tmpdirname) / "package/sources"
    shutil.copytree(src, dst, symlinks=True)
    print("ok! now zipping...")
    zip_path = Path.cwd() / f"{controlinfo['Package']}-{controlinfo['Version']}.spm.zip"
    base_dir = Path(tmpdirname) / "package"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for path in base_dir.rglob("*"):
            mode = path.stat().st_mode
            arcname = path.relative_to(base_dir)
            
            zinfo = zipfile.ZipInfo.from_file(str(path), arcname=str(arcname))
            zinfo.external_attr = mode << 16
            zinfo.create_system = 3
            
            if path.is_file():
                with path.open("rb") as f:
                    z.writestr(zinfo, f.read())
            elif path.is_dir():
                z.writestr(zinfo, "")
    print("saved in working dir")
elif sys.argv[1] == "arch":
    print("converting Arch Linux (.tar.zst) package!")
    print("getting ready temporary directory...")
    tmpdirname = f"/tmp/tospm_{random.randint(0, 99999)}"
    os.makedirs(tmpdirname)
    print("unpacking...")
else:
    print("no method selected!")
