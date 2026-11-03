"""Não troca um cartão existente por respostas de erro dos geradores."""
from pathlib import Path
import shutil,xml.etree.ElementTree as ET
root=Path(__file__).resolve().parents[1]
errors=['something went wrong','could not fetch','no languages data','no language data','error fetching','bad credentials','rate limit exceeded','not found']
for name in ['stats.svg','languages.svg','trophies.svg','snake.svg']:
 source=root/'.generated'/name
 if not source.is_file():continue
 try:
  data=source.read_text();node=ET.fromstring(data)
  if node.tag.split('}')[-1]!='svg':raise ValueError('not SVG')
  if any(term in data.lower() for term in errors):raise ValueError('error card')
  shutil.copyfile(source,root/'assets'/name)
  print('Published:',name)
 except (ValueError,ET.ParseError,UnicodeError) as e:print('Kept previous image:',name,str(e))
