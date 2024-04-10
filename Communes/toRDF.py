from bs4 import BeautifulSoup
import requests
import json
import unidecode
import re
from rdflib import Graph, Literal, RDF, URIRef, XSD,  RDFS
from SPARQLWrapper import SPARQLWrapper, JSON

fileToEdit="ThirdRepublic.ttl"
start=1870
end=1940

def overlap(i1,i2) :
    return (i1[0]<=i2[0] and i2[0]<i1[1]) or (i1[0]<i2[1] and i2[1]<=i1[1]) or (i2[0]<=i1[0] and i1[0]<i2[1]) or (i2[0]<i1[1] and i1[1]<=i2[1])

def createObject(prefix,text) :
    final=text.replace(" ", "_").replace("(", "").replace(")", "")
    return URIRef(prefix+final)


def updateSPARQL(endpoint, query) :
    sparql = SPARQLWrapper(endpoint)
    sparql.setMethod("POST")
    sparql.setQuery(query)
    ret = sparql.query()
    ret.response.read()

def querySPARQL(endpoint, query) :
    sparql = SPARQLWrapper(endpoint)
    sparql.setReturnFormat(JSON)
    sparql.setQuery(query)
    ret = sparql.queryAndConvert()
    return ret["results"]["bindings"]

def toList(dic) :
    l=[] 
    for e in dic :
        f=[]
        for el in e.values() :
            f.append(el["value"])
        l.append(f)
    return l

#g=Graph()
#g.parse("CommuneEvolution.ttl")

#h=Graph()
#h.parse(fileToEdit)

query="""PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                        PREFIX hht: <https://w3id.org/HHT#>
                        PREFIX time: <http://www.w3.org/2006/time#>
prefix xsd: <http://www.w3.org/2001/XMLSchema#>
    SELECT ?label ?unit ?version WHERE {
    ?unit hht:hasVersion ?version.
          ?version rdfs:label ?label.
      ?version hht:validityPeriod ?i.
      ?i time:hasEnd ?b.
      ?b time:inXSDgYear ?end.
      ?i time:hasBeginning ?e.
      ?e time:inXSDgYear ?begin.
      FILTER ("2011"^^xsd:gYear<?end && "2011"^^xsd:gYear>=?begin)
}"""

#liste=g.query(query)

sparql = SPARQLWrapper(
    "http://localhost:3030/communesV2/sparql"
)
sparql.setReturnFormat(JSON)
sparql.setQuery(query)

ret = sparql.queryAndConvert()
liste=[]
for r in ret["results"]["bindings"]: 
    liste.append((r["label"]["value"], r["unit"]["value"], r["version"]["value"]))

