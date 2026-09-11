# Releasing HalfFrameUtils

The [release workflow](../.github/workflows/release.yml) builds self-contained desktop applications with PyInstaller. Users do not need to install Python, OpenCV, NumPy, or the packages in `requirements.txt`.

## Build locally

PyInstaller must build on the operating system being targeted; it does not cross-compile. Use Python 3.12 to match the release workflow.

Create an isolated build environment from the repository root:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip pyinstaller
python -m pip install -r requirements.txt
```

On Windows PowerShell, activate the environment with:

```powershell
.venv\Scripts\Activate.ps1
```

Build the application:

```bash
python -m PyInstaller \
  --noconfirm \
  --clean \
  --windowed \
  --onedir \
  --name HalfFrameUtils \
  HalfFrameUtilsGUI.py
```

The result is written to `dist`. macOS produces `dist/HalfFrameUtils.app`; Windows and Linux produce a self-contained `dist/HalfFrameUtils` directory. Test the application directly from that location before packaging it.

To create an archive equivalent to the CI artifact, use the command for the current platform.

macOS:

```bash
ditto -c -k --keepParent dist/HalfFrameUtils.app HalfFrameUtils-macOS.zip
```

Windows PowerShell:

```powershell
Compress-Archive -Path dist/HalfFrameUtils -DestinationPath HalfFrameUtils-Windows-x86_64.zip
```

Linux:

```bash
tar -C dist -czf HalfFrameUtils-Linux-x86_64.tar.gz HalfFrameUtils
```

The `build`, `dist`, and generated `HalfFrameUtils.spec` paths are build outputs and can be deleted before rebuilding. PyInstaller's `--clean` option clears its cached build data, but it does not remove previous files from `dist`.

## Test a build

Before creating a release:

1. Open the repository's **Actions** tab on GitHub.
2. Select **Build desktop release**.
3. Choose **Run workflow** and select the branch to test.
4. Download and test the artifacts produced by the completed run.

A manual run builds packages but does not create a GitHub Release.

## Publish a release

Releases are created from version tags beginning with `v`. Make sure the commit to release is on `master`, then create and push a semantic-version tag:

```bash
git switch master
git pull --ff-only
git tag v1.0.0
git push origin v1.0.0
```

The workflow builds every target in parallel. If all builds succeed, it creates a GitHub Release named after the tag, generates release notes, and attaches all packaged applications.

## Release artifacts

Each release contains:

| Artifact | Target |
| --- | --- |
| `HalfFrameUtils-macOS-arm64.zip` | Apple Silicon Macs |
| `HalfFrameUtils-macOS-x86_64.zip` | Intel Macs |
| `HalfFrameUtils-Windows-x86_64.zip` | 64-bit Windows |
| `HalfFrameUtils-Linux-x86_64.tar.gz` | 64-bit Linux |

The workflow uses Python 3.12 and installs the application requirements in a clean runner before packaging the GUI with PyInstaller.

## Signing status

The generated applications are currently unsigned. macOS Gatekeeper and Windows SmartScreen may therefore warn users when opening a downloaded build. Public releases should eventually add Apple Developer ID signing and notarization, plus Windows code signing.

## Failed releases

The release job runs only after every platform build succeeds. If a build fails, inspect its log in the Actions run, fix the problem, and push a new version tag. Do not move or reuse a published version tag.
