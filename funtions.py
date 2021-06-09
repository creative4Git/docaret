import json
from django.http.response import HttpResponseGone, HttpResponseRedirect
from django.shortcuts import redirect
import pip._vendor.requests
from datetime import datetime
import io
from django.http import HttpResponse
from xhtml2pdf import pisa
from django.template.loader import get_template
import os
import os.path as path
from django.conf import settings
import sqlite3
from django.template import loader
import PIL
from cryptography.fernet import Fernet
import shutil 

BASE_URL='https://ui.boondmanager.com'
USER='finances@docaret.com'
PASS='TerraNova01'

db_path = "/app/docaret.sqlite3"

#pip._vendor.requests.put()

def load_key():
    return open("/app/key.key",'rb').read()

def encrypt(mes):
    key = load_key()
    f = Fernet(key)
    mes = bytes(mes,'utf-8')
    encMes = f.encrypt(mes)
    return encMes

def decrypt(mes):
    key = load_key()
    f = Fernet(key)
    if type(mes) is str and mes[0]=='b':
        a=mes.split("'")[1]
        mes = bytes(a,'utf-8')
    elif type(mes) is str:
        mes = bytes(mes,'utf-8')
    decMes = f.decrypt(mes)
    return decMes.decode('utf-8')

############ REQUETES POUR INFORMATION
def get_contract(contId):
    r5 = pip._vendor.requests.get(BASE_URL+'/api/contracts/'+str(contId)+'?&maxResults=500',auth=(USER,PASS)) #resources
    message5 = json.loads(r5.text)
    avantageList = message5['data']['attributes']['advantageTypes']
    frais = 0
    for adv in avantageList:
        if 'Frais' in adv['name']:
            frais = adv['employeeQuota']
    anneedébut = message5['data']['attributes']['startDate'].split('-')[0]
    anneefin = message5['data']['attributes']['endDate'].split('-')[0]
    if anneefin == '':
        anneefin = "Aujourd'hui"
    annuelBrut = 0
    coutjour = 0
    couttjour = 0
    couth = 0
    coutth = 0
    coutan = 0
    couttan = 0
    coutmois = 0
    couttmois = 0
    if "monthlySalary" in message5['data']['attributes']:
        annuelBrut = round(12*message5['data']['attributes']['monthlySalary'],0)
        coutjour = round(message5['data']['attributes']['contractAverageDailyCost'],2)
        couttjour = round(coutjour * 1.1,2)
        couth = round(coutjour*5 / message5['data']['attributes']['numberOfHoursPerWeek'],2)
        coutth = round(couth * 1.1,2)
        coutan = round(coutjour * message5['data']['attributes']['numberOfWorkingDays'],0)
        couttan = round(coutan * 1.1,0)
        coutmois = round(coutan / 12,0)
        couttmois = round(coutmois * 1.1,0)
    contractInfo = {
        "annee": anneedébut +'-'+ anneefin,
        "annuelBrut": annuelBrut,
        "frais": frais,
        #"couth": couth,
        #"coutjour": coutjour,
        #"coutmois": coutmois,
        #"coutan": coutan,
        #"coutth": coutth,
        #"couttjour": couttjour,
        #"couttmois": couttmois,
        #"couttan": couttan
    }
    return contractInfo

def define_contract(contType): #Permet de définir le type de contrat
    if contType == 0:
        contractType = 'CDI (Cadre avec RTT)'
    elif contType == 1:
        contractType = 'CDI (Cadre sans RTT)'
    elif contType == 2:
        contractType = 'CDI (ETAM avec RTT)'
    elif contType == 3:
        contractType = 'CDI (ETAM sans RTT)'
    elif contType == 4:
        contractType = 'CDD'
    elif contType == 5:
        contractType = 'Sous-Traitant / Freelance'
    elif contType == 6:
        contractType = 'Stage'
    elif contType == 7:
        contractType = 'Alternant'
    else:
        contractType = ''
    return contractType

def get_salaire(cont, weeklyHours): #Permet d'obtenir des informations salariales à partir d'un id et de ses horaires

    
    if "monthlySalary" in cont: # Si la resource a un salaire
        mensuelBrut = cont['monthlySalary']
        annuelBrut = mensuelBrut * 12
        mensuelNet = mensuelBrut * 0.75
        annuelNet = annuelBrut * 0.75
    else: #Sinon on met tout à 0
        mensuelBrut = 0
        annuelBrut = 0
        mensuelNet = 0
        annuelNet = 0
    annuelFrais = 0
    mensuelTransp = 0
    for adv in cont['advantageTypes']: #On regarde les avantages présent dans son contrat (Frais et transport)
        if 'Frais' in adv['name']:
            annuelFrais = adv['employeeQuota']
        if "Passe Navigo" in adv['name']:
            mensuelTransp = adv['participationQuota']
    mensuelFrais = annuelFrais / 12
    annuelTransp = mensuelTransp * 12
    coutTotal = round(int(annuelBrut)*1.45+int(annuelFrais)+int(annuelTransp),0) #On calcule mtn les couts pour l'entreprise
    coutTotalT = round(coutTotal * 1.1,0)
    coutj = round(coutTotal / 215,2)
    coutjT = round(coutTotalT / 215,2)
    coutm = round(coutTotal / 12,0)
    coutmT = round(coutTotalT / 12,0)
    couth = round(coutTotal / 52 / weeklyHours,2)
    couthT = round(coutTotalT / 52 / weeklyHours,2)
    salaire = {
        "mensuelBrut": round(mensuelBrut,0),
        "annuelBrut": round(annuelBrut,0),
        "mensuelNet": round(mensuelNet,0),
        "annuelNet": round(annuelNet,0),
        "mensuelFrais": round(mensuelFrais,0),
        "annuelFrais": round(annuelFrais,0),
        "mensuelTransp": round(mensuelTransp,0),
        "annuelTransp": round(annuelTransp,0),
        "coutTotal": coutTotal,
        "coutTotalT": coutTotalT,
        "coutj": coutj,
        "coutjT": coutjT,
        "couth": couth,
        "couthT": couthT,
        "coutm": coutm,
        "coutmT": coutmT,
    }
    return salaire

def get_commande(order,projInfo,production,prestation): #Permet d'obtenir des informations sur les commandes d'un projet
    listeCom=[]
    if len(order["data"]) != 0: #Si le projet a des commandes
        for com in order['data']: #Pour chaque commande associée au projet
            comId = com['id'] #On trouve l'id de la commande pour faire une requete sur l'API
            prestaLinked = pip._vendor.requests.get(BASE_URL+'/api/orders/'+str(comId)+'/information?&maxResults=500',auth=(USER,PASS))
            presta = json.loads(prestaLinked.text) 
            nbrJoursV = 0 #On initialise les valeurs
            nbrJoursC = 0
            refCommande = ''
            startDate = ''
            endDate = ''
            montantCom = 0
            montantFac = 0
            TJM = 0
            if len(presta['data']['relationships']['deliveriesPurchases']['data']) != 0: #Si la prestation est liée à une commande
                prestaId = presta['data']['relationships']['deliveriesPurchases']['data'][0]['id']
                refCommande = com['attributes']['number']
                startDate = com['attributes']['startDate']
                endDate = com['attributes']['endDate']
                montantCom = com['attributes']['turnoverOrderedExcludingTax']
                if projInfo['data']['attributes']['state'] == 2: #Si le projet est annulé
                    montantFac = "Annulé"
                else:
                    montantFac = str(com['attributes']['turnoverInvoicedExcludingTax'])+' €'
                nbrJoursV = 0
                nbrJoursC = 0
                for prod in production['data']: #On cherche ici la prestation dans 2 fichiers différents (on vérifie que l'on prend la bonne)
                    for prest in prestation['data']:
                        if prest['id'] == prestaId and prod['id'] == prestaId: 
                            TJM = prest['attributes']['averageDailyPriceExcludingTax']
                            nbrJoursV = prod['attributes']['numberOfDaysInvoicedOrQuantity']
                            nbrJoursC = prod['attributes']['regularTimesProduction']
            commande = {
                "refCommande": refCommande,
                "startDate": startDate,
                "endDate": endDate,
                "montantCom": montantCom,
                "montantFac": montantFac,
                "nbrJoursV": nbrJoursV,
                "nbrJoursC": nbrJoursC,
                "TJM": TJM
                    }
            listeCom.append(commande)
    else: #si il n'y a pas de commande associée au projet
        refCommande=""
        startDate = production['data'][0]['attributes']['startDate']
        endDate = production['data'][0]['attributes']['endDate']
        nbrJoursV = production['data'][0]['attributes']['numberOfDaysInvoicedOrQuantity']
        nbrJoursC = production['data'][0]['attributes']['regularTimesProduction']
        montantCom = order['meta']['totals']['turnoverOrderedExcludingTax']
        TJM = prestation['data'][0]['attributes']['averageDailyPriceExcludingTax']
        if projInfo['data']['attributes']['state'] == 2: #Si le projet a été annulé
            montantFac = "Annulé"
        else:
            montantFac = str(order['meta']['totals']['turnoverInvoicedExcludingTax'])+' €'
        commande = {
            "refCommande": refCommande,
            "startDate": startDate,
            "endDate": endDate,
            "montantCom": montantCom,
            "montantFac": montantFac,
            "nbrJoursV": nbrJoursV,
            "nbrJoursC": nbrJoursC,
            "TJM": TJM
            }
        listeCom.append(commande) #On ajoute la commande à la liste et on passe à la commande suivante si elle existe
    return listeCom

