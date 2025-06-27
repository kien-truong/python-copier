#!/bin/bash

set -euo pipefail

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "$SCRIPT_DIR/.."

DEST="$SCRIPT_DIR/tmp"

rm -fr "${DEST}"

echo "///////////////////////////////////////////"
echo "             TAGGING TEMPLATE COPY"
echo "///////////////////////////////////////////"
template=$(mktemp -d)
cp -rf . $template

pushd $template
git add -A . || true
git commit -m "test" || true
git tag 99.99.99
popd

echo "Template is located at ${template}"
echo
echo "///////////////////////////////////////////"
echo "             GENERATING PROJECT"
echo "///////////////////////////////////////////"
echo

copier copy -f "${template}" "${DEST}" \
-d project_name="copier-uv-testing" \
-d project_description='Testing this great template' \
-d author_fullname="Tester" \
-d author_username="tester" \
-d author_email="tester@example.org"

pushd $DEST
git init .
git add -A .
git commit -m "test"