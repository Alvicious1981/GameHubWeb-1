{pkgs}: {
  deps = [
    pkgs.glibcLocales
    pkgs.xsimd
    pkgs.pkg-config
    pkgs.libxcrypt
    pkgs.openssl
    pkgs.postgresql
  ];
}