def get_collab(): #Permet de récupérer les données pour le tableau
    listeCollab = get_names() #On récupère les noms des collaborateurs
    for resource in listeCollab: #On ajoute les données voulues à chaque collaborateur
        resource['client'] = ''
        resource['TJM'] = 0
        prj = pip._vendor.requests.get(BASE_URL+'/api/resources/'+str(resource['id'])+'/projects?&maxResults=500',auth=(USER,PASS))
        proj = json.loads(prj.text)
        if len(proj['data']) != 0:
            projId = proj['data'][0]['id']
            clientId = proj['data'][0]['relationships']['company']['data']['id']
            for inc in proj['included']:
                if inc['id'] == clientId and inc['type'] == "company":
                    resource['client'] = inc['attributes']['name']
            #prst = pip._vendor.requests.get(BASE_URL+'/api/projects/'+str(projId)+'/deliveries-groupments?&maxResults=500',auth=(USER,PASS))
            #prest = json.loads(prst.text)
            #if len(prest['data']) != 0:
                #resource['TJM'] = prest['data'][0]['attributes']['averageDailyPriceExcludingTax']
    return listeCollab
        
def get_names2(): #Récupère les noms et prénoms de tous les collaborateurs
    r = pip._vendor.requests.get(BASE_URL+'/api/resources?&maxResults=500',auth=(USER,PASS)) #resources
    message = json.loads(r.text) 
    listeCollab=[] #On initialise une liste vide pour stocker ces données
    for resource in message['data']: #On récupère les noms,prénoms et id de tous les collaborateurs (un par un)
        collab={"nom": resource['attributes']['lastName'],
                "prenom": resource['attributes']['firstName'],
                "id": resource['id']
                }
        listeCollab.append(collab) #On passe au collaborateur suivant
    listeCollab = sorted(listeCollab, key=lambda k: k['nom']) #On trie par ordre alphabétique des noms
    return listeCollab

def get_names(): #Récupère la liste des noms et prénoms
    conn = sqlite3.connect("app/docaret.sqlite3")
    #conn.text_factory = sqlite3.OptimizedUnicode
    c = conn.cursor()
    c.execute("SELECT BoondID,lastName,firstName FROM RESOURCES;")
    listeNames=[]
    for row in c:
        listeNames.append({"id": row[0], "nom": decrypt(row[1]), "prenom": decrypt(row[2])})
    listeNames = sorted(listeNames, key = lambda k: k['nom'])
    conn.close()
    return listeNames

def get_names_user(lastName,firstName): #Récupère le nom et prénom d'un collaborateur
    conn = sqlite3.connect("app/docaret.sqlite3")
    #conn.text_factory = sqlite3.OptimizedUnicode
    c = conn.cursor()
    c.execute("SELECT BoondID,lastName,firstName FROM RESOURCES WHERE lastName='%s' AND firstName='%s';"%(lastName,firstName))
    listeNames=[]
    for row in c:
        listeNames.append({"id": row[0], "nom": decrypt(row[1]), "prenom": decrypt(row[2])})
    listeNames = sorted(listeNames, key = lambda k: k['nom'])
    conn.close()
    return listeNames

def get_names_userId(resId):
    conn = sqlite3.connect('/app/docaret.sqlite3')
    c = conn.cursor()

    c.execute('SELECT BoondID,lastName,firstName FROM RESOURCES WHERE BoondID="%s";'%(resId))
    for k in c:
        info = {"id":k[0],"lastName": decrypt(k[1]), "firstName": decrypt(k[2])}
    conn.close()
    return info

