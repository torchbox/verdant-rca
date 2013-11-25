#!/bin/bash
rm -f id_rsa*
/usr/bin/ssh-keygen -f id_rsa -N "" -q
cat ./id_rsa.pub
