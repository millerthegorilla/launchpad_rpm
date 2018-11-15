Buildroot: /home/james/Src/kxfed/cadence-data-0.8.1+git20170711
Name: cadence-data
Version: 0.8.1+git20170711
Release: 2
Summary: JACK audio toolbox (data files)
License: see /usr/share/doc/cadence-data/copyright
Distribution: Debian
Group: Converted/sound

%define _rpmdir ../
%define _rpmfilename %%{NAME}-%%{VERSION}-%%{RELEASE}.%%{ARCH}.rpm
%define _unpackaged_files_terminate_build 0

%description
Cadence is a set of tools useful for audio production.

This package contains the shared data and modules.


(Converted from a deb package by alien version 8.95.)

%files
%dir "/"
%dir "/usr/"
%dir "/usr/share/"
%dir "/usr/share/cadence/"
%dir "/usr/share/cadence/src/"
"/usr/share/cadence/src/shared_settings.py"
"/usr/share/cadence/src/canvaspreviewframe.py"
"/usr/share/cadence/src/ui_settings_app.py"
"/usr/share/cadence/src/jacklib.py"
"/usr/share/cadence/src/patchcanvas_theme.py"
"/usr/share/cadence/src/jacklib_helpers.py"
"/usr/share/cadence/src/shared.py"
"/usr/share/cadence/src/shared_cadence.py"
"/usr/share/cadence/src/patchcanvas.py"
"/usr/share/cadence/src/clickablelabel.py"
"/usr/share/cadence/src/systray.py"
"/usr/share/cadence/src/shared_canvasjack.py"
"/usr/share/cadence/src/resources_rc.py"
%dir "/usr/share/doc/"
%dir "/usr/share/doc/cadence-data/"
"/usr/share/doc/cadence-data/copyright"
"/usr/share/doc/cadence-data/changelog.gz"
