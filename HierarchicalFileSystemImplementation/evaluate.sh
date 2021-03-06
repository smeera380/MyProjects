#!/bin/bash
cd fusemount
echo "Creating new directories:  mkdir -p dir1/dir2"
mkdir -p dir1/dir2

echo "------------------------------"

echo "Creating and Writing into a File:   echo ""hello"" > dir1/dir2/hello.txt"
echo "hello" > dir1/dir2/hello.txt

echo "------------------------------"

echo "Listing the newly created file : dir1/dir2/hello.txt"
cd dir1/dir2
ls -l

echo "------------------------------"
pwd
echo "Retrieving data from a file:  cat dir1/dir2/hello.txt"
cd ../../
cat dir1/dir2/hello.txt

echo "------------------------------"

pwd
echo "Listing the files in a directory(from mountpoint) : ls -l"
ls -l

echo "------------------------------"


echo " Renaming directory : mv -i dir1/ newdir1"
mv -i dir1/ newdir1

echo "Listing the directory information after renaming"
ls -l

echo "------------------------------"


echo " cd to newly renamed directory"
cd newdir1/
echo " Listing the current files under the renamed directory"
ls
echo  " Removing a directory : rmdir dir2"
rmdir dir2
echo  " Contents after deletion"
ls -l

echo "-------------------------------"

cd ../

