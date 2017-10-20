# **Golf Course Catalog**
This package gives anyone with access to the localhost port 5000 and a web browser the ability to interact with a fully-functioning ["CRUD" Website](https://en.wikipedia.org/wiki/Create,_read,_update_and_delete), implemented as a Golf Course Catalog. The website is complete with Google+ user authorization and authentication and 'personalized' user content.

## **Getting Started**
### Prior to installation
Prior to loading the package, you should have:
- Installed [Vagrant](http://vagrantup.com/) and [VirtualBox](https://www.virtualbox.org/)

### Installation
1. Clone this repo

2. Launch the Vagrant VM (after navigating to the directory in which you saved this repo):
```
$ vagrant up
$ vagrant ssh
```

3. Run:
```
$ python models.py
```
to initialize sqlite3 database

4. Run:
```
$ python application.py
```
to boot up web server

5. Access "localhost:5000/" to get started building a Golf Course Catalog

## **Common Usage**
The webserver is usually run via a VirtualBox VM, but can be run on an machine with the ability to host on localhost port 5000.

## **Known Issues**
1. The code has a bug in which the padding on the profile-picture is not consistent on all pages.

## **License**
This code is covered under an [MIT License](./LICENSE)
