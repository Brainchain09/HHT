from bs4 import BeautifulSoup
import requests
import json
import re


def isTable(tag):
    return tag.name=="table" or not tag.find("table") is None

def correctString(s):
    while s[0]==" " :
        s=s[1:]
    while s[-1]==" " :
        s=s[:-1]
    
    return s.replace("\n", "").replace("\xa0", " ")


def isPartial(t) :
    r=re.search(r'\([^)]*\)', t).group()
    return "partie" in r
        
def splitList(t) :
    t=t.replace(" du ", " Le ")
    t=t.replace(" de ", " ")
    t=t.replace(" d'", " ")
    f=t.split(" et ")
    if len(f)==1 :
        f=t.split(" et de ")
    if len(f)>1 :
        f2=f[0].split(", ")
        f2.append(f[1])
    else :
        f2=f
    return f2


def beforeAfter(string) :
    string=re.sub("\. ."," ", string)
    reg="((La | Le) )?[A-Z]([^ .]|[a-z])([^ .]|[a-z])([^ .]|[a-z])*"
    print(string)
    find=list(re.finditer(reg, string[1:]))
    print(find)
    before=[]
    after=[]
    second=False
    final=False
    for k in range(len(find)) :
        if not final :
            b=find[k].end()
            if second :
                before.append(find[k].group())
            else :
                after.append(find[k].group())
            if k+1<len(find) :
                e=find[k+1].start()
                s=string[b:e]
                if len(s.split(" "))>3 :
                    final=second
                    second=True
    return [before, after]          

def romanToInt(s):
      """
      :type s: str
      :rtype: int
      """
      roman = {'I':1,'V':5,'X':10,'L':50,'C':100,'D':500,'M':1000,'IV':4,'IX':9,'XL':40,'XC':90,'CD':400,'CM':900}
      i = 0
      num = 0
      while i < len(s):
         if i+1<len(s) and s[i:i+2] in roman:
            num+=roman[s[i:i+2]]
            i+=2
         else:
            #print(i)
            num+=roman[s[i]]
            i+=1
      return num


def parenthesisClean(t) :
        return re.sub(r'\([^)]*\)', '', t)

#Ajoute les fusions de villes sous forme [nomActuel]  [VilleFusionée1,VilleFusionée2...] ... [Date Decision] [Date Effet]
def parseTabFusion1toMult(soup, geo) :
    #colDateDeci = numéro de la colone de Date Decision ,colDateEffet = numéro de la colone de Date d'Effet
    try :
        header=soup.find("thead").find_all("th")
        count=0
        for case in header :
            if case.get_text()=="Date d'effet" :
                colDateEffet=count
            elif ("Date " in case.get_text() and "décision" in case.get_text()) :
                colDateDeci=count
            count+=1
        found=True
    except :
        found=False
    lines=soup.find("tbody").find_all("tr")
    remaining=0
    current={}
    for s in lines :
        if not found :
            count=0
            for case in s.find_all("th") :
                if "Date d'effet" in case.get_text()  :
                    colDateEffet=count
                elif ("Date" in case.get_text() or "Décision" in case.get_text()) :
                    colDateDeci=count
                count+=1
            try : 
                colDateEffet
            except UnboundLocalError :
                colDateEffet=colDateDeci
            found=True
        else :
            if remaining==0 :
                try :
                    if current!={}:
                        geo.append(current)
                    current={}
                    counter=0
                    cases=s.find_all("td")
                    for c in cases :
                            try:
                                current["type"]="Fusion"
                                if counter==0 :
                                    remaining=int(c["rowspan"])-1
                                    current["after"]=[correctString(c.get_text())]
                                elif counter==1 :
                                    current["before"]=[correctString(c.get_text())]
                                elif c.has_attr("colspan") and int(c["colspan"])==2 and counter==colDateEffet-1 :
                                    date=re.search("[12][07-9][0-9][0-9]",c.get_text())
                                    current["date"]=int(date.group())
                                elif counter==colDateEffet and "date" not in current.keys() :
                                    date=re.search("[12][07-9][0-9][0-9]",c.get_text())
                                    current["date"]=int(date.group())
                                counter+=1
                            except AttributeError :
                                date=re.search("[Aa]n [VIX]+",c.get_text())
                                current["date"]=1791+romanToInt(date.group()[3:])
                except KeyError :
                     pass
                #print(current)
            else :
                remaining-=1
                current["before"].append(correctString(s.find("td").get_text()))        
    return geo  


