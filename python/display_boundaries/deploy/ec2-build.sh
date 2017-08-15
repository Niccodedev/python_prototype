#!/usr/bin/env bash

# --------------------------------------------
# STEP 1 - update, upgrade and install stuff
# --------------------------------------------

# update and upgrade Ubuntu
sudo DEBIAN_FRONTEND=noninteractive apt-get -q -y update
sudo DEBIAN_FRONTEND=noninteractive apt-get -q -y -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" dist-upgrade

# install Postgres
sudo add-apt-repository -y "deb http://apt.postgresql.org/pub/repos/apt/ xenial-pgdg main"
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo DEBIAN_FRONTEND=noninteractive apt-get -q -y update
sudo DEBIAN_FRONTEND=noninteractive apt-get -q -y install postgresql-9.6
sudo DEBIAN_FRONTEND=noninteractive apt-get -q -y install postgresql-9.6-postgis-2.3 postgresql-contrib-9.6
sudo DEBIAN_FRONTEND=noninteractive apt-get -q -y install postgis

# ---------------------------------------------------
# STEP 2 - restore data to Postgres and run server
# ---------------------------------------------------

# alter postgres user and create database
sudo -u postgres psql -c "ALTER USER postgres ENCRYPTED PASSWORD '<postgres-password>';"
sudo -u postgres createdb geo
sudo -u postgres psql -c "CREATE EXTENSION adminpack;CREATE EXTENSION postgis;" geo

# create read only user and grant access to all tables & sequences
sudo -u postgres psql -c "CREATE USER rouser WITH ENCRYPTED PASSWORD '<rouser-password>';" geo
sudo -u postgres psql -c "GRANT CONNECT ON DATABASE geo TO rouser;" geo
sudo -u postgres psql -c "GRANT USAGE ON SCHEMA public TO rouser;" geo
sudo -u postgres psql -c "GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO rouser;" geo
sudo -u postgres psql -c "GRANT SELECT ON ALL TABLES IN SCHEMA public to rouser;" geo
sudo -u postgres psql -c "GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO rouser;" geo  # for PostGIS functions

# stuff for Zappa and AWS Lambda testing
sudo wget -q http://minus34.com/test/zappa/admin_bdys_201705_display.dmp -O ~/tmp/admin_bdys_201705_display.dmp
sudo pg_restore -Fc -v -d geo -p 5432 -U postgres -h localhost ~/tmp/admin_bdys_201705_display.dmp

sudo -u postgres psql -c "GRANT USAGE ON SCHEMA admin_bdys_201705_display TO rouser;" geo
sudo -u postgres psql -c "GRANT SELECT ON ALL SEQUENCES IN SCHEMA admin_bdys_201705_display TO rouser;" geo
sudo -u postgres psql -c "GRANT SELECT ON ALL TABLES IN SCHEMA admin_bdys_201705_display to rouser;" geo
sudo -u postgres psql -c "ALTER DEFAULT PRIVILEGES IN SCHEMA admin_bdys_201705_display GRANT SELECT ON SEQUENCES TO rouser;" geo
sudo -u postgres psql -c "ALTER DEFAULT PRIVILEGES IN SCHEMA admin_bdys_201705_display GRANT SELECT ON TABLES TO rouser;" geo

# alter whitelisted postgres clients (the AWS Lamdba and the test client)
sudo sed -i -e "s/#listen_addresses = 'localhost'/listen_addresses = '*'/g" /etc/postgresql/9.6/main/postgresql.conf
echo -e "host\t geo\t rouser\t 0.0.0.0/0\t md5" | sudo tee -a /etc/postgresql/9.6/main/pg_hba.conf
#echo -e "host\t geo\t rouser\t 859uppjni0.execute-api.ap-southeast-2.amazonaws.com\t md5" | sudo tee -a /etc/postgresql/9.6/main/pg_hba.conf
echo -e "host\t geo\t rouser\t 101.164.227.2/22\t md5" | sudo tee -a /etc/postgresql/9.6/main/pg_hba.conf
sudo service postgresql restart

# delete dump files
cd ~/tmp
sudo find . -name "*.dmp" -type f -delete

# set environment variables for census-loader web map
export PGUSER="rouser"
export PGPASSWORD="<rouser-password>"
