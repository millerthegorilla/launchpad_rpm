Buildroot: /home/james/Src/kxfed/carla-bridge-win64-1.9.12+git20181025
Name: carla-bridge-win64
Version: 1.9.12+git20181025
Release: 2
Summary: carla win64 bridge
License: see /usr/share/doc/carla-bridge-win64/copyright
Distribution: Debian
Group: Converted/sound

%define _rpmdir ../
%define _rpmfilename %%{NAME}-%%{VERSION}-%%{RELEASE}.%%{ARCH}.rpm
%define _unpackaged_files_terminate_build 0

%description
This package provides the Carla win64 bridge.


(Converted from a deb package by alien version 8.95.)

%files
%dir "/"
%dir "/usr/"
%dir "/usr/share/"
%dir "/usr/share/doc/"
%dir "/usr/share/doc/carla-bridge-win64/"
"/usr/share/doc/carla-bridge-win64/changelog.gz"
"/usr/share/doc/carla-bridge-win64/copyright"
%dir "/usr/lib/"
%dir "/usr/lib/lv2/"
%dir "/usr/lib/lv2/carla.lv2/"
%dir "/usr/lib/vst/"
%dir "/usr/lib/vst/carla.vst/"
%dir "/usr/lib/carla/"
"/usr/lib/carla/carla-bridge-win64.exe"
"/usr/lib/carla/carla-discovery-win64.exe"
"/usr/lib/lv2/carla.lv2/carla-bridge-win64.exe"
"/usr/lib/lv2/carla.lv2/carla-discovery-win64.exe"
"/usr/lib/vst/carla.vst/carla-bridge-win64.exe"
"/usr/lib/vst/carla.vst/carla-discovery-win64.exe"