def get_info2(resId,timeSetting): #Récuperer les données pour la fiche signalitique avec API
    r = pip._vendor.requests.get(BASE_URL+'/api/resources/'+str(resId)+'/information?&maxResults=500',auth=(USER,PASS)) #resources
    message = json.loads(r.text) 
    r2 = pip._vendor.requests.get(BASE_URL+'/api/resources/'+str(resId)+'/technical-data?&maxResults=500',auth=(USER,PASS)) #resources
    message2 = json.loads(r2.text) 
    r3 = pip._vendor.requests.get(BASE_URL+'/api/resources/'+str(resId)+'/administrative?&maxResults=500',auth=(USER,PASS)) #resources
    message3 = json.loads(r3.text) 
    urgence = message3['data']['attributes']['administrativeComments'].split('\n')
    ###############################
    #Chercher le contrat et agence 
    ######## Si contract existe
    if len(message3['data']['relationships']['contracts']['data']) != 0: #Si il y a des contrats
        currentContract = 0
        manager = 0
        agency = 0
        for data in message3['included']:
            if data['type'] == 'contract': 
                oldestContract = data
                oContractId = data['id']
                if currentContract == 0:
                    currentContract = data
                    cContractId = data['id']
            elif data['type'] == 'agency':
                agency = data
        r4 = pip._vendor.requests.get(BASE_URL+'/api/contracts/'+str(cContractId)+'?&maxResults=500',auth=(USER,PASS)) #resources
        message4 = json.loads(r4.text) 
        startDate = oldestContract['attributes']['startDate']
        classification = currentContract['attributes']["classification"]
        weeklyHours = message4['data']['attributes']['numberOfHoursPerWeek']
        contractType = ''
        contractList = []
        for contract in message3['data']['relationships']['contracts']['data']:
            contractList.append(get_contract(int(contract['id'])))
        for contract in contractList:
            k = contractList.index(contract)
            if k != len(contractList)-1 and contractList[k+1]['annuelBrut']!=0:
                aug = 100 * contract['annuelBrut'] / contractList[k+1]['annuelBrut'] - 100
            else:
                aug = 0
            contract["aug"] = round(aug,0)
        #Type de contrat
        contractType = define_contract(message4['data']['attributes']['typeOf'])
        #Format des infos contracts
        if classification != '-1':
            contractClass = classification.split(' ')
            cClassFormat = contractClass[1]+'-'+contractClass[-1]
            contract = contractType + ' / ' + str(weeklyHours) + ' / ' + cClassFormat
        else:
            contract = ""
    ################################################
    # Conditions Salariales
        salaire = get_salaire(message4['data']['attributes'],weeklyHours)
    ######## Si contrat n'existe pas 
    else:
        for data in message3['included']:
            if data['type'] == 'agency':
                agency = data
        contract= ""
        contractList = []
        salaire = {
            "mensuelBrut": 0,
            "annuelBrut": 0,
            "mensuelNet": 0,
            "annuelNet": 0,
            "mensuelFrais": 0,
            "annuelFrais": 0,
            "mensuelTransp": 0,
            "annuelTransp": 0,
            "coutTotal": 0,
            "coutTotalT": 0,
            "coutj": 0,
            "coutjT": 0,
            "couth": 0,
            "couthT": 0,
            "coutm": 0,
            "coutmT": 0
        }
        startDate = ""
    ##########################################
    # Chercher le managers
    if message3['data']['id'] not in ['1','2','149','160']:
        manager = 0
        managerId = message['data']['relationships']['mainManager']['data']['id']
        for res in message['included']:
            if res['type'] == 'resource' and res['id'] == managerId:
                manager = res
                managerName = manager['attributes']['lastName'].upper()+' '+manager['attributes']['firstName']
    else:
        managerName = ''
    #########################################
    # PROJETS
    r0 = pip._vendor.requests.get(BASE_URL+'/api/resources/'+str(resId)+'/projects?&maxResults=500',auth=(USER,PASS))
    message0 = json.loads(r0.text)
    listeProj = []
    for proj in message0['data']: #On récupère tous les projets associés à cette resource, ainsi que les données de ces projets
        ref = proj['attributes']['reference'].split(' ')[0][2:]
        clientId = proj['relationships']['company']['data']['id']
        projId = proj['id']
        rInfo = pip._vendor.requests.get(BASE_URL+'/api/projects/'+str(projId)+'/information?&maxResults=500',auth=(USER,PASS))
        projInfo = json.loads(rInfo.text)
        rPresta = pip._vendor.requests.get(BASE_URL+'/api/projects/'+str(projId)+'/deliveries-groupments?&maxResults=500',auth=(USER,PASS))
        prestation = json.loads(rPresta.text)
        rProd = pip._vendor.requests.get(BASE_URL+'/api/projects/'+str(projId)+'/productivity?&maxResults=500',auth=(USER,PASS))
        production = json.loads(rProd.text)
        rOrder = pip._vendor.requests.get(BASE_URL+'/api/projects/'+str(projId)+'/orders?&maxResults=500',auth=(USER,PASS))
        order = json.loads(rOrder.text)
        facture = round(order["meta"]['totals']['turnoverInvoicedExcludingTax'],2)
        listeCom = []
        startDateP = datetime.strptime(projInfo['data']['attributes']['startDate'],'%Y-%m-%d')
        endDateP = datetime.strptime(projInfo['data']['attributes']['endDate'],'%Y-%m-%d')
        if timeSetting == 1 and startDateP.year > datetime.now().year-3: #On cherche que certains projets en fonction de timeSetting
            listeCom.append(get_commande(order,projInfo,production,prestation)) #on récupère les données des commandes du projet
            for rel in message0['included']:
                if rel['id']==clientId and rel['type']=='company':
                    client = rel['attributes']['name']
            projet ={
                "ref": ref,
                "client": client,
                "facture": facture,
                "listeCom": listeCom
            }
            listeProj.append(projet)
        if timeSetting == 2 and endDateP > datetime.now():
            listeCom = get_commande(order,projInfo,production,prestation)
            for rel in message0['included']:
                if rel['id']==clientId and rel['type']=='company':
                    client = rel['attributes']['name']
            projet ={
                "ref": ref,
                "client": client,
                "facture": facture,
                "listeCom": listeCom
            }
            listeProj.append(projet)
        if timeSetting == 0: #On prend tous les projets associés
            listeCom = get_commande(order,projInfo,production,prestation)
            for rel in message0['included']:
                if rel['id']==clientId and rel['type']=='company':
                    client = rel['attributes']['name']
            projet ={
                "ref": ref,
                "client": client,
                "facture": facture,
                "listeCom": listeCom
            }
            listeProj.append(projet)
    #####################
    # Contact Urgence & Commentaires
    if 'URGENCE' in message3['data']['attributes']['administrativeComments']:
        urgence = message3['data']['attributes']['administrativeComments'].split('\n')
        if len(urgence)>=2:
            urgenceNom = urgence[-2]
            urgenceTel = urgence[-1]
        else:
            urgenceNom = urgence[0]
            urgenceTel = ''
    else:
        urgenceNom = ''
        urgenceTel = ''
    ###################### 
    # Finalisation
    Info = {
        "id": resId,
        "nom": message['data']['attributes']['lastName'].upper(),
        "prenom": message['data']['attributes']['firstName'],
        "dateNais": message['data']['attributes']['dateOfBirth'],
        "lieuNais": message3['data']['attributes']['placeOfBirth'],
        "address": message['data']['attributes']['address'],
        "postcode": message['data']['attributes']['postcode'],
        "town": message['data']['attributes']['town'],
        "email1": message['data']['attributes']['email1'],
        "email2": message['data']['attributes']['email2'],
        "phone1": message['data']['attributes']['phone1'],
        "urgenceNom": urgenceNom,
        "urgenceTel": urgenceTel,
        "title": message['data']['attributes']['title'],
        "diplomas": message2['data']['attributes']['diplomas'],
        "startDate": startDate ,
        "manager": managerName,
        "agency": agency['attributes']['name'],
        "SSN": message3['data']['attributes']['healthCareNumber'],
        "contract": contract,
        "salaire": salaire,
        "contractList": contractList,
        "listeProj": listeProj
    }
    return Info

def get_info(resId,timeSetting): #Récuperer les données pour la fiche signalitique
    conn = sqlite3.connect("/app/docaret.sqlite3")
    c = conn.cursor()
    #Récupération des données
    c.execute("SELECT * FROM RESOURCES WHERE BoondID=%s;" %(resId))
    for res in c:
        urgence = res[12]
        resId = res[0]
        Info = {
            "id": resId,
            "nom": decrypt(res[1]).upper(),
            "prenom": decrypt(res[2]),
            "dateNais": decrypt(res[3]),
            "lieuNais": decrypt(res[4]),
            "address": decrypt(res[5]),
            "postcode": decrypt(res[6]),
            "town": decrypt(res[7]),
            "country": decrypt(res[8]),
            "email1": decrypt(res[9]),
            "email2": decrypt(res[10]),
            "phone1": decrypt(res[11]),
            "urgenceNom": decrypt(urgence),
            "title": decrypt(res[14]),
            "healthCareNumber": decrypt(res[18]),
            "managerID": res[16],
            "agencyID": res[17],
            "diplomas": res[15].split('@µ§'),
        }
    c.execute('SELECT name FROM AGENCIES WHERE BoondID="%s";'%(Info['agencyID']))
    for k in c:
        Info['agency'] = decrypt(k[0])
    Info['documents'] = get_doc(resId)
    #Récupération des projets et commandes
    c.execute('SELECT * FROM ORDERS WHERE resource=%s;'%(resId))
    listeProjTemp = []
    listeProj = []
    listeCom = []
    rows = c.fetchall()
    for com in rows:
        projId = com[2]
        comInfo ={
            "reference": decrypt(com[1]),
            "startDate": decrypt(com[3]),
            "endDate": decrypt(com[4]),
            "TJM": com[6],
            "joursCom": com[7],
            "montantCom": com[9],
            "montantFac": com[8],
            "projId": projId
            }
        if timeSetting == 1:
            startDate = datetime.strptime(comInfo['startDate'].split('-')[0],'%Y')
            if startDate > datetime.today().year - 3:
                listeCom.append(comInfo)
        elif timeSetting == 2:
            endDate = datetime.strptime(comInfo['endDate'],'%Y-%m-%d')
            if endDate > datetime.today():
                listeCom.append(comInfo)
        else:
            listeCom.append(comInfo)
    for com in listeCom:
        c.execute('SELECT * FROM PROJECTS WHERE BoondID=%s;'%(com['projId']))
        for p in c:
            proj = {
                "id": p[0],
                "client": p[2],
                "reference": decrypt(p[1])
            }
            listeProjTemp.append(proj)
    for proj in listeProjTemp:
        c.execute('SELECT name FROM COMPANIES WHERE BoondID=%s;'%(proj['client']))
        for comp in c:
            proj['client'] = decrypt(comp[0])
        listeComP=[]
        for com in listeCom:
            if com['projId'] == proj['id']:
                listeComP.append(com)
        proj['listeCom'] = listeComP
        idList = [int(item['id']) for item in listeProj]
        if proj not in listeProj:
            listeProj.append(proj)
    Info['listeProj'] = listeProj
    #Récupération des contrats
    c.execute('SELECT * FROM CONTRACTS WHERE resource=%s;'%(resId))
    contractList = []
    for con in c:
        advList = []
        advs = decrypt(con[7]).split('\n')
        for adv in advs:
            if adv != '' and adv != ' ':
                if adv.split('_')[-1] in 'monthly ':
                    yearValue = round(float(adv.split('_')[1])*12,0)
                    monthValue = adv.split('_')[-2]
                else:
                    yearValue = adv.split('_')[1]
                    monthValue = round(float(adv.split('_')[1])/12,0)
                advInfo = {
                    "name": adv.split('_')[0],
                    "yearValue": yearValue,
                    "monthValue": monthValue
                }
                advList.append(advInfo)
        contract = {
            "startDate": decrypt(con[1]),
            "endDate": decrypt(con[2]),
            "classification": decrypt(con[3]),
            "coutJour": con[4],
            "monthlySalary": con[6],
            "annee": decrypt(con[1]).split('-')[0] +'-'+ decrypt(con[2]).split('-')[0],
            "annuelBrut": round(float(con[6])*12,0),
            "advantages": advList
        }
        #contract['annuelBrut'] = round(12*con[6],0)
        #contract['couttjour'] = round(contract['coutjour']*1.1,2)
        contractList.append(contract)
    Info['contractList'] = contractList
    if len(contractList) != 0:
        con = contractList[0]
        Info["currentContract"]=contractList[0]
        fraisSupp = sum(float(adv['yearValue']) for adv in con['advantages'])
        coutTotal = round(float(con['monthlySalary'])*12*1.45+fraisSupp,0)
        Info['salaire'] = {
            "coutTotal": coutTotal,
            "coutm": round(coutTotal/12,0),
            "coutj": round(coutTotal/215,2),
            "coutTotalT": round(coutTotal*1.1,0),
            "coutmT":round(coutTotal/12*1.1,0),
            "coutjT":round(coutTotal*1.1/215,2),
            "annuelBrut": round(float(con['monthlySalary'])*12,0),
            "mensuelBrut": round(float(con['monthlySalary']),0),
            "annuelNet": round(float(con['monthlySalary'])*12*0.75,0),
            "mensuelNet": round(float(con['monthlySalary'])*0.75,0),
            }
        #Informations Contrat
        Info['contract'] = contractList[0]['classification']
        Info['startDate'] = contractList[-1]['startDate']
        c.execute('SELECT name FROM AGENCIES WHERE BoondID=%s;'%(Info['agencyID']))
        for r in c:
            Info['agency'] = decrypt(r[0])
        c.execute('SELECT lastName,firstName FROM RESOURCES WHERE BoondID=%s;'%(Info['managerID']))
        for r in c:
            Info['manager'] = decrypt(r[0]).upper()+' '+decrypt(r[1])
    return Info

