Vagrant.configure("2") do |config|
  config.vm.box = "bento/centos-8"

  config.vm.box_check_update = false

  config.vm.provider "virtualbox" do |vb|
    vb.memory = "1024"
  end

  config.vm.define "mongo1" do |mongo1|
    mongo1.vm.box = "bento/centos-8"
    mongo1.vm.network "private_network", ip: "192.168.64.11"
    mongo1.vm.hostname = "mongo1"
    mongo1.vm.provision "shell", inline: <<-SHELL
      sudo echo "192.168.64.22 mongo2" | sudo tee -a /etc/hosts
      sudo echo "192.168.64.33 mongo3" | sudo tee -a /etc/hosts
    SHELL
    mongo1.vm.provision "ansible" do |ansible|
      ansible.playbook = "site.yml"
      ansible.extra_vars = {

      }
      ansible.raw_arguments = [
        "--become",
        "-vv"
      ]
    end
  end

  config.vm.define "mongo2" do |mongo2|
    mongo2.vm.box = "bento/centos-8"
    mongo2.vm.network "private_network", ip: "192.168.64.22"
    mongo2.vm.hostname = "mongo2"
    mongo2.vm.provision "shell", inline: <<-SHELL
      sudo echo "192.168.64.11 mongo1" | sudo tee -a /etc/hosts
      sudo echo "192.168.64.33 mongo3" | sudo tee -a /etc/hosts
    SHELL
    mongo2.vm.provision "ansible" do |ansible|
      ansible.playbook = "site.yml"
      ansible.extra_vars = {

      }
      ansible.raw_arguments = [
        "--become",
        "-vv"
      ]
    end
  end

  config.vm.define "mongo3" do |mongo3|
    mongo3.vm.box = "bento/centos-8"
    mongo3.vm.network "private_network", ip: "192.168.64.33"
    mongo3.vm.hostname = "mongo3"
    mongo3.vm.provision "shell", inline: <<-SHELL
      sudo echo "192.168.64.11 mongo1" | sudo tee -a /etc/hosts
      sudo echo "192.168.64.22 mongo2" | sudo tee -a /etc/hosts
    SHELL
    mongo3.vm.provision "ansible" do |ansible|
      ansible.playbook = "site.yml"
      ansible.extra_vars = {

      }
      ansible.raw_arguments = [
        "--become",
        "-vv"
      ]
    end
  end

end
