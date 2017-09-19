FROM centos:6

# This is needed so that ansible managed to read "ansible_default_ipv4"
RUN yum install iproute -y 

# This step is needed since standard CentOS docker image does not come with EPEL installed by default
RUN yum install epel-release -y

# we can has SSH
EXPOSE 22

# pepare for takeoff
CMD ["/usr/sbin/init"]
