#!/usr/bin/env python3
#
# -*- coding: utf-8 -*-
#
# Programme: reformatage_2_geosample.py
#
# le nom du fichier à traiter est passé en paramètre

# EN ENTREE : lecture d'un fichier excel qui contient tous les échantillons
# et ses analyses (une ligne par analyse)
# Les premières lignes contiennent des informations globales qui
#	serviront à remplir les fichiers de metadata
# Les analyses commencent à la première ligne dont la première colonne
#	contient la valeur SAMPLE_NAME, cette ligne contient le nom des champs
# La colonne 1 contient le nom des échantillons
#
# EN SORTIE : un fichier des metadatas + un fichier des données par échantillon
#
# 2020-01-20 PhS creation

import os, sys, io, configparser, re

if sys.version_info<(3,6,0):
  sys.stderr.write("You need python 3.6 or later to run this script\n")
  exit(1)

from openpyxl import Workbook
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
import pathlib
  
if len(sys.argv) != 2:
	print("Usage : python3 " + sys.argv[0] + " file.xls")
	sys.exit(1)

if sys.argv[1] == '-h' or sys.argv[1] == '--help':
	print("Usage : python3 " + sys.argv[0] + " file.xls")
	print()
	print("        program reads paramaters from configuration file ./config.ini")
	print()
	print("        Example")
	print()
	print("        [GENERAL]")
	print("        ; répertoire des fichiers d'échantillons et de metadata")
	print("        rep_data = ./DATA")
	print("        ; suffixe du nom des fichiers de metadata")
	print("        suff_meta = META")
	print("        ; valeur du 1er champ des en-tetes")
	print("        sep_entete = SAMPLE_NAME")
	print("        ; mode debug (0 | 1 | 2)")
	print("        debug = 0")
	print("        [ZONES]")
	print("        zones_obligatoires=TITLE,")
	print("                           DESCRIPTION,")
	print()
	print("        [sampling_point_header]")
	print("        ; liste des zones du point d'échantillonnage et leur en-tête associé pour le fichier de metadata")
	print("        ; les colonnes seront dans l'ordre d'apparition des déclarations")
	print("        SAMPLING_POINT-NAME = Sampling point")
	print("        SAMPLING_POINT-COORDINATE_SYSTEM = Coordinate system")
	print("        SAMPLING_POINT-ABBREV = Abbreviation")
	print("        SAMPLING_POINT-LONGITUDE = Longitude")
	print("        SAMPLING_POINT-LATITUDE = Latitude")
	print("        SAMPLING_POINT-ELEVATION = Elevation")
	print("        SAMPLING_POINT-DESCRIPTION = Description")
	print()
	print("        [measurement_header]")
	print("        ; liste des zones de measurement et leur en-tête associé pour le fichier de metadata")
	print("        ; les colonnes seront dans l'ordre d'apparition des déclarations")
	print("        MEASUREMENT-NAME = Nature of measurement")
	print("        MEASUREMENT-ABBREV = Measurement abbreviation")
	print("        MEASUREMENT-UNIT = Units")
	print()
	print("        [methodology_header]")
	print("        ; liste des en-têtes des méthodologies")
	print("        METHODOLOGY_SAMPLING = METHODOLOGY SAMPLING")
	print("        METHODOLOGY_INSTRUMENT = METHODOLOGY INSTRUMENT")
	print("        METHODOLOGY_COMMENT = COMMENT")
	print()
	sys.exit(0)
	

# ------------------------------------------------------------

# ---------- fichier d'entrée
input_file = sys.argv[1]
if not os.path.exists(input_file):
	print(sys.argv[0] + " : " + input_file + " : file not found")
	sys.exit(3)

# --------- lecture des paramètres ---------

config = configparser.ConfigParser(allow_no_value=True)
config.optionxform = lambda option: option # conservation de la casse des clefs
config.read("config.ini")

section='GENERAL'
# répertoire des fichiers d'échantillons et de metadata	
rep_data = config.get(section, 'rep_data', fallback='./DATA')
pathlib.Path(rep_data).mkdir(parents=True, exist_ok=True)

# valeur du 1er champ des en-tetes
sep_entete = config.get(section, 'sep_entete', fallback="SAMPLE_NAME")

