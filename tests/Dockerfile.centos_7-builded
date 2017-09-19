FROM centos:7

# This is needed so that ansible managed to read "ansible_default_ipv4"
RUN yum install iproute -y 

# This step is needed since standard CentOS docker image does not come with EPEL installed by default
RUN yum install epel-release -y

# This step is needed since standard CentOS docker image does not come with init-functions installed by default.
# This package seems to be required for Mongo 3.2 and downwards
RUN yum install initscripts -y

# we can has SSH
EXPOSE 22

# pepare for takeoff
CMD ["/usr/sbin/init"]
