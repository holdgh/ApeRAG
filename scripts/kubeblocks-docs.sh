#!/usr/bin/env bash

set -o errexit

version=$1

if [ -z $version ]; then
	echo "Please specify the release version, like 0.8"
	exit 1
fi
echo "release the doc for version $version"

echo "remove existing kubeblocks directory"
rm -rf kubeblocks

release_branch=release-$version
echo "clone kubeblocks repository with branch $release_branch"
git clone git@github.com:apecloud/kubeblocks.git --branch $release_branch
cd kubeblocks

release_docs_branch=kubeblocks-docs-$version
echo "remove the origin doc branch $release_docs_branch"
git ps -d origin $release_docs_branch || true

echo "checkout the doc branch $release_docs_branch"
git co -b $release_docs_branch


echo "remove all files without .md suffix"
find ./docs -type f ! -name '*.md' -delete

echo "remove history release notes other than v$version"
find docs/release_notes ! -name v$version.0 -delete

echo "commit and push"
git ci -am "chore: release docs version $version"
git ps
echo "successfuly release the branch $release_docs_branch"

rm -rf kubeblocks