# suffixe du nom des fichiers de metadata
suff_meta = config.get(section, 'suff_meta', fallback="META")

# mode debug
debug = int(config.get(section, 'debug', fallback=0))

# liste des zones obligatoires dans le fichier d'entrée
temp = config.get('ZONES', "zones_obligatoires").replace("\n", "")
temp = temp.replace("'", "") # suppression de caractères d'encadrement de chaînes
temp = temp.replace('"', "") # suppression de caractères d'encadrement de chaînes
T_zones_obligatoires = temp.split(",")
# suppression des espaces devant et derrière les valeurs
for i in range(0,len(T_zones_obligatoires) - 1): T_zones_obligatoires[i] = T_zones_obligatoires[i].strip()

# liste des en_têtes des zones MEASUREMENT
# les zones sont lues dans le fichier de configuration
# à chaque zone est associée un header d'affichage
T_measurement_header_z = [] # liste des zones de measurement
T_measurement_header = []   # liste des en-têtes des zones de measurement
for options in config.options('measurement_header'):
	T_measurement_header_z.append(options)
	T_measurement_header.append(config.get('measurement_header', options))

T_measurement_header_z.insert(0, "") # première colonne vide
T_measurement_header.insert(0, "") # première colonne vide

# liste des en-têtes des points d'échantillonnage
#temp = config.get('ZONES', "sampling_point_header").replace("\n", "")
#temp = temp.replace("'", "") # suppression de caractères d'encadrement de chaînes
#temp = temp.replace('"', "") # suppression de caractères d'encadrement de chaînes
#T_sampling_point_header = temp.split(",")
# suppression des espaces devant et derrière les valeurs
#for i in range(0,len(T_sampling_point_header)): T_sampling_point_header[i] = T_sampling_point_header[i].strip()
#T_sampling_point_header.insert(0, "") # première colonne vide

T_sampling_point_header_z = [] # liste des zones de sampling_point
T_sampling_point_header = []   # liste des en-têtes des zones de sampling_point
for options in config.options('sampling_point_header'):
	T_sampling_point_header_z.append(options)
	T_sampling_point_header.append(config.get('sampling_point_header', options))

T_sampling_point_header_z.insert(0, "") # première colonne vide
T_sampling_point_header.insert(0, "") # première colonne vide

# tableaux de sauvegarde
T_sampling_point_header_z_sav = T_sampling_point_header_z
T_sampling_point_header_sav = T_sampling_point_header

# liste des en-têtes des méthodologies
T_methodology_header_z = [] # liste des zones de methodology
T_methodology_header = []   # liste des en-têtes des zones de methodology
for options in config.options('methodology_header'):
	T_methodology_header_z.append(options)
	T_methodology_header.append(config.get('methodology_header', options))

T_methodology_header_z.insert(0, "") # première colonne vide
T_methodology_header.insert(0, "") # première colonne vide

# tableaux de sauvegarde
T_methodology_header_z_sav = T_methodology_header_z
T_methodology_header_sav = T_methodology_header


# ------------------------------------------------------------

# fichier d'entrée
wb_input = load_workbook(filename = input_file)

# feuille principale
ws_input = wb_input.active	

col_1 = ws_input['A']

if debug > 0:
	print("nombre de lignes   : " + str(len(col_1)))
	print("nombre de colonnes : " + str(ws_input.max_column))

