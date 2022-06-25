result=$(ps -e | grep tunserver)

if ! [[ $result ]]
then
	echo no
fi
