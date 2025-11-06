{ pkgs }: {
  deps = [
    pkgs.python311
    pkgs.python311Packages.pip
    pkgs.ffmpeg-full
    pkgs.libopus
    pkgs.libsodium
  ];
}
