#!/bin/sh

# RemiZOffAlex
#
# Description:
#   Скрипт установки YouTrack и минимальной настройки

#   CentOS
#       bash <(curl https://raw.githubusercontent.com/servancho/pytin/master/scripts/youtrack/setup.sh)

function set_conf {
    ### Begin: Not install security for OpenVZ
    ip link | grep venet
    if [ $? -ne 0 ];
    then

        # APF
        perl -pi -e 's/IG_TCP_CPORTS="[^\"]*"/IG_TCP_CPORTS="21,22,80,443"/g' /etc/apf/conf.apf
        perl -pi -e 's/IG_UDP_CPORTS="[^\"]*"/IG_UDP_CPORTS="53,953"/g' /etc/apf/conf.apf

    fi
}

bash <(curl https://raw.githubusercontent.com/servancho/pytin/master/scripts/centos/default.sh)

set_conf

# Create user youtrack
useradd youtrack
cd /home/youtrack

# Create directory
mkdir /var/run/youtrack
chown youtrack /var/run/youtrack

# Download and install
wget http://download-cf.jetbrains.com/charisma/youtrack-6.5.16807.jar -O /home/youtrack/youtrack.jar
yum -y install java-1.8.0-openjdk

wget https://raw.githubusercontent.com/servancho/pytin/master/scripts/youtrack/youtrack -O /etc/init.d/youtracker

chmod +x /etc/init.d/youtracker

service youtracker start
#chkconfig --add youtrack

# java -Xmx1g -jar youtrack-6.5.16807.jar 80
