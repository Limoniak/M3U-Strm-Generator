import os
import sys
import xml.etree.ElementTree as ET
import requests
import logging
import re
import configparser
import time  
from datetime import datetime

######################################################################################################################
                                    # DEBOGAGE # 
######################################################################################################################

# Fonction pour écrire dans le fichier error.txt
def log_error(message):
    logging.error(message)
    
######################################################################################################################
                                    # Fonction Main
######################################################################################################################

def main():
    print("*** Début de l'exécution du script...")

    # Obtient le répertoire contenant le script
    script_directory = os.path.dirname(os.path.abspath(__file__))
    config_file = os.path.join(script_directory, 'Config.cfg')

    # Vérification de la commande /C avant de charger la configuration
    if len(sys.argv) > 1 and sys.argv[1] == "/C":
        print("*** Création du fichier de configuration.")
        try:
            create_default_config(config_file)
        except Exception as e:
            log_error(f"*** Erreur lors de la création du fichier de configuration : {e}")
        return

    # Chargement de la configuration, création du fichier Config.cfg si absent
    if not os.path.exists(config_file):
        create_default_config(config_file)
        print(f"*** Le fichier de configuration '{config_file}' a été créé. "
              "*** Veuillez modifier son contenu avant de relancer le script.")
        return

    try:
        config = load_config(config_file)
    except Exception as e:
        log_error(f"*** Erreur lors du chargement de la configuration : {e}")
        return

    # Vérification des arguments fournis pour d'autres commandes
    if len(sys.argv) > 1 and sys.argv[1] == "/U":
        print("Récupération des groupes depuis le fichier M3U.")
        if os.path.exists("unwantedgroup.cfg"):
            if os.path.exists("unwantedgroup.old"):
                os.remove("unwantedgroup.old")
            os.rename("unwantedgroup.cfg", "unwantedgroup.old")
            print("*** Le fichier 'unwantedgroup.cfg' existant a été renommé en 'unwantedgroup.old'.")

        try:
            retrieve_groups_from_m3u(config["m3u8File"])
        except Exception as e:
            log_error(f"*** Erreur lors de la récupération des groupes : {e}")
        return

    # Exécution par défaut
    if config.get("DownloadM3U8Enabled"):
        try:
            download_m3u(config)
        except Exception as e:
            log_error(f"*** Erreur lors du téléchargement de M3U8 : {e}")
    else:
        print("*** Téléchargement désactivé dans la configuration... On traite le fichier existant...")

    # Traitement du fichier M3U après le téléchargement (ou s'il est désactivé)
    m3u_file_path = config.get("m3u8File")
    try:
        process_m3u_file(m3u_file_path)
    except Exception as e:
        log_error(f"*** Erreur lors du traitement du fichier M3U... {e}")

    # Traitement des groupes non désirés
    unwanted_groups_path = "unwantedgroup.cfg"

######################################################################################################################
                                    # CREATION DU FICHIER CONFIG # 
######################################################################################################################

def create_default_config(config_path):
    """Génération du fichier Config.cfg avec des valeurs par défaut."""
    current_directory = os.path.abspath(os.path.dirname(__file__))
    config_content = f"""<?xml version="1.0" encoding="utf-8"?>
<configuration>
    <appSettings>
        <!-- Localisation des dossiers -->
        <add key="BaseDirectory" value="{current_directory}" />
        <add key="OutDirectory" value="{current_directory}" />
        <add key="m3u8File" value="{os.path.join(current_directory, 'original.m3u8')}" />

        <!-- Renommage des dossiers -->
        <add key="MoviesSubDir" value="FILMS" />
        <add key="SeriesSubDir" value="SERIE" />
        <add key="TVSubDir" value="TV" />

		<!-- Suppression des préfixes-->
		<add key="PrefixDel" value="FR - ,UK - ,DE - ,ES - " />
		
		<!-- Discord Bot-->
		<add key="DiscordBotEnabled" value="False" />
		<add key="DiscordBot" value="example.com" />

        <!-- Téléchargement du fichier m3u -->
        <add key="DownloadM3U8Enabled" value="False" />
        <add key="UserURL" value="" />
        <add key="UserPort" value="" />
        <add key="UserName" value="" />
        <add key="UserPass" value="" />
    </appSettings>
</configuration>"""

    try:
        # Vérification si le fichier de configuration existe déjà
        if os.path.exists(config_path):
            # Chemin pour le fichier Config.old
            old_config_path = config_path.replace("Config.cfg", "Config.old")
            
            # Si Config.old existe déjà, le supprimer
            if os.path.exists(old_config_path):
                os.remove(old_config_path)  # Supprimer l'ancien Config.old s'il existe déjà
            
            # Renommer Config.cfg en Config.old
            os.rename(config_path, old_config_path)  # Renommer Config.cfg en Config.old

        # Écriture du nouveau fichier de configuration
        with open(config_path, "w", encoding="utf-8") as config_file:
            config_file.write(config_content)

    except Exception as e:
        print(f"*** Erreur lors de la création du fichier de configuration : {str(e)}")

