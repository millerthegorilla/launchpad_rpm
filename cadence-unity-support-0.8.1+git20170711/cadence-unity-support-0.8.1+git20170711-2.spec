Buildroot: /home/james/Src/kxfed/cadence-unity-support-0.8.1+git20170711
Name: cadence-unity-support
Version: 0.8.1+git20170711
Release: 2
Summary: JACK audio toolbox (Unity support)
License: see /usr/share/doc/cadence-unity-support/copyright
Distribution: Debian
Group: Converted/sound

%define _rpmdir ../
%define _rpmfilename %%{NAME}-%%{VERSION}-%%{RELEASE}.%%{ARCH}.rpm
%define _unpackaged_files_terminate_build 0

%description
Cadence is a set of tools useful for Audio-related
tasks, using Python and Qt.

This package contains a small daemon that show sJACK
related data in the Cadence icon when using Unity.


(Converted from a deb package by alien version 8.95.)

%files
%dir "/"
%dir "/usr/"
%dir "/usr/bin/"
"/usr/bin/cadence-unity-support"
%dir "/usr/share/"
%dir "/usr/share/applications/"
"/usr/share/applications/cadence-unity-support.desktop"
%dir "/usr/share/doc/"
%dir "/usr/share/doc/cadence-unity-support/"
"/usr/share/doc/cadence-unity-support/copyright"
"/usr/share/doc/cadence-unity-support/changelog.gz"
%dir "/etc/"
%dir "/etc/xdg/"
%dir "/etc/xdg/autostart/"
%config "/etc/xdg/autostart/cadence-unity-support.desktop"
