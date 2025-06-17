import os
from invoke import task  # type: ignore


def get_mount_point():
    mount_point = None
    for root, dirs, _ in os.walk("/media"):
        if "CIRCUITPY" in dirs:
            mount_point = os.path.join(root, "CIRCUITPY")
            return mount_point

    raise FileNotFoundError("CIRCUITPY mount point not found")


def get_available_examples():
    """Get list of available Python example scripts"""
    examples_dir = "examples"
    if not os.path.exists(examples_dir):
        return []

    examples = []
    for item in os.listdir(examples_dir):
        if item.endswith('.py') and os.path.isfile(os.path.join(examples_dir, item)):
            examples.append(item[:-3])  # Remove .py extension

    return sorted(examples)


def choose_example():
    """Interactive example selection"""
    examples = get_available_examples()

    if not examples:
        print("No Python examples found in examples/ directory")
        return None

    print("\nAvailable examples:")
    for i, example in enumerate(examples, 1):
        print(f"  {i}. {example}")

    while True:
        try:
            choice = input(f"\nSelect example (1-{len(examples)}) or 'q' to quit: ").strip()
            if choice.lower() == 'q':
                return None

            index = int(choice) - 1
            if 0 <= index < len(examples):
                return examples[index]
            else:
                print(f"Please enter a number between 1 and {len(examples)}")
        except (ValueError, KeyboardInterrupt):
            print("\nOperation cancelled")
            return None


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


@task
def list_examples(ctx):
    """list available example scripts"""
    examples = get_available_examples()

    if not examples:
        print("No Python examples found in examples/ directory")
        return

    print("Available examples:")
    for example in examples:
        print(f"  - {example}")


@task
def install(ctx, example=None):
    """install example script as main.py on the device"""
    mount_point = get_mount_point()

    # If no example provided, show interactive menu
    if example is None:
        example = choose_example()
        if example is None:
            return

    # Build path to example script
    example_path = f"examples/{example}"
    if not example.endswith('.py'):
        example_path += '.py'

    # Check if example exists
    if not os.path.exists(example_path):
        print(f"Example script {example_path} not found")
        # Show available options
        available = get_available_examples()
        if available:
            print(f"Available examples: {', '.join(available)}")
        return

    # Copy example to main.py
    main_py_path = os.path.join(mount_point, "main.py")
    ctx.run(f"cp {example_path} {main_py_path}")
    print(f"Installed {example_path} as main.py")


@task(pre=[install_deps, sync_lib])
def init(ctx):
    """initialize the board, use blink as the main code"""
    mount_point = get_mount_point()

    # Remove code.py if it exists
    code_py_path = os.path.join(mount_point, "code.py")
    if os.path.exists(code_py_path):
        os.remove(code_py_path)
        print(f"Removed {code_py_path}")

    # Copy the main code
    ctx.run(f"cp examples/hello_feather.py {mount_point}/main.py")
