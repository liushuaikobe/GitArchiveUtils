#!/bin/bash
if [ -z "$1" ]
then
	echo "Please tell me which year to get."
elif [ -z "$2" ]
then
	echo "Please tell me which month to get."
elif [ -z "$3" ]
then
	echo "Please tell me where to store these files."
else
	for day in $(seq 1 31)
	do
		for hour in $(seq 0 23)
		do
			if [ "$day" -lt "10" ]
			then
				wget -P "$3" http://data.githubarchive.org/"$1"-"$2"-0"$day"-"$hour".json.gz
			else
				wget -P "$3" http://data.githubarchive.org/"$1"-"$2"-"$day"-"$hour".json.gz
			fi
		done
	done
fi