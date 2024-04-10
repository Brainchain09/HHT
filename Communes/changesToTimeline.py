from bs4 import BeautifulSoup
import requests
import json
import re
import traceback


class block :

    count=0

    def __init__(self, name="PPP"+str(count )) :
        self.name=name
        self.sons=[]
    def split(self, count) :
        if len(self.sons)==0 :
            sp=block("BBB"+str(count))
            newSp=block(self.name)
            self.addSon(sp)
            self.addSon(newSp)
            return (newSp, sp)
        else :
            next=self.sons[0].split(count)
            newblock=block(self.name)
            newblock.addSon(next[0])
            for bl in self.sons [1:]:
                newblock.addSon(bl)
            
            return (newblock, next[1])

    def removefind(self, tree) :
        found=-1
        count=0
        for t in self.sons :
            if t!=tree and found ==-1 :
                if t.removefind(tree)!=-1 :
                    found=count
            elif t==tree :
                found=count
            count+=1
        return found
    
    def removeRec(self, tree) :
        k=self.removefind(tree)
        if k==-1 :
            newBlock=self
        else :
            newBlock=block(self.name)
            count=0
            for t in self.sons :
                if count==self.removefind(tree) :
                    if t!=tree :
                        toAdd=t.removeRec(tree)
                        if toAdd is not None :
                            newBlock.addSon(toAdd)
                else :
                    newBlock.addSon(t)
                count+=1
        if len (newBlock.sons)==0 :
            newBlock=None
        return newBlock
    
    def remove(self, tree) :
        n=self.name
        l=self.removeRec(tree)
        if l is None :
            l=block(n)
        return l
        
    
    def reduce(self) :
        l=[]
        if len(self.sons)==0 :
            if "PPP" in self.name :
                return [self.name]
            else :
                return ["BB_"+self.name]
        else :
            for t in self.sons :
                newL=t.reduce()
                l+=newL
        return l




    def addSon(self, son) :
        
        if type(son)==block:
            toAdd=son
            while (len(toAdd.sons)==1) :
                toAdd=toAdd.sons[0]
            self.sons.append(toAdd)
        else :
            raise Exception("Wrong Type", "Tip")
    
    def resolve(self) :
        result=[self]
        for sub in self.sons :
            result.append(sub)
            result+=sub.resolve()
        return result
    
    def core(self) :
        if len(self.sons==0) :
            return self
        else :
            return self.core()

    def find(self, name) :
        for sub in self.sons :
            sp=sub.name.split("_")
            if len(sp)>1 and sp[1]==name :
                return sub
            l=sub.find(name)
            if not (l is None) :
                return l
        return None
    



def newGeometry(name) :
    l=block(name)
    #l.addSon(block(name))
    return l

    
def isTable(tag):
    return tag.name=="table" or not tag.find("table") is None

def correctString(s):
    while s[0]==" " :
        s=s[1:]
    while s[-1]==" " :
        s=s[:-1]
    
    return s.replace("\n", "").replace("\xa0", " ").replace(" -", "")
  
def beforeAfter(string) :
    string=re.sub("\. ."," ", string)
    reg="((La | Le) )?[A-Z]([^ .]|[a-z])([^ .]|[a-z])([^ .]|[a-z])*"
    find=list(re.finditer(reg, string[1:]))
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


def parenthesisClean(t) :
        if t[0]=="(" and t[-1] ==")" :
            t=t[1:-1]
        f=re.search(r'\([^)]*\)', t)
        if not f is None :
            if "partie" not in f.group() and "canton" not in f.group() :
                final=t[:f.start()]+t[f.end():]
            elif "canton" in f.group() :
                final=t[:f.start()]+"{"+t[f.start()+1:f.end()-1]+"}"+t[f.end():]
            else :
                final=t[:f.start()]+"*"+t[f.end():]
            return parenthesisClean(final)
        else :
            return t
        
def bracketsClean(t):
        return re.sub(r'\[[^\]]*\]', '', t)

file=open("results.json")

types=set()
dic=json.load(file)


