import os
from invoke import task  # type: ignore


def get_mount_point():
    mount_point = None
    for root, dirs, _ in os.walk("/media"):
        if "CIRCUITPY" in dirs:
            mount_point = os.path.join(root, "CIRCUITPY")
            return mount_point

    raise FileNotFoundError("CIRCUITPY mount point not found")


@task
def find_device(ctx):
    """find the device mount point"""
    try:
        cpy = get_mount_point()
        print(f"Device found at {cpy}")

    except FileNotFoundError:
        print("Device not found")


@task
def install_deps(ctx):
    """install dependencies"""
    ctx.run("circup install -r cpy_requirements.txt")


@task
def sync_lib(ctx):
    """sync code with the board"""
    mount_point = get_mount_point()

    # Directory where the lib files will be copied
    destination = os.path.join(mount_point, "lib")  # type: ignore

    # Ensure the destination directory exists
    os.makedirs(destination, exist_ok=True)

    # Copy files with rsync, following symlinks
    ctx.run(f"rsync -avL --exclude '_*' lib/ {destination}/")

    # Flush buffers
    ctx.run("sync")


@task(pre=[install_deps, sync_lib])
def init(ctx):
    """initialize the board, use blink as the main code"""
    mount_point = get_mount_point()

    # Copy the main code
    ctx.run(f"cp examples/hello_feather.py {mount_point}/main.py")
