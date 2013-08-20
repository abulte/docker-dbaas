# Docker Databases As A Service

## /!\ Work In Progress

## Purpose & features

* Deploy and monitor MySQL and MongoDB databases on [Docker](http://www.docker.io)
* Command line tool
* Web UI
* Pluggable database type (write your own adapter)

## Install

TODO

## Use

TODO

## Depends and uses

* [Flask](http://flask.pocoo.org)
* [Flask-Script](http://flask-script.readthedocs.org/en/latest/)
* [Docker](http://www.docker.io)

## TODO

* Catch exception in command line client to print result
* See about the circular imports ugly mess (Flask Plugin/Extension?)
* Split optionnal and mandatory requirements (+ tests at import)
* Implement "port mapping?" option
* Automatic tests