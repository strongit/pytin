#!/bin/sh

# SugarCRM

/bin/bash <(/usr/bin/curl https://raw.githubusercontent.com/servancho/pytin/master/scripts/centos/default.sh)

/usr/bin/yum install -y httpd php php-cli php-gd php-mysql php-tidy php-xml php-xmlrpc mysql mysql-server php-mbstring php-imap

# iptables
cat <<EOF > /etc/sysconfig/iptables
# Firewall configuration written by system-config-firewall
# Manual customization of this file is not recommended.
*filter
:INPUT ACCEPT [0:0]
:FORWARD ACCEPT [0:0]
:OUTPUT ACCEPT [0:0]
-A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
-A INPUT -p icmp -j ACCEPT
-A INPUT -i lo -j ACCEPT
-A INPUT -m state --state NEW -m tcp -p tcp --dport 22 -j ACCEPT
-A INPUT -m state --state NEW -m tcp -p tcp --dport 80 -j ACCEPT
-A INPUT -j REJECT --reject-with icmp-host-prohibited
-A FORWARD -j REJECT --reject-with icmp-host-prohibited
COMMIT
EOF
service iptables restart

# Генерация паролей
passmysql=`perl -le'print map+(A..Z,a..z,0..9)[rand 62],0..15'`
echo "MySQL password: "${passmysql} > ~/sugarcrm.txt

# Запуск MySQL и установка пароля
chkconfig mysqld on
service mysqld start
/usr/bin/mysqladmin -u root password ${passmysql}

cat <<EOF > /etc/my.cnf
[mysqld]
datadir=/var/lib/mysql
socket=/var/lib/mysql/mysql.sock
user=mysql
# Disabling symbolic-links is recommended to prevent assorted security risks
symbolic-links=0
bind-address = 127.0.0.1

[mysqld_safe]
log-error=/var/log/mysqld.log
pid-file=/var/run/mysqld/mysqld.pid
EOF

# Загруза и распаковка SugarCRMmkdir -p /data/www
mkdir -p /data/www
wget http://garr.dl.sourceforge.net/project/sugarcrm/1%20-%20SugarCRM%206.5.X/SugarCommunityEdition-6.5.X/SugarCE-6.5.20.zip
unzip SugarCE-6.5.20.zip
mv SugarCE-Full-6.5.20 /data/www/sugarcrm
chown -R apache:apache /data/www/sugarcrm

# Apache
mkdir /etc/httpd/vhosts
cat <<EOF > /etc/httpd/vhosts/sugarcrm.conf
<VirtualHost *:80>
        ServerAdmin info@domain.ltd
        DocumentRoot "/data/www/sugarcrm"
        ErrorLog "/var/log/httpd/sugarcrm-error.log"
        CustomLog "/var/log/httpd/sugarcrm-access.log" common
        AcceptPathInfo On
        <Directory /data/www/sugarcrm>
                AllowOverride All
                Order allow,deny
                Allow from all
        </Directory>
</VirtualHost>
EOF

cat <<EOF >> /etc/httpd/conf/httpd.conf
NameVirtualHost *:80
include vhosts/*.conf
EOF
chkconfig httpd on
service httpd start

# crontab
echo "*    *    *    *    *     cd /data/www/sugarcrm; php -f cron.php > /dev/null 2>&1" >> /etc/crontab

# php.ini
cp /etc/php.ini /etc/php.ini.orig
sed 's/upload_max_filesize =.*/upload_max_filesize = 16M/' /etc/php.ini.orig > /etc/php.ini
