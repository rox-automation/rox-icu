import os
import time

from click import prompt
from invoke import task  # type: ignore

CWD = os.path.dirname(os.path.realpath(__file__))


def get_mount_point():
    mount_point = None
    for root, dirs, _ in os.walk("/media"):
        if "CIRCUITPY" in dirs:
            mount_point = os.path.join(root, "CIRCUITPY")
            print(f"CIRCUITPY mount point found: {mount_point}")
            return mount_point

    if mount_point is None:
        raise FileNotFoundError("CIRCUITPY mount point not found")


@task
def clean(ctx):
    """
    Remove all files and directories that are not under version control to ensure a pristine working environment.
    Use caution as this operation cannot be undone and might remove untracked files.

    """

    ctx.run("git clean -nfdx")

    if (
        prompt(
            "Are you sure you want to remove all untracked files? (y/n)", default="n"
        )
        == "y"
    ):
        ctx.run("git clean -fdx")


@task
def lint(ctx):
    """
    Perform static analysis on the source code to check for syntax errors and enforce style consistency.
    """
    # ctx.run("ruff check src tests")
    ctx.run("pylint -E src", warn=True, pty=True)
    ctx.run("pylint -E tests", warn=True, pty=True)
    ctx.run("mypy src", warn=True, pty=True)


@task
def test(ctx):
    """
    Run tests with coverage reporting to ensure code functionality and quality.
    """
    ctx.run("pytest --cov=src --cov-report term-missing tests", pty=True)


@task
def install(ctx):
    """install dependencies"""
    ctx.run("circup install -r cpy_requirements.txt")


@task
def sync(ctx):
    """sync code with the board"""
    mount_point = get_mount_point()

    # Directory where the lib files will be copied
    destination = os.path.join(mount_point, "lib")  # type: ignore

    # Ensure the destination directory exists
    os.makedirs(destination, exist_ok=True)

    # Copy files with rsync, following symlinks
    ctx.run(f"rsync -avL --exclude '_*' embedded_lib/ {destination}/")

    # Flush buffers
    ctx.run("sync")


@task(pre=[install, sync])
def init(ctx):
    """initialize the board, use blink as the main code"""
    mount_point = get_mount_point()

    # Copy the main code
    ctx.run(f"cp examples/101_hello_icu.py {mount_point}/code.py")

    # Flush


@task
def ci(ctx):
    """
    run ci locally in a fresh container

    """
    t_start = time.time()
    # get script directory

    try:
        ctx.run(f"docker run --rm -v {CWD}:/workspace roxauto/python-ci")
    finally:
        t_end = time.time()
        print(f"CI run took {t_end - t_start:.1f} seconds")


@task
def tox(ctx):
    """run tox tests in a fresh container"""
    ctx.run(
        f"docker run --rm -it -v {CWD}:/app divio/multi-python:latest tox", pty=True
    )


@task
def build_package(ctx):
    """
    Build package in docker container.
    """

    ctx.run("rm -rf dist")
    t_start = time.time()
    # get script directory
    script_dir = os.path.dirname(os.path.realpath(__file__))
    try:
        ctx.run(
            f"docker run --rm -v {script_dir}:/workspace roxauto/python-ci /scripts/build.sh"
        )
    finally:
        t_end = time.time()
        print(f"CI run took {t_end - t_start:.1f} seconds")


@task
def release(ctx):
    """publish package to pypi"""

    token = os.getenv("PYPI_TOKEN")
    if not token:
        raise ValueError("PYPI_TOKEN environment variable is not set")

    ctx.run(
        f"docker run --rm -e PYPI_TOKEN={token} -v {CWD}:/workspace roxauto/python-ci /scripts/publish.sh"
    )