def get_doc(resId): #Récupère les données des documents d'un collaborateur

    conn = sqlite3.connect('/app/docaret.sqlite3')
    c = conn.cursor()
    Info={'resId': resId.split('%')}
    c.execute('SELECT * FROM DOCUMENTS WHERE resource="%s";'%(resId.split('%')[0]))
    for k in c:
        Info['id'] = k[0]
        Info['num1'] = decrypt(k[2])
        Info['startDate1'] = decrypt(k[3])
        Info['endDate1'] = decrypt(k[4])
        Info['num2'] = decrypt(k[5])
        Info['startDate2'] = decrypt(k[6])
        Info['endDate2'] = decrypt(k[7])
    conn.close()
    return Info

def modify_doc(docId,num1,startDate1,endDate1,num2,startDate2,endDate2): #Modifie les données des documents
    conn = sqlite3.connect('/app/docaret.sqlite3')
    c = conn.cursor()
    docId = docId.split('%')[0]
    num1 = encrypt(num1)
    num2 = encrypt(num2)
    c.execute('UPDATE DOCUMENTS SET num1="%s" WHERE id=%s;'%(num1,docId))
    c.execute('UPDATE DOCUMENTS SET startDate1="%s" WHERE id=%s;'%(encrypt(startDate1),docId))
    c.execute('UPDATE DOCUMENTS SET endDate1="%s" WHERE id=%s;'%(encrypt(endDate1),docId))
    c.execute('UPDATE DOCUMENTS SET num2="%s" WHERE id=%s;'%(num2,docId))
    c.execute('UPDATE DOCUMENTS SET startDate2="%s" WHERE id=%s;'%(encrypt(startDate2),docId))
    c.execute('UPDATE DOCUMENTS SET endDate2="%s" WHERE id=%s;'%(encrypt(endDate2),docId))
    conn.commit()
    conn.close()
###############################################################################################

############ MODIFICATION VERS BOOND (NON FONCTIONNEL)
def get_modifyPage(resId):

    r = pip._vendor.requests.get(BASE_URL+'/api/resources/'+str(resId)+'/information?&maxResults=500',auth=(USER,PASS)) #resources
    message = json.loads(r.text) 
    r2 = pip._vendor.requests.get(BASE_URL+'/api/resources/'+str(resId)+'/technical-data?&maxResults=500',auth=(USER,PASS)) #resources
    message2 = json.loads(r2.text) 
    r3 = pip._vendor.requests.get(BASE_URL+'/api/resources/'+str(resId)+'/administrative?&maxResults=500',auth=(USER,PASS)) #resources
    message3 = json.loads(r3.text) 
    urgence = message3['data']['attributes']['administrativeComments'].split('\n')
    if 'URGENCE' in message3['data']['attributes']['administrativeComments']:
        urgence = message3['data']['attributes']['administrativeComments'].split('\n')
    else:
        urgence = ['','','']
    Info = {
        "nom": message['data']['attributes']['lastName'].upper(),
        "prenom": message['data']['attributes']['firstName'],
        "dateNais": message['data']['attributes']['dateOfBirth'],
        "lieuNais": message3['data']['attributes']['placeOfBirth'],
        "address": message['data']['attributes']['address'],
        "postcode": message['data']['attributes']['postcode'],
        "town": message['data']['attributes']['town'],
        "email1": message['data']['attributes']['email1'],
        "email2": message['data']['attributes']['email2'],
        "phone1": message['data']['attributes']['phone1'],
        "urgenceNom": urgence[-2],
        "urgenceTel": urgence[-1]
    }
    return Info

def send_modif(info):
    information={
        "data":{
            "attributes":{
                "lastName":info['lastName'],
                "firstName":info['firstName'],
                "dateOfBirth":info['dateOfBirth'],
                "address":info['address'],
                "postcode":info['postcode'],
                "town":info['town'],
                "mail1":info['mail1'],
                "mail2":info['mail2'],
                "phone1":info['phone1']
            }
        },
        "type": "resource"
    }
    information = json.dumps(information)
    return pip._vendor.requests.put(BASE_URL+'/resources/'+str(info['id'])+'/information',json=information,auth=(USER,PASS))
###############################################################################################

############ EXPORT EN PDF
def link_callback(uri, rel):
    """
    Convert HTML URIs to absolute system paths so xhtml2pdf can access those
    resources
    """
    # use short variable names
    sUrl = settings.STATIC_URL      # Typically /static/
    sRoot = settings.STATIC_ROOT    # Typically /home/userX/project_static/
    mUrl = settings.MEDIA_URL       # Typically /static/media/
    mRoot = settings.MEDIA_ROOT     # Typically /home/userX/project_static/media/

    # convert URIs to absolute system paths
    if uri.startswith(mUrl):
        path = os.path.join(mRoot, uri.replace(mUrl, ""))
    elif uri.startswith(sUrl):
        path = os.path.join(sRoot, uri.replace(sUrl, ""))
    else:
        return uri  # handle absolute uri (ie: http://some.tld/foo.png)

    # make sure that file exists
    if not os.path.isfile(path):
            raise Exception(
                'media URI must start with %s or %s' % (sUrl, mUrl)
            )
    return path

def render_to_pdf(template_src, context_dict):
    template = get_template(template_src) #On prend le template source pour la mise en page
    context={}
    context['segment'] = 'details'
    context['collabInfo'] = context_dict #On prend les données pour les envoyers vers le pdf
    html  = template.render(context)
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("utf-8")), result, link_callback=link_callback)
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        return response
    
def fetch_resources(uri, rel):
    if os.sep == '\\': # deal with windows and wrong slashes
        uri2 = os.sep.join(uri.split('/'))
    else:# else, just add the untouched path.
       uri2 = uri
    path = '%s%s' % (settings.SITE_ROOT, uri2)
    return path

def search_collab(searchValue,listeNames):
    collab = 0
    r = pip._vendor.requests.get(BASE_URL+'/api/projects?&maxResults=500',auth=(USER,PASS))
    message = json.loads(r.text)
    for col in listeNames:
        if searchValue.lower() == (col['prenom']+'+'+col['nom']).lower() or searchValue.lower() == (col['nom']+'+'+col['prenom']).lower():
            collab = col
            return collab['id']
        elif col['prenom'].lower() == searchValue.lower() or col['nom'].lower() == searchValue.lower():
            collab = col
            return collab['id']
