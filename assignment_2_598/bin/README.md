# Bundled visibility executables

`prepare.py` chooses the executable automatically. These programs read a binary
PNG and write JSON; Python then stores the portable shelf. Students need no
Rust toolchain or build tools.

| Folder | Target | Verification on the development Mac |
| --- | --- | --- |
| `darwin-arm64` | Apple Silicon macOS | Built and executed; Rust/Python FOVs compared |
| `darwin-x86_64` | Intel macOS | Cross-built and executed through Rosetta |
| `linux-x86_64` | x86-64 Linux, static musl | Cross-built; ELF format inspected; not executed on Linux |
| `windows-x86_64` | x86-64 Windows | Cross-built; PE format and imports inspected; not executed on Windows |

Other architectures, or systems that cannot start the executable, automatically
use the tested Python fallback. Force that path with `--backend python --force`.
The native Windows/Linux builds still need a smoke run on those operating
systems before claiming native runtime verification there.

For instructor rebuilds on the target operating system, with Rust and its
platform linker installed:

```sh
python tools/build_native.py
```

This utility is not part of the student setup or generation path. The Rust
source is in `src/main.rs`; dependencies are pinned in `Cargo.lock`.

The included builds used Rust 1.82.0. macOS builds used Apple's linker. Linux
used the `x86_64-unknown-linux-musl` target and Rust's bundled `rust-lld`. Windows
used the `x86_64-pc-windows-gnu` target, `-C panic=abort`, and Zig 0.13.0's MinGW
runtime and LLVM unwinder. Runtime DLL imports are Windows system/UCRT libraries;
there is no separate Rust DLL or GCC runtime DLL to install.

`manifest.json` records executable hashes. Library notices are in the root
`THIRD_PARTY_NOTICES.txt`.
