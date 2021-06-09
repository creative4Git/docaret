# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.template import loader
from django.http import HttpResponse, HttpResponseRedirect
from django import template
import cgi
import pip._vendor.requests
from urllib import parse
from reportlab.pdfgen import canvas
import io
import threading
from django.shortcuts import redirect

from app.funtions import get_certif, get_modifyPage,get_names,get_info, get_respoList, send_modif, render_to_pdf, get_collab, search_collab, copy_db
from app.funtions import get_contact, get_contacts, validate_contact, modify_contact, get_projects, add_contact, close_contact
from app.funtions import get_habilitation, add_hab, get_hab, modify_hab, get_addresses, get_clients, get_respoList, get_certif
from app.funtions import fill_agencies, fill_companies, fill_contracts, fill_orders, fill_projects, fill_resources
from app.funtions import get_tjm, get_names_user, get_doc, modify_doc, get_names_userId

agencies_thread = threading.Thread(target=fill_agencies, name="Database Updater")
companies_thread = threading.Thread(target=fill_companies, name="Database Updater")
contracts_thread = threading.Thread(target=fill_contracts, name="Database Updater")
orders_thread = threading.Thread(target=fill_orders, name="Database Updater")
projects_thread = threading.Thread(target=fill_projects, name="Database Updater")
resources_thread = threading.Thread(target=fill_resources, name="Database Updater")
updateValue = 0
threadsValue = 1

@login_required(login_url="/login/")
def index(request):
    context = {}
    context['userLevel'] = 'user'
    if request.user.is_staff:
        context['userLevel'] = 'staff'
    if request.user.is_superuser:
        context['userLevel'] = 'admin'
    context['segment'] = 'index'
    html_template = loader.get_template( 'index.html' )
    return HttpResponse(html_template.render(context, request)) #


