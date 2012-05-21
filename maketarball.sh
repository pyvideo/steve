#!/bin/bash

#######################################################################
# This file is part of steve.
#
# Copyright (C) 2012 Will Kahn-Greene
# 
# steve is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# steve is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with steve.  If not, see <http://www.gnu.org/licenses/>.
#######################################################################


USAGE="Usage: $0 -h | [-dr] REVISH

Creates a tarball of the repository at rev REVISH.  This can be a branch
name, tag, or commit sha.

Options:

   -d
      Adds date to the directory name.

   -h
      Shows help and exits.

Examples:

   ./maketarball v1.5
   ./maketarball -d master
"

REVISH="none"
PREFIX="none"
NOWDATE=""

while getopts ":dhr" opt;
do
    case "$opt" in
        h)
            echo "$USAGE"
            exit 0
            ;;
        d)
            NOWDATE=`date "+%Y-%m-%d-"`
            shift $((OPTIND-1))
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            echo "$USAGE" >&2
            ;;
    esac 
done

if [[ -z "$1" ]]; then
    echo "$USAGE";
    exit 1;
fi

REVISH=$1
PREFIX="$NOWDATE$REVISH"

# convert PREFIX to all lowercase and nix the v from tag names.
PREFIX=`echo "$PREFIX" | tr '[A-Z]' '[a-z]' | sed s/v//`

# build the filename base minus the .tar.gz stuff--this is also
# the directory in the tarball.
FNBASE="pyblosxom-$PREFIX"

STARTDIR=`pwd`

function cleanup {
    pushd $STARTDIR

    if [[ -e tmp ]]
    then
        echo "+ cleaning up tmp/"
        rm -rf tmp
    fi
    popd
}

echo "+ Building tarball from: $REVISH"
echo "+ Using prefix:          $PREFIX"
echo "+ Release?:              $RELEASE"

echo ""

if [[ -e tmp ]]
then
    echo "+ there's an existing tmp/.  please remove it."
    exit 1
fi

mkdir $STARTDIR/tmp
echo "+ generating archive...."
git archive \
    --format=tar \
    --prefix=$FNBASE/ \
    $REVISH > tmp/$FNBASE.tar

if [[ $? -ne 0 ]]
then
    echo "+ git archive command failed.  See above text for reason."
    cleanup
    exit 1
fi

echo "+ compressing...."
gzip tmp/$FNBASE.tar

echo "+ archive at tmp/$FNBASE.tar.gz"

echo "+ done."