def parseTabDemembrement(soup, geo) :
    #print(soup)
    #colDateDeci = numéro de la colone de Date Decision ,colDateEffet = numéro de la colone de Date d'Effet
    found=False
    lines=soup.find("tbody").find_all("tr")
    remaining=0
    current={}
    for s in lines :
            if not found :
                count=0
                for c in s.find_all("th") :
                    #print(c.get_text())
                    if "anciennes communes" in c.get_text() or "Anciennes communes" in c.get_text() or "Ancienne commune" in c.get_text() or "Commune affectée" in c.get_text() or "Commune concernée" in c.get_text() or "Commune supprimée" in c.get_text():
                        AncienNom=count
                    if "Nouvelle commune" in c.get_text() or "nouvelle commune" in c.get_text()  or "commune créée" in c.get_text() or correctString(c.get_text())=="Nom" or "Communes restaurées" in c.get_text():
                        new=count
                    if "Date d'effet" in c.get_text() or "Date d’effet" in c.get_text() or "Date (et nature)" in c.get_text() or "Décision" in c.get_text()or "Date" in c.get_text() :
                        date=count
                    count+=1
                print(date)
                found=True
            else :
                print(remaining) 
                if remaining==0 :
                    if current!={}:
                        geo.append(current)
                    current={}
                    counter=0
                    cases=s.find_all("td")
                    issue=0
                    for c in cases :
                        if c.has_attr("rowspan") and remaining==0 and (counter==AncienNom or counter==new) :
                            remaining=int(c["rowspan"])-1
                            issue=counter
                        counter+=1
                    counter=0
                    for c in cases :
                            if counter==new :
                                print(c.get_text())
                                current["after"]=splitList(correctString(c.get_text()))
                            elif counter==AncienNom :
                                    current["before"]=splitList(correctString(c.get_text()))
                            elif counter==2 :
                                current["type"]=correctString(c.get_text())
                            elif c.has_attr("colspan") and counter==(date-1) :
                                try :
                                    dateV=re.search("[12][07-9][0-9][0-9]",c.get_text())
                                    current["date"]=int(dateV.group())
                                except AttributeError :
                                    print(c.get_text())
                                    dateV=re.search("[Aa]n [VIX]+",c.get_text())
                                    current["date"]=1791+romanToInt(dateV.group()[3:])
                            elif counter==date and "date" not in current.keys():
                                try :
                                    dateV=re.search("[12][07-9][0-9][0-9]",c.get_text())
                                    current["date"]=int(dateV.group())
                                except AttributeError :
                                    print(c.get_text())
                                    dateV=re.search("[Aa]n [VIX]+", c.get_text())
                                    current["date"]=1791+romanToInt(dateV.group()[3:])
                            counter+=1
                    if "type" not in current.keys() :
                        current["type"]="Création"
                else :
                    remaining-=1
                    if issue==new :
                        current["before"].append(correctString(s.find("td").get_text())) 
                    elif issue ==AncienNom :
                        current["after"].append(correctString(s.find("td").get_text())) 
    return geo     

def parseTabName(soup, geo) :
    #colDateDeci = numéro de la colone de Date Decision ,colDateEffet = numéro de la colone de Date d'Effet
    found=False
    lines=soup.find("tbody").find_all("tr")
    remaining=0
    current={}
    for s in lines :
            if not found :
                count=0
                for c in s.find_all("th") :
                    #print(c.get_text())
                    if "Ancien nom" in c.get_text() or "Ancien nom" in c.get_text():
                        AncienNom=count
                    if "Nouveau nom" in c.get_text() or "Nom" in c.get_text() :
                        new=count
                    if "Date d'effet" in c.get_text() or "Date d’effet" in c.get_text() or "Date (et nature)" in c.get_text() or "Date" in  c.get_text() or "Décision" in  c.get_text() :
                        date=count
                    count+=1
                found=True
            else : 
                    current={"type": "Name"}
                    cases=s.find_all("td")
                    counter=0
                    for c in cases :
                            if counter==AncienNom :
                                current["before"]=[correctString(c.get_text())]
                            elif counter==new :
                                current["after"]=[correctString(c.get_text())]
                            elif remaining!=0 :
                                current["date"]=int(dateval.group())
                            elif counter==date or(counter==len(cases)-1 and date>len(cases)-1) and remaining==0:
                                if c.has_attr("rowspan") :
                                    remaining=int(c["rowspan"])-1
                                #print(c.get_text())
                                try :
                                    dateval=re.search("[12][07-9][0-9][0-9]",c.get_text())
                                    current["date"]=int(dateval.group())
                                except AttributeError :
                                    try : 
                                        dateval=re.search("[Aa]n [VIX]+",c.get_text())
                                        current["date"]=1791+romanToInt(dateval.group()[3:])
                                    except AttributeError :
                                        current["date"]=1793
                            counter+=1
                    remaining=max(0, remaining-1)
                    geo.append(current)

    return geo  


