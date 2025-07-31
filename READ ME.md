# Créer les specs
pyi-makespec `
  --onefile `
  --windowed `
  --name AssistantData `
  --icon assets/icon.ico `
  --add-data "frontend;frontend" `
  --paths "." `
  main.py

# s'il manque des imports concernant tools
hiddenimports=['tools.mysql'],

# lancer le fichier des specs
pyinstaller AssistantData.spec
