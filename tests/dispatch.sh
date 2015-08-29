#!/bin/bash

SUITE=${1:-all}

case $SUITE in
    test )
        py.test tests/
        ;;
    lint )
        flake8 steve/
        ;;
    * )
        echo "Unknown test suite '$SUITE'."
        exit 1
esac
