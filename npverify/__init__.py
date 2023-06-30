import base64
import hashlib
import json
import logging
import re
import tarfile

import requests

from .package import normalize, TODO

logger = logging.getLogger()


def download_package(package, folder):
    url = f"https://registry.npmjs.com/{package}"
    logger.debug(f"Download {url}")
    r = requests.get(url)
    base_name = re.sub("[^a-zA-z0-9-]", "_", package)
    manifest = folder.joinpath(base_name + ".json")
    with manifest.open("wb") as f:
        for data in r.iter_content():
            f.write(data)
    latest_version = r.json()["dist-tags"]["latest"]
    url = r.json()["versions"][latest_version]["dist"]["tarball"]
    logger.debug(f"Download {url}")
    r = requests.get(url)
    tarball = folder.joinpath(base_name + ".tgz")
    with tarball.open("wb") as f:
        for data in r.iter_content():
            f.write(data)
    return manifest, tarball


def verify_package(manifest, tarball):
    with manifest.open("r") as f:
        manifest_json = json.load(f)
    try:
        with tarfile.open(tarball, "r:gz") as tgz:
            package_json = json.load(tgz.extractfile("package/package.json"))
    except Exception as e:
        logger.error(e)
        return {"EXCEPTION:PACKAGE"}
    version = manifest_json["dist-tags"]["latest"]
    result = set()
    logger.info("Compare manifest and package.json")
    normalized_package_json = normalize(package_json)
    keys = set(package_json) | set(normalized_package_json)
    for key in keys:
        manifest_val = manifest_json["versions"][version].get(key)
        package_json_val = package_json.get(key)
        normalized_val = normalized_package_json.get(key)
        ok = manifest_val == package_json_val or manifest_val == normalized_val
        if not ok:
            if key in TODO:
                logger.debug(
                    f'Mismatch between manifest and package.json for "{key}"\n'
                    + f"package.json\t\t{package_json_val}\n"
                    + f"package.json (norm)\t{normalized_val}\n"
                    + f"manifest\t\t{manifest_val}"
                )
            else:
                logger.warning(
                    f'Mismatch between manifest and package.json for "{key}"\n'
                    + f"package.json\t\t{package_json_val}\n"
                    + f"package.json (norm)\t{normalized_val}\n"
                    + f"manifest\t\t{manifest_val}"
                )
                result.add(key)
    logger.info("Verify integrity")
    manifest_integrity = manifest_json["versions"][version]["dist"]["integrity"]
    if not manifest_integrity.startswith("sha512-"):
        # TODO: Implement sha1
        logger.warning(f"Unknown integrity algorithm: {manifest_integrity}")
        result.add("dist.integrity")
    else:
        tarball_integrity = "sha512-" + base64.b64encode(hashlib.sha512(tarball.open("rb").read()).digest()).decode(
            "ascii"
        )
        if manifest_integrity != tarball_integrity:
            logger.error("Integrity check failed")
            result.add("dist.integrity")
    return result
