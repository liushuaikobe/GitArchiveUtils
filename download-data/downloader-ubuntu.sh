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
	wget -P "$3" http://data.githubarchive.org/"$1"-"$2"-{01..31}-{0..23}.json.gz
fi