def parseFusionList(soup, geo) :
    #colDateDeci = numéro de la colone de Date Decision ,colDateEffet = numéro de la colone de Date d'Effet
    listNewDate=[]
    while soup.next_sibling.name!="h2" :
        soup=soup.next_sibling
        if soup.name=="h3" :
            try:
                dateval=re.search("[12][07-9][0-9][0-9]",soup.get_text())
                date=int(dateval.group())
            except AttributeError :
                if "inconnu" in soup.get_text() :
                    date=1793
                else :
                    date=-1
            geo=geo+listNewDate
            listNewDate=[]
        elif soup.name=="ul" and date>0 :
            for line in soup.find_all("li") :
                text=correctString(line.get_text())
                #print(text)
                new=("*" in text)
                if new :
                    text=text.split("*")[0]
                ba=text.split(" > ")
                if len(ba)==1 :
                    ba=text.split("> ")
                #print(ba)
                i=0
                Found=False
                try :
                    while i<len(listNewDate) and not Found :
                        if listNewDate[i]["after"][0]==ba[1] :
                            listNewDate[i]["before"].append(ba[0])
                            Found=True
                        i+=1
                    if not Found :
                        newChange={"date" : date, "type" : "Fusion", "after" :[ba[1]], "before" :[ba[0]]}
                        if not new :
                            newChange["before"].append(ba[1])
                        listNewDate.append(newChange)
                except IndexError :
                    pass
    return geo 


def parseFusionMocheList(soup, geo) :
    #colDateDeci = numéro de la colone de Date Decision ,colDateEffet = numéro de la colone de Date d'Effet
    while soup.next_sibling.name!="h2" :
        soup=soup.next_sibling
        if soup.name=="h3" :
            try:
                dateval=re.search("[12][07-9][0-9][0-9]",soup.get_text())
                date=int(dateval.group())
            except AttributeError :
                if "inconnu" in soup.get_text() :
                    date=1793
                else :
                    date=-1
        elif soup.name=="ul" and date>0 :
            for line in soup.find_all("li") :
                analyse=beforeAfter(correctString(line.get_text()))
                if len(analyse[0])==1 :
                    analyse[1]+=analyse[0]
                newChange={"date" : date, "type" : "Fusion", "after" :analyse[1], "before" :analyse[0]}
                geo.append(newChange)
    return geo


def parseDemMocheList(soup, geo) :
    #colDateDeci = numéro de la colone de Date Decision ,colDateEffet = numéro de la colone de Date d'Effet
    while soup.next_sibling.name!="h2" :
        soup=soup.next_sibling
        if soup.name=="h3" :
            try:
                dateval=re.search("[12][07-9][0-9][0-9]",soup.get_text())
                date=int(dateval.group())
            except AttributeError :
                if "inconnu" in soup.get_text() :
                    date=1793
                else :
                    date=-1
        elif soup.name=="ul" and date>0 :
            for line in soup.find_all("li") :
                analyse=beforeAfter(correctString(line.get_text()))
                newChange={"date" : date, "type" : "Rétablissement", "after" :analyse[1], "before" :analyse[0]}
                geo.append(newChange)
    return geo


