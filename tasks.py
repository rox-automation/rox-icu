from invoke import task
import os


@task
def install(ctx):
    """install dependencies"""
    ctx.run("circup install -r cpy_requirements.txt")


@task
def sync(ctx):
    """sync code with the board"""
    mount_point = None
    for root, dirs, files in os.walk("/media"):
        if "CIRCUITPY" in dirs:
            mount_point = os.path.join(root, "CIRCUITPY")
            break

    if not mount_point:
        print("CircuitPython drive not found")
        return

    print(f"CircuitPython drive found at {mount_point}")

    # Directory where the lib files will be copied
    destination = os.path.join(mount_point, "lib")

    # Ensure the destination directory exists
    os.makedirs(destination, exist_ok=True)

    # Copy files with rsync, following symlinks
    ctx.run(f"rsync -avL libraries/ {destination}/")

    # Flush buffers
    ctx.run("sync")