@login_required(login_url="/login/")
def pages(request):
    # All resource paths end in .html.
    # Pick out the html file name from the url. And load that template.
    context = {}
    context['userLevel'] = 'user'
    if request.user.is_staff:
        context['userLevel'] = 'staff'
    if request.user.is_superuser:
        context['userLevel'] = 'admin'
    
    try:
        #listeNames = get_names()
        urlRequest = request.path.split('/')[-1]
        ###################### CAS DE LA TABLE D'HABILITATION
        if urlRequest == 'tables.html':
            if not request.user.is_superuser:
                context={}
                
                context['updateState'] = "Vous n'avez pas les autorisations pour accéder à ces données."
                html_template = loader.get_template('index.html')
                return HttpResponse(html_template.render(context, request))
            
            
            context['segment'] = 'tables'
            context['listeCollab'] = get_habilitation()
            html_template = loader.get_template( 'tables.html' )
            return HttpResponse(html_template.render(context, request))
        ###################### CAS DE LA PAGE DE GARDE
        elif urlRequest == 'icons.html':
            if not request.user.is_superuser:
                lastName = str(request.user.last_name)
                firstName = str(request.user.first_name)
                listeNames = get_names_user(lastName,firstName)
                
                
                context['segment'] = 'icons'
                context['listeNames'] = listeNames
                html_template = loader.get_template( 'icons.html' )
                return HttpResponse(html_template.render(context, request))
            listeNames = get_names()
            
            
            context['segment'] = 'icons'
            context['listeNames'] = listeNames
            html_template = loader.get_template( 'icons.html' )
            return HttpResponse(html_template.render(context, request))
        ###################### CAS DE LA FICHE SIGNALITIQUE
        elif urlRequest[:12] == "details.html":
            listeNames = get_names()
            url = request.get_full_path()
            parameters = url.split('&')
            collabId = parameters[-4].split('=')[-1]
            timeSetting = parameters[-3].split('=')[-1]
            export = parameters[-2].split('=')[-1]
            searchBar = parameters[-1].split('=')[-1]
            name = get_names_userId(collabId)
            lastName = str(request.user.last_name)
            firstName = str(request.user.first_name)
            if (lastName == name['lastName'] and firstName == name['firstName']) or request.user.is_superuser:
                if searchBar == '0':
                    collabInfo = get_info(int(collabId),int(timeSetting))
                else:
                    collabId = search_collab(collabId,listeNames)
                    collabInfo = get_info(int(collabId),int(timeSetting))
                if export == '1':
                    if collabInfo['agency'] == 'YATIC':
                        collabInfo['borderColor'] = 'rgb(149, 115, 0)'
                        collabInfo['darkColor'] = 'rgb(255, 196, 0)'
                        collabInfo['lightColor'] = 'rgb(255, 218, 94)'
                    elif collabInfo['agency'] == 'TRACK AND LOCATE':
                        collabInfo['borderColor'] = 'rgb(120, 0, 0)'
                        collabInfo['darkColor'] = 'rgb(255, 0, 0)'
                        collabInfo['lightColor'] = 'rgb(255, 87, 87)'
                    else:
                        collabInfo['borderColor'] = 'rgb(0, 6, 88)'
                        collabInfo['darkColor'] = 'rgb(0, 76, 255)'
                        collabInfo['lightColor'] = 'rgb(126, 149, 255)'
                    return render_to_pdf('exportpdf.html',collabInfo)
                #if len(collabInfo) == 0:
                #    collabInfo = {"nom":'Empty',"prenom":'Empty'}
                context['segment'] = 'details'
                context['collabInfo'] = collabInfo
                context['timeSetting'] = timeSetting
                context['collabId'] = collabId
                html_template = loader.get_template('details.html')
                return HttpResponse(html_template.render(context, request))
            else:
                context['updateState'] = "Vous n'avez pas les autorisations pour accéder à ces données."
                html_template = loader.get_template('index.html')
                return HttpResponse(html_template.render(context, request))
        ###################### AFFICHAGE DES CONTACTS
        elif urlRequest[:14] == "newChoice.html":    # CHOIX DU COLLABORATEUR
            if not request.user.is_superuser:
                context['updateState'] = "Vous n'avez pas les autorisations pour accéder à ces données."
                html_template = loader.get_template('index.html')
                return HttpResponse(html_template.render(context, request))
            listeNames = get_names()
            
            
            context['segment'] = 'newChoice'
            context['listeNames'] = listeNames
            html_template = loader.get_template( 'newChoice.html' )
            return HttpResponse(html_template.render(context, request))
        elif urlRequest[:13] == "contacts.html":    # AFFICHAGE CONTACTS PAGE 1
            if not request.user.is_superuser:
                context['updateState'] = "Vous n'avez pas les autorisations pour accéder à ces données."
                html_template = loader.get_template('index.html')
                return HttpResponse(html_template.render(context, request))
            url = request.get_full_path()
            parameters = url.split('&')
            onglet = 1
            resId = parameters[0].split('=')[-1]
            contactList = get_contacts(resId,onglet)
            
            
            context['segment'] = 'contacts'
            context['collabId'] = resId
            context['contactList'] = contactList
            html_template = loader.get_template('contacts.html')
            return HttpResponse(html_template.render(context, request))
        elif urlRequest[:14] == "contacts2.html":    # AFFICHAGE CONTACTS PAGE 2
            if not request.user.is_superuser:
                
                context['updateState'] = "Vous n'avez pas les autorisations pour accéder à ces données."
                html_template = loader.get_template('index.html')
                return HttpResponse(html_template.render(context, request))
            url = request.get_full_path()
            parameters = url.split('&')
            onglet = 2
            resId = parameters[0].split('=')[-1]
            contactList = get_contacts(resId,onglet)
            
            
            context['collabId'] = resId
            context['segment'] = 'contacts2'
            context['contactList'] = contactList
            html_template = loader.get_template('contacts2.html')
            return HttpResponse(html_template.render(context, request))
        ###################### MODIFICATION DES CONTACTS
        elif urlRequest[:15] == "newContact.html":    # CONTACT
            if not request.user.is_superuser:
                lastName = str(request.user.last_name)
                firstName = str(request.user.first_name)
                listeNames = get_names_user(lastName,firstName)
                
                
                context['segment'] = 'newContact'
                context['listeNames'] = listeNames
                html_template = loader.get_template( 'newContact.html' )
                return HttpResponse(html_template.render(context, request))
            else:
                listeNames = get_names()
                
                
                context['segment'] = 'newContact'
                context['listeNames'] = listeNames
                html_template = loader.get_template( 'newContact.html' )
                return HttpResponse(html_template.render(context, request))
        elif urlRequest[:16] == "contactsMod.html":    # PAGE PERMETTANT LA MODIFICATION
            if not request.user.is_superuser:
                url = request.get_full_path()
                parameters = url.split('&')
                onglet = 1
                resId = parameters[0].split('=')[-1].split('%')[0]
                contactList = get_contacts(resId,onglet)
                
                context['collabId'] = resId
                context['segment'] = 'contactsMod'
                context['contactList'] = contactList
                html_template = loader.get_template('contactsMod.html')
                return HttpResponse(html_template.render(context, request))
            else:
                url = request.get_full_path()
                parameters = url.split('&')
                onglet = 1
                resId = parameters[0].split('=')[-1].split('%')[0]
                contactList = get_contacts(resId,onglet)
                
                
                context['collabId'] = resId
                context['segment'] = 'contactsMod'
                context['contactList'] = contactList
                html_template = loader.get_template('contactsMod.html')
                return HttpResponse(html_template.render(context, request))
        elif urlRequest[:12] == "validOK.html":    # VALIDATION CONTACT
            if not request.user.is_superuser:
                url = request.get_full_path()
                parameters = url.split('&')
                resId = parameters[0].split('=')[-1]
                conId = parameters[1].split('=')[-1]
                validate_contact(conId)
                
                context['collabId'] = resId
                context['segment'] = 'validOK'
                html_template = loader.get_template('validOK.html')
                return HttpResponse(html_template.render(context, request))
            else:
                url = request.get_full_path()
                parameters = url.split('&')
                resId = parameters[0].split('=')[-1]
                conId = parameters[1].split('=')[-1]
                validate_contact(conId)
                
                
                context['collabId'] = resId
                context['segment'] = 'validOK'
                html_template = loader.get_template('validOK.html')
                return HttpResponse(html_template.render(context, request))
        elif urlRequest[:18] == "modifyContact.html":    # MODIFICATION CONTACT
            if not request.user.is_superuser:
                url = request.get_full_path()
                parameters = url.split('&')
                resId = parameters[0].split('=')[-1]
                conId = parameters[1].split('=')[-1]
                projId = parameters[2].split('=')[-1]
                contact = get_contact(conId)
                
                context['collabId'] = resId
                context['conId'] = conId
                context['contact'] = contact
                context['projId'] = projId
                context['segment'] = 'modifyContact'
                html_template = loader.get_template('modifyContact.html')
                return HttpResponse(html_template.render(context, request))
            else:
                url = request.get_full_path()
                parameters = url.split('&')
                resId = parameters[0].split('=')[-1]
                conId = parameters[1].split('=')[-1]
                projId = parameters[2].split('=')[-1]
                contact = get_contact(conId)
                
                
                context['collabId'] = resId
                context['conId'] = conId
                context['contact'] = contact
                context['projId'] = projId
                context['segment'] = 'modifyContact'
                html_template = loader.get_template('modifyContact.html')
                return HttpResponse(html_template.render(context, request))
        elif urlRequest[:16] == "modifContOK.html":    # MODIFICATION VALIDE
            url = request.get_full_path()
            parameters = url.split('&')
            resId = parameters[0].split('=')[-1]
            conId = parameters[1].split('=')[-1]
            values=[]
            for val in parameters:
                values.append(val.split('=')[-1])
            modify_contact(conId,values)
            
            context['collabId'] = resId
            context['segment'] = 'modifContOK'
            html_template = loader.get_template('modifContOK.html')
            return HttpResponse(html_template.render(context, request))
        elif urlRequest[:17] == "enterContact.html":    # AJOUT CONTACT
            url = request.get_full_path()
            parameters = url.split('&')
            resId = parameters[0].split('=')[-1]
            projects = get_projects(resId)
            
            context['collabId'] = resId
            context['projects'] = projects
            context['segment'] = 'enterContact'
            html_template = loader.get_template('enterContact.html')
            return HttpResponse(html_template.render(context, request))
        elif urlRequest[:16] == "ajoutContOK.html":    # AJOUT CONTACT OK
            url = request.get_full_path()
            parameters = url.split('&')
            resId = parameters[0].split('=')[-1]
            values=[]
            for val in parameters:
                values.append(val.split('=')[-1])
            add_contact(values)
            
            context['collabId'] = resId
            context['segment'] = 'ajoutContOK'
            html_template = loader.get_template('ajoutContOK.html')
            return HttpResponse(html_template.render(context, request))
        elif urlRequest[:15] == "endContact.html":    # CLOTURER CONTACT
            url = request.get_full_path()
            parameters = url.split('&')
            resId = parameters[0].split('=')[-1]
            conId = parameters[1].split('=')[-1]
            endDate = parameters[2].split('=')[-1]
            close_contact(conId,endDate)
            
            context['collabId'] = resId
            context['segment'] = 'endContact'
            html_template = loader.get_template('endContact.html')
            return HttpResponse(html_template.render(context, request))
        ###################### CAS DE L'HABILITATION
        elif urlRequest[:11] == "newHab.html":    # AJOUT HABILITATION
            if not request.user.is_superuser:
                context['updateState'] = "Vous n'avez pas les autorisations pour accéder à ces données."
                html_template = loader.get_template('index.html')
                return HttpResponse(html_template.render(context, request))
            listeNames = get_names()
            
            context['listeNames'] = listeNames
            html_template = loader.get_template('newHab.html')
            return HttpResponse(html_template.render(context, request))
        elif urlRequest[:13] == "newHabOK.html":    # AJOUT VALIDE
            if not request.user.is_superuser:
                context['updateState'] = "Vous n'avez pas les autorisations pour accéder à ces données."
                html_template = loader.get_template('index.html')
                return HttpResponse(html_template.render(context, request))
            url = request.get_full_path()
            parameters = url.split('&')
            resId = parameters[0].split('=')[-1]
            sendDate = parameters[1].split('=')[-1]
            startDate = parameters[2].split('=')[-1]
            endDate = parameters[3].split('=')[-1]
            docRef = parameters[4].split('=')[-1]
            dgaRef = parameters[5].split('=')[-1]
            state = parameters[6].split('=')[-1]
            certifNumber = parameters[7].split('=')[-1]
            add_hab(resId,sendDate,startDate,endDate,docRef,dgaRef,state,certifNumber)
            
            html_template = loader.get_template('newHabOK.html')
            return HttpResponse(html_template.render(context, request))
        elif urlRequest[:11] == "modHab.html":    # MODIFICATION
            if not request.user.is_superuser:
                context['updateState'] = "Vous n'avez pas les autorisations pour accéder à ces données."
                html_template = loader.get_template('index.html')
                return HttpResponse(html_template.render(context, request))
            url = request.get_full_path()
            parameters = url.split('&')
            habId = parameters[0].split('=')[-1].split('%')[0]
            hab = get_hab(habId)
            
            context['hab'] = hab
            html_template = loader.get_template('modHab.html')
            return HttpResponse(html_template.render(context, request))
        elif urlRequest[:13] == "modHabOK.html":    # MODIFICATION VALIDE
            if not request.user.is_superuser:
                context['updateState'] = "Vous n'avez pas les autorisations pour accéder à ces données."
                html_template = loader.get_template('index.html')
                return HttpResponse(html_template.render(context, request))
            url = request.get_full_path()
            parameters = url.split('&')
            habId = parameters[0].split('=')[-1]
            sendDate = parameters[1].split('=')[-1]
            startDate = parameters[2].split('=')[-1]
            endDate = parameters[3].split('=')[-1]
            docRef = parameters[4].split('=')[-1]
            dgaRef = parameters[5].split('=')[-1]
            state = parameters[6].split('=')[-1]
            certifNumber = parameters[7].split('=')[-1]
            actif = parameters[8].split('=')[-1]
            modify_hab(habId,actif,sendDate,startDate,endDate,docRef,dgaRef,state,certifNumber)
            
            html_template = loader.get_template('modHabOK.html')
            return HttpResponse(html_template.render(context, request))
        ###################### TABLEAU ADRESSES MAIL
        elif urlRequest[:9] == "mail.html":
            if not request.user.is_superuser:
                context['updateState'] = "Vous n'avez pas les autorisations pour accéder à ces données."
                html_template = loader.get_template('index.html')
                return HttpResponse(html_template.render(context, request))
            url = request.get_full_path()
            parameters = url.split('&')
            
            context['listeClient'] = get_clients()
            context['listeRespo'] = get_respoList()
            if len(parameters) == 1 or len(parameters) == 2:
                if parameters[0].split('=')[-1] == '/mail.html':
                    listeMail = get_addresses('-1','-1',0)
                    context['listeMail'] = listeMail
                    html_template = loader.get_template('mail.html')
                else:
                    client = parameters[0].split('=')[-1]
                    respo = parameters[1].split('=')[-1]
                    listeMail = get_addresses(client,respo,0)
                    context['listeMail'] = listeMail
                    html_template = loader.get_template('mail.html')
                return HttpResponse(html_template.render(context, request))
            elif len(parameters) == 3:
                if parameters[0].split('=')[-1] == '/mail.html':
                    listeMail = get_addresses('-1','-1',1)
                    context['listeMail'] = listeMail
                    html_template = loader.get_template('mail.html')
                else:
                    client = parameters[0].split('=')[-1]
                    respo = parameters[1].split('=')[-1]
                    listeMail = get_addresses(client,respo,1)
                    context['listeMail'] = listeMail
                    html_template = loader.get_template('mail.html')
                return HttpResponse(html_template.render(context, request))
        ###################### TABLEAU/FILTRAGE TJM
        elif urlRequest[:8] == "tjm.html":
            if not request.user.is_superuser:
                context['updateState'] = "Vous n'avez pas les autorisations pour accéder à ces données."
                html_template = loader.get_template('index.html')
                return HttpResponse(html_template.render(context, request))
            url = request.get_full_path()
            parameters = url.split('&')
            
            context['listeClient'] = get_clients()
            context['listeRespo'] = get_names()
            if len(parameters) == 2:
                clientID = parameters[0].split('?')[-1].split('=')[-1]
                collabID = parameters[1].split('=')[-1]
                listeCollab = get_tjm(clientID,collabID)
                context['listeCollab'] = listeCollab
                html_template = loader.get_template('tjm.html')
                return HttpResponse(html_template.render(context, request))
            elif parameters[0] == '/tjm.html':
                listeCollab = get_tjm(-1,-1)
                context['listeCollab'] = listeCollab
                html_template = loader.get_template('tjm.html')
                return HttpResponse(html_template.render(context, request))

            url = request.get_full_path()
            #nom=YATIC&mail1=finances%40yatic.fr&prenom=Finances&address=&mail2=+&dob=&postc=&town=&phone1=&pob=&ssn=&urgenceC=&urgenceT=
            url_query = parse.parse_qs(parse.urlparse(url).query)
            keys = ["id","lastName", "mail1","firstName","address","mail2","dateOfBirth","placeOfBirth","postcode","town","phone1","healthCareNumber","urgenceC","urgenceT"]  # etc
            info = {key: (url_query[key][0] if key in url_query else "") for key in keys}
            response = send_modif(info)
            context['segment'] = 'modify'
            context['response'] = response.text
            html_template = loader.get_template('modifOK.html')
            return HttpResponse(html_template.render(context, request))
        ###################### AUTRES 
        elif urlRequest[:12] == 'loading.html':    # PAGE DE CHARGEMENT
            global updateValue
            global threadsValue
            global agencies_thread
            global companies_thread
            global contracts_thread
            global orders_thread
            global projects_thread
            global resources_thread
            if threadsValue == 1:
                agencies_thread = threading.Thread(target=fill_agencies, name="Database Updater")
                companies_thread = threading.Thread(target=fill_companies, name="Database Updater")
                contracts_thread = threading.Thread(target=fill_contracts, name="Database Updater")
                orders_thread = threading.Thread(target=fill_orders, name="Database Updater")
                projects_thread = threading.Thread(target=fill_projects, name="Database Updater")
                resources_thread = threading.Thread(target=fill_resources, name="Database Updater")
                threadsValue = 0
            if updateValue == 0:
                agencies_thread.start()
                companies_thread.start()
                contracts_thread.start()
                orders_thread.start()
                projects_thread.start()
                resources_thread.start()
                updateValue = 1
            updateState = 0
            if agencies_thread.is_alive():
                agenciesState = 'en cours de chargement'
            else:
                agenciesState = 'Chargement terminé'
                updateState += 1
            if companies_thread.is_alive():
                companiesState = 'en cours de chargement'
            else:
                companiesState = 'Chargement terminé'
                updateState += 1
            if contracts_thread.is_alive():
                contractsState = 'en cours de chargement'
            else:
                contractsState = 'Chargement terminé'
                updateState += 1
            if orders_thread.is_alive():
                ordersState = 'en cours de chargement'
            else:
                ordersState = 'Chargement terminé'
                updateState += 1
            if projects_thread.is_alive():
                projectsState = 'en cours de chargement'
            else:
                projectsState = 'Chargement terminé'
                updateState += 1
            if resources_thread.is_alive():
                resourcesState = 'en cours de chargement'
            else:
                resourcesState = 'Chargement terminé'
                updateState += 1
            if updateState == 6:
                updateValue = 0
                threadsValue = 1
                copy_db()
                context['updateState'] = 'Base de données mise à jour.'
                html_template = loader.get_template('index.html')
                return HttpResponse(html_template.render(context, request))
            else:
                context['agenciesState'] = agenciesState
                context['companiesState'] = companiesState
                context['contractsState'] = contractsState
                context['ordersState'] = ordersState
                context['projectsState'] = projectsState
                context['resourcesState'] = resourcesState
                html_template = loader.get_template('loading.html')
                return HttpResponse(html_template.render(context, request))
        elif urlRequest[:14] == "certifpdf.html":    #EXPORT PDF DU CERTIFICAT
            url = request.get_full_path()
            parameters = url.split('&')
            habId = parameters[0].split('=')[-1].split('%')[0]
            hab = get_certif(habId)
            return render_to_pdf('certifpdf.html',hab)
        elif urlRequest[:11] == 'modDoc.html':
            url = request.get_full_path()
            parameters = url.split('&')
            resId = parameters[0].split('=')[-1]
            doc = get_doc(resId)
            
            context['collabId'] = resId
            context['doc'] = doc
            html_template = loader.get_template('modDoc.html')
            return HttpResponse(html_template.render(context, request))
        elif urlRequest[:13] == 'modDocOK.html':
            url = request.get_full_path()
            parameters = url.split('&')
            docId = parameters[0].split('=')[-1]
            num1 = parameters[1].split('=')[-1]
            startDate1 = parameters[2].split('=')[-1]
            endDate1 = parameters[3].split('=')[-1]
            num2 = parameters[4].split('=')[-1]
            startDate2 = parameters[5].split('=')[-1]
            endDate2 = parameters[6].split('=')[-1]
            modify_doc(docId,num1,startDate1,endDate1,num2,startDate2,endDate2)
            
            html_template = loader.get_template('modDocOK.html')
            return HttpResponse(html_template.render(context, request))

        ###############################################################
        else:
            
            context['segment'] = urlRequest
            html_template = loader.get_template( urlRequest )
            return HttpResponse(html_template.render(context, request))
        
    except template.TemplateDoesNotExist:
        
        html_template = loader.get_template( 'page-404.html' )
        return HttpResponse(html_template.render(context, request))

    #except:
        
        html_template = loader.get_template( 'page-500.html' )
        return HttpResponse(html_template.render(context, request))