# ---------- fonction ecriture_meta ----------
def ecriture_meta(iwb_meta):
	
	# ---------- ajout des sampling_points au fichier de metadata
	iwb_meta +=1 # ligne vide
	for i in range(0, len(T_sampling_point_header)):
		ws_meta.cell(row=iwb_meta, column=i+1, value=T_sampling_point_header[i])
		ws_meta.cell(row=iwb_meta+1, column=i+1, value=T_sampling_point[i])
		# setting de la largeur d'affichage de la colonne
		ws_meta.column_dimensions[get_column_letter(i + 1)].width = len(T_sampling_point[i]) + 2
	iwb_meta +=2 # ligne vide
	ws_meta.cell(row=iwb_meta, column=1, value='SAMPLING_DATE')
	ws_meta.cell(row=iwb_meta, column=2, value=sampling_date)
	iwb_meta +=1 # ligne vide
	ws_meta.cell(row=iwb_meta, column=1, value="SAMPLE_NAME")
	ws_meta.cell(row=iwb_meta, column=2, value=nom_echt)
	
	iwb_meta +=2 # 2 lignes vides
	
	# ---------- ajout des info de mesure au fichier de metadata
	iwb_meta +=1 # ligne vide
	for i in range(0, len(T_measurement_header)):
		ws_meta.cell(row=iwb_meta, column=i+1, value=T_measurement_header[i])
		ws_meta.cell(row=iwb_meta+1, column=i+1, value=T_measurement[i])
	
	iwb_meta +=3 # saut de ligne + 2 lignes vides
	
	# ---------- ajout des info de méthodologies au fichier de metadata
	iwb_meta +=1 # ligne vide
	# écriture des en-têtes
	for i in range(0, len(T_methodology_header)):
		ws_meta.cell(row=iwb_meta, column=i+1, value=T_methodology_header[i])
	iwb_meta += 1
	# écriture des méthodologies
	for i in range(0, len(T_methodology)):
		for j in range(0, len(T_methodology[i])):
			ws_meta.cell(row=iwb_meta, column=j+1, value=T_methodology[i][j])
		iwb_meta += 1
	
	iwb_meta +=2 # 2 lignes vides
	
	# --------- écriture du fichier de metadata ----------
	wb_meta.save(filename=dest_meta_filename)
	if debug > 0: print("Ecriture du fichier META " + dest_meta_filename)

# ---------- fin de ecriture_meta ----------

# ---------- MAIN ----------

T_metadata = []       # liste des zones de metadata (clef, valeur))
T_entete = []         # liste des en-têtes des colonnes des analyses
T_measurement = [''] * len(T_measurement_header_z) # informations sur les mesures, init au nombre de zones de headers
T_measurement[0] = 'MEASUREMENT'
T_sampling_point = [''] * len(T_sampling_point_header_z) # informations sur le sampling_point, init au nombre de zones de headers
T_sampling_point[0] = 'SAMPLING_POINT'
T_methodology = [] # liste des info sur les méthodologies
sampling_date = "" # date d'un échantillon'
der_lig_meta = 0 # dernière ligne qui contient des metadata
lig_entetes = 0 # numero de la ligne qui contient del en-têtes d'analyse
lig = 1
arret = 0 # condition d'arret de la lecture des metadata et des en-têtes
i_title = 0 # numéro de colonne de l'en-tête DATASET_TITLE
i_description = 0 # numéro de colonne de l'en-tête DATASET_DESCRIPTION

T_zones_obligatoires_verif = T_zones_obligatoires # duplication de la liste

# ----------

while (lig <= len(col_1) and arret == 0):
	
	if ws_input.cell(row=lig, column=ws_input.min_column).value is not None:
		if ws_input.cell(row=lig, column=ws_input.min_column).value != sep_entete:
			# les zones de metadata jusqu'au premier échantillon
		
			if debug > 0:
				print("METADATA ligne " + str(lig) + " : " + ws_input.cell(row=lig, column=ws_input.min_column).value + " = " + str(ws_input.cell(row=lig, column=ws_input.min_column + 1).value))
			T_metadata.append([ ws_input.cell(row=lig, column=ws_input.min_column).value, str(ws_input.cell(row=lig, column=ws_input.min_column + 1).value) ])
			if ws_input.cell(row=lig, column=ws_input.min_column).value in T_zones_obligatoires_verif:
				# suppression de la zone rencontree dans la liste
				T_zones_obligatoires_verif.remove(ws_input.cell(row=lig, column=ws_input.min_column).value)
			der_lig_meta = lig

		else:
			# les en-têtes de colonnes des échantillons/analyses
			
			if debug > 1:
				print("arret metadata : " + str(der_lig_meta))
				print("ligne en-tetes : " + str(lig))
				
			lig_entetes = lig
			# la ligne d'en-têtes
			for i in range(ws_input.min_column, ws_input.max_column + 1) :
				T_entete.append(ws_input.cell(row=lig, column=i).value)
				if ws_input.cell(row=lig, column=i).value == 'DATASET_TITLE':
					i_title = i # indice de la colonne
				elif ws_input.cell(row=lig, column=i).value == 'DATASET_DESCRIPTION':
					i_description = i # indice de la colonne
					
				if ws_input.cell(row=lig, column=i).value in T_zones_obligatoires_verif:
					# suppression de la zone rencontree de la liste
					# à la fin, il ne restera plus que les zones manquantes
					T_zones_obligatoires_verif.remove(ws_input.cell(row=lig, column=i).value)	
			
			if debug > 0:
				print("En-têtes : ")
				for i in range(len(T_entete)):
					print(str(i) + ": " + T_entete[i], ", ")
			if debug > 1:
				print("indice title : " + str(i_title) + " indice description : " + str(i_description))
				
			arret = 1 # fin des metadata

	lig += 1

