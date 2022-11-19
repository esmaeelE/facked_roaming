#!/bin/bash  

# 
# set -x
# trap read debug
# 

#####################
# BASH CLI
# monitor process ### 
# 
# 0: script name
# 1 ... n: arguments
#####################

# echo print all cli arguments: $@ , $*, $#
echo ---------------------------------------
echo number_of_args: $#
echo list_of_args: $*
echo Running program
echo ---------------------------------------

# read list of files in this bash script 
# then for each files pass to python core
# then in python do process 
# then monitor processes inside this bash script


for x in {1..52}
do

i=0

while IFS="" read -r p || [ -n "$p" ]
do

	((i=i+1))

	stem=$(basename "${p}")
	pypy3 fixlen.py "$p" ../$2/${i}_$stem $3 $4
	
	echo "*******", ../output/${i}_$stem, "###: ", $i

	#pgrep -f fix(process name)

done < $1

echo endoneloop
# [todo]: run multiple instace of core app to make it faster
done
