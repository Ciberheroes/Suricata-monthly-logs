import schedule
import time
from datetime import datetime
import re
import os

def setEnv():
    try:
        with open(".env") as config:
            for line in config:
                key, value = line.strip().split("=")
                os.environ[key] = value
    except Exception as e:
        print("Error al cargar el archivo de configuración: " + str(e))
        exit(1)
setEnv()
LOG_FILE = os.getenv("LOG_FILE")
REPORTS_PATH=os.getenv("REPORTS_PATH")
TEST=os.getenv("TEST")

def getDateBefore():
    if TEST == "1":
        return 2024, 4
    if datetime.now().month == 1:
        return datetime.now().year-1, 12
    else:
        return datetime.now().year, datetime.now().month-1
    
def getService(rule):
    if rule == "[1:1:1]":
        return "HTTP"
    elif rule == "[1:3:1]":
        return "SSH"
    elif rule == "[1:4:1]":
        return "FTP"

def doReport():
    print("Ejecutando la función mensual")
    rules={}
    sources={}
    with open(LOG_FILE) as logs:
        for line in logs:
            
            if line.strip() == "":
                continue
            try:
                date=datetime.strptime(line.split("  ")[0],'%m/%d/%Y-%H:%M:%S.%f')
                yearBefore, monthBefore = getDateBefore()
                if date.month == monthBefore and date.year == yearBefore:
                    rule, message = re.search(r"(\[\d*:\d*:\d*\]) (.*) \[\*\*\]", line).groups()                  
                    source, destination = re.search(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d*) -> (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d*)", line).groups()
                    if source not in sources:
                        sources[source] = 1
                    else:
                        sources[source] += 1
                    if rule not in rules:
                        rules[rule] = []
                    rules[rule].append([date, rule, message, source, destination])
            except Exception as e:
                print("Error en la línea: " + line)
                continue
            
    if REPORTS_PATH != "":
        if not os.path.exists(REPORTS_PATH):
            os.makedirs(REPORTS_PATH)

    yearBefore, monthBefore = getDateBefore()
    with open(REPORTS_PATH + "report_"+str(yearBefore)+"-"+str(monthBefore).zfill(2), "w") as report:
        report.write("Reporte de alertas mensuales\n")
        report.write("\nResumen por servicio\n____________________\n\n")
        report.write("Regla        Servicio       Cantidad\n")
        for rule in rules:
            service=getService(rule)
            report.write(rule + "       " + str(service) + "            " + str(len(rules[rule])) + "\n")
        
        report.write("\nResumen por origen\n____________________\n\n")
        report.write("Origen        Cantidad\n")
        sources = dict(sorted(sources.items(), key=lambda item: item[1], reverse=True))
        for source in sources:
            report.write(source + "       " + str(sources[source]) + "\n")

        report.write("\nDetalles\n")
        report.write("____________________\n")
        for rule in rules:
            service=getService(rule)
            report.write("\nRegla:" + rule + " (" + str(service) + ")\n")
            report.write("Fecha                        Regla     Mensaje                                              Origen           Destino\n") 
            for line in rules[rule]:
                report.write(str(line[0]) + "   " + line[1] + "   " + line[2] + "   " + line[3] + "   " + line[4] + "\n")        
    
    



def task():
    if datetime.now().day == 1:
        doReport()

if TEST == "1":
    doReport()
    exit(0)

else:
    schedule.every().day.at("00:00").do(task)

    while True:
        schedule.run_pending()
        time.sleep(1)