import argparse
import os
import shutil
import sys
import PyInstaller.__main__
import colorama


PKG_DIR_NAME = "package"
PKG_DIR = f"./{PKG_DIR_NAME}"
PKG_ASSETS_DIR_NAME = "packaging_assets"

STEP_COLOR = colorama.Fore.LIGHTCYAN_EX
ERROR_COLOR = colorama.Fore.LIGHTRED_EX
SUCCESS_COLOR = colorama.Fore.LIGHTGREEN_EX

project_path = os.path.dirname(os.path.realpath(__file__))
pkgDirPathAbsolute = os.path.join(project_path, PKG_DIR_NAME)
pkgDirAssetsPathAbsolute = os.path.join(project_path, PKG_ASSETS_DIR_NAME)


def step(text: str):
    print(f"{STEP_COLOR}{text}")


def error(text: str):
    print(f"{ERROR_COLOR}An error occurred during the packaging process:")
    print(f"{text}\n")
    sys.exit(1)


def success(text: str):
    print(f"{SUCCESS_COLOR}{text}")


colorama.init(autoreset=True)
parser = argparse.ArgumentParser(
    description="Packaging script for Keyboard Forecast Service", allow_abbrev=False
)
parser.add_argument(
    "-c",
    "--clean",
    action="store_true",
    help="delete the package directory prior to build",
)
args = parser.parse_args()

if args.clean:
    step("Deleting the package directory...")
    if os.path.exists(PKG_DIR) and os.path.isdir(PKG_DIR):
        shutil.rmtree(PKG_DIR)

step("Building a self-contained package with PyInstaller...")
PyInstaller.__main__.run(
    [
        "src/service.py",
        "--name=keebforecast",
        "--hidden-import=win32timezone",
        f"--workpath={PKG_DIR}/build",
        f"--distpath={PKG_DIR}",
        f"--specpath={PKG_DIR}",
        # f"--runtime-tmpdir={os.path.expandvars("%LOCALAPPDATA%\\Programs\\keyboard-forecast")}",
        "--runtime-tmpdir=.",
        "--clean",
        "--noconfirm",
        "--onefile",
    ]
)
