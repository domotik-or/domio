==================================================
Procédure d'installation du Raspberry Pi 4 Model B
==================================================

+--------------------+----------+----------------------------+
| Date               | Version  | Auteur                     |
+--------------------+----------+----------------------------+
| 2 mars 2025        | 1.0      | Franck Barbenoire          |
+--------------------+----------+----------------------------+

.. contents:: Table des matières
    :depth: 4

.. section-numbering::

.. raw:: pdf

   PageBreak oneColumn

.. header::
    ###Title###

.. footer::

    \- ###Page### -

Introduction
============

Ce document détaille la configuration matérielle et logicielle du calculateur.
Cela concerne un système de développement. Pour un système en production, on
utilise le projet Yocto (https://github.com/franckinux/yocto-domotik.git).

Ce document détaille également la procédure d'installation d'une carte Rasbperry
Pi 4 modèle B.

La procédure d'installation est décrite pour le système d'exploitation
Raspi OS (https://www.raspberrypi.com/software/operating-systems/).

Matériel
========

================================================ ===========
Désignation                                      Abréviation
================================================ ===========
Raspberry Pi 4, 2 ou 4 Gb de mémoire RAM         RPI
Coordinateur Zigbee                              ZIG
Relais carillon                                  CAR
Bouton sonnette                                  BUT
Horloge temps réel                               RTC
Compteur Linky                                   LKY
Convertisseur analogique numérique               ADC
Capteur de pression                              PRE
================================================ ===========

Bus
---

SPI
...

Non utilisé.

I2C
...

===== ========= ================
Carte Composant Adresse (7 bits)
===== ========= ================
PRE   BMP280    0x76
RTC   DS3231    0x68
===== ========= ================

UART
....

===== ==== ============ ================ ======= =======
Carte Port Device       Configuration    Gpio Tx Gpio Rx
===== ==== ============ ================ ======= =======
ZIG   USB  /dev/ttyACM0 \-               \-      \-
LKY   \-   /dev/ttyAMA0 9600, 7, 1, E    14      15
\-    \-   /dev/ttyAMA1 \-               14      15
\-    \-   /dev/ttyAMA2 \-               0       1
\-    \-   /dev/ttyAMA3 \-               4       5
\-    \-   /dev/ttyAMA4 \-               8       9
\-    \-   /dev/ttyAMA5 \-               12      13
===== ==== ============ ================ ======= =======

Extrait de https://raspberrypi.stackexchange.com/questions/45570/how-do-i-make-serial-work-on-the-raspberry-pi3-pizerow-pi4-or-later-models/107780#107780 :

.. table:: Tableau d'affection des signaux des uarts

    ===== === === === === ========
    UART  TXD RXD CTS RTS Alt
    ===== === === === === ========
    uart0 14  15
    uart1 14  15
    uart2 0   1   2   3   I2C0
    uart3 4   5   6   7
    uart4 8   9   10  11  SPI0
    uart5 12  13  14  15  gpio-fan
    ===== === === === === ========

You CAN use uart2 on Pi4 but need to disable other uses of GPIO0/1 with
`force_eeprom_read=0` & `disable_poe_fan=1`.

Affectation des pins
--------------------

La table ci-dessous est l'inventaire des broches du bus du Raspberry Pi et de
leur affectation.

.. table:: Tableau d'affection des signaux du bus du Raspberry Pi

    === ==== ===========================================
    Pin Gpio Affectation
    === ==== ===========================================
    1   \-   3.3V
    2   \-   5V
    3   2    GPIO | **I2C - SDA**
    4   \-   5V
    5   3    GPIO | **I2C - SCL**
    6   \-   GND
    7   4    GPIO | GPCLK0 | UART /dev/ttyAMA3 - TX
    8   14   GPIO | UART /dev/ttyAMA0 - TX
    9   \-   GND
    10  15   GPIO | **UART /dev/ttyAMA0 - RX : Linky**
    11  17   **GPIO - input : Shutdown**
    12  18   GPIO | PCMCLK
    13  27   GPIO
    14  \-   GND
    15  22   GPIO
    16  23   **GPIO - out : Buzzer**
    17  \-   3.3V
    18  24   **GPIO - out : Carillon**
    19  10   GPIO | MOSI
    20  \-   GND
    21  9    GPIO | MISO | UART /dev/ttyAMA4 - RX
    22  25   GPIO
    23  11   GPIO | SCLK
    24  8    GPIO | CE0 | UART /dev/ttyAMA4 - TX
    25  GND  \-
    26  7    GPIO | CE1
    27  0    GPIO | ID_SD | UART /dev/ttyAMA2 - TX
    28  1    GPIO | ID_SC | UART /dev/ttyAMA2 - RX
    29  5    **GPIO - in : présence 220V** | UART /dev/ttyAMA3 - RX
    30  \-   GND
    31  6    **GPIO - in : Bouton de sonnette**
    32  12   GPIO | PWM0 | UART /dev/ttyAMA5 - TX
    33  13   GPIO | PWM1 | UART /dev/ttyAMA5 - RX
    34  \-   GND
    35  19   GPIO | PCM_FS
    36  16   GPIO
    37  26   GPIO
    38  20   GPIO | PCM_DIN
    39  \-   GND
    40  21   GPIO | PCM_DOUT
    === ==== ===========================================

.. figure:: GPIO-Pinout-Diagram-2.png
    :width: 100%

    Détail du connecteur de 40 broches du Raspberry Pi 4 B

Installation
============

L'installation est décrite pour un Raspberry Pi 4 B.

Préparation de la carte SD
--------------------------

Télécharger l'image de la carte SD, la décompressser et l'écrire dans la carte
SD.

Bien vérifier la destination `/dev/sdX` (risque d'écrasement d'une
autre partition que celle souhaitée avec des conséquences dramatiques...).

.. code:: console

    $ wget https://downloads.raspberrypi.com/raspios_lite_armhf/images/raspios_lite_armhf-2024-11-19/2024-11-19-raspios-bookworm-armhf-lite.img.xz
    $ unxz 2024-11-19-raspios-bookworm-armhf-lite.img.xz
    $ sudo dd bs=1M if=2024-11-19-raspios-bookworm-armhf-lite.img of=/dev/sdX
    $ sudo sync

Activer la sortie vidéo composite
---------------------------------

Je ne disose pas du câble micro-HDMI ↔ HDMI, j'ai dû activer l'affichage par
la vidéo composite. Les signaux sont disponibles dans le connecteur jack à 4
contacts de type TRRS (Tip-Ring-Ring-Sleeve).

Le câble dont je disposais n'était pas le bon : Ground sur le contact 4
(Sleeve) et vidéo sur contact 3. J'ai dû le refaire avec :

- Vidéo composite sur contact 4 (Sleeve) ;
- Ground sur contact 3 ;
- Audio non connectée.

.. image:: Model-B-Plus-Audio-Video-Jack-Diagram.png
    :width: 80%

Source de l'image : https://forums.raspberrypi.com/viewtopic.php?t=83446

Avant de booter sur la carte SD, modifier les fichiers suivants :

- Ajouter à la fin du fichier `boot/cmdline.txt` avec un espace en guise de
  séparateur :

.. code:: console

    vc4.tv_norm=PAL

- Dans le fichier `boot/config.txt` :

  - Commenter la ligne suivante :

.. code:: console

    # dtoverlay=vc4-kms-v3d

-

  - Ajouter les lignes suivantes :

.. code:: console

    sdtv_mode=2
    hdmi_ignore_hotplug=1
    enable_tvout=1

-

  - Et modifier la ligne suivante :

.. code:: console

    disable_overscan=0

Premier boot sur la carte SD
----------------------------

Connexions de base :

- Un écran sur le port HDMI ou l'entrée vidéo composite ;
- Un clavier sur un port USB ;
- Un câble Ethernet entre le RPI et une box.

Introduire la cartes SD dans le RPI et le mettre sous tension. Après la
séquence de boot, un menu de configuration appararaît :

- Configuration du clavier : `Other` puis  `French` puis `French` ;
- Création d'un nouvel utilisateur : `domotik` avec le mot de passe
  `h***s****h***` ;

Se connecter sous le compte précédemment créé puis mettre à jour les packages :

.. code:: console

    $ sudo apt update
    $ sudo apt full-upgrade

Mettre à jour le firmware du RPI :

.. code:: console

    $ sudo rpi-update
    $ sudo reboot

Communication par ssh
---------------------

Configurer une liaison avec le RPI par Ethernet ou Wifi. Dans ce dernier cas,
on peut utliser `rpi-config`.

Également, autoriser le protocle ssh sur le RPI :

.. code:: console

   $ sudo systemctl start ssh.service
   $ sudo systemctl enable ssh.service

Générer les clés ssh sur le PC qui va communiquer avec le RPI :

.. code:: console

   $ ssh-keygen -t ed25519 -C "domotik@domain.com"

Puis les transférer dans le RPI par ssh :

.. code:: console

   $ sh-copy-id -f -i .ssh/domotik.pub domotik@xxx.xxx.xxx.xxx

Et enfin, on peut se connecter en ssh :

.. code:: console

   $ ssh domotik@xxx.xxx.xxx.xxx

Une fois la connexion réseau établie avec le RPI, on peut désactiver la vidéo
composite.

Fixer une adresse ip fixe
-------------------------

Déterminer quel gestionnaire de périphérique réseaux gère linterface. Exemple :

.. code:: console

    $ nmcli device status
    DEVICE  TYPE      STATE                   CONNECTION
    eth0    ethernet  connected               Wired connection 1
    lo      loopback  connected (externally)  lo
    wlan0   wifi      unavailable             --

    $ networkctl list
    WARNING: systemd-networkd is not running, output will be incomplete.

    IDX LINK  TYPE     OPERATIONAL SETUP
      1 lo    loopback -           unmanaged
      2 eth0  ether    -           unmanaged
      3 wlan0 wlan     -           unmanaged

    3 links listed.

L'interface `eth0` est gérée par NetworkManager. Assurez vous que l'adresse ip
fixe choisie n'entrera pas en conflit avec les adresses allouées par le DHCP.
L'adresse ip est fixée par l'outil en ligne de commande du NetworkManager :

.. code:: console

    sudo nmcli connection modify "Wired connection 1" ipv4.method "manual" \
    ipv4.addresses "192.168.1.50/24" ipv4.gateway "192.168.1.1" \
    ipv4.dns "80.10.246.2,80.10.246.129"

Gestion des périphériques intégrés
----------------------------------

Pour autoriser le bus I2C et SPI, modifier les lignes suivantes du fichier
`/boot/firmware/config.txt` :

.. code:: console

    dtparam=i2c_arm=on
    dtparam=spi=on

Pour interdire le Bluetooth et le Wifi, ajouter les lignes suivantes à la fin du
fichier `/boot/firmware/config.txt` :

.. code:: console

    # Disable Bluetooth
    dtoverlay=disable-bt
    # Disable Wifi
    dtoverlay=disable-wifi

Ajouter les lignes suivantes à la fin du fichier `/etc/modules` :

.. code:: console

    i2c-dev

Bouton de shutdown
------------------

Pour disposer d'un bouton de shutdown, ajouter le ligne suivantes à la fin du
fichier `/boot/firmware/config.txt` :

.. code:: console

    dtoverlay=gpio-shutdown,gpio_pin=17,active_low=1,gpio_pull=up,debounce=200

Installation d'une horloge sauvegardée
--------------------------------------

Ajouter les lignes suivantes au fichier `/boot/firmware/config.txt` :

.. code:: console

    # Enable real time clock
    dtoverlay=i2c-rtc,ds3231

Supprimer un package :

.. code:: console

    $ sudo apt remove fake-hwclock

Si on utilise une autre source de temps (gps, dcf77, ...), on arrête la
synchronisation avec un serveur ntp :

.. code:: console

    $ sudo timedatectl set-ntp false

Modifier le fichier `/lib/udev/hwclock-set`. Mettre en commentaire ces trois
lignes :

.. code:: console

   #if [ -e /run/systemd/system ] ; then
   # exit 0
   #fi

Détermination du fuseau horaire
-------------------------------

.. code:: console

   timedatectl set-timezone Europe/Paris

Configuration de la liaison série
---------------------------------

Modifier le fichier `/boot/cmdline` et supprimer le texte depuis `console`
jusqu'à `115200`.

Ne pas démarrer un shell sur la liaison série.

.. code:: console

    $ sudo systemctl mask serial-getty@ttyAMA0.service

Installation de packages supplémentaires
----------------------------------------

.. code:: console

    $ sudo install vim git pigpio i2c-tools spi-tools picocom
    $ sudo install python3-setuptools python3-pip
    $ sudo install ufw

Démarrage du daemon `pigpiod` :

.. code:: console

    $ sudo systemctl start pigpiod
    $ sudo systemctl enable pigpiod
    $ sudo systemctl start ufw
    $ sudo systemctl enable ufw

Arrêt de services
-----------------

.. code:: console

    $ sudo systemctl stop ModemManager.service
    $ sudo systemctl disable ModemManager.service

Installation de l'application
-----------------------------

Cloner l'application :

.. code:: console

    $ cd ~
    $ git clone https://github.com/franckinux/domio.git

Installer des packages Python supplémentaires :

.. code:: console

    $ cd domotik
    $ pip install --user --break-system-packages -r requirements.txt

Permettre de lancement de l'application au démarrage du RPI :

.. code:: console

    $ cd ~/domio
    $ mkdir -p ~/.config/domotik
    $ cp config.toml ~/.config/domotik/domio.toml
    $ sudo cp domio.service /etc/systemd/system
    $ sudo systemctl enable domio.service
    $ sudo systemctl start domio.service

Zigbee
======

Mosquitto
---------

 Installer Mosquitto :

.. code:: console

    $ sudo apt install mosquitto mosquitto-clients
    $ sudo systemctl enable mosquitto
    $ sudo systemctl start mosquitto

Nodejs
------

.. code:: console

    $ sudo curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    $ sudo apt install -y nodejs git make g++ gcc libsystemd-dev
    $ npm install -g pnpm
    $ node --version
    v20.18.3
    $ pnpm --version
    9.15.4

Zigbee2mqtt
-----------

Source :
`Zigbee2mqtt installation on Linux <https://www.zigbee2mqtt.io/guide/installation/01_linux.html>`_.

Installation :

.. code:: console

    $ sudo mkdir /opt/zigbee2mqtt
    $ sudo chown -R ${USER}: /opt/zigbee2mqtt
    $ git clone --depth 1 https://github.com/Koenkk/zigbee2mqtt.git /opt/zigbee2mqtt
    $ cd /opt/zigbee2mqtt
    $ pnpm i --frozen-lockfile

    <needs update>

    $ pnpm run build

    > zigbee2mqtt@2.1.1 build /opt/zigbee2mqtt
    > tsc && node index.js writehash

Configuration :

.. code:: console

    cp /opt/zigbee2mqtt/data/configuration.example.yaml /opt/zigbee2mqtt/data/configuration.yaml

Lancement :

.. code:: console

	$ npm start

	> zigbee2mqtt@1.37.1 start
	> node index.js

	[2024-05-13 21:18:53] info: 	z2m: Logging to console, file (filename: log.log)
	[2024-05-13 21:18:53] info: 	z2m: Starting Zigbee2MQTT version 1.37.1 (commit #c02c61d)
	[2024-05-13 21:18:53] info: 	z2m: Starting zigbee-herdsman (0.46.6)
	[2024-05-13 21:18:54] info: 	zh:zstack:znp: Opening SerialPort with {"path":"/dev/ttyACM0","baudRate":115200,"rtscts":false,"autoOpen":false}
	[2024-05-13 21:18:54] info: 	zh:zstack:znp: Serialport opened
	[2024-05-13 21:18:54] info: 	z2m: zigbee-herdsman started (resumed)
	[2024-05-13 21:18:54] info: 	z2m: Coordinator firmware version: '{"meta":{"maintrel":2,"majorrel":2,"minorrel":7,"product":2,"revision":20190425,"transportrev":2},"type":"zStack30x"}'
	[2024-05-13 21:18:54] info: 	z2m: Currently 0 devices are joined:
	[2024-05-13 21:18:54] info: 	z2m: Zigbee: disabling joining new devices.
	[2024-05-13 21:18:54] info: 	z2m: Connecting to MQTT server at mqtt://localhost
	[2024-05-13 21:18:55] info: 	z2m: Connected to MQTT server
	[2024-05-13 21:18:55] info: 	z2m: Started frontend on port 8080
	[2024-05-13 21:18:55] info: 	z2m: Zigbee2MQTT started!

	[2024-05-13 21:20:25] info: 	z2m: Zigbee: allowing new devices to join.
	[2024-05-13 21:20:58] info: 	zh:controller: Interview for '0x8cf681fffed7d4c7' started
	[2024-05-13 21:20:58] info: 	z2m: Device '0x8cf681fffed7d4c7' joined
	[2024-05-13 21:20:58] info: 	z2m: Starting interview of '0x8cf681fffed7d4c7'
	[2024-05-13 21:22:14] info: 	zh:controller: Succesfully interviewed '0x8cf681fffed7d4c7'
	[2024-05-13 21:22:14] info: 	z2m: Successfully interviewed '0x8cf681fffed7d4c7', device has successfully been paired
	[2024-05-13 21:22:14] info: 	z2m: Device '0x8cf681fffed7d4c7' is supported, identified as: HEIMAN Smart doorbell button (HS2SS-E_V03)
	[2024-05-13 21:22:14] info: 	z2m: Configuring '0x8cf681fffed7d4c7'
	[2024-05-13 21:22:22] info: 	z2m: Successfully configured '0x8cf681fffed7d4c7'

	^C
    [2024-05-13 21:25:10] info: 	z2m: Disconnecting from MQTT server
	[2024-05-13 21:25:10] info: 	z2m: Stopping zigbee-herdsman...
	[2024-05-13 21:25:12] info: 	zh:controller: Wrote coordinator backup to '/opt/zigbee2mqtt/data/coordinator_backup.json'
	[2024-05-13 21:25:12] info: 	zh:zstack:znp: closing
	[2024-05-13 21:25:12] info: 	zh:zstack:znp: Port closed
	[2024-05-13 21:25:12] info: 	z2m: Stopped zigbee-herdsman
	[2024-05-13 21:25:12] info: 	z2m: Stopped Zigbee2MQTT

Autostart
---------

Contenu du fichier `zigbee2mqtt.service` :

.. code:: console

    [Unit]
    Description=zigbee2mqtt
    After=network.target

    [Service]
    Environment=NODE_ENV=production
    Type=notify
    ExecStart=/usr/bin/node index.js
    WorkingDirectory=/opt/zigbee2mqtt
    StandardOutput=inherit
    # Or use StandardOutput=null if you don't want Zigbee2MQTT messages filling syslog, for more options see systemd.exec(5)
    StandardError=inherit
    WatchdogSec=10s
    Restart=always
    RestartSec=10s
    User=domotik

    [Install]
    WantedBy=multi-user.target

.. code:: console

	$ sudo cp zigbee2mqtt.service /etc/systemd/system
	$ sudo systemctl daemon-reload
	$ sudo systemctl enable zigbee2mqtt.service
	$ sudo systemctl start zigbee2mqtt.service

Mettre à jour Zigbee2mqtt
-------------------------

.. code:: console

    $ cd /opt/zigbee2mqtt
    $ ./update.sh

Debug
-----

.. code:: console

    mosquitto_pub -t home/doorbell/timestamp -m "`date +%s`"
    mosquitto_sub -t home/doorbell/button
