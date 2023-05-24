### Usage

To build dependencies for the current arch+OS:

    make

To build for another arch/OS:

    make HOST=host-platform-triplet

For example:

    make HOST=x86_64-w64-mingw32 -j4

**Tapyrus Core's `configure` script by default will ignore the depends output.** In
order for it to pick up libraries, tools, and settings from the depends build,
you must set the `CONFIG_SITE` environment variable to point to a `config.site` settings file.
In the above example, a file named `depends/x86_64-w64-mingw32/share/config.site` will be
created. To use it during compilation:

    CONFIG_SITE=$PWD/depends/x86_64-w64-mingw32/share/config.site ./configure

    ./configure --prefix=`pwd`/depends/x86_64-w64-mingw32

Common `host-platform-triplets` for cross compilation are:

- `i686-pc-linux-gnu` for Linux 32 bit
- `x86_64-pc-linux-gnu` for x86 Linux
- `x86_64-w64-mingw32` for Win64
- `x86_64-apple-darwin` for macOS
- `arm64-apple-darwin` for ARM macOS
- `arm-linux-gnueabihf` for Linux ARM 32 bit
- `aarch64-linux-gnu` for Linux ARM 64 bit
- `riscv32-linux-gnu` for Linux RISC-V 32 bit
- `riscv64-linux-gnu` for Linux RISC-V 64 bit

No other options are needed, the paths are automatically configured.

Install the required dependencies: Ubuntu & Debian
--------------------------------------------------

For macOS cross compilation:

       sudo apt-get install curl bsdmainutils cmake libz-dev python3-setuptools libtinfo5 xorriso

For Win64 cross compilation:

- see [build-windows.md](../doc/build-windows.md#cross-compilation-for-ubuntu-and-windows-subsystem-for-linux)

For linux (including i386, ARM) cross compilation:

Common linux dependencies:

    sudo apt-get install make automake cmake curl g++-multilib libtool binutils bsdmainutils pkg-config python3 patch bison

For linux ARM cross compilation:

    sudo apt-get install g++-arm-linux-gnueabihf binutils-arm-linux-gnueabihf

For linux AARCH64 cross compilation:

    sudo apt-get install g++-aarch64-linux-gnu binutils-aarch64-linux-gnu

For linux POWER 64-bit cross compilation (there are no packages for 32-bit):

    sudo apt-get install g++-powerpc64-linux-gnu binutils-powerpc64-linux-gnu g++-powerpc64le-linux-gnu binutils-powerpc64le-linux-gnu

For linux RISC-V 64-bit cross compilation (there are no packages for 32-bit):

    sudo apt-get install g++-riscv64-linux-gnu binutils-riscv64-linux-gnu

For linux S390X cross compilation:

    sudo apt-get install g++-s390x-linux-gnu binutils-s390x-linux-gnu

Dependency Options:
The following can be set when running make: make FOO=bar

    SOURCES_PATH: downloaded sources will be placed here
    BASE_CACHE: built packages will be placed here
    SDK_PATH: Path where sdk's can be found (used by macOS)
    FALLBACK_DOWNLOAD_PATH: If a source file can't be fetched, try here before giving up
    NO_QT: Don't download/build/cache qt and its dependencies
    NO_WALLET: Don't download/build/cache libs needed to enable the wallet
    NO_UPNP: Don't download/build/cache packages needed for enabling upnp
    DEBUG: disable some optimizations and enable more runtime checking
    HOST_ID_SALT: Optional salt to use when generating host package ids
    BUILD_ID_SALT: Optional salt to use when generating build package ids

If some packages are not built, for example `make NO_WALLET=1`, the appropriate
options will be passed to bitcoin's configure. In this case, `--disable-wallet`.

Additional targets:

    download: run 'make download' to fetch all sources without building them
    download-osx: run 'make download-osx' to fetch all sources needed for macOS builds
    download-win: run 'make download-win' to fetch all sources needed for win builds
    download-linux: run 'make download-linux' to fetch all sources needed for linux builds

### Other documentation

- [description.md](description.md): General description of the depends system
- [packages.md](packages.md): Steps for adding packages

