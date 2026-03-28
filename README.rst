Used links
==========

- https://community.volumio.com/t/guide-prepare-raspberry-pi-for-boot-from-usb-nvme/65700
- https://www.adgensee.com/blog/culture-geek-2/redimensionner-partition-linux-47
- https://www.chienlit.com/booter-un-raspberry-pi-4-b-sur-un-ssd-externe-ne-demarre-pas/
- https://github.com/MichaIng/DietPi/issues/7721
- https://www.f4htb.fr/2021/04/29/synchroniser-date-et-heure-du-raspberry-pi-sur-ds3231-au-demarrage-puis-via-gps/
- https://askubuntu.com/questions/246077/how-to-setup-a-static-ip-for-network-manager-in-virtual-box-on-ubuntu-server
- https://www.monpetitforfait.com/comparateur-box-internet/aides/dns-orange#:~:text=Cette%20%C3%A9tape%20technique%20implique%20la,l%27adresse%20du%20DNS%20secondaire.

Can bus configuration
=====================

In config.txt :

.. code::

    dtparam=spi=on
    dtoverlay=mcp2515-can0,oscillator=8000000,interrupt=25
    dtoverlay=spi-bcm2835-overlay

Reboot.

.. code:: console

    # ip link set can0 up type can bitrate 125000

    # ip a
    1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
        ...
    2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000
        ...
    3: can0: <NOARP,UP,LOWER_UP,ECHO> mtu 16 qdisc pfifo_fast state UP group default qlen 10
        link/can
    4: wlan0: <BROADCAST,MULTICAST> mtu 1500 qdisc noop state DOWN group default qlen 1000
        ...

.. code:: console

    # ls /sys/bus/spi/devices/spi0.0/net/can0/
addr_assign_type  broadcast        carrier_down_count  dev_id    duplex             ifalias  link_mode         napi_defer_hard_irqs  phys_port_id    power       speed       testing       type
address           carrier          carrier_up_count    dev_port  flags              ifindex  mtu               netdev_group          phys_port_name  proto_down  statistics  threaded      uevent
addr_len          carrier_changes  device              dormant   gro_flush_timeout  iflink   name_assign_type  operstate             phys_switch_id  queues      subsystem   tx_queue_len

.. code:: console

    # candump can0
      can0  101   [4]  09 DA 16 F5
      can0  101   [4]  09 D9 16 F6
      can0  101   [4]  09 DA 16 F4
      can0  101   [4]  09 DB 16 F8
      can0  101   [4]  09 DA 16 F5
