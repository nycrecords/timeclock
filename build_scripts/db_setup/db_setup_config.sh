#!/usr/bin/env bash

# 11. Create postgres users
sudo -u postgres /opt/rh/rh-postgresql95/root/usr/bin/createuser -s -e developer
sudo -u postgres /opt/rh/rh-postgresql95/root/usr/bin/createuser -s -e timeclock_db

# 12. Create database
sudo -u postgres /opt/rh/rh-postgresql95/root/usr/bin/createdb timeclock

# 13. Add the following lines to /etc/sudoers file (allows running postgres commands without sudo access)
#timeclock  ALL=(ALL) NOPASSWD: /etc/init.d/rh-postgresql95-postgresql start
#timeclock  ALL=(ALL) NOPASSWD: /etc/init.d/rh-postgresql95-postgresql stop
#timeclock  ALL=(ALL) NOPASSWD: /etc/init.d/rh-postgresql95-postgresql status
#timeclock  ALL=(ALL) NOPASSWD: /etc/init.d/rh-postgresql95-postgresql restart
#timeclock  ALL=(ALL) NOPASSWD: /etc/init.d/rh-postgresql95-postgresql condrestart
#timeclock  ALL=(ALL) NOPASSWD: /etc/init.d/rh-postgresql95-postgresql try-restart
#timeclock  ALL=(ALL) NOPASSWD: /etc/init.d/rh-postgresql95-postgresql reload
#timeclock  ALL=(ALL) NOPASSWD: /etc/init.d/rh-postgresql95-postgresql force-reload
#timeclock  ALL=(ALL) NOPASSWD: /etc/init.d/rh-postgresql95-postgresql initdb
#timeclock  ALL=(ALL) NOPASSWD: /etc/init.d/rh-postgresql95-postgresql upgrade
