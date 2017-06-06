#!/usr/bin/env bash

# Copy proxy.sh to profile.d
cp /vagrant/build_scripts/proxy.sh /etc/profile.d/

# 1. Install Python 3.5
yum -y install rh-python35

# 2. Install Redis 32
yum -y install rh-redis32

# 3. Setup /etc/profile.d/python.sh
bash -c "printf '#\!/bin/bash\nsource /opt/rh/rh-python35/enable\n' > /etc/profile.d/python35.sh"

# 4. Install Postgres Python Package (psycopg2) and Postgres Developer Package
yum -y install rh-postgresql95-postgresql-devel
yum -y install rh-python35-python-psycopg2

# 5. Install Developer Tools
yum -y groupinstall "Development Tools"

# 6. Install SAML Requirements
sudo yum -y install libxml2-devel xmlsec1-devel xmlsec1-openssl-devel libtool-ltd1-devel

# 7. Install Required pip Packages
source /opt/rh/rh-python35/enable
pip install virtualenv
mkdir /home/vagrant/.virtualenvs
virtualenv --system-site-packages /home/vagrant/.virtualenvs/gpp
chown -R vagrant:vagrant /home/vagrant
source /home/vagrant/.virtualenvs/gpp/bin/activate
echo "source /home/vagrant/.virtualenvs/gpp/bin/activate" >> /home/vagrant/.bash_profile
pip install -r /vagrant/requirements.txt --no-use-wheel

# 8. Install telnet-server
yum -y install telnet-server

# 9. Install telnet
yum -y install telnet

# 10. Add the following lines to /etc/sudoers file
# gpp ALL=(ALL) NOPASSWD: /etc/init.d/rh-redis32-redis start
# gpp ALL=(ALL) NOPASSWD: /etc/init.d/rh-redis32-redis stop
# gpp ALL=(ALL) NOPASSWD: /etc/init.d/rh-redis32-redis status
# gpp ALL=(ALL) NOPASSWD: /etc/init.d/rh-redis32-redis restart
# gpp ALL=(ALL) NOPASSWD: /etc/init.d/rh-redis32-redis condrestart
# gpp ALL=(ALL) NOPASSWD: /etc/init.d/rh-redis32-redis try-restart
