# Node Package Verify

This package was inspired by Darcy Clarke's blog post about [manifest confusion](https://blog.vlt.sh/blog/the-massive-hole-in-the-npm-ecosystem).

npverify is still pretty hacky and I'm happy to consider any pull requests to improve it.

## Usage

npverify can be used as a command line tool or as a library. To use it as a command line tool, simply run

`python -m npverify verify [PACKAGENAME]`.

npverify will download the manifest and tarball for the latest release of the package and compare the values in `package.json` against the manifest.

As it turns out, this is a mess, and almost no package is without some kind of deviation. To eliminate expected deviations npverify attempts to (incompletely) implements [npm's normalization](https://github.com/npm/normalize-package-data) for package data. 
