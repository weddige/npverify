import argparse
import logging
import tempfile
from pathlib import Path

from . import download_package, verify_package
from .cli import add_verbosity_argument, configure_logger

logger = logging.getLogger()

parser = argparse.ArgumentParser(description="Node Package Verify")
subparsers = parser.add_subparsers(dest="cmd")
parser_download = subparsers.add_parser("download")
parser_download.add_argument("PACKAGE")
parser_download.add_argument("TARGET", type=Path, default=Path("."), nargs="?")
parser_compare = subparsers.add_parser("compare")
parser_compare.add_argument("MANIFEST", type=Path)
parser_compare.add_argument("TARBALL", type=Path, nargs="?")
parser_verify = subparsers.add_parser("verify")
parser_verify.add_argument("PACKAGE")
add_verbosity_argument(parser)
args = parser.parse_args()

configure_logger(args)

if args.cmd == "download":
    download_package(args.PACKAGE, args.TARGET)
elif args.cmd == "compare":
    ret = verify_package(args.MANIFEST, args.TARBALL)
    exit(0 if ret else 1)
elif args.cmd == "verify":
    with tempfile.TemporaryDirectory() as dir:
        manifest, tarball = download_package(args.PACKAGE, Path(dir))
        errors = verify_package(manifest, tarball)
        exit(1 if errors else 0)