###############################################################################################

############# REMPLISSAGE DE LA BASE DE DONNEES

#%% Requetes pour remplir la table RESOURCES
def fill_resources():
    r = pip._vendor.requests.get(BASE_URL+'/api/resources?&maxResults=500',auth=(USER,PASS))
    data0 = json.loads(r.text)

    conn = sqlite3.connect('/app/docaret.sqlite3')
    c = conn.cursor()
    
    for res in data0['data']:
        resId = res['id']
        r1 = pip._vendor.requests.get(BASE_URL+'/api/resources/'+str(resId)+'/administrative?&maxResults=500',auth=(USER,PASS))
        admin = json.loads(r1.text)
        r2 = pip._vendor.requests.get(BASE_URL+'/api/resources/'+str(resId)+'/information?&maxResults=500',auth=(USER,PASS))
        info = json.loads(r2.text)
        r3 = pip._vendor.requests.get(BASE_URL+'/api/resources/'+str(resId)+'/technical-data?&maxResults=500',auth=(USER,PASS))
        tech = json.loads(r3.text)
        if res['relationships']['mainManager']['data'] == None:
            mainManager = 0
        else:
            mainManager = res['relationships']['mainManager']['data']['id']
        diplomas = tech['data']['attributes']['diplomas']
        dipText = ''
        for dip in diplomas:
            newdip = dip + '@µ§'
            dipText += newdip
        collab = {
                "BoondID": resId,
                "lastName": encrypt(res['attributes']['lastName']),
                "firstName": encrypt(res['attributes']['firstName']),
                "dateOfBirth": encrypt(admin['data']['attributes']['dateOfBirth']),
                "placeOfBirth": encrypt(admin['data']['attributes']['placeOfBirth']),
                "address": encrypt(info['data']['attributes']['address']),
                "postcode": encrypt(info['data']['attributes']['postcode']),
                "town": encrypt(info['data']['attributes']['town']),
                "country": encrypt(info['data']['attributes']['country']),
                "email1": encrypt(res['attributes']['email1']),
                "email2": encrypt(info['data']['attributes']['email2']),
                "phone1": encrypt(res['attributes']['phone1']),
                "phone2": encrypt(res['attributes']['phone2']),
                "administrativeComments": encrypt(admin['data']['attributes']['administrativeComments']),
                "title": encrypt(res['attributes']['title']),
                "diplomas": dipText,
                "mainManager": mainManager,
                "agency": res['relationships']['agency']['data']['id'],
                "healthCareNumber": encrypt(admin['data']['attributes']['healthCareNumber'])
                }
        values = (collab['BoondID'],collab['lastName'],collab['firstName'],collab['dateOfBirth'],collab['placeOfBirth'],collab['address'],collab['postcode'],collab['town'],collab['country'],collab['email1'],collab['email2'],collab['phone1'],collab['phone2'],collab['administrativeComments'],collab['title'],collab['mainManager'],collab['agency'],collab['healthCareNumber'],collab['diplomas'])
        #collabList.append(collab)
        c.execute("INSERT OR REPLACE INTO RESOURCES (BoondID,lastName,firstName,dateOfBirth,placeOfBirth,address,postcode,town,country,email1,email2,phone1,phone2,administrativeComments,title,mainManager,agency,healthCareNumber,diplomas) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", values)
        conn.commit()
    conn.close()

#%%  Requetes pour remplir la table AGENCIES
def fill_agencies():
    r = pip._vendor.requests.get(BASE_URL+'/api/agencies?&maxResults=500',auth=(USER,PASS))
    data0 = json.loads(r.text)
    
    conn = sqlite3.connect('/app/docaret.sqlite3')
    c = conn.cursor()
    
    for agency in data0['data']:
        name = encrypt(agency['attributes']['name'])
        BoondID = agency['id']
        vatNumber = encrypt(agency['attributes']['vatNumber'])
        address = encrypt(agency['attributes']['address'])
        town = encrypt(agency['attributes']['town'])
        country = encrypt(agency['attributes']['country'])
    
        values = (BoondID, name, vatNumber, address, town, country)
        c.execute("INSERT OR REPLACE INTO AGENCIES (BoondID,name,vatNumber,address,town,country) VALUES (?,?,?,?,?,?);", values)
        conn.commit()
    conn.close()

#%% Requetes pour remplir la table COMPANIES
def fill_companies():
    r = pip._vendor.requests.get(BASE_URL+'/api/companies?&maxResults=500',auth=(USER,PASS))
    data0 = json.loads(r.text)
    
    conn = sqlite3.connect('/app/docaret.sqlite3')
    c = conn.cursor()
    
    
    for client in data0['data']:
        BoondID = client['id']
        name = encrypt(client['attributes']['name'])
        expertiseArea = encrypt(client['attributes']['expertiseArea'])
        town = encrypt(client['attributes']['town'])
        country = encrypt(client['attributes']['country'])
        mainManager = encrypt(client['relationships']['mainManager']['data']['id'])
        
        values = (BoondID, name, expertiseArea, town, country, mainManager)
        c.execute("INSERT OR REPLACE INTO COMPANIES (BoondID,name,expertiseArea,town,country,mainManager) VALUES (?,?,?,?,?,?);", values)
        conn.commit()
    conn.close()

#%% Requete pour remplir la table CONTRACTS
def fill_contracts():
    r = pip._vendor.requests.get(BASE_URL+'/api/contracts?&maxResults=500',auth=(USER,PASS))
    data0 = json.loads(r.text)
    
    conn = sqlite3.connect('/app/docaret.sqlite3')
    c = conn.cursor()
    
    contractList = []
    for contract in data0['data']:
        contractInfo = {
        "BoondID" : contract['id'],
        "startDate" : encrypt(contract['attributes']['startDate']),
        "endDate" : encrypt(contract['attributes']['endDate']),
        "classification" : encrypt(contract['attributes']['classification']),
        "contractAverageDailyCost" : contract['attributes']['contractAverageDailyCost'],
        "resource" : contract['relationships']['dependsOn']['data']['id'],
        "monthlySalary" : contract['attributes']['monthlySalary'],
        }
        contractList.append(contractInfo)
    for contract in contractList:
        r2 = pip._vendor.requests.get(BASE_URL+'/api/contracts/'+str(contract['BoondID'])+'?&maxResults=500',auth=(USER,PASS))
        data1 = json.loads(r2.text)
        contract['advantages']=''
        for adv in data1['data']['attributes']['advantageTypes']:
            if adv['name'] == 'Passe Navigo' or adv['name'] == 'Mutuelle AG2R':
               contract['advantages'] = contract['advantages'] +'\n'+ adv['name'] + '_' + str(adv['participationQuota'])+'_'+adv['frequency']
            else:
                contract['advantages'] = contract['advantages'] +' \n'+ adv['name'] + '_' + str(adv['employeeQuota'])+'_'+adv['frequency']
        values = (contract['BoondID'],contract['startDate'],contract['endDate'],contract['classification'],contract['contractAverageDailyCost'],contract['resource'],contract['monthlySalary'],encrypt(contract['advantages']))
        c.execute("INSERT OR REPLACE INTO CONTRACTS (BoondID,startDate,endDate,classification,contractAverageDailyCost,resource,monthlySalary,advantages) VALUES (?,?,?,?,?,?,?,?);", values)
        conn.commit()
    conn.close()

#%% Requetes pour remplir la table PROJECTS
def fill_projects():
    r = pip._vendor.requests.get(BASE_URL+'/api/projects?&maxResults=500',auth=(USER,PASS))
    data0 = json.loads(r.text)
    
    conn = sqlite3.connect('/app/docaret.sqlite3')
    c = conn.cursor()


    for project in data0['data']:
        BoondID = project['id']
        r2 = pip._vendor.requests.get(BASE_URL+'/api/projects/'+str(BoondID)+'/information?&maxResults=500',auth=(USER,PASS))
        data1 = json.loads(r2.text)
        for inc in data1['included']:
            if inc['type'] == 'contact':
                contactFirstName = encrypt(inc['attributes']['firstName'])
                contactLastName = encrypt(inc['attributes']['lastName'])
            elif inc['type'] == 'company':
                client = inc['id']
        reference = encrypt(project['attributes']['reference'])
        startDate = encrypt(project['attributes']['startDate'])
        endDate = encrypt(project['attributes']['endDate'])
        client = client

        values = (BoondID, reference, client, startDate, endDate, contactLastName, contactFirstName)
        c.execute("INSERT OR REPLACE INTO PROJECTS (BoondID, reference, client, startDate, endDate, contactLastName, contactFirstName) VALUES (?,?,?,?,?,?,?);", values)
        conn.commit()
    conn.close()

