#!/usr/bin/env python
import subprocess
import os
import sys
import glob

deps = [
    ['https://github.com/robmcmullen/GnomeTools.git', {'builddir': 'post_gnome'}],
    ['https://github.com/robmcmullen/OWSLib.git',],
    ['https://github.com/fathat/glsvg.git',],
    ['https://github.com/robmcmullen/pyugrid.git',],
]

parent_dep_dir = ".."
#parent_dep_link_target = {"pyfilesystem": "fs"}

parent_deps = glob.glob("%s/*/__init__.py" % parent_dep_dir)
for dep in parent_deps:
    dep = os.path.dirname(dep)
    if dep.endswith("8bit") or dep.endswith("_extra") or dep.endswith("udis"):
        continue
    here = os.path.basename(dep)
    print(dep, here)
    try:
        os.unlink(here)
    except FileNotFoundError as e:
        pass
    try:
        os.symlink(dep, here)
    except OSError as e:
        print("Couldn't symlink %s" % dep)

link_map = {
    "OWSLib": "owslib",
    "GnomeTools": "post_gnome",
}

real_call = subprocess.call
def git(args, branch=None):
    real_args = ['git']
    real_args.extend(args)
    real_call(real_args)

dry_run = False
if dry_run:
    def dry_run_call(args):
        print("in %s: %s" % (os.getcwd(), " ".join(args)))
    subprocess.call = dry_run_call
    def dry_run_symlink(source, name):
        print("in %s: %s -> %s" % (os.getcwd(), name, source))
    os.symlink = dry_run_symlink

setup = "python setup.py "

linkdir = os.getcwd()
topdir = os.path.join(os.getcwd(), "deps")
try:
    os.mkdir(topdir)
except OSError:
    # exists
    pass

for dep in deps:
    os.chdir(topdir)
    try:
        repourl, options = dep
    except ValueError:
        repourl = dep[0]
        options = {}
    if repourl.startswith("http"):
        print("UPDATING %s" % repourl)
        _, repo = os.path.split(repourl)
        repodir, _ = os.path.splitext(repo)
        if os.path.exists(repodir):
            os.chdir(repodir)
            git(['pull'])
        else:
            git(['clone', repourl])
    else:
        repodir = repourl

    builddir = options.get('builddir', ".")

    command = options.get('command',
        setup + "build_ext --inplace")
    link = repodir
    if "install" in command:
        link = None
    else:
        link = repodir
    if command:
        os.chdir(topdir)
        os.chdir(repodir)
        if 'branch' in options:
            git(['checkout', options['branch']])
        licenses = glob.glob("LICENSE*")
        os.chdir(builddir)
        subprocess.call(command.split())

    if link and sys.platform != "win32":
        os.chdir(linkdir)
        name = link_map.get(repodir, repodir)
        if name is None:
            print("No link for %s" % repodir)
        else:
            src = os.path.normpath(os.path.join("deps", repodir, builddir, name))
            if os.path.islink(name):
                os.unlink(name)
            os.symlink(src, name)

        for license in licenses:
            src = os.path.normpath(os.path.join("deps", repodir, license))
            try:
                os.symlink(src, license + "." + repodir)
            except FileExistsError as e:
                pass
