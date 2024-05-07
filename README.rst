==================================================
Procédure d'installation du Raspberry Pi 4 Model B
==================================================

+--------------------+----------+----------------------------+
| Date               | Version  | Auteur                     |
+--------------------+----------+----------------------------+
| 7 mai 2024         | 1.0      | Franck Barbenoire          |
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
Coordonateur Zigbee                              ZIG
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
ADC
PRE   BMP180A   0x77
RTC   DS3231    0x68
===== ========= ================

UART
....

Du fait de la suppression de la liaison Bluetooth, il semble que les numéros
soient décalés :

- 2 → 1 ;
- 3 → 2 ;
- etc.

===== ==== ============ ================ ======= =======
Carte Port Device       Configuration    Gpio Tx Gpio Rx
===== ==== ============ ================ ======= =======
ZIG   USB  /dev/ttyACM0 \-               \-      \-
LKY   \-   /dev/ttyAMA0 9600, 7, 1, E    14      15
\-    \-   /dev/ttyAMA1 \-               4       5
\-    \-   /dev/ttyAMA2 \-               8       9
\-    \-   /dev/ttyAMA3 \-               12      13
===== ==== ============ ================ ======= =======

Installation
============

Préparation de la carte SD
--------------------------

Télécharger l'image de la carte SD, la décompressser et finalement l'écrire dans
la carte SD.

Bien vérifier que la destination est bien `/dev/sda` (risque d'écrasement d'une
autre partition que celle souhaitée avec des conséquences dramatiques...)

.. code:: console

    wget https://downloads.raspberrypi.com/raspios_lite_arm64/images/raspios_lite_arm64-2024-03-15/2024-03-15-raspios-bookworm-arm64-lite.img.xz
    unxz 2024-03-15-raspios-bookworm-arm64-lite.img.xz
    sudo dd bs=1M if=2024-03-15-raspios-bookworm-arm64-lite.img of=/dev/sda

Premier boot sur la carte SD
----------------------------

Connecter un écran sur le port HDMI et un clavier sur un port USB du RPI.

Introduire la cartes SD dans le RPI et le mettre sous tension. Après la
séquence de boot, un menu de configuration apararaît :

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

Autorisation de périphériques intégrés
--------------------------------------

Modifier les lignes suivantes au fichier `/boot/config.txt` :

    dtparam=i2c_arm=on

Ajouter les lignes suivantes à la fin du fichier `/boot/config.txt` :

.. code:: console

    # Disable Bluetooth
    dtoverlay=disable-bt
    # Disable Wifi
    dtoverlay=disable-wifi

Ajouter les lignes suivantes à la fin du fichier `/etc/modules` :

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
    sudo install python3-setuptools python3-pip python3-venv

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
