Can bus configuration
=====================

In config.txt :

.. code::

    dtparam=spi=on
    dtoverlay=mcp2515-can0,oscillator=8000000,interrupt=25
    dtoverlay=spi-bcm2835-overlay

Reboot.

.. code:: console

    # ip a
    1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
        ...
    2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000
        ...
    3: can0: <NOARP,UP,LOWER_UP,ECHO> mtu 16 qdisc pfifo_fast state UP group default qlen 10
        link/can

.. code:: console

    # ls /sys/bus/spi/devices/spi0.0/net/can0/
addr_assign_type  broadcast        carrier_down_count  dev_id    duplex             ifalias  link_mode         napi_defer_hard_irqs  phys_port_id    power       speed       testing       type
address           carrier          carrier_up_count    dev_port  flags              ifindex  mtu               netdev_group          phys_port_name  proto_down  statistics  threaded      uevent
addr_len          carrier_changes  device              dormant   gro_flush_timeout  iflink   name_assign_type  operstate             phys_switch_id  queues      subsystem   tx_queue_len

.. code:: console

    # /sbin/ip link set can0 up type can bitrate 125000

    # candump can0
      can0  101   [4]  09 DA 16 F5
      can0  101   [4]  09 D9 16 F6
      can0  101   [4]  09 DA 16 F4
      can0  101   [4]  09 DB 16 F8
      can0  101   [4]  09 DA 16 F5