#%% Requetes pour remplir la table ORDERS
def fill_orders():
    r = pip._vendor.requests.get(BASE_URL+'/api/orders?&maxResults=500',auth=(USER,PASS))
    data0 = json.loads(r.text)
    
    conn = sqlite3.connect('/app/docaret.sqlite3')
    c = conn.cursor()
    
    
    for order in data0['data']:
        BoondID = order['id']
        r2 = pip._vendor.requests.get(BASE_URL+'/api/orders/'+str(BoondID)+'/information?&maxResults=500',auth=(USER,PASS))
        data1 = json.loads(r2.text)
        reference = ''
        startDate = ''
        endDate = ''
        resource = ''
        project = ''
        turnoverInvoicedExcludingTax = ''
        turnoverOrderedExcludingTax = ''
        averageDailyPriceExcludingTax = ''
        numberOfDaysInvoicedOrQuantity = ''
        if len(data1['data']['relationships']['deliveriesPurchases']['data']) != 0:
            reference = order['attributes']['number']
            startDate = data1['data']['attributes']['startDate']
            endDate = data1['data']['attributes']['endDate']
            project = data1['data']['relationships']['project']['data']['id']
            turnoverInvoicedExcludingTax = order['attributes']['turnoverInvoicedExcludingTax']
            turnoverOrderedExcludingTax = order['attributes']['turnoverOrderedExcludingTax']
            prestaID = data1['data']['relationships']['deliveriesPurchases']['data'][0]['id']
            r3 = pip._vendor.requests.get(BASE_URL+'/api/deliveries/'+str(prestaID)+'?&maxResults=500',auth=(USER,PASS))
            data2 = json.loads(r3.text)
            averageDailyPriceExcludingTax = data2['data']['attributes']['averageDailyPriceExcludingTax']
            resource = data2['data']['relationships']['dependsOn']['data']['id']
            numberOfDaysInvoicedOrQuantity = data2['data']['attributes']['numberOfDaysInvoicedOrQuantity']
        
        values = (BoondID, encrypt(reference), project, encrypt(startDate), encrypt(endDate), resource, averageDailyPriceExcludingTax, numberOfDaysInvoicedOrQuantity, turnoverInvoicedExcludingTax, turnoverOrderedExcludingTax)
        c.execute("INSERT OR REPLACE INTO ORDERS (BoondID, reference, project, startDate, endDate, resource, averageDailyPriceExcludingTax, numberOfDaysInvoicedOrQuantity, turnoverInvoicedExcludingTax, turnoverOrderedExcludingTax) VALUES (?,?,?,?,?,?,?,?,?,?);", values)
        conn.commit()
    conn.close()

# Fonctions permettant le remplissage total de la BdD
def copy_db():
    shutil.copy('/app/docaret.sqlite3','/app/docaret2.sqlite3')
###############################################################################################

###################NOUVELLES FONCTIONNALITES
#Récupération des fiches de contacts pour un collaborateur
def get_contacts(resId,onglet):
    conn = sqlite3.connect('/app/docaret.sqlite3')
    c = conn.cursor()
    
    contactList = []
    c.execute('SELECT * FROM CONTACTS WHERE resource=%s;'%(resId))
    for contact in c:
        proj = {
            "id": contact[0],
            "projId": contact[1],
            "resId": resId,
            "dataN": decrypt(contact[3]),
            "dataN1": decrypt(contact[6]),
            "dataN2": decrypt(contact[9]),
            "telN": decrypt(contact[4]),
            "telN1": decrypt(contact[7]),
            "telN2": decrypt(contact[10]),
            "mailN": decrypt(contact[5]),
            "mailN1": decrypt(contact[8]),
            "mailN2": decrypt(contact[11]),
            "startDate": decrypt(contact[12]),
            "endDate": decrypt(contact[13]),
            "lastUpdate": decrypt(contact[14])
        }
        if onglet == 2 and proj['endDate'] != None and proj['endDate'] != '':
            endDate = datetime.strptime(proj['endDate'],'%Y-%m-%d')
            if endDate < datetime.today():
                contactList.append(proj)
        elif onglet == 1:
            if proj['endDate'] == '' or proj['endDate'] == None:
                contactList.append(proj)
    for proj in contactList:
        c.execute('SELECT client,reference FROM PROJECTS WHERE BoondID=%s;'%(proj['projId']))
        for clt in c:
            proj['client'] = clt[0]
            proj['pRef'] = decrypt(clt[1])
        c.execute('SELECT name FROM COMPANIES WHERE BoondID=%s;'%(proj['client']))
        for clt in c:
            proj['client'] = decrypt(clt[0])
        c.execute('SELECT lastName,firstName,phone1,email1 FROM RESOURCES WHERE BoondID=%s;'%(resId))
        for res in c:
            proj['lastName'] = decrypt(res[0])
            proj['firstName'] = decrypt(res[1])
            proj['phone1'] = decrypt(res[2])
            proj['email1'] = decrypt(res[3])
    conn.close()
    return contactList

#Validation d'une fiche de contact
def validate_contact(conId):
    conn = sqlite3.connect("/app/docaret.sqlite3")
    c = conn.cursor()
    today = str(datetime.today()).split(' ')[0]
    c.execute('UPDATE CONTACTS SET lastUpdate="%s" WHERE id=%s;'%(encrypt(today),conId))
    conn.commit()
    conn.close()

#Récupération des données d'une fiche de contact (pour la page de modification)
def get_contact(conId):
    conn = sqlite3.connect('/app/docaret.sqlite3')
    c = conn.cursor()

    c.execute('SELECT * FROM CONTACTS WHERE id=%s;'%(conId))
    for con in c:
        contact = {
            "dataN": decrypt(con[3]),
            "dataN1": decrypt(con[4]),
            "dataN2": decrypt(con[5]),
            "telN": decrypt(con[6]),
            "telN1": decrypt(con[7]),
            "telN2": decrypt(con[8]),
            "mailN": decrypt(con[9]),
            "mailN1": decrypt(con[10]),
            "mailN2": decrypt(con[11]),
        }
    conn.close()
    return contact

#Modification d'une fiche de contact
def modify_contact(conId,values):
    conn = sqlite3.connect('/app/docaret.sqlite3')
    c = conn.cursor()
    today = str(datetime.today()).split(' ')[0]
    c.execute('UPDATE CONTACTS SET endDate="%s" WHERE id=%s;'%(encrypt(today),conId))
    c.execute('UPDATE CONTACTS SET lastUpdate="%s" WHERE id=%s;'%(encrypt(today),conId))
    c.execute('SELECT project FROM CONTACTS WHERE id=%s;'%(values[1]))
    for con in c:
        projId = con[0]
    formValues = [
        projId, #project
        values[0], #resource
        encrypt(values[5].replace('%40','@')), #mailN
        encrypt(values[3]), #dataN
        encrypt(values[4]), #telN
        encrypt(values[8].replace('%40','@')),
        encrypt(values[6]),
        encrypt(values[7]),
        encrypt(values[11].replace('%40','@')),
        encrypt(values[9]),
        encrypt(values[10]),
        encrypt(str(datetime.today()).split(' ')[0]),
        encrypt(str(datetime.today()).split(' ')[0]),
    ]
    c.execute('INSERT INTO CONTACTS (project,resource,mailN,dataN,telN,mailN1,dataN1,telN1,mailN2,dataN2,telN2,startDate,lastUpdate) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?);',formValues)
    conn.commit()
    conn.close()