######################################################################################################################
                                   # CHARGEMENT DU FICHIER CONFIG 
######################################################################################################################

def load_config(config_file):
    """Chargement du fichier Config.cfg."""
    config = {}

    # Vérification si le fichier existe
    if not os.path.exists(config_file):
        log_error(f"*** Le fichier de configuration {config_file} n'existe pas.")
        return config  # Retourne un dictionnaire vide si le fichier n'existe pas

    # Parse le fichier XML
    try:
        tree = ET.parse(config_file)
        root = tree.getroot()

        # Parcours des éléments XML pour extraire les valeurs
        for elem in root.findall('.//add'):
            key = elem.get('key')
            value = elem.get('value')
            config[key] = value

        # Retourne le dictionnaire avec les clés attendues
        return {
            "UserURL": config.get("UserURL"),
            "UserPort": config.get("UserPort"),
            "UserName": config.get("UserName"),
            "UserPass": config.get("UserPass"),
            "m3u8File": config.get("m3u8File"),
            "DownloadM3U8Enabled": config.get("DownloadM3U8Enabled") == "True"
        }
    except ET.ParseError as e:
        log_error(f"*** Erreur lors du parsing du fichier de configuration : {e}")
        return config
    except Exception as e:
        log_error(f"*** Erreur lors du chargement du fichier de configuration : {e}")
        return config

######################################################################################################################
                                   # Télécharger le fichier M3U
######################################################################################################################

def download_m3u(config):
    user_url = config.get("UserURL")
    user_port = config.get("UserPort")
    username = config.get("UserName")
    password = config.get("UserPass")
    m3u_url = f"{user_url}{user_port}/get.php?username={username}&password={password}&type=m3u_plus&output=ts"

    print("*** Téléchargement du fichier M3U en cours ...")
    try:
        response = requests.get(m3u_url)
        if response.status_code == 200:
            with open(config["m3u8File"], "wb") as file:
                file.write(response.content)
            print("*** Téléchargement du fichier M3U réussi.")
        else:
            error_message = f"*** Erreur de téléchargement : {response.status_code} - {response.text}"
            print(error_message)
            log_error(error_message)
    except requests.RequestException as e:
        error_message = f"*** Erreur de requête : {str(e)}"
        print(error_message)
        log_error(error_message)

######################################################################################################################
                                   # Traitement le fichier M3U
######################################################################################################################

def process_m3u_file(file_path):
    if file_path is None:
        error_message = "*** Le chemin du fichier M3U n'est pas défini dans la configuration."
        print(error_message)
        log_error(error_message)
        return

    if os.path.exists(file_path):
        try:
            # Ouvrir le fichier avec l'encodage UTF-8
            with open(file_path, "r", encoding='utf-8') as file:
                content = file.readlines()
                # Ajoutez ici le code pour traiter le contenu du fichier
                print(f"*** Traitement du fichier M3U en cours...")
                # Processus d'analyse et de filtrage ici
                # Par exemple, filtrer les chaînes en fonction des groupes non désirés
        except Exception as e:
            error_message = f"*** Erreur lors de l'ouverture ou du traitement du fichier M3U : {str(e)}"
            print(error_message)
            log_error(error_message)
    else:
        error_message = f"*** Le fichier M3U spécifié n'existe pas : {file_path}"
        print(error_message)
        log_error(error_message)

######################################################################################################################
                                   #Génération du Fichier Unwantedgroup
######################################################################################################################

