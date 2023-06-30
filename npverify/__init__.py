import base64
import hashlib
import json
import logging
import tarfile

import requests

logger = logging.getLogger()


def download_package(package, folder):
    url = f"https://registry.npmjs.com/{package}"
    logger.debug(f"Download {url}")
    r = requests.get(url)
    manifest = folder.joinpath(package + ".json")
    with manifest.open("wb") as f:
        for data in r.iter_content():
            f.write(data)
    latest_version = r.json()["dist-tags"]["latest"]
    url = r.json()["versions"][latest_version]["dist"]["tarball"]
    logger.debug(f"Download {url}")
    r = requests.get(url)
    tarball = folder.joinpath(package + ".tgz")
    with tarball.open("wb") as f:
        for data in r.iter_content():
            f.write(data)
    return manifest, tarball


def inspect_package(tarball):
    with tarfile.open(tarball, "r:gz") as tgz:
        print(tgz.getmembers())
        print(json.load(tgz.extractfile("package/package.json")))


def verify_package(manifest, tarball):
    with manifest.open("r") as f:
        manifest_json = json.load(f)
    with tarfile.open(tarball, "r:gz") as tgz:
        package_json = json.load(tgz.extractfile("package/package.json"))
    version = manifest_json["dist-tags"]["latest"]
    result = True
    logger.info("Compare manifest and package.json")
    for key, val in package_json.items():
        manifest_val = manifest_json["versions"][version].get(key)
        if val != manifest_val:
            logger.warning(
                f'Mismatch between manifest and package.json for "{key}"\n'
                + f"package.json\t{val}\n"
                + f"manifest\t{manifest_val}"
            )
            result = False
    logger.info("Verify integrity")
    manifest_integrity = manifest_json["versions"][version]["dist"]["integrity"]
    if not manifest_integrity.startswith("sha512-"):
        # TODO: Implement sha1
        logger.warning(f"Unknown integrity algorithm: {manifest_integrity}")
        result = False
    else:
        tarball_integrity = "sha512-" + base64.b64encode(hashlib.sha512(tarball.open("rb").read()).digest()).decode(
            "ascii"
        )
        if manifest_integrity != tarball_integrity:
            logger.error("Integrity check failed")
            result = False
    return result
