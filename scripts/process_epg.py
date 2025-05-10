import requests
from unidecode import unidecode
import xml.etree.ElementTree as ET
import gzip
import shutil

# URL dell'EPG XMLTV originale
URL_EPG = "https://iptvx.one/EPG_NOARCH"

# Scarica l'EPG compresso
response = requests.get(URL_EPG)
with open("epg.xml.gz", "wb") as f:
    f.write(response.content)

# Decomprimi il file
with gzip.open("epg.xml.gz", "rb") as f_in:
    with open("epg.xml", "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)

# Carica l'XML
tree = ET.parse("epg.xml")
root = tree.getroot()

# Translitera testi cirillici in ASCII
for elem in root.iter():
    if elem.text and any("\u0400" <= c <= "\u04FF" for c in elem.text):
        elem.text = unidecode(elem.text)

# Salva l'XML modificato
tree.write("epg_modified.xml", encoding="utf-8", xml_declaration=True)

# Comprimi nuovamente il file elaborato
with open("epg_modified.xml", "rb") as f_in:
    with gzip.open("docs/epg.xml.gz", "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