def generate_unwanted_group_file(config_file):
    def get_m3u8_file_path():
        m3u8_file = None
        try:
            with open(config_file, "r", encoding='utf-8') as file:
                lines = file.readlines()
                for line in lines:
                    if '<add key="m3u8File"' in line:
                        start = line.find('value="') + len('value="')
                        end = line.find('"', start)
                        m3u8_file = line[start:end]
                        break
        except FileNotFoundError:
            with open("error.txt", "a", encoding='utf-8') as error_file:
                error_file.write(f"*** Fichier de configuration non trouvé : {config_file}\n")
        return m3u8_file

    def retrieve_groups_from_m3u(m3u8_file):
        if not os.path.exists(m3u8_file):
            with open("error.txt", "a", encoding='utf-8') as error_file:
                error_file.write(f"*** Le fichier {m3u8_file} n'existe pas.\n")
            return

        with open(m3u8_file, "r", encoding='utf-8') as file:
            lines = file.readlines()

        all_groups = set()
        empty_group_found = False  # Indicateur pour les groupes vides

        for line in lines:
            if 'group-title="' in line:
                start = line.find('group-title="') + len('group-title="')
                end = line.find('"', start)
                group = line[start:end].strip()
                if group:
                    all_groups.add(group)
                else:
                    empty_group_found = True  # Marquer qu'un groupe vide a été trouvé

        # Classer les groupes selon les sections demandées
        sorted_groups = []
        sorted_groups.extend(sorted([group for group in all_groups if "|" in group]))  # Section 1: groupes avec "|"
        sorted_groups.extend(sorted([group for group in all_groups if group.startswith("VOD")]))  # Section 2: VOD
        sorted_groups.extend(sorted([group for group in all_groups if group.startswith("SRS")]))  # Section 3: SRS
        sorted_groups.extend(sorted([group for group in all_groups if not (group.startswith("VOD") or group.startswith("SRS") or "|" in group)]))  # Section 4: tout le reste

        # Créer le fichier unwantedgroup.cfg
        if os.path.exists("unwantedgroup.cfg"):
            if os.path.exists("unwantedgroup.old"):
                os.remove("unwantedgroup.old")
            os.rename("unwantedgroup.cfg", "unwantedgroup.old")

        with open("unwantedgroup.cfg", "w", encoding='utf-8') as f:
            f.write("######################################################################################################################\n")
            f.write("DELETE ONLY GROUP YOU WANT TO BE DOWNLOADED AND TRAITED\n")  # Écrire le titre NOGROUP en premier
            f.write(".NOGROUP-ASSIGNED | The first group assigned, it means they dont have (groupe-title"") completed \n")  # Écrire le titre NOGROUP en premier
            f.write("######################################################################################################################\n")
            
            # Ajouter .NOGROUP-ASSIGNED si des groupes vides ont été trouvés
            if empty_group_found:
                f.write(".NOGROUP-ASSIGNED\n")
            
            for group in sorted_groups:
                f.write(group + "\n")

        print(f"*** {len(sorted_groups)} groupes récupérés et écrits dans unwantedgroup.cfg.")

    # Exécution des étapes
    m3u8_file = get_m3u8_file_path()
    if m3u8_file:
        retrieve_groups_from_m3u(m3u8_file)
    else:
        print("*** Aucun fichier M3U8 trouvé dans la configuration.")

######################################################################################################################
                                   #Parametres Fonction FOLDER GENERATOR
######################################################################################################################
def log_error(message):
    if not os.path.exists("error.txt"):
        with open("error.txt", "w", encoding='utf-8') as error_file:
            error_file.write("Fichier d'erreurs créé\n")

    with open("error.txt", "a", encoding='utf-8') as error_file:
        error_file.write(message + "\n")