for depart in dic :
    cantonade=set()
    for v in dic[depart] :

        for i in range(len(v["before"])) :
            v["before"][i]= correctString(bracketsClean(parenthesisClean(v["before"][i].replace("*", "").replace(",", ""))))
            if "{" in v["before"][i] :
                cantonade.add(v["before"][i])
        for i in range(len(v["after"])) :
            v["after"][i]= correctString(bracketsClean(parenthesisClean(v["after"][i].replace("*", "").replace(",", ""))))
            if "{" in v["after"][i] :
                cantonade.add(v["after"][i])
        try :
            t=v["type"]
            types.add(v["type"])
        except :
            t=v["type"][0]
            types.add(v["type"][0])
        if ("Fusion" in t or "Simple" in t or "Commune associée" in t) and len(v["after"])>len(v["before"]) :
            c=v["after"]
            v["after"]=v["before"]
            v["before"]=c
        try :
            date=v["date"]
        except :
            v["date"]=date
    print(cantonade)
    for el in cantonade :
        tolookI=el.index("{")
        look=el[:tolookI]
        if look[-1]==" " :
            look=look[:-1]
        for v in dic[depart] :
            for i in range(len(v["after"])) :
                if v["after"][i]==look :
                    if el in v["before"] :
                        v["after"][i]=el

    for el in cantonade :
        tolookI=el.index("{")
        look=el[:tolookI]
        if look[-1]==" " :
            look=look[:-1]
        for v in dic[depart] :
            for i in range(len(v["before"])) :
                if v["before"][i]==look :
                    print(v)
            for i in range(len(v["after"])) :
                if v["after"][i]==look :
                    print(v)



def dateEl(element):
    return element["date"]

def startEl(element):
    return element["start"]

list(types).sort()

def lookUp(blockName, dico,key,date) :
    for k in dico :
        if key!=k :
            start=len(dico[k])-1
            while start>=0 :
                if dico[k][start]["start"]<date :
                    if blockName in dico[k][start]["contains"] :
                        return k
                start-=1
            start=0


def cleanMerge(name, neo ,dicoDep, date) :
    if dicoDep[name][-1]["start"]==date :
        toadd=dicoDep[name][-1]["contains"]
        dicoDep[name]=dicoDep[name][:-1]
        dicoDep[neo][-1]["contains"].addSon(toadd)


def retroactiveGeometryInjection(portionName, date, cityKey, oldKeys, dicoD) :
    if cityKey in dicoD :
        k=cityKey
    else : 
        k=oldKeys[cityKey]
    start=len(dicoD[k])-1
    while start>=0 :
        if dicoD[k][start]["start"]<date :
            dicoD[k][start]["contains"].append(portionName)
        start-=1
    start=0
    if dicoD[k][start]["start"]!=1789 :
        i=0
        while i<len(dicoD[k][start]["contains"]) and "PPP" in dicoD[k][start]["contains"][i] and  dicoD[k][start]["contains"][i]==dicoD[k][start]["name"]:
            i+=1
        if "PPP" in dicoD[k][start]["contains"][i]:
                next=lookUp(dicoD[k][start]["contains"][i], dicoD, k, dicoD[k][start]["start"])
        else :
            next=dicoD[k][start]["contains"][i]


        retroactiveGeometryInjection(portionName, dicoD[k][start]["start"], next, oldKeys, dicoD)




