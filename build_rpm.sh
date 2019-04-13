#!/usr/bin/env bash

RPM_BUILD_ROOT=$1
RPMS_DIR=$2
ARCH=$3
DEB_PATH=$4
USER=$5

RPM_BUILD_ROOT=${RPM_BUILD_ROOT}$(basename ${DEB_PATH})/
if [ ! -d "$RPM_BUILD_ROOT" ]; then
  mkdir -p "$RPM_BUILD_ROOT"
fi

cd "$RPM_BUILD_ROOT"

sudo alien -r -g -k -v "${DEB_PATH}"
# perl -e 'use Privileges::Drop; drop_privileges(${USER});'
DEBFN=$(basename ${DEB_PATH})

ALIENDIR=$(echo ${DEBFN%_*})

SPECFILEPATH=$(find ${RPM_BUILD_ROOT} -type f -name \*.spec)
SPECFILENAME=$(basename ${SPECFILENAME})

sed -i '/^%dir/ d' "${SPECFILEPATH}"

LINE=$(grep '%define _rpmfilename' ${SPECFILEPATH})
LINE=${LINE#'%define _rpmfilename '}
NAME=$(grep 'Name: ' ${SPECFILEPATH})
NAME=${NAME#'Name: '}
VERSION=$(grep 'Version: ' ${SPECFILEPATH})
VERSION=${VERSION#'Version: '}
RELEASE=$(grep 'Release: ' ${SPECFILEPATH})
RELEASE=${RELEASE#'Release: '}
ARCH=$(rpm --eval '%{_arch}')
RPMFILENAME=$(echo ${LINE} | sed 's/%%{NAME}/'${NAME}'/' | sed 's/%%{VERSION}/'${VERSION}'/' \
           | sed 's/%%{RELEASE}/'${RELEASE}'/' | sed 's/%%{ARCH}/'${ARCH}'/')

echo debfn is ${DEBFN}
echo rpmbuild_root is ${RPM_BUILD_ROOT}
echo aliendir is ${ALIENDIR}
echo adir is ${ADIR}
echo specfilename is ${SPECFILENAME}
echo SPECFILEPATH is ${SPECFILEPATH}
echo line is ${LINE}
echo name is ${NAME}
echo version is ${VERSION}
echo release is ${RELEASE}
echo arch is ${ARCH}
echo rpmfilename is ${RPMFILENAME}
echo id is $(id -u)
echo id group is $(id -u)
user is ${USER}

# TODO need to get NAME VERSION RELEASE and ARCH from specfile
# TODO to be certain about the rpm filename
# TODO so find the following line in specfile:
# TODO %define _rpmfilename %%{NAME}-%%{VERSION}-%%{RELEASE}.%%{ARCH}.rpm
# and parse the name replacing the variables

# --buildroot "$RPM_BUILD_ROOT"
rpmbuild --bb --rebuild --noclean --buildroot ${RPM_BUILD_ROOT} "$SPECFILEPATH"

#FILENAME=$(basename ${DEB_PATH})
#FILENAME=${FILENAME/'_'/'-'}
#if [ ${ARCH} = 'amd64' ]; then
#    FILENAME=${FILENAME%_amd64.deb}-2.x86_64.rpm
#elif [ ${ARCH} = 'i386' ]; then
#    FILENAME=${FILENAME%_i386.deb}-2.i386.rpm  # untested
#fi

# TODO need to make below work
echo moving ${RPM_BUILD_ROOT}${RPMFILENAME} to ${RPMS_DIR}${RPMFILENAME}
# mv ${RPM_BUILD_ROOT}${RPMFILENAME} ${RPMS_DIR}
# mv ${RPM_BUILD_ROOT}*.rpm ${RPMS_DIR}

echo -e "Converted ${DEB_PATH} to ${RPMFILENAME}\n"