def log_results(new_films, new_series, new_tv, new_others):
    log_directory = "log"
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    now = datetime.now().strftime("%H-%M-%d-%Y")
    film_log_file_path = os.path.join(log_directory, f"NewFilms-{now}.txt")
    series_log_file_path = os.path.join(log_directory, f"NewSeries-{now}.txt")
    tv_log_file_path = os.path.join(log_directory, f"NewTV-{now}.txt")
    others_log_file_path = os.path.join(log_directory, f"NewTV-{now}.txt")

    if new_films:
        with open(film_log_file_path, 'a', encoding='utf-8') as log_file:
            log_file.write(f"Log pour {datetime.now()}\n")
            for group_title, films in new_films.items():
                log_file.write(f"--------------------\n{group_title}\n")
                log_file.write("\n".join(films) + "\n")
            log_file.write("---------------------------------------------------\n")

    if new_series:
        with open(series_log_file_path, 'a', encoding='utf-8') as log_file:
            log_file.write(f"Log pour {datetime.now()}\n")
            for group_title, series in new_series.items():
                log_file.write(f"--------------------\n{group_title}\n")
                log_file.write("\n".join(series) + "\n")
            log_file.write("---------------------------------------------------\n")

    if new_tv:
        with open(tv_log_file_path, 'a', encoding='utf-8') as log_file:
            log_file.write(f"Log pour {datetime.now()}\n")
            for group_title, tvs in new_tv.items():
                log_file.write(f"--------------------\n{group_title}\n")
                log_file.write("\n".join(tvs) + "\n")
            log_file.write("---------------------------------------------------\n")
    if new_others:
        with open(others_log_file_path, 'a', encoding='utf-8') as log_file:
            log_file.write(f"Log pour {datetime.now()}\n")
            for group_title, tvs in new_others.items():
                log_file.write(f"--------------------\n{group_title}\n")
                log_file.write("\n".join(tvs) + "\n")
            log_file.write("---------------------------------------------------\n")
          
def log_global_script_status(total_films_added, total_series_added, total_tv_added, total_others_added, execution_time):
    log_directory = "log"
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    now = datetime.now().strftime("%H-%M-%d-%Y")
    global_log_file_path = os.path.join(log_directory, f"ScriptSuccess-{now}.txt")

    with open(global_log_file_path, 'a', encoding='utf-8') as log_file:
        log_file.write(f"Traitement Terminé le {datetime.now()}\n")
        log_file.write(f"Total Films ajoutés : {total_films_added}\n")
        log_file.write(f"Total Séries ajoutées : {total_series_added}\n")
        log_file.write(f"Total Chaînes TV ajoutées : {total_tv_added}\n")
        log_file.write(f"Total Others TV ajoutées : {total_others_added}\n")
        log_file.write(f"Temps d'exécution : {execution_time}\n")  # Inclure le temps formaté
        log_file.write("---------------------------------------------------\n")

