==================================================
Procédure d'installation du Raspberry Pi 4 Model B
==================================================

+--------------------+----------+----------------------------+
| Date               | Version  | Auteur                     |
+--------------------+----------+----------------------------+
| 8 mai 2024         | 1.0      | Franck Barbenoire          |
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
PRE   BMP180A   0x77
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
    10  15   GPIO
    11  17   GPIO
    12  18   GPIO | PCMCLK
    13  27   GPIO
    14  \-   GND
    15  22   GPIO
    16  23   **GPIO - out : Carillon**
    17  \-   3.3V
    18  24   **GPIO - in : Bouton de sonnette**
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
    29  5    GPIO | UART /dev/ttyAMA3 - RX
    30  \-   GND
    31  6    GPIO
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

    wget https://downloads.raspberrypi.com/raspios_lite_arm64/images/raspios_lite_arm64-2024-03-15/2024-03-15-raspios-bookworm-arm64-lite.img.xz
    unxz 2024-03-15-raspios-bookworm-arm64-lite.img.xz
    sudo dd bs=1M if=2024-03-15-raspios-bookworm-arm64-lite.img of=/dev/sdX
    sudo sync

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
- Un câble Ethernet entre le RPI une box.

Introduire la cartes SD dans le RPI et le mettre sous tension. Après la
séquence de boot, un menu de configuration appararaît :

- Configuration du clavier : `Other` puis  `French` puis `French` ;
- Création d'un nouvel utilisateur : `domotik` avec le mot de passe
  `h***s****h***` ;

Se connecter sous le compte précédemment créé puis mettre à jour les packages :

.. code:: console

    sudo apt update
    sudo apt full-upgrade

Mettre à jour le firmware du RPI :

.. code:: console

    sudo rpi-update
    sudo reboot

Communication par ssh
---------------------

Configurer une liaison avec le RPI par Ethernet ou Wifi. Dans ce dernier cas,
on peut utliser `rpi-config`.

Également, autoriser le protocle ssh sur le RPI :

.. code:: console
   sudo systemctl start ssh.service
   sudo systemctl enable ssh.service

Générer les clés ssh sur le PC qui va communiquer avec le RPI :

.. code:: console

   ssh-keygen -t ed25519 -C "domotik@domain.com"

Puis les transférer dans le RPI par ssh :

.. code:: console

   sh-copy-id -f -i .ssh/domotik.pub domotik@xxx.xxx.xxx.xxx

Et enfin, on peut se connecter en ssh :

.. code:: console

   ssh domotik@xxx.xxx.xxx.xxx

Ceci est à faire uniquement si un câble Ethernet est connecté. Dans le RPI,
fixer une adresse ip fixe pour la liaison filaire. Ajouter les lignes ci-dessous
(à adapter à votre cas) dans le fichier `/etc/network/interfaces`  :

.. code:: console

    auto eth0
    iface eth0 inet static
    address 192.168.1.50
    netmask 255.255.255.0
    gateway 192.168.1.1
    dns-nameservers xxx.xxx.xxx.xxx,xxx.xxx.xxx.xxx

Une fois la connexion réseau établie avec le RPI, on peut désactiver la vidéo
composite.

Gestion des périphériques intégrés
----------------------------------

Pour autoriser le bus I2C, modifier les lignes suivantes du fichier
`/boot/config.txt` :

.. code:: console

    dtparam=i2c_arm=on

Pour interdire le Bluetooth et le Wifi, ajouter les lignes suivantes à la fin du
fichier `/boot/config.txt` :

.. code:: console

    # Disable Bluetooth
    dtoverlay=disable-bt
    # Disable Wifi
    dtoverlay=disable-wifi

Ajouter les lignes suivantes à la fin du fichier `/etc/modules` :

.. code:: console

    i2c-dev

Installation d'une horloge sauvegardée
--------------------------------------

Ajouter les lignes suivantes au fichier `/boot/config.txt` :

.. code:: console

    # Enable real time clock
    dtoverlay=i2c-rtc,ds3231

Supprimer un package :

.. code:: console

    sudo apt remove fake-hwclock

Si on utilise une autre source de temps (gps, dcf77, ...), on arrête la
synchronisation avec un serveur ntp :

.. code:: console

    sudo timedatectl set-ntp false

Modifier le fichier `/lib/udev/hwclock-set`. Mettre en commentaire ces trois
lignes :

.. code:: console

   #if [ -e /run/systemd/system ] ; then
   # exit 0
   #fi

Configuration de la liaison série
---------------------------------

Modifier le fichier `/boot/cmdline` et supprimer le texte depuis `console`
jusqu'à `115200`.

Ne pas démarrer un shell sur la liaison série.

.. code:: console

    sudo systemctl mask serial-getty@ttyAMA0.service

Installation de packages supplémentaires
----------------------------------------

.. code:: console

    sudo install git pigpio i2c-tools picocom
    sudo install python3-setuptools python3-pip

Démarrage du daemon `pigpiod` :

    sudo systemctl start pigpiod
    sudo systemctl enable pigpiod

Installation de l'application
-----------------------------

Cloner l'application :

.. code:: console

    cd ~
    git clone https://github.com/franckinux/python3-domotik.git

Installer des packages Python supplémentaires :

.. code:: console

    pip install --user -r requirements.txt

Permettre de lancement de l'application au démarrage du RPI :

.. code:: console

    cd ~/domotik
    sudo cp python3-domotik.service /etc/systemd/system
    sudo systemctl enable python3-domotik.service
    sudo systemctl start python3-domotik.service
