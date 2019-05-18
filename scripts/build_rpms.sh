#!/bin/bash
#    This file is part of rpm_maker.

#    rpm_maker is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    rpm_maker is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with rpm_maker.  If not, see <https://www.gnu.org/licenses/>.
#    (c) 2018 - James Stewart Miller
USER=$1
RPMS_DIR=$2
ARCH=$3
SCRIPT_PATH=$4

RPM_BUILD_ROOT=${SCRIPT_PATH}rpmbuild/BUILDROOT/
MAX_NUM_OF_JOBS=10

if [ ! -d "$RPMS_DIR" ]; then
  mkdir -p "$RPMS_DIR"
fi

. ${SCRIPT_PATH}job_pool.sh

number_of_debs=$(($#-4))

if [ ${MAX_NUM_OF_JOBS} -lt ${number_of_debs} ]; then
    number_of_jobs=${MAX_NUM_OF_JOBS}
else
    number_of_jobs=${number_of_debs}
fi

job_pool_init ${number_of_jobs} 0

for (( i=5; i<=$#; i++ ))
do
    job_pool_run ${SCRIPT_PATH}build_rpm.sh ${RPM_BUILD_ROOT} ${RPMS_DIR} ${ARCH} ${!i} ${USER}
done

job_pool_wait

job_pool_shutdown

function finish {
    rm -rf ${SCRIPT_PATH}rpmbuild
}

trap finish EXIT
# check the $job_pool_nerrors for the number of jobs that exited non-zero
#echo "job_pool_nerrors: ${job_pool_nerrors}"
exit 0
