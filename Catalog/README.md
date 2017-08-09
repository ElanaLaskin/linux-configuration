# Restaurant Menus #

# This is an application that provides a list of items within a variety of categories as well as a user registration and authentication system. Registered users have the ability to post, edit and delete their own items.

This project contains:
* "static" directory for CSS styling
* "templates" directory with the html page templates
* client_secrets.json
* database_setup.py
* final-project.py
* lotsofmenus.py
* pg_config.sh
* Vagrantfile

Instructions to run application:

1. Install vagrant and Virtual Box
2. Cd to this project directory--to the level of the Vagrantfile
3. run `vagrant up && vagrant ssh`
4. run `python database_setup.py` # sets up database
5. run `python lotsofmenus.py` # populates the database
6. run `python final-project.py` # runs application
7. visit http://localhost:5000/login in browser


## Public Ip Address ##
34.201.153.57:80
http://34.201.153.57/

## Summary of Software Installed and Configuration Changes ##

sudo apt-get update
sudo apt-get upgrade
sudo apt-get dist-upgrade
sudo ufw allow 2200/tcp
sudo ufw allow www
sudo ufw allow 2200/ntp
sudo ufw allow 123/ntp
sudo ufw allow 123/tcp
sudo ufw allow ssh
sudo ufw enable
sudo ufw deny ssh
sudo useradd grader
sudo vi /etc/ssh/sshd_config
sudo service ssh restart
sudo a2enmod
sudo -H pip install sqlalchemy
sudo apt-get install postgresql
sudo pip install psycopg2 
sudo apt-get install git
