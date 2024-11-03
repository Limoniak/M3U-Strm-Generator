# M3U8-STRM-GENERATOR

**Générateur de fichiers et dossier pour affiner votre fichier m3u en classant les fichiers dans des dossiers bien distinct pour ressembler a ceci.
Parfait pour une médiathéque sur EMBY ou sur PLEX.**

Script basé sur ce dépot : https://github.com/trix7777/m2strm?tab=readme-ov-file
Le dépot n'étant plus a jour je souhaite faire quelque améliorations 

**Bien sur ce script à pour but de centraliser vos films et series qui vous appartiennent déjà, aucune promotion pour service divers n'est faite. A utiliser pour votre usage personnel avec les DVD que vous avez achetés ou service M3U fournie par votre opérateur Internet.**

--FILMS

-------VOD - FRANCE ULTRA HD

--------------FR - Spiderman (2023).strm

---------------------FR - Superman (2023).strm

--SERIES

-------SRS - SERIES DIVERS FR

--------------FR - Plus belle la vie 

---------------------FR - Plus belle la vie S01 - E01.strm

-- TV 

-------FRANCE GENERAL 

--------------FR - TF1.strm



**Ce script est un générer entiérement par CHAT-GPT (N'ayant pas vraiement de compétences en code :D).**

Projet avec ce script :

- ✅ Suppresion des préfixes pour éviter les erreur avec Emby/Plex etc
- ✅ Ajout d'un webhooks Discord pour recevoir les données de l'éxecution du script
- Suppresion de doublons de films présent dans plusieurs répertoire
- Création de dossier pour plusieurs films avec plusieurs version ou par collection

# Description

**M3U8-STRM-GENERATOR** est un outil Python conçu pour faciliter la gestion et l'organisation des chaînes de télévision à partir de fichiers M3U8. 

Ce script permet de trier, filtrer et nettoyer les chaînes en fonction de divers critères, tout en assurant une journalisation complète des opérations.

# Fonctionnalités

- **Gestion des Chaînes** : Recharge et organise les Chaînes de télévision à partir d'un fichier de configuration.
- **Gestion des Films** : Recharge et organise les Films à partir d'un fichier de configuration.
- **Gestion des Series** : Recharge et organise les Series  à partir d'un fichier de configuration. | Chaque serie créér dans chaque dossier de groupes sera transformer en dossier de series pour eviter d'avoir tout épisodes en vrac
- **Journalisation** : Enregistre les erreurs rencontrées lors du traitement dans un fichier `error.txt`.
- **Génération de Logs** : Création automatique de fichiers de log pour les nouveaux films, séries et chaînes.
- **Nettoyage Automatique** : Nettoie les noms de répertoires et fichiers pour éviter les conflits.

## Prérequis

Avant d'utiliser le script, assurez-vous d'avoir [Python 3.x](https://www.python.org/downloads/) installé. Vérifiez cela en exécutant la commande suivante :

# Installation

`python --version`

Pour installer les dépendances requises, exécutez la commande suivante dans le répertoire contenant le script :

`pip install request`

# Modules utiliser

Modules Utilisés

Le script utilise plusieurs modules Python pour ses fonctionnalités :

    os
    sys
    xml.etree.ElementTree
    requests
    logging
    re
    configparser
    time
    datetime

# Utilisation

Creer un répertoire ou seul le Script sera utiliser pour éviter les erreurs 

**Etapes 1 :** 

`python Strm-Generator.py /C`
Ouvrir votre terminal et lancer cette commande 
Cette commande génére le fichier de `Config.cfg` qui sera utilise pour la suite

**Etape 2 :**

Une fois les informations modifié dans le fichier `Config.cfg` lancer cette commande 

`python Strm-Generator.py /U`
	
Un fichier `unwantedgroup.cfg` sera générer. 
Ouvrir ce fichier et supprimer les groupes de la liste si vous voulez que les groupe soit traités et leur fichiers générer

**Etape 3 :**

	`python Strm-Generator.py`
Si vous avez déja un fichier m3u veuillez a bien désactivé le téléchargement dans le fichier Config.cfg

Le traitement sera lancé et vos dossier créer en fonction de vos critéres.

Vérification des Logs : Consultez le fichier error.txt pour toute erreur rencontrée. 

Les fichiers de log pour les films, séries et chaînes ajoutées seront générés automatiquement dans le dossier "log" creer a la racine du script.

# Aide

Si vous avez des questions ou rencontrez des problèmes, n'hésitez pas à ouvrir une issue sur le dépôt GitHub.

Les contributions sont les bienvenues ! Si vous souhaitez contribuer à ce projet :

Forkez le projet.

Créez une nouvelle branche :

	git checkout -b feature/YourFeature

Faites vos modifications.

Soumettez une pull request.

# License

Ce projet est sous licence MIT. 

Merci d'utiliser M3U8-STRM-GENERATOR. Nous espérons qu'il répondra à vos besoins en matière de gestion de chaînes de télévision !