def parseListName(soup, geo) :
    #colDateDeci = numéro de la colone de Date Decision ,colDateEffet = numéro de la colone de Date d'Effet
    listNewDate=[]
    while soup.next_sibling.name!="h2" :
        soup=soup.next_sibling
        if soup.name=="h3" :
            try :
                dateval=re.search("[12][07-9][0-9][0-9]",soup.get_text())
                date=int(dateval.group())
            except AttributeError :
                date=1790
            geo=geo+listNewDate
            listNewDate=[]
        elif soup.name=="ul" :
            for line in soup.find_all("li") :
                text=correctString(line.get_text())
                ba=text.split(" > ")
                if len(ba)==1 :
                    ba=text.split(" >, ")
                #print(ba)
                newChange={"date" : date, "type" : "Name", "after" :[ba[1]], "before" :[ba[0]]}
                listNewDate.append(newChange)
    geo=geo+listNewDate
    return geo 


def parseListNameMoche(soup, geo) :
    #colDateDeci = numéro de la colone de Date Decision ,colDateEffet = numéro de la colone de Date d'Effet
    listNewDate=[]
    while soup.next_sibling.name!="h2" :
        soup=soup.next_sibling
        if soup.name=="h3" :
            try :
                dateval=re.search("[12][07-9][0-9][0-9]",soup.get_text())
                date=int(dateval.group())
            except AttributeError :
                date=1790
            geo=geo+listNewDate
            listNewDate=[]
        elif soup.name=="ul" :
            for line in soup.find_all("li") :
                text=correctString(line.get_text())
                ba=text.split(" devient ")
                print(ba)
                ba[1]=re.search("((La | Le) )?[A-Z][^ .]*",ba[1]).group()
                newChange={"date" : date, "type" : "Name", "after" :[ba[1]], "before" :[ba[0]]}
                listNewDate.append(newChange)
    geo=geo+listNewDate
    return geo 


def parseCreationSentence(soup, geo) :
    listNewDate=[]
    while soup.next_sibling.name!="h2" :
        soup=soup.next_sibling
        if soup.name=="h3" :
            try :
                dateval=re.search("[12][07-9][0-9][0-9]",soup.get_text())
                date=int(dateval.group())
            except AttributeError :
                date=1793
            geo=geo+listNewDate
            print(geo)
            listNewDate=[]
        elif soup.name=="ul" :
            for line in soup.find_all("li") :
                text=correctString(line.get_text())
                typeD="Rétablissement"
                if " par démembrement d" in text :
                    r=re.split(" par démembrement d[^A-ZÉÊÈÇ]*", text)
                    after=[r[0]]
                    before=splitList(r[1])
                elif " à partir de parcelles d" in text :
                    r=re.split(" à partir de parcelles d[^A-ZÉÊÈÇ]*", text)
                    after=[r[0]]
                    before=splitList(r[1])
                elif "à partir" in text or "à la suite" in text:
                    if ", commune supprimée" in text :
                        text=text[:-len(", commune supprimée")]
                        typeD+=" et suppression"
                    text=text.replace(" du ", " de Le ")
                    text=text.replace(" des ", " de Les ")
                    sp=text.split(" à partir de ")
                    #print(text)
                    if len(sp)==1 :
                        sp=text.split(" à partir d'")
                    if len(sp)==1 :
                        sp=text.split(" à la suite d'")
                    if "Rétablissement de " in sp[0] :
                        l=len("Rétablissement de ")
                    elif "Rétablissement d'" in sp[0] :
                        l=len("Rétablissement d'")
                    elif "Création de " in sp[0] :
                        l=len("Création de ")
                    elif "Rétablissement du " in sp[0] :
                        sp[0]="Le "+sp[0][len("Rétablissement du "):]
                        l=0
                    after=splitList(sp[0][l :])
                    before=[sp[1]]
                elif " par scission de la commune de " in text :
                    r=re.split(" par scission de la commune d[^A-Z]*", text)
                    after=[r[0]]
                    before=splitList(r[1])
                else :
                    print("Missing !!!"+" "+text)
                    before=[input()]
                    after=[text]
                listNewDate.append({"date" : date, "type" : typeD, "before" : before, "after" : after})

    return geo 

                    

