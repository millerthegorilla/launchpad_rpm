# LaunchpadRPM

This repository is for a small app to allow apps to be downloaded from launchpad.net, and then converted and installed on Fedora, or simply installed on a debian system.

The app keeps track of the status of packages, and allows the user the ability to uninstall these custom packages.

Many projects on Launchpad.net use different naming conventions for their packages, veering away from the guidelines for Name + "_" + Version + Release, or whatever the current recommendations are.  In order to resolve this issue, I am using fuzzy comparisons, but will also be implementing pattern based comparison, where the user will have the ability to specify a pattern for potential files that are in keeping with the specific ppa's naming conventions.

I will be packaging the app in both rpm and deb files eventually.  Any bugs, please use the repository issue tracker.

Enjoy!

ps.  All code is released under the GPLv3 license, including where specified in some other form, for the time being.


