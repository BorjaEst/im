 IM - Infrastructure Manager
============================

* Version ![PyPI](https://img.shields.io/pypi/v/im.svg)
* PyPI ![PypI](https://img.shields.io/pypi/dm/IM.svg)
* Build Status [![Build Status](http://jenkins.i3m.upv.es/buildStatus/icon?job=grycap/im-unit)](http://jenkins.i3m.upv.es/job/grycap/job/im-unit/)

IM is a tool that deploys complex and customized virtual infrastructures on IaaS
Cloud deployments (such as AWS, OpenStack, etc.). It eases the access and the
usability of IaaS clouds by automating the VMI (Virtual Machine Image)
selection, deployment, configuration, software installation, monitoring and
update of the virtual infrastructure. It supports APIs from a large number of virtual
platforms, making user applications cloud-agnostic. In addition it integrates a
contextualization system to enable the installation and configuration of all the
user required applications providing the user with a fully functional
infrastructure.

Read the documentation and more at http://www.grycap.upv.es/im.

There is also an Infrastructure Manager YouTube reproduction list with a set of videos with demos
of the functionality of the platform: https://www.youtube.com/playlist?list=PLgPH186Qwh_37AMhEruhVKZSfoYpHkrUp.


1 INSTALLATION
===============

1.1 REQUISITES
--------------

IM is based on Python, so Python 2.6 or higher runtime and standard library must
be installed in the system.

If you use pip to install the IM, all the requisites will be installed.
However, if you install IM from sources you should install:

 + The RADL parser (https://github.com/grycap/radl), available in pip
   as the 'RADL' package.

 + The paramiko ssh2 protocol library for python version 1.14 or later
(http://www.lag.net/paramiko/), typically available as the 'python-paramiko' package.

 + The YAML library for Python, typically available as the 'python-yaml' or 'PyYAML' package.

 + The suds library for Python, typically available as the 'python-suds' package.
 
 + The Netaddr library for Python, typically available as the 'python-netaddr' package.

 + The Requests library for Python, typically available as the 'python-requests' package.

 + Ansible (http://www.ansibleworks.com/) to configure nodes in the infrastructures.
   In particular, Ansible 1.4.2+ must be installed.
   To ensure the functionality the following values must be set in the ansible.cfg file (usually found in /etc/ansible/):

```
[defaults]
transport  = smart
host_key_checking = False
# For old versions 1.X
sudo_user = root
sudo_exe = sudo

# For new versions 2.X
become_user      = root
become_method    = sudo

[paramiko_connection]

record_host_keys=False

[ssh_connection]

# Only in systems with OpenSSH support to ControlPersist
ssh_args = -o ControlMaster=auto -o ControlPersist=900s
# In systems with older versions of OpenSSH (RHEL 6, CentOS 6, SLES 10 or SLES 11) 
#ssh_args =
pipelining = True
```

1.2 OPTIONAL PACKAGES
---------------------

The Bottle framework (http://bottlepy.org/) is used for the REST API. 
It is typically available as the 'python-bottle' package.

The CherryPy Web framework (http://www.cherrypy.org/), is needed for the REST API. 
It is typically available as the 'python-cherrypy' or 'python-cherrypy3' package.
In newer versions (9.0 and later) the functionality has been moved to the 'cheroot' library
(https://github.com/cherrypy/cheroot) it can be installed using pip.

Apache-libcloud (http://libcloud.apache.org/) 0.17 or later is used in the
LibCloud, OpenStack and GCE connectors.

Boto (http://boto.readthedocs.org) 2.29.0 or later is used as interface to
Amazon EC2. It is available as package named ``python-boto`` in Debian based
distributions. It can also be downloaded from `boto GitHub repository (https://github.com/boto/boto).
Download the file and copy the boto subdirectory into the IM install path.

In case of using the a MySQL DB as the backend to store IM data. The Python interface to MySQL
must be installed, typically available as the package 'python-mysqldb' or 'MySQL-python' package.
In case of using Python 3 use the PyMySQL package, available as the package 'python3-pymysql' on 
debian systems or PyMySQL package in pip.  

In case of using the SSL secured version of the REST API pyOpenSSL must be installed.

Azure python SDK (https://azure.microsoft.com/es-es/develop/python/) is used to connect with the 
Microsoft Azure platform.


1.3 INSTALLING
--------------

### 1.3.1 Using installer (Recommended option)

The IM provides a script to install the IM in one single step (using pip).
You only need to execute the following command:

```sh
$ wget -qO- https://raw.githubusercontent.com/grycap/im/master/install.sh | bash
```

It works for the most recent version of the main Linux distributions (RHEL, CentOS, Fedora, Ubuntu, Debian).
In case that you O.S. does not work with this install script see next sections.

### 1.3.2 From PIP

**WARNING: In some linux old distributions (REL 6 or equivalents) you must unistall
the package python-crypto and python-paramiko before installing the IM with pip.**

```sh
$ rpm -e python-crypto python-paramiko --nodeps
```

First you need to install pip tool and some packages needed to compile some of the IM requirements.
To install them in Debian and Ubuntu based distributions, do::

```sh
$ apt update
$ apt install gcc python-dev libffi-dev libssl-dev python-pip sshpass python-pysqlite2 python-requests
```

In Red Hat based distributions (RHEL, CentOS, Amazon Linux, Oracle Linux,
Fedora, etc.), do:

```sh
$ yum install epel-release
$ yum install which gcc python-devel libffi-devel openssl-devel python-pip sshpass python-sqlite3dbm
```

For some problems with the dependencies of the apache-libcloud package in some systems (as ubuntu 14.04 or CentOS 6)
this package has to be installed manually:

```sh
$ pip install backports-ssl_match_hostname
```

Then you only have to call the install command of the pip tool with the IM package:

```sh
$ pip install IM
```

Pip will also install the, non installed, pre-requisites needed. So Ansible  1.4.2 or later will 
be installed in the system. Some of the optional packages are also installed please check if some
of IM features that you need requires to install some of the packages of section OPTIONAL PACKAGES. 

You must also remember to modify the ansible.cfg file setting as specified in the 
REQUISITES section.

### 1.3.3 From RPM packages (RH7)

Download the RPM package from [GitHub](https://github.com/grycap/im/releases/latest). 
Also remember to download the RPM of the RADL package also from [GitHub](https://github.com/grycap/radl/releases/latest). 
You must have the epel repository enabled:

```sh
$ yum install epel-release
```

Then install the downloaded RPMs:

```sh
$ yum localinstall IM-*.rpm RADL-*.rpm
```

Azure python SDK is not available in CentOS. So if you need the Azure plugin you have to manually install them using pip:

```sh
$ pip install msrest msrestazure azure-common azure-mgmt-storage azure-mgmt-compute azure-mgmt-network azure-mgmt-resource azure-mgmt-dns 
```

### 1.3.4 From Deb package (Tested with Ubuntu 14.04 and 16.04)

Download the Deb package from [GitHub](https://github.com/grycap/im/releases/latest).
Also remember to download the Deb of the RADL package also from [GitHub](https://github.com/grycap/radl/releases/latest).

In Ubuntu 14.04 there are some requisites not available for the "trusty" version or are too old, so you have to manually install them manually.
You can download it from their corresponding PPAs. But here you have some links:
 
 * python-backports.ssl-match-hostname: [download](http://archive.ubuntu.com/ubuntu/pool/universe/b/backports.ssl-match-hostname/python-backports.ssl-match-hostname_3.4.0.2-1_all.deb)
 * python-scp: [download](http://archive.ubuntu.com/ubuntu/pool/universe/p/python-scp/python-scp_0.10.2-1_all.deb)
 * python-libcloud: [download](http://archive.ubuntu.com/ubuntu/pool/universe/libc/libcloud/python-libcloud_0.20.0-1_all.deb)

Also Azure python SDK is not available in Ubuntu 16.04. So if you need the Azure plugin you have to manually install them.
You can download it from their corresponding PPAs. But here you have some links:

 * python-msrestazure: [download](https://launchpad.net/ubuntu/+archive/primary/+files/python-msrestazure_0.4.3-1_all.deb)
 * python-msrest: [download](https://launchpad.net/ubuntu/+archive/primary/+files/python-msrest_0.4.4-1_all.deb)
 * python-azure: [download](https://launchpad.net/ubuntu/+archive/primary/+files/python-azure_2.0.0~rc6+dfsg-2_all.deb)

It is also recommended to configure the Ansible PPA to install the newest versions of Ansible (see [Ansible installation](http://docs.ansible.com/ansible/intro_installation.html#latest-releases-via-apt-ubuntu)):

```sh
$ sudo apt-get install software-properties-common
$ sudo apt-add-repository ppa:ansible/ansible
$ sudo apt-get update
```

Put all the .deb files in the same directory and do::

```sh
$ sudo dpkg -i *.deb
$ sudo apt install -f -y
```

### 1.3.5 FROM SOURCE

Select a proper path where the IM service will be installed (i.e. /usr/local/im,
/opt/im or other). This path will be called IM_PATH

```sh
$ tar xvzf IM-X.XX.tar.gz
$ chown -R root:root IM-X.XX
$ mv IM-X.XX /usr/local
```

Finally you must copy (or link) $IM_PATH/scripts/im file to /etc/init.d directory.

```sh
$ ln -s /usr/local/im/scripts/im /etc/init.d/im
```

1.4 CONFIGURATION
-----------------

In case that you want the IM service to be started at boot time, you must
execute the next set of commands:

On Debian Systems:

```sh
$ chkconfig im on
```

Or for newer systems like ubuntu 14.04:

```sh
$ sysv-rc-conf im on
```

On RedHat Systems:

```sh
$ update-rc.d im start 99 2 3 4 5 . stop 05 0 1 6 .
```

Or you can do it manually:

```sh
$ ln -s /etc/init.d/im /etc/rc2.d/S99im
$ ln -s /etc/init.d/im /etc/rc3.d/S99im
$ ln -s /etc/init.d/im /etc/rc5.d/S99im
$ ln -s /etc/init.d/im /etc/rc1.d/K05im
$ ln -s /etc/init.d/im /etc/rc6.d/K05im
```

Adjust the installation path by setting the IMDAEMON variable at /etc/init.d/im
to the path where the IM im_service.py file is installed (e.g. /usr/local/im/im_service.py),
or set the name of the script file (im_service.py) if the file is in the PATH
(pip puts the im_service.py file in the PATH as default).

Check the parameters in $IM_PATH/etc/im.cfg or /etc/im/im.cfg. Please pay attention
to the next configuration variables, as they are the most important:

DATA_DB - must be set to the URL to access the database to store the IM data. 
         Be careful if you have two different instances of the IM service running in the same machine!!.
         It can be a MySQL DB: 'mysql://username:password@server/db_name' or 
         a SQLite one: 'sqlite:///etc/im/inf.dat'.

CONTEXTUALIZATION_DIR - must be set to the full path where the IM contextualization files
		are located. In case of using pip installation the default value is correct
		(/usr/share/im/contextualization) in case of installing from sources set to
		$IM_PATH/contextualization (e.g. /usr/local/im/contextualization)

### 1.4.1 SECURITY

Security is disabled by default. Please notice that someone with local network access can "sniff" the traffic and
get the messages with the IM with the authorisation data with the cloud providers.

Security can be activated both in the XMLRPC and REST APIs. Setting this variables:

XMLRCP_SSL = True

or

REST_SSL = True

And then set the variables: XMLRCP_SSL_* or REST_SSL_* to your certificates paths.

2 DOCKER IMAGE
===============

A Docker image named `grycap/im` has been created to make easier the deployment of an IM service using the 
default configuration. Information about this image can be found here: https://registry.hub.docker.com/u/grycap/im/.

How to launch the IM service using docker::

```sh
$ sudo docker run -d -p 8899:8899 -p 8800:8800 --name im grycap/im
```

To make the IM data persistent you also have to specify a persistent location for the IM database using the IM_DATA_DB environment variable and adding a volume::

```sh
$ sudo docker run -d -p 8899:8899 -p 8800:8800 -v "/some_local_path/db:/db" -e IM_DATA_DB=/db/inf.dat --name im grycap/im
```

You can also specify an external MySQL server to store IM data using the IM_DATA_DB environment variable::
  
```sh
$ sudo docker run -d -p 8899:8899 -p 8800:8800 -e IM_DATA_DB=mysql://username:password@server/db_name --name im grycap/im 
```

Or you can also add a volume with all the IM configuration::

```sh
$ sudo docker run -d -p 8899:8899 -p 8800:8800 -v "/some_local_path/im.cfg:/etc/im/im.cfg" --name im grycap/im
```
