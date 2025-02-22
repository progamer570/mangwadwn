env_vars = {
  # Get From my.telegram.org
  "API_HASH": "b7de0dfecd19375d3f84dbedaeb92537",
  # Get From my.telegram.org
  "API_ID": "20457610",
  #Get For @BotFather
  "BOT_TOKEN": "8083329920:AAEoQNvl-7cnXq7dQ2shY2qRlLFrKiawlCo", 
  # Get For tembo.io
  "DATABASE_URL_PRIMARY": "postgresql://postgres:z8VSFBCFcEQ5PXP9@remotely-profound-threadfin.data-1.use1.tembo.io:5432/postgres",
  # Logs Channel Username Without @
  "CACHE_CHANNEL": "-1002373950767",
  # Force Subs Channel username without @
  "CHANNEL": "Manhwa_gods",
  # {chap_num}: Chapter Number
  # {chap_name} : Manga Name
  # Ex : Chapter {chap_num} {chap_name} @Manhwa_Arena
  "FNAME": "{chap_num} ⌯ {chap_name} [@PornhwaT]"
}

dbname = env_vars.get('DATABASE_URL_PRIMARY') or env_vars.get('DATABASE_URL') or 'sqlite:///test.db'

if dbname.startswith('postgres://'):
    dbname = dbname.replace('postgres://', 'postgresql://', 1)
    
