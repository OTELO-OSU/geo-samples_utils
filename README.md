# geo-samples_utils
Utilitaires pour geo-samples

Le programme est piloté par un fichier de configuration (config.ini)
Ce fichier contient :
 * des variables nécessaire à l'environnement du programme
 * les zones obligatoires du format, zones de metadata et certaines zones de données
 * Les zones d'affichage des paragraphes MEASUREMENT, METHODOLOGY, SAMPLE POINT
 
Les fichier produits sont enregistrés dans un sous-répertoire, fichiers d'analyse et de métadonnées.
Pour chaque échantillon, un fichier de metadata et un fichier de données d'analyse sont produits.
Les fichiers sont nommés du nom de l'échantillon, suffixé de "_META" pour le fichier de métadonnées.
 
Un fichier de metadata est constitué des informations de metadata d'un échantillon
suivies des informations du point d'échantillonnage, de mesures et des méthodologies employées pour les analyses.
Les informations du point d'échantillonnage sont rangées sur une seule ligne, sauf la date.
Les informations de mesures sont également rangées sur une seule ligne.
Les informations relatives au méthodologies employées sont une liste d'informations par méthodologie.
 
Les fichiers d'analyses contiennent les informations de toutes les analyses pour un échantillon.
 
 ----