def format_execution_time(seconds):
    """Convertit le temps d'exécution en format minutes et secondes."""
    minutes = int(seconds // 60)
    seconds = seconds % 60
    return f"{minutes} min {seconds:.2f} s"

def extract_group_title(line):
    match = re.search(r'group-title="(.*?)"', line)
    return match.group(1) if match else "Unknown"


def get_prefixes_from_config(file_path):
    # Lire le fichier Config.cfg
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    # Chercher la ligne avec la clé "PrefixDel"
    prefix_del = root.find(".//add[@key='PrefixDel']")
    
    if prefix_del is not None:
        # Récupérer la valeur et la diviser en une liste de préfixes
        prefixes = prefix_del.get('value', '').split(',')
        return [prefix.strip() for prefix in prefixes]  # Retourner une liste de préfixes
    return []

prefixes_displayed = False

def prefixes_to_remove():
    global prefixes_displayed  # Indique que nous utilisons la variable globale
    
    # Nom du fichier de configuration
    config_file_name = 'Config.cfg'
    
    # Construire le chemin du fichier dans le répertoire actuel
    config_file_path = os.path.join(os.getcwd(), config_file_name)

    # Vérifiez si le fichier de configuration existe
    if not os.path.exists(config_file_path):
        print(f"*** Le fichier de configuration '{config_file_name}' est manquant.")
        print("*** Faire cette commande '/C' pour le générer.")
        return []  # Retourne une liste vide si le fichier n'existe pas

    # Récupérer les préfixes
    prefixes_to_remove = get_prefixes_from_config('Config.cfg')
    
    # Affichage unique des préfixes
    if not prefixes_displayed:  # Vérifiez si le message a déjà été affiché
        print("*** Prefixes to remove:", prefixes_to_remove)
        prefixes_displayed = True  # Marquez le message comme affiché

    # Retourner les préfixes
    return prefixes_to_remove

def clean_directory_name(name):
    # Récupérer les préfixes à supprimer
    prefixes = prefixes_to_remove()  # Appel de la fonction pour obtenir la liste des préfixes
    # Supprimer les préfixes spécifiés
    for prefix in prefixes:
        name = name.replace(prefix, '')  # Remplacer le préfixe par une chaîne vide
    
    # Nettoyer les caractères non valides sauf les crochets []
    name = re.sub(r'[<>:"/\\|?*...]', '', name)  # Retirer [ et ] de la liste
    name = re.sub(r'\s+', ' ', name).strip()

    # Remplacer "4K" ou "4k" par "UHD"
    name = name.replace('4K', 'UHD').replace('4k', 'UHD')

    return name

def clean_file_name(name):
    # Récupérer les préfixes à supprimer
    prefixes = prefixes_to_remove()  # Appel de la fonction pour obtenir la liste des préfixes
    # Supprimer les préfixes spécifiés
    for prefix in prefixes:
        name = name.replace(prefix, '')  # Remplacer le préfixe par une chaîne vide

    # Supprimer les caractères non valides, y compris ':'
    name = re.sub(r'[<>:"/\\|?*:...]', '', name)

    # Remplacer "4K" ou "4k" par "UHD"
    name = name.replace('4K', 'UHD').replace('4k', 'UHD')
    
    return re.sub(r'\s+', ' ', name).strip()

def extract_tvg_name(line):
    match = re.search(r'tvg-name="(.*?)"', line)
    return match.group(1) if match else "Unknown"

def get_directory_names(config_path):
    tree = ET.parse(config_path)
    root = tree.getroot()
    films_dir = root.find(".//add[@key='MoviesSubDir']").get('value')
    series_dir = root.find(".//add[@key='SeriesSubDir']").get('value')
    tv_dir = root.find(".//add[@key='TVSubDir']").get('value')
    return films_dir, series_dir, tv_dir

def read_unwanted_group(unwanted_file_path):
    """Lit le fichier unwantedgroup.cfg et renvoie une liste de group-title indésirables."""
    if not os.path.exists(unwanted_file_path):
        return  # Retourne une liste vide si le fichier n'existe pas
    
    with open(unwanted_file_path, 'r', encoding='utf-8') as file:
        unwanted_groups = {line.strip() for line in file if line.strip()}  # Utilisation d'un set pour éviter les doublons
    
    if not unwanted_groups:
        log_error("Aucun groupe indésirable trouvé dans le fichier.")  # Enregistrer une information si le fichier est vide
    
    return unwanted_groups

def process_tv(line, output_directory, link, config_path):
    group_title = extract_group_title(line)
    tvg_name = extract_tvg_name(line)

    films_dir, series_dir, tv_dir = get_directory_names(config_path)

    tv_directory = os.path.join(output_directory, tv_dir, clean_directory_name(group_title))

    # Création du dossier avec exist_ok=True
    os.makedirs(tv_directory, exist_ok=True)

    file_name = f"{clean_file_name(tvg_name)}.strm"
    full_file_path = os.path.join(tv_directory, file_name)

    # Vérifiez si le fichier existe déjà
    if not os.path.exists(full_file_path):
        with open(full_file_path, 'w', encoding='utf-8') as tv_file:
            tv_file.write(link)
        return 1, clean_file_name(tvg_name)  # Renvoie 1 et le nom de la chaîne
    return 0, clean_file_name(tvg_name)

def process_film(line, output_directory, link, config_path):
    group_title = extract_group_title(line)
    film_name = extract_tvg_name(line)

    films_dir, series_dir, tv_dir = get_directory_names(config_path)

    film_directory = os.path.join(output_directory, films_dir, clean_directory_name(group_title))

    # Création du dossier avec exist_ok=True
    os.makedirs(film_directory, exist_ok=True)

    file_name = f"{clean_file_name(film_name)}.strm"
    full_file_path = os.path.join(film_directory, file_name)

    # Vérifiez si le fichier existe déjà
    if not os.path.exists(full_file_path):
        with open(full_file_path, 'w', encoding='utf-8') as film_file:
            film_file.write(link)
        return 1, clean_file_name(film_name)  # Renvoie 1 et le nom du film
    return 0, clean_file_name(film_name)

def process_series(line, output_directory, link, config_path):
    group_title = extract_group_title(line)  
    tvg_name = extract_tvg_name(line)  

    films_dir, series_dir, tv_dir = get_directory_names(config_path)

    # Création du dossier pour le groupe
    group_directory = os.path.join(output_directory, series_dir, clean_directory_name(group_title))
    os.makedirs(group_directory, exist_ok=True)  # Crée le répertoire pour le groupe

    # Nettoyer le nom de la série
    series_name = re.sub(r' S\d+ E\d+', '', tvg_name)
    series_name_clean = clean_directory_name(series_name)

    # Création du répertoire pour la série à l'intérieur du répertoire du groupe
    series_sub_dir = os.path.join(group_directory, series_name_clean)
    os.makedirs(series_sub_dir, exist_ok=True)  # Crée le répertoire de la série

    # Définition du nom du fichier
    file_name = f"{clean_file_name(tvg_name)}.strm"
    full_file_path = os.path.join(series_sub_dir, file_name)

    # Vérifiez si le fichier existe déjà
    if not os.path.exists(full_file_path):
        with open(full_file_path, 'w', encoding='utf-8') as series_file:
            series_file.write(link)
        return 1, clean_file_name(tvg_name)  # Renvoie 1 et le nom de la série

    return 0, clean_file_name(tvg_name)  # Renvoie 0 si le fichier existe déjà

def process_others(line, output_directory, link, config_path):
    group_title = extract_group_title(line)  # Extraction du titre de groupe
    tvg_name = extract_tvg_name(line)  # Extraction du nom TVG

    # Récupération du répertoire de sortie à partir de la configuration
    tree = ET.parse(config_path)
    root = tree.getroot()
    out_directory = root.find(".//add[@key='OutDirectory']").get('value')

    # Vérification de l'existence de groupes indésirables dans unwantedgroup.cfg
    unwanted_group_file = "unwantedgroup.cfg"  # Remplacez par le chemin correct si nécessaire
    unwanted_groups = read_unwanted_group(unwanted_group_file)

    # Vérification si le group-title est vide
    if not group_title:
        group_title = ".NOGROUP-ASSIGNED"  # Assigner le groupe pour les titres vides

    # Vérifier si le groupe est dans les groupes indésirables
    if group_title in unwanted_groups:
        return 0, clean_file_name(tvg_name)  # Ne pas télécharger si le groupe est indésirable

    others_directory = os.path.join(out_directory, "OTHERS")

    # Préparation du chemin de répertoire pour le groupe
    group_directory = os.path.join(others_directory, clean_directory_name(group_title))

    # Vérifier si le répertoire du groupe doit être créé
    if not os.path.exists(group_directory):
        os.makedirs(group_directory)  # Créer le répertoire du groupe s'il n'existe pas

    series_name = re.sub(r' S\d+ E\d+', '', tvg_name)  # Retirer la partie S01 E01, etc.
    series_name_clean = clean_directory_name(series_name)
    series_sub_dir = os.path.join(group_directory, series_name_clean)

    os.makedirs(series_sub_dir, exist_ok=True)  # Créer le sous-dossier pour la série

    file_name = f"{clean_file_name(tvg_name)}.strm"
    full_file_path = os.path.join(series_sub_dir, file_name)

    if os.path.exists(full_file_path):
        return 0, clean_file_name(tvg_name)  # Renvoie 0 et le nom de la chaîne si le fichier existe déjà

    try:
        with open(full_file_path, 'w', encoding='utf-8') as series_file:
            series_file.write(link)
        
        # Vérifier si le dossier OTHERS doit être créé
        if not os.path.exists(others_directory):
            os.makedirs(others_directory)

        return 1, clean_file_name(tvg_name)  # Renvoie 1 et le nom de la série

    except Exception as e:
        log_error(f"Erreur lors de l'écriture du fichier: {str(e)}")
        return 0, clean_file_name(tvg_name)  # Renvoie 0 et le nom de la chaîne en cas d'erreur
######################################################################################################################
                                   #Fonction FOLDER GENERATOR
######################################################################################################################
def folder_generator():
    start_time = time.time()  # Démarre le compteur de temps

    try:
        config_path = "Config.cfg"
        unwanted_groups_path = "unwantedgroup.cfg"  # Chemin vers le fichier unwantedgroup.cfg
        unwanted_groups = read_unwanted_group(unwanted_groups_path)  # Lecture des groupes indésirables

        tree = ET.parse(config_path)
        root = tree.getroot()
        output_directory = root.find(".//add[@key='OutDirectory']").get('value')

        films_dir, series_dir, tv_dir = get_directory_names(config_path)

        # Compteurs pour les films, séries, chaînes TV et autres
        new_films, existing_films, skipped_films = {}, {}, {}
        new_series, existing_series, skipped_series = {}, {}, {}
        new_tv, existing_tv, skipped_tv = {}, {}, {}
        new_others, existing_others, skipped_others = {}, {}, {}

        m3u8_file = root.find(".//add[@key='m3u8File']").get('value')
        
        m3u8_file = root.find(".//add[@key='m3u8File']").get('value')
        with open(m3u8_file, 'r', encoding='utf-8') as m3u8:
            for line in m3u8:
                if not line.startswith("#EXTINF"):
                    continue

                link = next(m3u8).strip()  # Récupère le lien suivant
                group_title = extract_group_title(line)

                # Vérifie si le group-title est dans la liste des indésirables
                if group_title in unwanted_groups:
                    continue  # Passe au groupe suivant si c'est indésirable

                # Classification basée sur le group-title
                if "VOD" in group_title:
                    result = process_film(line, output_directory, link, config_path)
                    if result[0]:  # Vérifie si un nouveau film a été ajouté
                        if group_title not in new_films:
                            new_films[group_title] = []
                        new_films[group_title].append(result[1])

                elif "SRS" in group_title:
                    result = process_series(line, output_directory, link, config_path)
                    if result[0]:  # Vérifie si une nouvelle série a été ajoutée
                        if group_title not in new_series:
                            new_series[group_title] = []
                        new_series[group_title].append(result[1])

                elif "|" in group_title:
                    result = process_tv(line, output_directory, link, config_path)
                    if result[0]:  # Vérifie si une nouvelle chaîne TV a été ajoutée
                        if group_title not in new_tv:
                            new_tv[group_title] = []
                        new_tv[group_title].append(result[1])

                else:
                    # Si aucune des conditions précédentes n'est remplie, on traite comme "autre"
                    result = process_others(line, output_directory, link, config_path)
                    if result[0]:  # Vérifie si un nouveau fichier autre a été ajouté
                        if group_title not in new_others:
                            new_others[group_title] = []
                        new_others[group_title].append(result[1])
                        
        # Logging des résultats
        log_results(new_films, new_series, new_tv, new_others)

        # Calcul des totaux pour l'affichage final
        total_films_added = sum(len(v) for v in new_films.values())
        total_series_added = sum(len(v) for v in new_series.values())
        total_tv_added = sum(len(v) for v in new_tv.values())
        total_others_added = sum(len(v) for v in new_others.values())

        execution_time_seconds = time.time() - start_time
        execution_time_formatted = format_execution_time(execution_time_seconds)

        log_global_script_status(total_films_added, total_series_added, total_tv_added, total_others_added, execution_time_formatted)

        # Affichage des totaux formatés
        print("*** Movies summary: {} new, {} skipped (whereof {} dupes), {} in total".format(
            total_films_added, len(skipped_films), len(existing_films), total_films_added + len(existing_films)))

        print("*** Episodes summary: {} new, {} skipped (whereof {} dupes), {} in total".format(
            total_series_added, len(skipped_series), len(existing_series), total_series_added + len(existing_series)))

        print("*** TV-channels summary: {} new, {} skipped (whereof {} dupes), {} in total".format(
            total_tv_added, len(skipped_tv), len(existing_tv), total_tv_added + len(existing_tv)))

        print("*** Processing time: {}".format(execution_time_formatted))

        return total_films_added, total_series_added, total_tv_added, total_others_added, execution_time_formatted

    except Exception as e:
        log_error(f"Erreur lors de la génération des dossiers: {str(e)}")
   
######################################################################################################################
                                   #Discord Notification
######################################################################################################################      

def Discord_Notification(total_films_added, total_series_added, total_tv_added, total_others_added, execution_time_formatted):
    # Nom du fichier de configuration
    config_file_name = 'Config.cfg'
    
    # Construire le chemin du fichier dans le répertoire actuel
    config_file_path = os.path.join(os.getcwd(), config_file_name)

    # Vérifiez si le fichier de configuration existe
    if not os.path.exists(config_file_path):
        print(f"*** Le fichier de configuration '{config_file_name}' est manquant.")
        print("*** Faire cette commande '/C' pour le générer.")
        return  # Retourne si le fichier n'existe pas

    # Charger le fichier de configuration
    tree = ET.parse(config_file_path)
    root = tree.getroot()

    # Chercher la clé "DiscordBotEnabled"
    discordbot_enabled = root.find(".//add[@key='DiscordBotEnabled']")
    if discordbot_enabled is None:
        print("*** Clé 'DiscordBotEnabled' est vide ou introuvable dans la configuration.")
        return  # Retourne si la clé n'existe pas

    # Vérifiez si la valeur est "True" ou "False"
    if discordbot_enabled.get('value', 'False') == 'True':
        # Notifications Discord sont activées
        print("*** Notifications Discord sont activées.")

        # Chercher la clé "DiscordBot" pour obtenir le webhook
        DiscordBot = root.find(".//add[@key='DiscordBot']")
        if DiscordBot is not None and DiscordBot.get('value'):
            webhook_url = DiscordBot.get('value')
            
            # Construire le message avec les résultats de la fonction folder_generator
            message = (
                "```markdown\n"  # Début du bloc de code
                "📝 Résumé du traitement\n"
                "===========================\n\n"

                f"📽️ Films ajoutés :    {total_films_added}\n\n"
                
                f"📺 Séries ajoutées :   {total_series_added}\n\n"
                
                f"📡 Chaînes TV ajoutées : {total_tv_added}\n\n"
                
                f"📁 Autres ajoutés :     {total_others_added}\n\n"
                
                f"⏱️ Temps d'exécution :   {execution_time_formatted}\n\n"
                
                "===========================\n"
                "✅ Fin du résumé\n"
                "```"  # Fin du bloc de code
            )
            
            payload = {
                "content": message
            }
            try:
                response = requests.post(webhook_url, json=payload)
                if response.status_code == 204:
                    print("*** Message envoyé avec succès à Discord.")
                else:
                    print(f"*** Échec de l'envoi du message. Code d'erreur : {response.status_code}")
            except Exception as e:
                print(f"*** Une erreur s'est produite lors de l'envoi du message : {e}")
        else:
            print("*** Le lien 'DiscordBot' est vide ou incorrect.")
    else:
        print("*** Notifications Discord sont désactivées.")
   
######################################################################################################################
                                   #Derouler du script Logic
######################################################################################################################      

if __name__ == "__main__":
    # Chemin des fichiers de configuration
    config_file = "Config.cfg"
    unwanted_file_path = "unwantedgroup.cfg"

    # Vérifier la commande de création de configuration
    if len(sys.argv) > 1 and sys.argv[1] == "/C":
        print("*** Commande '/C' détectée : Création du fichier de configuration...")
        create_default_config(config_file)
        print("*** Le fichier de configuration 'Config.cfg' a été créé avec succès.")
        sys.exit(0)

    # Vérifier si le fichier de configuration existe
    if not os.path.exists(config_file):
        print("*** Le fichier de configuration 'Config.cfg' est manquant.")
        print("*** Veuillez exécuter le script avec '/C' pour créer le fichier de configuration.")
        sys.exit(1)

    # Charger la configuration
    try:
        config = load_config(config_file)
    except Exception as e:
        log_error(f"*** Erreur lors du chargement de la configuration : {e}")
        sys.exit(1)

    # Vérifier l'argument /U pour générer unwantedgroup.cfg
    if len(sys.argv) > 1 and sys.argv[1] == "/U":
        print("*** Commande '/U' détectée : Récupération des groupes indésirables...")
        generate_unwanted_group_file(config_file)
        print("*** Le fichier 'unwantedgroup.cfg' a été généré avec succès.")
        sys.exit(0)

    # Vérifier si unwantedgroup.cfg existe
    unwanted_group = read_unwanted_group(unwanted_file_path)
    if unwanted_group is None:
        print("*** Le fichier 'unwantedgroup.cfg' n'existe pas.")
        print("*** Veuillez exécuter le script avec l'option '/U' pour le générer.")
        sys.exit(1)

    # Suite du traitement
    download_enabled = config.get("DownloadM3U8Enabled")
    m3u_file_path = config.get("m3u8File")

    if download_enabled:
        print("*** Téléchargement du fichier M3U activé...")
        download_m3u(config)
    else:
        print("*** Téléchargement désactivé dans la configuration... On traite le fichier existant...")

    # Traitement du fichier M3U
    process_m3u_file(m3u_file_path)

    # Si unwanted_group est défini, lancer folder_generator
    if unwanted_group:
        total_films_added, total_series_added, total_tv_added, total_others_added, execution_time_formatted = folder_generator()
    
    if folder_generator:
        Discord_Notification(total_films_added, total_series_added, total_tv_added, total_others_added, execution_time_formatted)
      
    print("*** End of Script.")
