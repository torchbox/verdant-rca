# -*- mode: ruby -*-
# vi: set ft=ruby :


Vagrant.configure(2) do |config|
  # Base box
  config.vm.box = "torchbox/wagtail-jessie64"
  config.vm.box_version = "~> 1.0"

  # Port forwarding
  config.vm.network "forwarded_port", guest: 8000, host: 8000

  # More memory
  config.vm.provider "virtualbox" do |vb|
    vb.memory = "2048"
  end

  # Provision with bash script
  config.vm.provision :shell, :path => "vagrant/provision.sh"

  # Enable agent forwarding over SSH connections.
  config.ssh.forward_agent = true
end
