{ pkgs }: {
  deps = [
    pkgs.python311
    pkgs.python311Packages.pip
    pkgs.ffmpeg_6
    pkgs.libopus
    pkgs.libsodium
    pkgs.pkg-config
  ];
}
