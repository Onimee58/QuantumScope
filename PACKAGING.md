# GitHub Actions runnable packages

The `.github/workflows/release.yml` workflow builds **two separate executable distributions** using PyInstaller `--onedir`: Windows and Linux x86_64. Both need to be extracted before launching; they are not installers.

**How to use:** Create an empty GitHub repository. Upload the contents of this folder **including `.github/`** (GitHub's web UI may hide dot directories; Git via command line is more reliable). Open **Actions > Build downloadable applications > Run workflow**. After both jobs complete, download the two ZIPs under the run's **Artifacts** section.

**Tagged release:** push `v0.1.3` to trigger the workflow and attach ZIPs to the GitHub Release. Tags should match the package version. Grant Actions write permission if your repository settings restrict release creation.

**Windows:** Extract `QuantumScope-v0.1.3-Windows.zip`, then double-click `QuantumScope\QuantumScope.exe`.

**Linux:** Extract `QuantumScope-v0.1.3-Linux.zip`, then `chmod +x QuantumScope/QuantumScope && ./QuantumScope/QuantumScope`. On NVIDIA PRIME systems use `chmod +x run_packaged_nvidia.sh && ./run_packaged_nvidia.sh`. The Linux release is built on Ubuntu 24.04; portability to other Linux distributions is not guaranteed due to system GL, libc, and Qt requirements.

**Limitations:** Native GUI behavior and PyInstaller's included Qt/VTK plugins still require testing on actual Windows and Linux machines. Windows GPU selection uses Windows Graphics settings. A successful build does not prove rendering works. The `--version` switch can be tested without an OpenGL context.
