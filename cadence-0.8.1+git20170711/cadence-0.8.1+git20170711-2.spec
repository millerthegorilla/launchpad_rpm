Buildroot: /home/james/Src/kxfed/cadence-0.8.1+git20170711
Name: cadence
Version: 0.8.1+git20170711
Release: 2
Summary: JACK audio toolbox
License: see /usr/share/doc/cadence/copyright
Distribution: Debian
Group: Converted/sound

%define _rpmdir ../
%define _rpmfilename %%{NAME}-%%{VERSION}-%%{RELEASE}.%%{ARCH}.rpm
%define _unpackaged_files_terminate_build 0

%description
Cadence is a set of tools useful for audio production.

This package contains the main application.


(Converted from a deb package by alien version 8.95.)

%files
%dir "/"
%dir "/usr/"
%dir "/usr/bin/"
"/usr/bin/cadence"
%dir "/usr/share/"
%dir "/usr/share/cadence/"
%dir "/usr/share/cadence/src/"
"/usr/share/cadence/src/ui_cadence_tb_alsa.py"
"/usr/share/cadence/src/ui_cadence_tb_jack.py"
"/usr/share/cadence/src/ui_cadence_tb_pa.py"
"/usr/share/cadence/src/ui_cadence_tb_a2j.py"
"/usr/share/cadence/src/cadence.py"
"/usr/share/cadence/src/ui_cadence_rwait.py"
"/usr/share/cadence/src/ui_cadence.py"
%dir "/usr/share/icons/"
%dir "/usr/share/icons/hicolor/"
%dir "/usr/share/icons/hicolor/48x48/"
%dir "/usr/share/icons/hicolor/48x48/apps/"
"/usr/share/icons/hicolor/48x48/apps/cadence.png"
%dir "/usr/share/icons/hicolor/256x256/"
%dir "/usr/share/icons/hicolor/256x256/apps/"
"/usr/share/icons/hicolor/256x256/apps/cadence.png"
%dir "/usr/share/icons/hicolor/128x128/"
%dir "/usr/share/icons/hicolor/128x128/apps/"
"/usr/share/icons/hicolor/128x128/apps/cadence.png"
%dir "/usr/share/icons/hicolor/16x16/"
%dir "/usr/share/icons/hicolor/16x16/apps/"
"/usr/share/icons/hicolor/16x16/apps/cadence.png"
%dir "/usr/share/icons/hicolor/scalable/"
%dir "/usr/share/icons/hicolor/scalable/apps/"
"/usr/share/icons/hicolor/scalable/apps/cadence.svg"
%dir "/usr/share/applications/"
"/usr/share/applications/cadence.desktop"
%dir "/usr/share/doc/"
%dir "/usr/share/doc/cadence/"
"/usr/share/doc/cadence/copyright"
"/usr/share/doc/cadence/changelog.gz"
%dir "/etc/"
%dir "/etc/X11/"
%dir "/etc/X11/Xsession.d/"
%config "/etc/X11/Xsession.d/61cadence-session-inject"
%dir "/etc/xdg/"
%dir "/etc/xdg/autostart/"
%config "/etc/xdg/autostart/cadence-session-start.desktop"