#Récupérations des projets d'un collaborateur
def get_projects(resId):
    conn = sqlite3.connect('/app/docaret.sqlite3')
    c = conn.cursor()

    c.execute('SELECT project FROM ORDERS WHERE resource=%s;'%(resId))
    listeProjTemp = []
    listeProj = []
    listeCom = []
    for com in c:
        projId = com[0]
        comInfo ={
            "projId": projId
            }
        listeCom.append(comInfo)
    for com in listeCom:
        c.execute('SELECT * FROM PROJECTS WHERE BoondID=%s;'%(com['projId']))
        for p in c:
            proj = {
                "id": p[0],
                "client": p[2],
                "reference": decrypt(p[1])
            }
            listeProjTemp.append(proj)
    for proj in listeProjTemp:
        c.execute('SELECT name FROM COMPANIES WHERE BoondID=%s;'%(proj['client']))
        for comp in c:
            proj['client'] = decrypt(comp[0])
        listeComP=[]
        for com in listeCom:
            if com['projId'] == proj['id']:
                listeComP.append(com)
        proj['listeCom'] = listeComP
        if proj not in listeProj:
            listeProj.append(proj)

    conn.close()
    return listeProj

#Ajout d'une nouvelle fiche contact
def add_contact(values):
    conn = sqlite3.connect('/app/docaret.sqlite3')
    c = conn.cursor()
    formValues = [
        values[0], #project
        values[1], #resource
        encrypt(values[6].replace('%40','@')), #mailN
        encrypt(values[4]), #dataN
        encrypt(values[5]), #telN
        encrypt(values[9].replace('%40','@')),
        encrypt(values[7]),
        encrypt(values[8]),
        encrypt(values[12].replace('%40','@')),
        encrypt(values[10]),
        encrypt(values[11]),
        encrypt(values[2]),
        encrypt(values[3]),
        encrypt(str(datetime.today()).split(" ")[0])
    ]
    c.execute('INSERT INTO CONTACTS (project,resource,mailN,dataN,telN,mailN1,dataN1,telN1,mailN2,dataN2,telN2,startDate,endDate,lastUpdate) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?);',formValues)
    conn.commit()
    conn.close()

#Permet de cloturer un contact
def close_contact(conId,endDate):
    conn = sqlite3.connect('/app/docaret.sqlite3')
    c = conn.cursor()
    today = str(datetime.today()).split(' ')[0]
    c.execute('UPDATE CONTACTS SET endDate="%s" WHERE id=%s;'%(encrypt(endDate),conId))
    c.execute('UPDATE CONTACTS SET lastUpdate="%s" WHERE id=%s;'%(encrypt(today),conId))
    conn.commit()
    conn.close()

#Requetes permettant de récupérer l'ensemble des données d'habilitation
def get_habilitation():
    conn = sqlite3.connect('/app/docaret.sqlite3')
    c = conn.cursor()

    c.execute('SELECT * FROM HABILITATION;')
    habList=[]
    for hab in c:
        habInfo = {
            "id": hab[0],
            "resId": hab[1],
            "actif": decrypt(hab[2]),
            "sendDate": decrypt(hab[3]),
            "docRef": decrypt(hab[6]),
            "dgaRef": decrypt(hab[7]),
            "state": decrypt(hab[8]),
            "certifNumber": decrypt(hab[9]),
            "startDate": decrypt(hab[4]),
            "endDate": decrypt(hab[5])
        }
        habList.append(habInfo)
    for hab in habList:
        c.execute('SELECT lastName,firstName FROM RESOURCES WHERE BoondID=%s;'%(hab['resId']))
        for k in c:
            hab['lastName'] = decrypt(k[0])
            hab['firstName'] = decrypt(k[1])
    conn.close()
    return habList

#Ajout d'une nouvelle habilitation
def add_hab(resId,sendDate,startDate,endDate,docRef,dgaRef,state,certifNumber):
    conn = sqlite3.connect('/app/docaret.sqlite3')
    c = conn.cursor()

    values = [resId,encrypt('X'),encrypt(sendDate),encrypt(startDate),encrypt(endDate),encrypt(docRef),encrypt(dgaRef),encrypt(state),encrypt(certifNumber)]
    c.execute('INSERT INTO HABILITATION (resource,actif,sendDate,startDate,endDate,docRef,dgaRef,state,certifNumber) VALUES (?,?,?,?,?,?,?,?,?);',values)
    conn.commit()
    conn.close()

#données d'une habilitation (pour la page de modification)
def get_hab(habId):
    conn = sqlite3.connect('/app/docaret.sqlite3')
    c = conn.cursor()

    c.execute('SELECT * FROM HABILITATION WHERE id=%s;'%(habId))
    for hab in c:
        habInfo = {
            "id": hab[0],
            "resId": hab[1],
            "actif": decrypt(hab[2]),
            "sendDate": decrypt(hab[3]),
            "docRef": decrypt(hab[6]),
            "dgaRef": decrypt(hab[7]),
            "state": decrypt(hab[8]),
            "certifNumber": decrypt(hab[9]),
            "startDate": decrypt(hab[4]),
            "endDate": decrypt(hab[5])
        }
    conn.close()
    return habInfo

#Modification d'une habilitation
def modify_hab(habId,actif,sendDate,startDate,endDate,docRef,dgaRef,state,certifNumber):
    conn = sqlite3.connect('/app/docaret.sqlite3')
    c = conn.cursor()

    values = [encrypt(actif),encrypt(sendDate),encrypt(startDate),encrypt(endDate),encrypt(docRef),encrypt(dgaRef),encrypt(state),encrypt(certifNumber)]
    c.execute('UPDATE HABILITATION SET actif="%s" WHERE id=%s;'%(actif,habId))
    c.execute('UPDATE HABILITATION SET sendDate="%s" WHERE id=%s;'%(sendDate,habId))
    c.execute('UPDATE HABILITATION SET startDate="%s" WHERE id=%s;'%(startDate,habId))
    c.execute('UPDATE HABILITATION SET endDate="%s" WHERE id=%s;'%(endDate,habId))
    c.execute('UPDATE HABILITATION SET docRef="%s" WHERE id=%s;'%(docRef,habId))
    c.execute('UPDATE HABILITATION SET dgaRef="%s" WHERE id=%s;'%(dgaRef,habId))
    c.execute('UPDATE HABILITATION SET state="%s" WHERE id=%s;'%(state,habId))
    c.execute('UPDATE HABILITATION SET certifNumber="%s" WHERE id=%s;'%(certifNumber,habId))
    conn.commit()
    conn.close()

#Récupération des adresses mails (email1) après filtrage
def get_addresses(clientId,respoId,single):
    conn = sqlite3.connect('/app/docaret.sqlite3')
    c = conn.cursor()
    listeID = []
    if clientId == '-1' and respoId == '-1':
        listeMail = []
        c.execute('SELECT lastName,firstName,email1,BoondID FROM RESOURCES;')
        for res in c:
            if res[3] not in listeID:
                listeID.append(res[3])
                listeMail.append({"lastName":decrypt(res[0]), "firstName":decrypt(res[1]), "mail":decrypt(res[2])})
    elif respoId == '-1':
        listeMail=[]
        c.execute('SELECT lastName,firstName,email1,ORDERS.endDate,RESOURCES.BoondID FROM RESOURCES JOIN ORDERS,PROJECTS WHERE ORDERS.resource=RESOURCES.BoondID AND PROJECTS.client="%s" AND ORDERS.project=PROJECTS.BoondID;'%(clientId))
        for res in c:
            if res[4] not in listeID:
                if res[3] != None and res[3] != '' and res[3] != ' ':
                    endDate = datetime.strptime(res[3],"%Y-%m-%d")
                    if endDate > datetime.today():
                        listeMail.append({"lastName":res[0], "firstName":res[1], "mail":res[2]})
                        listeID.append(res[4])
    elif clientId == '-1':
        listeMail = []
        c.execute('SELECT lastName,firstName,email1,CONTACTS.endDate,RESOURCES.BoondID FROM RESOURCES JOIN CONTACTS WHERE (CONTACTS.dataN="%s" OR CONTACTS.dataN1="%s" OR CONTACTS.dataN2="%s") AND CONTACTS.resource=RESOURCES.BoondID;'%(respoId,respoId,respoId))
        for res in c:
            if res[4] not in listeID:
                if res[3] == None or res[3] == '' or res[3] == ' ':
                    listeMail.append({"lastName":res[0], "firstName":res[1], "mail":res[2]})
                    listeID.append(res[4])
                else:
                    endDate = datetime.strptime(res[3],"%Y-%m-%d")
                    if endDate > datetime.today():
                        listeMail.append({"lastName":res[0], "firstName":res[1], "mail":res[2]})
                        listeID.append(res[4])
    else:
        listeMail = []
        c.execute('SELECT lastName,firstName,email1,CONTACTS.endDate,ORDERS.endDate,RESOURCES.BoondID FROM RESOURCES JOIN CONTACTS,ORDERS,PROJECTS WHERE (CONTACTS.dataN="%s" OR CONTACTS.dataN1="%s" OR CONTACTS.dataN2="%s") AND CONTACTS.resource=RESOURCES.BoondID AND ORDERS.resource=RESOURCES.BoondID AND PROJECTS.client="%s" AND ORDERS.project=PROJECTS.BoondID;'%(respoId,respoId,respoId,clientId))
        for res in c:
            if res[5] not in listeID:
                endDate2 = datetime.strptime(res[4],"%Y-%m-%d")
                if res[3] == None or res[3] == '' or res[3] == ' ' and endDate2 > datetime.today():
                    listeMail.append({"lastName":res[0], "firstName":res[1], "mail":res[2]})
                    listeID.append(res[5])
                else:
                    endDate = datetime.strptime(res[3],"%Y-%m-%d")
                    if endDate > datetime.today() and endDate2 > datetime.today():
                        listeMail.append({"lastName":res[0], "firstName":res[1], "mail":res[2]})
                        listeID.append(res[5])
    conn.close()
    listeMail = sorted(listeMail, key = lambda k: k['lastName'])
    if single == 1:
        for m in listeMail:
            m['lastName'] = ''
            m['firstName'] = ''
    return listeMail