for r in liste :
    bb1="""PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
             PREFIX hht: <https://w3id.org/HHT#>
             PREFIX time: <http://www.w3.org/2006/time#>
            SELECT ?bb WHERE {
            <"""+str(r[2])+"""> hht:hasGeometry ?bb.
    }"""
    print(bb1)
    dic={}
    sparql.setQuery(bb1)
    buildings=sparql.queryAndConvert()
    buildings=toList(buildings["results"]["bindings"])
    for b in buildings :
        bb="""PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
             PREFIX hht: <https://w3id.org/HHT#>
             PREFIX time: <http://www.w3.org/2006/time#>

            SELECT ?version ?start ?end WHERE {
            ?version hht:hasGeometry <"""+str(b[0])+""">.
            ?version hht:validityPeriod ?i.
            ?i time:hasBeginning ?b.
            ?b time:inXSDgYear ?start.
            ?i time:hasEnd ?e.
            ?e time:inXSDgYear ?end.
        }"""
        include=querySPARQL("http://localhost:3030/communesV2/sparql", bb)
        include=toList(include)
        dic[str(b[0])]={}
        for chronos in include:
            dic[str(b[0])][(int(chronos[1]), int(chronos[2]))]=chronos[0]



    match="""PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
             PREFIX hht: <https://w3id.org/HHT#>
             PREFIX time: <http://www.w3.org/2006/time#>
             prefix oba: <http://www.semanticweb.org/melodi/types#>
            SELECT ?unit WHERE {
            ?unit hht:hasVersion ?v.
            ?v hht:isMemberOf oba:Commune.
            ?v rdfs:label ?label.
            FILTER (?label=\""""+str(unidecode.unidecode(r[0].upper()))+"""\")
    }"""
    matches=querySPARQL("http://localhost:3030/thirdMatch/sparql", match)
    matches=toList(matches)
    if len(matches)!=1 :
            if len(matches)>1 :
                dep=str(r[1]).split("#")[1].split("_")[0]
                if dep=="2A" or dep=="2B" :
                    d=dep
                elif int(dep)>20 :
                    d=int(dep)-1
                else :
                    d=int(dep)
                print(dep)
                res=None
                for q in matches :
                    try :
                        f=re.search("[0-9]+[AB]?[0-9]+", str(q[0]))
                        id=f.group()[-5:-3]
                        print(id)
                        if ("A" not in id and "B" not in id and int(id)==d) or (id==dep) :
                            res=str(q[0])
                    except :
                        pass
            if len(matches)==0 or res==None :   
                print(matches)
                print(r[1])
                print("Actual match : ")
                res=input()
    else :
        res=str(matches[0][0])
    rename="""PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
             PREFIX hht: <https://w3id.org/HHT#>
             PREFIX time: <http://www.w3.org/2006/time#>
            DELETE {
                ?s ?p ?o.
            } INSERT {
                ?s2 ?p ?o2.
            } WHERE {
                {BIND (<"""+str(r[1])+"""> AS ?s).
                BIND (<"""+res+"""> AS ?s2).
                ?s ?p ?o.
                BIND (?o AS ?o2)} UNION {BIND (<"""+str(r[1])+"""> AS ?o).
                BIND (<"""+res+"""> AS ?o2).
                ?s ?p ?o.
                BIND (?s AS ?s2).}
            }    
    """
    updateSPARQL("http://localhost:3030/communesV2",rename )
    inclusions="""PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
             PREFIX hht: <https://w3id.org/HHT#>
             PREFIX time: <http://www.w3.org/2006/time#>
            SELECT ?upper ?start ?end WHERE {
                <"""+res+"""> hht:hasVersion ?v.
                ?upper hht:contains ?v.
                ?upper hht:validityPeriod ?i.
                ?i time:hasBeginning ?i1.
                ?i1 time:inXSDgYear ?start.
                ?i time:hasEnd ?i2.
                ?i2 time:inXSDgYear ?end.
            }
    """
    print(inclusions)
    inc=querySPARQL("http://localhost:3030/thirdMatch/sparql", inclusions)
    inc=toList(inc)
    sub="""PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
             PREFIX hht: <https://w3id.org/HHT#>
             PREFIX time: <http://www.w3.org/2006/time#>
            SELECT ?upper ?start ?end WHERE {
                <"""+res+"""> hht:hasVersion ?v.
                ?upper hht:hasSubUnit ?v.
                ?upper hht:validityPeriod ?i.
                ?i time:hasBeginning ?i1.
                ?i1 time:inXSDgYear ?start.
                ?i time:hasEnd ?i2.
                ?i2 time:inXSDgYear ?end.
            }
    """
    subs=toList(querySPARQL("http://localhost:3030/thirdMatch/sparql", sub))
    prune="""PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX hht: <https://w3id.org/HHT#>
            PREFIX time: <http://www.w3.org/2006/time#>
        DELETE {
            ?version ?p ?o.
            ?o2 ?p2 ?version.
        } WHERE {
            <"""+ res+"""> hht:hasVersion ?version
            {?version ?p ?o.} UNION {?o2 ?p2 ?version.}
                
    }"""
    print(len(inc))
    for version in inc :
        interval=(int(version[1]),int(version[2]))
        for b in buildings :
            for k in dic[str(b[0])] :
                
                if overlap(interval, k) :
                    print(k)
                    print(interval)
                    updateSPARQL("http://localhost:3030/communesV2","""PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX hht: <https://w3id.org/HHT#>
            PREFIX time: <http://www.w3.org/2006/time#>
        INSERT DATA {
            <"""+str(version[0])+"""> hht:contains <"""+dic[str(b[0])][k]+""">
        }    
""")
                    
    for version in subs :
        interval=(int(version[1]),int(version[2]))
        for b in buildings :
            for k in dic[str(b[0])] :
                if overlap(interval, k) :
                    updateSPARQL("http://localhost:3030/communesV2","""PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX hht: <https://w3id.org/HHT#>
            PREFIX time: <http://www.w3.org/2006/time#>
        INSERT DATA {
            <"""+str(version[0])+"""> hht:hasSubUnit <"""+dic[str(b[0])][k]+""">
        }    
""")
    updateSPARQL("http://localhost:3030/thirdMatch",prune)

fragment="""PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX hht: <https://w3id.org/HHT#>
            PREFIX time: <http://www.w3.org/2006/time#>
            prefix xsd: <http://www.w3.org/2001/XMLSchema#>
        DELETE {
            ?version ?p ?o.
            ?o2 ?p2 ?version.
        } WHERE {
            ?version hht:validityPeriod ?i.
            ?i time:hasBeginning ?b.
            ?b time:inXSDgYear ?bV.
            ?i time:hasEnd ?e.
            ?e time:inXSDgYear ?eV.
            FILTER(?bV>=\""""+str(end)+"""\"^^xsd:gYear)
            FILTER(?eV<=\""""+str(start)+"""\"^^xsd:gYear)
            {?version ?p ?o.} UNION {?o2 ?p2 ?version.}
        }    
"""
updateSPARQL("http://localhost:3030/communesV2",fragment)
troncateDown="""PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX hht: <https://w3id.org/HHT#>
            PREFIX time: <http://www.w3.org/2006/time#>
            prefix xsd: <http://www.w3.org/2001/XMLSchema#>
        DELETE {
            ?t time:inXSDgYear ?instant
        } INSERT {?t time:inXSDgYear ?newT} WHERE {
            ?version hht:validityPeriod ?i.
            {?i time:hasBeginning ?t.
             ?t time:inXSDgYear ?instant.
             FILTER (?instant<\""""+str(start)+"""\"^^xsd:gYear)
             BIND (\""""+str(start)+"""\"^^xsd:gYear AS ?newT)
        }    UNION {?i time:hasEnd ?t.
             ?t time:inXSDgYear ?instant.
             FILTER (?instant>\""""+str(end)+"""\"^^xsd:gYear)
             BIND (\""""+str(end)+"""\"^^xsd:gYear AS ?newT)
        }  
}"""
updateSPARQL("http://localhost:3030/communesV2",troncateDown)

commune="""PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
             PREFIX hht: <https://w3id.org/HHT#>
             PREFIX time: <http://www.w3.org/2006/time#>
             prefix oba: <http://www.semanticweb.org/melodi/types#>
            INSERT {?v hht:isMemberOf oba:Commune.} WHERE {?v a hht:UnitVersion.}"""

updateSPARQL("http://localhost:3030/communesV2",commune)
   

