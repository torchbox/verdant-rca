# -*- mode: ruby -*-
# vi: set ft=ruby :


Vagrant.configure(2) do |config|
  # Base box
  config.vm.box = "wagtail/buster64"
  config.vm.box_version = "~> 1.1"

  # Port forwarding
  config.vm.network "forwarded_port", guest: 8000, host: 8000

  # Provision with bash script
  config.vm.provision :shell, :path => "vagrant/provision.sh"

  # Enable agent forwarding over SSH connections.
  config.ssh.forward_agent = true

  config.vm.provider "virtualbox" do |v|
      v.memory = 1024
  end

end
