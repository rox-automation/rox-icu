from invoke import task
import os
from click import prompt


def get_mount_point():
    mount_point = None
    for root, dirs, files in os.walk("/media"):
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
    ctx.run("ruff check src tests")
    ctx.run("mypy src")


@task
def test(ctx):
    """
    Run tests with coverage reporting to ensure code functionality and quality.
    """
    ctx.run("pytest --cov=src --cov-report term-missing tests")


@task
def install(ctx):
    """install dependencies"""
    ctx.run("circup install -r cpy_requirements.txt")


@task
def sync(ctx):
    """sync code with the board"""
    mount_point = get_mount_point()

    # Directory where the lib files will be copied
    destination = os.path.join(mount_point, "lib")

    # Ensure the destination directory exists
    os.makedirs(destination, exist_ok=True)

    # Copy files with rsync, following symlinks
    ctx.run(f"rsync -avL --exclude '_*' libraries/ {destination}/")

    # Flush buffers
    ctx.run("sync")


@task(pre=[install, sync])
def init(ctx):
    """initialize the board, use blink as the main code"""
    mount_point = get_mount_point()

    # Copy the main code
    ctx.run(f"cp examples/101_hello_icu.py {mount_point}/code.py")

    # Flush
