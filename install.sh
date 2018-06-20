#!/bin/sh


echo "#########################################################"
echo "Installation script for sibus.picamera module"
echo "#########################################################"

SUPERVISOR_ORG="sibus-camera.conf"
INSTALL_SCRIPT="$( realpath "$0" )"
INSTALL_DIR="$( dirname "$INSTALL_SCRIPT" )"


if [ "$(whoami)" != "root" ]; then
	echo "Sorry, you are not root."
	exit 1
fi

echo " + Installing dependency packages"
sudo apt-get -y install python
sudo apt-get -y install python-opencv
echo " + done"

echo " + Creating supervisor service"
sed 's|<INSTALL_DIR>|'$INSTALL_DIR'|g' $INSTALL_DIR/$SUPERVISOR_ORG > "/etc/supervisor/conf.d/sibus-camera.conf"
sudo service supervisor restart
sudo service supervisor status
echo " + done"

echo "Enabling Raspberry camera"
sudo modprobe bcm2835-v4l2

LINE='bcm2835-v4l2'
FILE="/etc/modules"
grep -qF -- "$LINE" "$FILE" || echo "$LINE" >> "$FILE"


exit 0

