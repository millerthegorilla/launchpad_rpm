Buildroot: /home/james/Src/kxfed/carla-bridge-win32-1.9.12+git20181025
Name: carla-bridge-win32
Version: 1.9.12+git20181025
Release: 2
Summary: carla win32 bridge
License: see /usr/share/doc/carla-bridge-win32/copyright
Distribution: Debian
Group: Converted/sound

%define _rpmdir ../
%define _rpmfilename %%{NAME}-%%{VERSION}-%%{RELEASE}.%%{ARCH}.rpm
%define _unpackaged_files_terminate_build 0

%description
This package provides the Carla win32 bridge.


(Converted from a deb package by alien version 8.95.)

%files
%dir "/"
%dir "/usr/"
%dir "/usr/share/"
%dir "/usr/share/doc/"
%dir "/usr/share/doc/carla-bridge-win32/"
"/usr/share/doc/carla-bridge-win32/changelog.gz"
"/usr/share/doc/carla-bridge-win32/copyright"
%dir "/usr/lib/"
%dir "/usr/lib/lv2/"
%dir "/usr/lib/lv2/carla.lv2/"
%dir "/usr/lib/vst/"
%dir "/usr/lib/vst/carla.vst/"
%dir "/usr/lib/carla/"
"/usr/lib/carla/carla-bridge-win32.exe"
"/usr/lib/carla/carla-discovery-win32.exe"
"/usr/lib/lv2/carla.lv2/carla-bridge-win32.exe"
"/usr/lib/lv2/carla.lv2/carla-discovery-win32.exe"
"/usr/lib/vst/carla.vst/carla-bridge-win32.exe"
"/usr/lib/vst/carla.vst/carla-discovery-win32.exe"
