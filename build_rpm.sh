#!/usr/bin/env bash

RPM_BUILD_ROOT=$1
RPMS_DIR=$2
ARCH=$3
DEB_PATH=$4
USER=$5
# TODO the user is in case I need to drop privileges for rpmbuild
# TODO I read somewhere that rpmbuild should not be run as root,
# TODO but it seems to be doing fine as is.  Any problems and
# TODO I'll use sudo -H -u ${USER} rpmbuild ...
RPM_BUILD_ROOT=${RPM_BUILD_ROOT}$(basename ${DEB_PATH})/
if [ ! -d "$RPM_BUILD_ROOT" ]; then
  mkdir -p "$RPM_BUILD_ROOT"
fi

cd "$RPM_BUILD_ROOT"

sudo alien -r -g -k -v "${DEB_PATH}"

SPECFILEPATH=$(find ${RPM_BUILD_ROOT} -type f -name \*.spec)
SPECFILENAME=$(basename ${SPECFILEPATH})
SPECFILEPATH=${SPECFILEPATH%/*}/
ALIENDIR=$(echo ${SPECFILENAME%-*})

sed -i '/^%dir/ d' "${SPECFILEPATH}${SPECFILENAME}"

LINE=$(grep '%define _rpmfilename' ${SPECFILEPATH}${SPECFILENAME})
LINE=${LINE#'%define _rpmfilename '}
NAME=$(grep 'Name: ' ${SPECFILEPATH}${SPECFILENAME})
NAME=${NAME#'Name: '}
VERSION=$(grep 'Version: ' ${SPECFILEPATH}${SPECFILENAME})
VERSION=${VERSION#'Version: '}
RELEASE=$(grep 'Release: ' ${SPECFILEPATH}${SPECFILENAME})
RELEASE=${RELEASE#'Release: '}
ARCH=$(rpm --eval '%{_arch}')
RPMFILENAME=$(echo ${LINE} | sed 's/%%{NAME}/'${NAME}'/' | sed 's/%%{VERSION}/'${VERSION}'/' \
           | sed 's/%%{RELEASE}/'${RELEASE}'/' | sed 's/%%{ARCH}/'${ARCH}'/')

sudo rpmbuild --bb --rebuild --noclean --buildroot ${SPECFILEPATH} ${SPECFILEPATH}${SPECFILENAME}

echo moving ${RPM_BUILD_ROOT}../${RPMFILENAME} to ${RPMS_DIR}${RPMFILENAME}
mv ${RPM_BUILD_ROOT}../${RPMFILENAME} ${RPMS_DIR}

echo -e "Converted ${DEB_PATH} to ${RPMFILENAME}\n"

