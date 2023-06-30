import re
import urllib.parse

TODO = ["bin", "repository", "files", "bugs"]


def normalizePerson(person):
    # First unparse
    if isinstance(person, str):
        tmp = person
    else:
        tmp = ""
        if "name" in person:
            tmp += person["name"]
        url = person.get("url", person.get("web"))
        if url:
            tmp += f" ({url})"
        email = person.get("email", person.get("mail"))
        if email:
            tmp += f" <{url}>"
    # Then parse
    matchedName = re.match("^([^(<]+)", tmp)
    matchedUrl = re.search("\(([^()]+)\)", tmp)
    matchedEmail = re.search("<([^<>]+)>", tmp)
    result = {}
    if matchedName:
        result["name"] = matchedName.group(0).strip()
    if matchedEmail:
        result["email"] = matchedEmail.group(1).strip()
    if matchedUrl:
        result["url"] = matchedUrl.group(1).strip()
    return result


def normalizePackageData(data):
    result = data.copy()
    if (
        "scripts" in data
        and result["scripts"].get("install") == "node-gyp rebuild"
        and not result["scripts"].get("preinstall")
    ):
        result["scripts"]["gypfile"] = True
    # Fix name
    result["name"] = result.get("name", "").strip()
    # Fix version
    result["version"] = result.get("version", "").strip()
    # TODO: result['version'] = cleanSemver(data.version, loose)
    # Fix description
    if "description" in result and not isinstance(result["description"], str):
        del result["description"]
    if "readme" in result and "description" not in result:
        result["description"] = result["readme"]
    # Fix repository
    if "repositories" in result:
        result["repository"] = result["repositories"][0]
    if "repository" in result:
        if isinstance(result["repository"], str):
            result["repository"] = {"type": "git", "url": result["repository"]}
        if url := result["repository"].get("url"):
            # This is very hacky
            # TODO: Check https://www.npmjs.com/package/hosted-git-info to resolve shortcuts
            if not url.startswith("git"):
                url = "git+" + url
            if not url.endswith(".git"):
                url += ".git"
            result["repository"]["url"] = url
    # Fix modules
    if "modules" in result:
        del result["modules"]
    # Fix scripts
    if "scripts" in result:
        if not isinstance(result["scripts"], dict):
            # I don't want to think about it right now, but I believe normalize-package-data has a bug if this is a list:
            # https://github.com/npm/normalize-package-data/blob/74e9c910921ef2110309e7684e306b7268ff1a1f/lib/fixer.js#L62C5-L62C16
            del result["scripts"]
        scripts = {}
        for script in result["scripts"]:
            if isinstance(script, str):
                typos = {"server": "start", "tests": "test"}
                if script in typos:
                    scripts[script] = result["scripts"][typos[script]]
                else:
                    scripts[script] = result["scripts"][script]
        result["scripts"] = scripts
    # Fix files
    if "files" in result:
        if not isinstance(result["files"], list):
            del result["files"]
        else:
            result["files"] = list(filter(lambda file: isinstance(file, str), result["files"]))
    # Fix bin
    if isinstance(result.get("bin"), str):
        if match := re.match("^@[^/]+[/](.*)$", result["bin"]):
            result["bin"] = match.group(1)
    # Fix man
    if "man" in result and isinstance(result["man"], str):
        result["man"] = [result["man"]]
    # Fix keywords
    if isinstance(result.get("keywords"), str):
        result["keywords"] = re.split(",\s+", result["keywords"])
    if "keywords" in result:
        if not isinstance(result["keywords"], list):
            del result["keywords"]
        else:
            result["keywords"] = list(filter(lambda file: isinstance(file, str), result["keywords"]))
    # Fix readme
    if "readme" not in result:
        result["readme"] = "ERROR: No README data found!"
    # Fix homepage
    if "homepage" not in result and "url" in result.get("repository", {}):
        # TODO: Get info from git repo
        pass
    if "homepage" in result and not isinstance(result["homepage"], str):
        del result["homepage"]
    if "homepage" in result and not urllib.parse.urlparse(result["homepage"]).scheme:
        result["homepage"] = "http://" + result["homepage"]
    # Fix license
    # This only warns if license is invalid
    # Fix dependencies
    if "dependencies" in result:
        if not isinstance(result["dependencies"], dict):
            del result["dependencies"]
        for dependency in list(result["dependencies"]):
            if not isinstance(dependency, str):
                del result["dependencies"][dependency]
    if "devDependencies" in result:
        if not isinstance(result["devDependencies"], dict):
            del result["devDependencies"]
        for dependency in list(result["devDependencies"]):
            if not isinstance(dependency, str):
                del result["devDependencies"][dependency]
    # Fix people
    if "author" in result:
        result["author"] = normalizePerson(result["author"])
    if "maintainers" in result:
        result["maintainers"] = list(map(normalizePerson, result["maintainers"]))
    if "contributors" in result:
        result["contributors"] = list(map(normalizePerson, result["contributors"]))
    # Fix typos
    # This only warns

    result["_id"] = f"{result['name']}@{result['version']}"
    return result


def normalize(data):
    result = data.copy()
    scripts = result.get("scripts", {})
    # _attributes
    for key in data:
        if key.startswith("_"):
            del result[key]
    # bundledDependencies
    if "bundleDependencies" not in result and "bundledDependencies" in result:
        result["bundleDependencies"] = result["bundledDependencies"]
        del result["bundledDependencies"]
    # bundleDependencies, bundleDependenciesDeleteFalse
    if result.get("bundleDependencies") is True:
        result["bundleDependencies"] = list(result.get("dependencies", {}))
    elif isinstance(result.get("bundleDependencies"), dict):
        result["bundleDependencies"] = list(result["bundleDependencies"])
    elif "bundleDependencies" in result and not isinstance(result.get("bundleDependencies"), list):
        del result["bundleDependencies"]
    # gypfile
    if not scripts.get("install") and not scripts.get("install") and result.get("gypfile") is not False:
        if False:  # TODO: Search for '*.gyp' in the package
            scripts["install"] = "node-gyp rebuild"
            result["scripts"] = scripts
            result["gypfile"] = True
    # serverjs
    if False:  # TODO: Check for server.js
        scripts["start"] = "node server.js"
        result["scripts"] = scripts
    # authors
    if "contributors" not in result:
        # TODO: Check for AUTHORS
        # We can skip this for now, as this will not cause an error.
        pass
    # readme
    if "readme" not in result:
        # TODO: Check for README
        # We can skip this for now, as this will not cause an error.
        pass
    # mans
    if "mans" not in result:
        # TODO: Check for result['directories]['man']
        # We can skip this for now, as this will not cause an error.
        pass
    # binDir
    if "bin" in result.get("directories", {}) and "bin" not in result:
        # TODO: Search for bins
        pass
    # TODO: normalizePackageBin(data)
    # gitHead
    if "gitHead" not in result:
        # TODO: Find git head
        # We can skip this for now, as this will not cause an error.
        pass
    # fillTypes
    index = result.get("main", "index.js")
    if isinstance(index, str):
        # TODO: Read DTSFile
        pass
    # normalizeData
    result = normalizePackageData(result)
    # binRefs
    # This just creates warnings; nothing to do.
    return result
