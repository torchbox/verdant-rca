#!/bin/bash

PROJECT_DIR=/vagrant/django-verdant
VIRTUALENV_DIR=/home/vagrant/.virtualenvs/rca

PYTHON=$VIRTUALENV_DIR/bin/python
PIP=$VIRTUALENV_DIR/bin/pip

NODE_VERSION=v4.2.3

# Dependencies for LDAP
apt-get install -y libldap2-dev libsasl2-dev

# Node.js, CoffeeScript and LESS
if ! command -v npm; then
    INSTALL_NODE=1
elif [ $NODE_VERSION != `node --version` ]; then
    rm -rf /opt/node-`node --version`-linux-x64/
    rm /usr/local/bin/node
    rm /usr/local/bin/npm
    INSTALL_NODE=1
else
    INSTALL_NODE=0
fi
if [ $INSTALL_NODE = 1 ]; then
    wget http://nodejs.org/dist/$NODE_VERSION/node-$NODE_VERSION-linux-x64.tar.gz
    cd /opt && tar -xzf /home/vagrant/node-$NODE_VERSION-linux-x64.tar.gz
    ln -s /opt/node-$NODE_VERSION-linux-x64/bin/node /usr/local/bin/node
    ln -s /opt/node-$NODE_VERSION-linux-x64/bin/npm /usr/local/bin/npm
    cd /home/vagrant
    rm node-$NODE_VERSION-linux-x64.tar.gz
fi
if ! command -v coffee; then
    npm install -g coffee-script
fi
if ! command -v lessc; then
    npm install -g less
fi

# use YAML for test fixtures
apt-get install -y libyaml-dev

# Create database
su - vagrant -c "createdb verdant"


# Virtualenv setup for project
su - vagrant -c "virtualenv --python=python2 $VIRTUALENV_DIR"
su - vagrant -c "echo $PROJECT_DIR > $VIRTUALENV_DIR/.project"


# Install PIP requirements
su - vagrant -c "$PIP install -r $PROJECT_DIR/requirements.txt"


# Install CoffeeScript and LESS (into /home/vagrant/node_modules/)
su - vagrant -c "npm install --prefix=/home/vagrant/ coffee-script less"


# Set execute permissions on manage.py as they get lost if we build from a zip file
chmod a+x $PROJECT_DIR/manage.py


# Add a couple of aliases to manage.py into .bashrc
cat << EOF >> /home/vagrant/.bashrc
export PYTHONPATH=$PROJECT_DIR
export DJANGO_SETTINGS_MODULE=rcasite.settings.dev

alias dj="django-admin.py"
alias djrun="dj runserver 0.0.0.0:8000"

source $VIRTUALENV_DIR/bin/activate
export PS1="[rca \W]\\$ "
export PATH=/home/vagrant/node_modules/.bin/:\$PATH
cd $PROJECT_DIR
EOF