#Récupération de la liste des clients
def get_clients():
    conn = sqlite3.connect('/app/docaret.sqlite3')
    c = conn.cursor()

    c.execute('SELECT BoondID,name FROM COMPANIES ORDER BY name;')
    listeClient = []
    for comp in c:
        listeClient.append({'id': comp[0], 'name': decrypt(comp[1])})
    conn.close()
    return sorted(listeClient, key = lambda k: k['name'])

#Récupération de la liste des responsables chez les clients
def get_respoList():
    conn = sqlite3.connect('/app/docaret.sqlite3')
    c = conn.cursor()

    c.execute('SELECT dataN,dataN1,dataN2 FROM CONTACTS;')
    contactList = []
    for con in c:
        if con[0] not in contactList and con[0] != '':
            contactList.append(decrypt(con[0]))
        if con[1] not in contactList and con[0] != '':
            contactList.append(decrypt(con[1]))
        if con[2] not in contactList and con[0] != '':
            contactList.append(decrypt(con[2]))
    conn.close()
    contactList.sort()
    return contactList

#Export en PDF du certificat d'habilitation
def get_certif(habId):
    conn = sqlite3.connect("/app/docaret.sqlite3")
    c = conn.cursor()

    c.execute('SELECT * FROM HABILITATION WHERE id=%s;'%(habId))
    for k in c:
        hab = {
            "resId": k[1],
            "dgaRef": decrypt(k[7]),
            "certifNumber": decrypt(k[9]),
            "startDate": decrypt(k[4]),
            "endDate": decrypt(k[5]),
            "date": str(datetime.today()).split(' ')[0]
        }
    c.execute('SELECT lastName,firstName,dateOfBirth,placeOfBirth,title FROM RESOURCES WHERE BoondID=%s;' %(hab['resId']))
    for k in c:
        hab['lastName'] = decrypt(k[0])
        hab['firstName'] = decrypt(k[1])
        hab['dateOfBirth'] = decrypt(k[2])
        hab['placeOfBirth'] = decrypt(k[3])
        hab['title'] = decrypt(k[4])
    conn.close()
    return hab

#Récupération des données de TJM avec filtrage
def get_tjm(clientID,collabID):
    conn = sqlite3.connect('/app/docaret.sqlite3')
    c = conn.cursor()
    if clientID != '-1' and collabID != '-1':
        c.execute('SELECT BoondID,lastName,firstName FROM RESOURCES WHERE BoondID="%s";'%(collabID))
        listeCollab = []
        for res in c:
            listeCollab.append({"BoondID": res[0], "lastName": decrypt(res[1]), "firstName": decrypt(res[2])})
        listeTJM = []
        for res in listeCollab:
            c.execute('SELECT project,ORDERS.startDate,ORDERS.endDate,averageDailyPriceExcludingTax FROM ORDERS JOIN PROJECTS WHERE resource="%s" AND PROJECTS.BoondID=project AND PROJECTS.client="%s";'%(res['BoondID'],clientID))
            for ord in c:
                TJM = {
                    "lastName": res['lastName'],
                    "firstName": res['firstName'],
                    "startDate": decrypt(ord[1]),
                    "endDate": decrypt(ord[2]),
                    "TJM": ord[3],
                    "project": ord[0]
                }
                listeTJM.append(TJM)
        for ord in listeTJM:
            c.execute('SELECT name FROM COMPANIES JOIN PROJECTS WHERE PROJECTS.BoondID="%s" AND PROJECTS.client=COMPANIES.BoondID;'%(ord['project']))
            for comp in c:
                ord['client'] = decrypt(comp[0])
    elif clientID != '-1':
        c.execute('SELECT BoondID,lastName,firstName FROM RESOURCES;')
        listeCollab = []
        for res in c:
            listeCollab.append({"BoondID": res[0], "lastName": decrypt(res[1]), "firstName": decrypt(res[2])})
        listeTJM = []
        for res in listeCollab:
            c.execute('SELECT averageDailyPriceExcludingTax,ORDERS.startDate,ORDERS.endDate,project FROM ORDERS JOIN PROJECTS WHERE ORDERS.project=PROJECTS.BoondID AND PROJECTS.client="%s" AND ORDERS.resource="%s";'%(clientID,res['BoondID']))
            for ord in c:
                TJM = {
                    "lastName": res['lastName'],
                    "firstName": res['firstName'],
                    "startDate": decrypt(ord[1]),
                    "endDate": decrypt(ord[2]),
                    "TJM": ord[0],
                    "project": ord[3]
                }
                listeTJM.append(TJM)
        for ord in listeTJM:
            c.execute('SELECT name FROM COMPANIES JOIN PROJECTS WHERE PROJECTS.BoondID="%s" AND PROJECTS.client=COMPANIES.BoondID;'%(ord['project']))
            for comp in c:
                ord['client'] = decrypt(comp[0])
    elif collabID != '-1':
        c.execute('SELECT BoondID,lastName,firstName FROM RESOURCES WHERE BoondID="%s";'%(collabID))
        listeCollab = []
        for res in c:
            listeCollab.append({"BoondID": res[0], "lastName": decrypt(res[1]), "firstName": decrypt(res[2])})
        listeTJM = []
        for res in listeCollab:
            c.execute('SELECT project,startDate,endDate,averageDailyPriceExcludingTax FROM ORDERS WHERE resource="%s";'%(res['BoondID']))
            for ord in c:
                TJM = {
                    "lastName": res['lastName'],
                    "firstName": res['firstName'],
                    "startDate": decrypt(ord[1]),
                    "endDate": decrypt(ord[2]),
                    "TJM": ord[3],
                    "project": ord[0]
                }
                listeTJM.append(TJM)
        for ord in listeTJM:
            c.execute('SELECT name FROM COMPANIES JOIN PROJECTS WHERE PROJECTS.BoondID="%s" AND PROJECTS.client=COMPANIES.BoondID;'%(ord['project']))
            for comp in c:
                ord['client'] = decrypt(comp[0])
    else:
        c.execute('SELECT BoondID,lastName,firstName FROM RESOURCES;')
        listeCollab = []
        for res in c:
            listeCollab.append({"BoondID": res[0], "lastName": decrypt(res[1]), "firstName": decrypt(res[2])})
        listeTJM = []
        for res in listeCollab:
            c.execute('SELECT project,startDate,endDate,averageDailyPriceExcludingTax FROM ORDERS WHERE resource="%s";'%(res['BoondID']))
            for ord in c:
                TJM = {
                    "lastName": res['lastName'],
                    "firstName": res['firstName'],
                    "startDate": decrypt(ord[1]),
                    "endDate": decrypt(ord[2]),
                    "TJM": ord[3],
                    "project": ord[0]
                }
                listeTJM.append(TJM)
        for ord in listeTJM:
            c.execute('SELECT name FROM COMPANIES JOIN PROJECTS WHERE PROJECTS.BoondID="%s" AND PROJECTS.client=COMPANIES.BoondID;'%(ord['project']))
            for comp in c:
                ord['client'] = decrypt(comp[0])
    conn.close()
    return listeTJM
###############################################################################################