dicoConvert={}
oldKeys={}
portionNumber=1
removals={}
for depart in dic :
    dic[depart].sort(key=dateEl)
    print(depart)
    try :
        date=dic[depart][0]["date"]
        dicoConvert[depart]={}
    except : 
        pass
    
    for change in dic[depart] :
        try :
            if change["date"] != date :
                for name in removals :
                    cleanMerge(name, removals[name], dicoConvert[depart], date)
                removals={}
            date=change["date"]
            if change["before"][0]!="N/A" and change["before"][0]!="Irrelevant" :
                for ville in change["before"] :
                    v=ville.replace(" *", "").replace("*", "")
                    if v not in dicoConvert[depart].keys():
                        bl=newGeometry(depart+"-"+str(portionNumber)+"_"+v)
                        portionNumber+=1
                        dicoConvert[depart][v]=[{"start":1789, "name":v, "contains" :bl}]
                if type(change["type"])==list :
                    types=change["type"][0]
                else :
                    types=change["type"]
                if types=="Name" :
                    if "end" in dicoConvert[depart][change["before"][0]][-1] and dicoConvert[depart][change["before"][0]][-1]["end"]!=date :
                        change["before"][0]= change["before"][0]+" {canton "+change["after"][0]+"}"
                        v=change["before"][0]
                        if v not in dicoConvert[depart].keys():
                            bl=newGeometry(depart+"-"+str(portionNumber)+"_"+v)
                            portionNumber+=1
                            dicoConvert[depart][v]=[{"start":1789, "name":v, "contains" :bl}]
                    if change["after"][0] not in dicoConvert[depart].keys() :
                        dicoConvert[depart][change["after"][0]]=dicoConvert[depart][change["before"][0]]
                    else :
                        dicoConvert[depart][change["after"][0]]+=dicoConvert[depart][change["before"][0]]
                        dicoConvert[depart][change["after"][0]].sort(key=startEl)
                    
                    del (dicoConvert[depart])[change["before"][0]]
                    oldKeys[change["before"][0]]=change["after"][0]
                    for k in oldKeys :
                        if oldKeys[k]==change["before"][0]:
                            oldKeys[k]=change["after"][0]
                    move=dicoConvert[depart][change["after"][0]][-1]["contains"]
                    dicoConvert[depart][change["after"][0]][-1]["end"]=date
                    dicoConvert[depart][change["after"][0]].append({"start":date, "name":change["after"][0], "contains" :move})
                elif "Fusion" in types or "Simple" in types or "Commune associée" in types :
                    beforeSet=[]
                    for ville in change["before"] :
                        #print(ville)
                        if "*" in ville :
                            trueName=ville.replace(" *", "").replace("*", "")
                            if dicoConvert[depart][trueName][-1]["start"]!=date :
                                dicoConvert[depart][trueName][-1]["end"]=date
                                dicoConvert[depart][trueName].append({"start":date, "name":trueName, "contains" :dicoConvert[depart][trueName][-1]["contains"]})
                            res=dicoConvert[depart][trueName][-1]["contains"].split(portionNumber)
                            dicoConvert[depart][trueName][-1]["contains"]=res[0]
                            portionNumber+=1
                            beforeSet.append(res[1])
                            removals[trueName]=change["after"][0]
                        else :
                            dicoConvert[depart][ville][-1]["end"]=date
                            beforeSet.append(dicoConvert[depart][ville][-1]["contains"])
                    after=change["after"][0]
                    geomAfter=block(depart+"-"+str(portionNumber)+"_"+after)
                    portionNumber+=1
                    for b in beforeSet :
                        geomAfter.addSon(b)
                    if after not in dicoConvert[depart].keys():
                        dicoConvert[depart][after]=[{"start": date, "name":after, "contains" :geomAfter}]
                    else :
                        dicoConvert[depart][after].append({"start": date, "name":after, "contains" :geomAfter})
                else :
                    beforeSet={}
                    spec=""
                    if "suppression" in types or "Suppression" in types :
                        for ville in change["before"] :
                            if ville in types :
                                spec=ville
                    for ville in change["before"] :
                            trueName=ville.replace(" *", "").replace("*", "")
                            if dicoConvert[depart][trueName][-1]["start"]==date :
                                r=-2
                            else :
                                r=-1
                            
                            if "suppression" in types or "Suppression" in types and (trueName==spec or spec==""):
                                if r==-2 :
                                    r=-1
                                    erroneous=dicoConvert[depart][trueName][-1]
                                    dicoConvert[depart][trueName]=dicoConvert[depart][trueName][:-1]
                                    toSplit=erroneous["contains"]
                                else :
                                    if "end" not in dicoConvert[depart][trueName][-1] :
                                        dicoConvert[depart][trueName][-1]["end"]=date
                                    if "inheritor" not in dicoConvert[depart][trueName][-1] :
                                        toSplit=dicoConvert[depart][trueName][-1]["contains"]
                                    else : 
                                        toSplit=dicoConvert[depart][dicoConvert[depart][trueName][-1]["inheritor"]][-1]["contains"]
                                splitness=(toSplit, None)
                                for  ville2 in change["after"][:-1]:
                                    ville2Block=dicoConvert[depart][trueName][r]["contains"].find(ville2)
                                    if ville2Block is None :
                                        splitness=splitness[0].split(portionNumber)
                                        res=splitness[1]
                                        portionNumber+=1
                                    else :
                                        res=ville2Block
                                        splitness=(splitness[0].remove(res), res)
                                    if ville2 not in beforeSet :
                                        beforeSet[ville2]=[]
                                    beforeSet[ville2].append(res)
                                if change["after"][-1] not in beforeSet :
                                    beforeSet[change["after"][-1]]=[]
                                if "inheritor" not in dicoConvert[depart][trueName][-1] :
                                    dicoConvert[depart][trueName][-1]["inheritor"]=change["after"][-1]
                                else :
                                    splitness=splitness[0].split(portionNumber)
                                    portionNumber+=1
                                    dicoConvert[depart][dicoConvert[depart][trueName][-1]["inheritor"]][-1]["contains"]=splitness[0]
                                if trueName in removals :
                                    del removals[trueName]
                                beforeSet[change["after"][-1]].append(splitness[0])
                                dicoConvert[depart][trueName][-1]["end"]=date
                            else : 
                                splitness=(dicoConvert[depart][trueName][-1]["contains"], None)
                                for  ville2 in change["after"]:
                                    ville2Block=dicoConvert[depart][trueName][-1]["contains"].find(ville2)
                                    if ville2Block is None :
                                        splitness=splitness[0].split(portionNumber)
                                        res=splitness[1]
                                        portionNumber+=1
                                    else :
                                        res=ville2Block
                                        splitness=(splitness[0].remove(res), res)
                                    if ville2 not in beforeSet :
                                        beforeSet[ville2]=[]
                                    beforeSet[ville2].append(res)
                                if r==-1 :
                                    dicoConvert[depart][trueName][-1]["end"]=date
                                    dicoConvert[depart][trueName].append({"start":date, "name":trueName, "contains" :splitness[0]})
                                else :
                                    try:
                                        dicoConvert[depart][trueName][-1]["contains"]=splitness[0]
                                    except:
                                        pass
                    for after in change["after"] :
                        blocks=block(depart+"-"+str(portionNumber)+"_"+after)
                        portionNumber+=1
                        for b in beforeSet[after] :
                            blocks.addSon(b)
                        if after not in dicoConvert[depart].keys():
                            dicoConvert[depart][after]=[{"start":date, "name":after, "contains" :blocks}]
                        else :
                            dicoConvert[depart][after].append({"start":date, "name":after, "contains" :blocks})
        except IndexError as error:
                print(traceback.format_exc())
                print(change)
                print(dicoConvert[depart][trueName])
                print(r)
    for name in removals :
                cleanMerge(name, removals[name], dicoConvert[depart])
    removals={}


def filter(v) :
    l=[]
    for e in v :
        if "end" not in e or e["start"]!=e["end"] :
            l.append(e)
    return l


for k in dicoConvert :
    for e in dicoConvert[k] :
        dicoConvert[k][e]=filter(dicoConvert[k][e])
        
for k in dicoConvert :
    for e in dicoConvert[k] :
        for v in dicoConvert[k][e] :
            if "{" in v["name"] :
                e=v["name"].index("{")
                if v["name"][e-1]==" " :
                    e=e-1
                v["name"]=v["name"][:e]
            v["contains"]=v["contains"].reduce()


    
 

def serializeJSON(geo,fileName) :
    
    out_file = open(fileName, "w")
    
    json.dump(geo, out_file, indent = 6)
    out_file.close()

serializeJSON(dicoConvert, "resultsTimeline.json")



b=block("test")
b.addSon(block("test2"))
b.addSon(block("test3"))
print(b.reduce())
                        

                
            


            


