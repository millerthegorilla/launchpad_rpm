#!/usr/bin/env bash

RPM_BUILD_ROOT=$1
RPMS_DIR=$2
ARCH=$3
DEB_PATH=$4

RPM_BUILD_ROOT=${RPM_BUILD_ROOT}$(basename ${DEB_PATH})/
if [ ! -d "$RPM_BUILD_ROOT" ]; then
  mkdir -p "$RPM_BUILD_ROOT"
fi

cd "$RPM_BUILD_ROOT"

sudo alien -r -g -v "$DEB_PATH"

aliendir=$(find . -maxdepth 1 -type d -name '[^.]?*' -printf %f -quit)

specfilename=$(find "$RPM_BUILD_ROOT$aliendir" -type f -name \*.spec)
specfilename=$(basename "$specfilename")

if [ "$ARCH"=='amd64' ] || [ "$ARCH"=='x86_64' ]; then
    adir=$(echo "$specfilename" | sed 's/spec/x86_64\//')
else
    adir=$(echo "$specfilename" | sed 's/spec/x386\//')
fi

mv "$RPM_BUILD_ROOT$aliendir" "$RPM_BUILD_ROOT$adir"
mv "$RPM_BUILD_ROOT$adir/usr" "$RPM_BUILD_ROOT"

specfilepath="$RPM_BUILD_ROOT$adir$specfilename"

# edit spec file to remove unnecessary prefixes
sed -i '/^%dir/ d' "$specfilepath"

cd "$adir"
# --buildroot "$RPM_BUILD_ROOT"
rpmbuild --bb --rebuild --noclean --buildroot ${RPM_BUILD_ROOT} "$specfilepath"

mv ${RPM_BUILD_ROOT}*.rpm ${RPMS_DIR}

echo -e "Converted $(basename ${DEB_PATH})\n"