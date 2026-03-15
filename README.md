# gcc-portable

<p align="center">
  <a href="https://github.com/cuinixam/gcc-portable/actions/workflows/ci.yml?query=branch%3Amain">
    <img src="https://img.shields.io/github/actions/workflow/status/cuinixam/gcc-portable/ci.yml?branch=main&label=CI&logo=github&style=flat-square" alt="CI Status" >
  </a>
  <a href="https://github.com/astral-sh/uv">
    <img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json" alt="uv">
  </a>
  <a href="https://github.com/astral-sh/ruff">
    <img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="ruff">
  </a>
  <a href="https://github.com/cuinixam/pypeline">
    <img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/cuinixam/pypeline/refs/heads/main/assets/badge/v0.json" alt="pypeline">
  </a>
  <a href="https://github.com/pre-commit/pre-commit">
    <img src="https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white&style=flat-square" alt="pre-commit">
  </a>
</p>

---

## What is this?

This project **does not build GCC from source**. It repackages the pre-built GCC binaries from [conda-forge](https://conda-forge.org/) into a self-contained, portable archive for macOS.

The resulting archives are available for download from the [GitHub Releases](https://github.com/cuinixam/gcc-portable/releases) page for both **ARM64** (Apple Silicon) and **x64** (Intel) macOS.

## Why?

If you just need GCC on macOS to compile something, **use [Homebrew](https://brew.sh/)** (`brew install gcc`). This project exists for a different reason.

These portable archives are meant to be used with [poks](https://github.com/cuinixam/poks) — a portable package manager that downloads and manages tool archives. The [gcc poks manifest](https://github.com/cuinixam/poks-bucket/blob/main/gcc.json) was missing macOS support, and this project fills that gap by providing GCC archives in a format that poks can download and use.

## How it works

1. Downloads GCC and its dependencies from conda-forge using [micromamba](https://mamba.readthedocs.io/en/latest/user_guide/micromamba.html)
2. Extracts the relevant directories (bin, lib, libexec, include, share)
3. Patches hardcoded conda paths to make the installation relocatable:
   - Rewrites shebangs in scripts to use `#!/usr/bin/env`
   - Removes hardcoded paths from GCC specs files
   - Creates symlinks to fix dynamic library resolution (rpaths)
4. Packages everything into a `.tar.gz` archive
5. Verifies the archive by compiling and running a hello world program

## License and attribution

This project is a repackaging tool only. The GCC binaries distributed in the releases are built and provided by the [conda-forge](https://conda-forge.org/) community. GCC itself is licensed under the [GNU General Public License v3](https://gcc.gnu.org/onlinedocs/gcc/Copying.html), which permits using GCC to compile proprietary programs.

This repackaging tool itself is open source. See the project license for details.

## Credits

[![Copier](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/copier-org/copier/master/img/badge/badge-grayscale-inverted-border-orange.json)](https://github.com/copier-org/copier)

This package was created with
[Copier](https://copier.readthedocs.io/) and the
[browniebroke/pypackage-template](https://github.com/browniebroke/pypackage-template)
project template.
