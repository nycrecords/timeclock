#!/usr/bin/env bash

# 1. Install Python 3.5
yum -y install rh-python35

# 2. Install Redis 3.2
yum -y install rh-redis32

# 3. Setup /etc/profile.d/python.sh
bash -c "printf '#\!/bin/bash\nsource /opt/rh/rh-python35/enable\n' > /etc/profile.d/python35.sh"

# 4. Install Postgres Python Package (psycopg2) and Postgres Developer Packagecd /
yum -y install rh-postgresql95-postgresql-devel
yum -y install rh-python35-python-psycopg2
yum -y install openssl-devel
yum -y install libffi-devel
yum -y install libxslt
yum -y install libxslt-devel
yum -y install libxml2
yum -y install libxml2-devel
yum -y install libtiff-devel
yum -y install libjpeg-devel
yum -y install libzip-devel
yum -y install freetype-devel
yum -y install lcms2-devel
yum -y install libwebp-devel
yum -y install tcl-devel
yum -y install tk-devel
yum -y install xmlsec1-devel
yum -y install xmlsec1-openssl-devel

# 5. Install Developer Tools
yum -y groupinstall "Development Tools"

# 6. Install Required pip Packages
source /opt/rh/rh-python35/enable
pip install virtualenv
mkdir /home/vagrant/.virtualenvs
virtualenv --system-site-packages /home/vagrant/.virtualenvs/timeclock
chown -R vagrant:vagrant /home/vagrant
source /home/vagrant/.virtualenvs/timeclock/bin/activate
pip install -r /vagrant/requirements.txt --no-binary :all:

# 7. Install telnet-server
yum -y install telnet-server

# 8. Install telnet
yum -y install telnet

# 9. Automatically Use Virtualenv
echo "source /home/vagrant/.virtualenvs/timeclock/bin/activate" >> /home/vagrant/.bash_profile

# 9. Add the following lines to /etc/sudoers file
#womens_activism   ALL=(ALL) NOPASSWD: /etc/init.d/rh-redis32-redis start
#womens_activism   ALL=(ALL) NOPASSWD: /etc/init.d/rh-redis32-redis stop
#womens_activism   ALL=(ALL) NOPASSWD: /etc/init.d/rh-redis32-redis status
#womens_activism   ALL=(ALL) NOPASSWD: /etc/init.d/rh-redis32-redis restart
#womens_activism   ALL=(ALL) NOPASSWD: /etc/init.d/rh-redis32-redis condrestart
#womens_activism   ALL=(ALL) NOPASSWD: /etc/init.d/rh-redis32-redis try-restart