if debug > 1: print("lig fin des metadata : " + str(der_lig_meta))

if len(T_zones_obligatoires_verif) > 0 :
	print()
	print('=================================== ERROR ===================================')
	print('Les zones obligatoires suivantes sont manquantes dans le fichier à traiter :')
	print('=================================== ERROR ===================================')
	for i in T_zones_obligatoires:
		print(i)
	print('=================================== ERROR ===================================')
	sys.exit(2)

# ---------- traitement des échantillons ----------

# initialisation pour le premier échantillon
lig_1_echt = lig_entetes + 1
nom_echt = ""
l = 2 # indice de ligne dans le workbook de sortie


for lig in range(lig_1_echt,len(col_1) + 1):
	
	if ws_input.cell(row=lig, column=ws_input.min_column).value is not None:
		
		if ws_input.cell(row=lig, column=ws_input.min_column).value != nom_echt :
		
			if debug > 0:
				print("ligne " + str(lig) + " : changement d'echantillon (" + nom_echt + ", " + ws_input.cell(row=lig, column=ws_input.min_column).value + " )")

			# écriture du fichier
			if nom_echt != "" :
				# --------- écriture du fichier de données ----------
				wb_output.save(filename=dest_don_filename)
				if debug > 0: print("Ecriture du fichier " + dest_don_filename)
				
				# --------- écriture du fichier de metadata ----------

				ecriture_meta(iwb_meta)
			
			# ---------- initialisation des fichiers ----------
			
			# nom de l'échantillon
			nom_echt = ws_input.cell(row=lig, column=ws_input.min_column).value
			
			# le nom du fichier est le nom de l'échantillon
			dest_filename = rep_data + "/" + nom_echt
			dest_don_filename = dest_filename + '.xlsx'
			
			# nom du fichier de metadata
			dest_meta_filename = dest_filename + "_" + suff_meta + ".xlsx"
			
			# initialisation du nouveau fichier de données
			wb_output = Workbook()
			ws_output = wb_output.active
	
			# la ligne d'en-tête
			for i in range(ws_input.min_column, ws_input.max_column + 1) :
				ws_output.cell(row=1, column=i, value=T_entete[i - 1])
				# setting de la largeur d'affichage de la colonne
				ws_output.column_dimensions[get_column_letter(i)].width = len(T_entete[i - 1]) + 2

			# la ligne d'analyse de l'échantillon
			l = 2 # première ligne d'analyse dans le nouveau fichier
		
			# ---------- initialisation du nouveau fichier de metadata ----------
			wb_meta = Workbook()
			ws_meta = wb_meta.active
			iwb_meta = 1 # index de ligne dans le workbook des metadata
			i_methodology = 0 # numero d'occurence dans le tableau de methodology
			b_methodology = False # indicateur d'occurrence de methodology créée pour un échantillon
			T_methodology_header_z = T_methodology_header_z_sav
			T_methodology_header = T_methodology_header_sav
			T_measurement = [''] * len(T_measurement_header_z) # informations sur les mesures, init au nombre de zones de headers
			T_measurement[0] = 'MEASUREMENT'
			T_sampling_point = [''] * len(T_sampling_point_header_z) # informations sur le sampling_point, init au nombre de zones de headers
			T_sampling_point[0] = 'SAMPLING_POINT'
			T_methodology = [] # liste des info sur les méthodologies
			sampling_date = "" # date d'un échantillon
			# ---------- traitement des données
			ws_meta.cell(row=iwb_meta, column=1, value="TITLE")
			ws_meta.cell(row=iwb_meta, column=2, value=ws_input.cell(row=lig, column=i_title).value)
			iwb_meta += 1
			ws_meta.cell(row=iwb_meta, column=1, value="DESCRIPTION")
			ws_meta.cell(row=iwb_meta, column=2, value=ws_input.cell(row=lig, column=i_description).value)
			iwb_meta += 1
			
			for i in range(1,len(T_metadata)):
				if debug > 0: print(str(i) + " : " + str(T_metadata[i]))
				ws_meta.cell(row=iwb_meta, column=1, value=T_metadata[i][0])
				ws_meta.cell(row=iwb_meta, column=2, value=T_metadata[i][1])
				iwb_meta += 1
			
			# ----------
			
		else:
			l += 1

		# ---------- copie de la ligne d'analyse dans le fichier de données
		for i in range(ws_input.min_column, ws_input.max_column + 1) :
			# ---------- copie de la zone dans le fichier de données
			ws_output.cell(row=l, column=i, value=ws_input.cell(row=lig,column=i).value)
			# ---------- extraction des metadata
				# ------------------------SAMPLING_DATE
			if ( i == T_entete.index("SAMPLING_DATE") + 1):
				sampling_date = ws_input.cell(row=lig,column=i).value
			
			else:
				if ws_input.cell(row=lig,column=i).value is not None:
					
					# ------------------------MEASUREMENT
					
					if T_entete[i - 1] != "" and re.search("^MEASUREMENT", T_entete[i - 1]):
						
						if T_entete[i - 1] not in T_measurement_header_z:
							# ajout de la zone dans la ligne des en-têtes de mesures
							# si elle n'existe pas
							T_measurement_header_z.append(T_entete[i - 1])
							T_measurement_header.append(T_entete[i - 1])
							# ajout de la zone dans la ligne de mesures
							T_measurement.append(ws_input.cell(row=lig,column=i).value)
						else: # l'en-tête est dans la liste des en-têtes
							T_measurement[T_measurement_header_z.index(T_entete[i - 1])] = ws_input.cell(row=lig,column=i).value
							
					# ------------------------SAMPLING_POINT
					
					elif T_entete[i - 1] != "" and re.search("^SAMPLING_POINT", T_entete[i - 1]):
						
						if T_entete[i - 1] not in T_sampling_point_header_z:
							# ajout de la zone dans la ligne des en-têtes de sampling_point
							# si elle n'existe pas
							T_sampling_point_header_z.append(T_entete[i - 1])
							T_sampling_point_header.append(T_entete[i - 1])
							# ajout de la zone dans la ligne de sampling_point
							T_sampling_point.append(ws_input.cell(row=lig,column=i).value)
						else: # l'en-tête est dans la liste des en-têtes
							T_sampling_point[T_sampling_point_header_z.index(T_entete[i - 1])] = ws_input.cell(row=lig,column=i).value
							
					# ------------------------METHODOLOGY
					
					elif T_entete[i - 1] != ""  and re.search("^METHODOLOGY", T_entete[i - 1]):
						
						# zone liée aux méthodologies
						if b_methodology == False: # ajout d'une nouvelle ligne
							T_methodology.append([''] * len(T_methodology_header_z)) # init au nombre de zones de headers
							T_methodology[len(T_methodology) - 1][0] = 'METHODOLOGY'
							b_methodology = True
						# ajout de la zone dans la ligne de methodologie en cours
						if T_entete[i - 1] not in T_methodology_header_z:
							T_methodology_header_z.append(T_entete[i - 1])
							T_methodology_header.append(T_entete[i - 1])
							T_methodology[len(T_methodology) - 1].append(ws_input.cell(row=lig,column=i).value)
						else:
							T_methodology[len(T_methodology) - 1][T_methodology_header_z.index(T_entete[i - 1])] = ws_input.cell(row=lig,column=i).value
					
			
		b_methodology = False

# écriture du dernier fichier
if nom_echt != "" :
	wb_output.save(filename=dest_don_filename)
	if debug > 0: print("Ecriture du fichier " + dest_don_filename)
	
	# --------- écriture du fichier de metadata ----------
	ecriture_meta(iwb_meta)
	
sys.exit(0)

# ---------- fin du fichier ----------