def parseTabFusionMoche(soup, geo) :
    #colDateDeci = numéro de la colone de Date Decision ,colDateEffet = numéro de la colone de Date d'Effet
    found=False
    lines=soup.find("tbody").find_all("tr")
    current={}
    for s in lines :
            if not found :
                count=0
                for c in s.find_all("th") :
                    #print(c.get_text())
                    if "anciennes communes" in c.get_text() or "Anciennes communes" in c.get_text():
                        AncienNom=count
                    if "Nouvelle commune" in c.get_text() or "nouvelle commune" in c.get_text() :
                        new=count
                    if "Date d'effet" in c.get_text() or "Date d’effet" in c.get_text() or "Date (et nature)" in c.get_text() or "Date" in c.get_text() :
                        date=count
                    count+=1
                found=True
            else : 
                    current={"type": "Fusion"}
                    cases=s.find_all("td")
                    counter=0
                    for c in cases :
                            if counter==AncienNom :
                                current["before"]=splitList(correctString(c.get_text()))
                            elif counter==new :
                                current["after"]=[correctString(c.get_text())]
                            elif counter==date :
                                #print(c.get_text())
                                dateval=re.search("[12][07-9][0-9][0-9]",c.get_text())
                                current["date"]=int(dateval.group())
                            counter+=1
                    geo.append(current)

    return geo   

def isFusion(tag) :
    return (tag.name=="h2" or tag.name=="h3") and "Fusion" in tag.get_text()

def isCreation(tag) :
    return (tag.name=="h2" or tag.name=="h3") and ("Création" in tag.get_text() or "Restaurations" in tag.get_text()) and "modifications des frontières du pays" not in tag.get_text()

def isNameChange(tag) :
    return (tag.name=="h2" or tag.name=="h3") and ("nom officiel" in tag.get_text() or "Changements de nom" in tag.get_text()or "noms officiels" in tag.get_text())

def isLimit(tag) :
    return (tag.name=="h2" or tag.name=="h3") and " limites " in tag.get_text()

def isLink(tag) :
    return tag.has_attr("href")

def checkShape(soup, number, dico) :
        print(number)
        geo=[]
        if number not in ["22", "26", "27", "28", "39", "40", "43", "50", "51", "52", "53", "55", "56", "58", "62", "68", "69", "70","71", "72", "74", "75", "76", "77", "81","88", "89", "90", "91"] :
    #try :
            status="Fusion"
            fusionTable=soup.find(isFusion).find_next_sibling("table")
            if number=="15" :
                parseTabFusionMoche(fusionTable, geo)
            else :
                parseTabFusion1toMult(fusionTable, geo)
            status="Creation"
            creationTable=soup.find(isCreation).find_next_sibling("table")
            parseTabDemembrement(creationTable, geo)
            status="Name"
            nameTable=soup.find(isNameChange).find_next_sibling(isTable)
            parseTabName(nameTable, geo)
            #status="Limits"
            #limitTable=soup.find(isLimit).find_next_sibling("table")
        elif number=="88" :
            fusionTitle=soup.find(isFusion)
            parseFusionMocheList(fusionTitle, geo)
            creationTable=soup.find(isCreation)
            parseDemMocheList(creationTable, geo)
            nameTable=soup.find(isNameChange)
            geo=parseListNameMoche(nameTable, geo)
        elif number!="76" :
            fusionTitle=soup.find(isFusion)
            geo=parseFusionList(fusionTitle, geo)
            creationTable=soup.find(isCreation)
            geo=parseCreationSentence(creationTable, geo)
            nameTable=soup.find(isNameChange)
            geo=parseListName(nameTable, geo)
        dico[number]=geo
        




    #except :
        #print("Bad shape detected for "+number+" : "+status)


def getSoup(url) :
    headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '3600',
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'
    }
    req = requests.get(url, headers)
    soup = BeautifulSoup(req.content, "html.parser")
    return soup



file=open("scanOldLists.html", 'rb')
soup = BeautifulSoup(file, "html.parser")
integer=1
dico={}
for s in soup.find_all(isLink):
    listT=getSoup("https://fr.wikipedia.org"+s["href"])
    checkShape(listT,str(integer), dico)
    integer+=1


def serializeJSON(geo,fileName) :
    
    out_file = open(fileName, "w")
    
    json.dump(geo, out_file, indent = 6)
    out_file.close()

serializeJSON(dico, "results.json")
                

