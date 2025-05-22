from rdflib import Graph, Literal, RDF, URIRef, XSD,  RDFS
from SPARQLWrapper import SPARQLWrapper, JSON
import sys

import requests

#Similar to SPARQL's STRAFTER
def strafter(string, c) :
    i=0
    while string[i]!=c :
        i+=1
    return string[i+1:]

startDate=2010
endDate=2016

hhtChange="https://w3id.org/HHT/Change#"
hht="https://w3id.org/HHT#"

# Used to order the versions by time interval
def orderInterval(q) :
    return int(q[0])+int(q[1])

# Difference between two sets
def difference(set1, set2) :
    before=[]
    for e in set1 :
        if e not in set2 :
            before.append(e)
    after=[]
    for e in set2 :
        if e not in set1 :
            after.append(e)
    return (before, after)

# Returns the nature of a feature change
def getNatureSingleChange(change) :
    nature=[]
    if change["start"]["label"]!=change["stop"]["label"] :
        nature.append("NameChange")
    before=len(change["start"]["geometry"])
    after=len(change["stop"]["geometry"])
    intersect=len(change["start"]["geometry"].intersection(change["stop"]["geometry"]))
    if intersect !=before or intersect!=after :
        nature.append("GeometryChange")
        if before> after and after==intersect :
            nature.append("Contraction")
        elif before< after and before==intersect :
            nature.append("Expansion")
        elif before> intersect and after>intersect :
            nature.append("Deformation")
    return nature

# Find all the feature changes based on the timeline of a unit
def findUnitChanges(unit, result) :
    global startDate
    global endDate
    sequence=list(unit.keys())
    sequence.sort(key=orderInterval)
    if int(sequence[0][0])>startDate :
        result["appearance"]["http://www.semanticweb.org/melodi/data#Apparition_"+strafter(unit[sequence[0]]["uri"], "#")]={ "start" : unit[sequence[0]]}
        result["appearance"]["http://www.semanticweb.org/melodi/data#Apparition_"+strafter(unit[sequence[0]]["uri"], "#")]["nature"]=["Appearance"]
        result["appearance"]["http://www.semanticweb.org/melodi/data#Apparition_"+strafter(unit[sequence[0]]["uri"], "#")]["year"]=sequence[0][0]

    for k in range(len(sequence)) :
        if k==len(sequence)-1 :
            if int(sequence[k][1])<endDate :
                result["disappearance"]["http://www.semanticweb.org/melodi/data#Disparition_"+strafter(unit[sequence[k]]["uri"], "#")]={"stop" : unit[sequence[k]]}
                result["disappearance"]["http://www.semanticweb.org/melodi/data#Disparition_"+strafter(unit[sequence[k]]["uri"], "#")]["nature"]=["Disappearance"]
                result["disappearance"]["http://www.semanticweb.org/melodi/data#Disparition_"+strafter(unit[sequence[k]]["uri"], "#")]["year"]=sequence[k][1]
        else :
            if sequence[k][1]==sequence[k+1][0] :
                result["change"]["http://www.semanticweb.org/melodi/data#Change"+strafter(unit[sequence[k]]["uri"], "#")+strafter(unit[sequence[k+1]]["uri"], "#")]={"stop" : unit[sequence[k]], "start" : unit[sequence[k+1]]}
                result["change"]["http://www.semanticweb.org/melodi/data#Change"+strafter(unit[sequence[k]]["uri"], "#")+strafter(unit[sequence[k+1]]["uri"], "#")]["year"]=sequence[k][1]
            else : 
                result["appearance"]["http://www.semanticweb.org/melodi/data#Apparition_"+strafter(unit[sequence[k+1]]["uri"], "#")]={ "start" : unit[sequence[k+1]]}
                result["appearance"]["http://www.semanticweb.org/melodi/data#Apparition_"+strafter(unit[sequence[k+1]]["uri"], "#")]["nature"]=["Appearance"]
                result["appearance"]["http://www.semanticweb.org/melodi/data#Apparition_"+strafter(unit[sequence[k+1]]["uri"], "#")]["year"]=sequence[k+1][0]
                result["disappearance"]["http://www.semanticweb.org/melodi/data#Disparition_"+strafter(unit[sequence[k]]["uri"], "#")]={"stop" : unit[sequence[k]]}
                result["disappearance"]["http://www.semanticweb.org/melodi/data#Disparition_"+strafter(unit[sequence[k]]["uri"], "#")]["nature"]=["Disappearance"]
                result["disappearance"]["http://www.semanticweb.org/melodi/data#Disparition_"+strafter(unit[sequence[k]]["uri"], "#")]["year"]=sequence[k][1]


    return result

#Tool for quick creation of URI objects
def createObject(prefix,text) :
    final=text.replace(" ", "_").replace("(", "").replace(")", "")
    return URIRef(prefix+final)

# Identify the next set of changes for the computation of a composite change
def findNext(key, finalChange) :
    change=finalChange[key]
    composite=[key]
    if "GeometryChange" in change["nature"] :
            diff=difference(change["stop"]["geometry"], change["start"]["geometry"])
    elif "Disappearance" in change["nature"] :
            diff=(list(change["stop"]["geometry"]), [])
    else : 
            diff=([], list(change["start"]["geometry"]))
    for block in diff[0] :     
            pikachuInBath=False
            i=0
            l=list(finalChange.keys())
            while not pikachuInBath and i<len(l) :
                suspect=finalChange[l[i]]
                if "start" in suspect and suspect["year"]==change["year"] and suspect["start"]["niveau"]==change["stop"]["niveau"] and block in suspect["start"]["geometry"] :
                    composite.append(l[i])
                    pikachuInBath=True
                i+=1
    for block in diff[1] :
            
            pikachuInBath=False
            i=0
            l=list(finalChange.keys())
            while not pikachuInBath and i<len(l) :
                suspect=finalChange[l[i]]
                if "stop" in suspect and suspect["year"]==change["year"] and suspect["stop"]["niveau"]==change["start"]["niveau"] and block in suspect["stop"]["geometry"] :
                    composite.append(l[i])
                    pikachuInBath=True
                i+=1
    return composite



def main() :
    global startDate
    global endDate
    args = sys.argv[1:]
    endpoint=args[0]
    startDate=int(args[1])
    endDate=int(args[2])
    if len(args)>3 :
        filename=args[3]
    else :
        filename="resultAlgo.ttl"
    allunits="""    			PREFIX hht: <https://w3id.org/HHT#>
			PREFIX time: <http://www.w3.org/2006/time#>
			PREFIX oba: <http://www.semanticweb.org/melodi/types#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT DISTINCT ?target ?unit ?unitApres ?l ?b ?e ?niveau WHERE {
	            ?target a hht:UnitVersion.
  	            ?unit hht:hasVersion ?target.
                ?target rdfs:label ?l.
                ?target hht:isMemberOf ?niveau.
                ?target  hht:properContains ?subApres.
				?subApres hht:isMemberOf ?level.
				?level a hht:ElementaryLevelVersion.
				{FILTER NOT EXISTS {?subApres hht:properContains ?x.}
                FILTER NOT EXISTS {?subApres hht:hasGeometry ?y.}
				?unitApres hht:hasVersion ?subApres.} UNION {FILTER NOT EXISTS {?subApres hht:properContains ?x.}
				?subApres hht:hasGeometry ?unitApres.} UNION
                {?subApres hht:properContains+ ?x.
				FILTER NOT EXISTS {?x hht:properContains ?y.}
                FILTER NOT EXISTS {?x hht:hasGeometry ?y.}
				?unitApres hht:hasVersion ?x.}
                UNION 
                {?subApres hht:properContains+ ?x.
				FILTER NOT EXISTS {?x hht:properContains ?y.}
				?x hht:hasGeometry ?unitApres.}

                ?target hht:validityPeriod ?interval.
				?interval time:hasBeginning ?start.
                ?start time:inXSDgYear ?b.
				?interval time:hasEnd ?stop.
                ?stop time:inXSDgYear ?e.
}"""
    unitR={}

    changeGraph=Graph()

    sparql = SPARQLWrapper(
        endpoint
    )

    allElemunits="""    			PREFIX hht: <https://w3id.org/HHT#>
                PREFIX time: <http://www.w3.org/2006/time#>
                PREFIX oba: <http://www.semanticweb.org/melodi/types#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT DISTINCT ?target ?unit ?unitApres ?l ?b ?e ?niveau WHERE {
                    ?target a hht:UnitVersion.
                    ?unit hht:hasVersion ?target.
                    ?target rdfs:label ?l.
                    ?target hht:isMemberOf ?niveau.
                    {?niveau a hht:ElementaryLevelVersion.} UNION {?niveau a hht:SubElementaryLevelVersion.}
                    {FILTER NOT EXISTS {?target hht:properContains ?x.}
                    FILTER NOT EXISTS {?target hht:hasGeometry ?y.}
                    ?unitApres hht:hasVersion ?target.} UNION {FILTER NOT EXISTS {?target hht:properContains ?x.}
                    ?target hht:hasGeometry ?unitApres.} UNION
                    {?target hht:properContains+ ?x.
                    FILTER NOT EXISTS {?x hht:properContains ?y.}
                    FILTER NOT EXISTS {?x hht:hasGeometry ?y.}
                    ?unitApres hht:hasVersion ?x.}
                    UNION 
                    {?target hht:properContains+ ?x.
                    FILTER NOT EXISTS {?x hht:properContains ?y.}
                    ?x hht:hasGeometry ?unitApres.}
                    ?target hht:validityPeriod ?interval.
                    ?interval time:hasBeginning ?start.
                    ?start time:inXSDgYear ?b.
                    ?interval time:hasEnd ?stop.
                    ?stop time:inXSDgYear ?e.
    }"""

    sparql.setReturnFormat(JSON)

    sparql.setQuery(allunits)

    try:
        ret = sparql.queryAndConvert()
        result=[]
        sparql.setQuery(allElemunits)
        ret2=sparql.queryAndConvert()
        ret["results"]["bindings"]+=ret2["results"]["bindings"]
        for r in ret["results"]["bindings"]:
            if str(r["unit"]["value"]) not in unitR.keys() :
                unitR[str(r["unit"]["value"])]={}
            if (str(r["b"]["value"]), str(r["e"]["value"])) not in unitR[str(r["unit"]["value"])] :
                unitR[str(r["unit"]["value"])][(str(r["b"]["value"]), str(r["e"]["value"]))]={"uri" : str(r["target"]["value"]), "label" : str(r["l"]["value"]), "geometry": {str(r["unitApres"]["value"])}, "niveau" : str(r["niveau"]["value"])}
            else :
                unitR[str(r["unit"]["value"])][(str(r["b"]["value"]), str(r["e"]["value"]))]["geometry"].add(str(r["unitApres"]["value"]))

    except Exception as e:
        print(e)  
    print("Query results loaded...")

    changes={"change" : {}, "disappearance" :{}, "appearance" :{}}
    for unit in unitR.values() :
        changes=findUnitChanges(unit, changes)
    for key in changes["change"] :
        change=changes["change"][key]
        change["nature"]=getNatureSingleChange(change)
        changeGraph.add((URIRef(change["stop"]["uri"]), createObject(hhtChange, "goesThrough"), URIRef(key)))
        changeGraph.add((URIRef(key), createObject(hhtChange, "before"), URIRef(change["stop"]["uri"])))
        changeGraph.add((URIRef(change["start"]["uri"]), createObject(hhtChange, "emergesFrom"), URIRef(key)))
        changeGraph.add((URIRef(key), createObject(hhtChange, "after"), URIRef(change["start"]["uri"])))
        changeGraph.add((URIRef(key), RDF.type, createObject(hhtChange, "FeatureChange")))
        for n in change["nature"] :
            changeGraph.add((URIRef(key), RDF.type, createObject(hhtChange, n)))
    for key in changes["appearance"] :
        change=changes["appearance"][key]
        changeGraph.add((URIRef(change["start"]["uri"]), createObject(hhtChange, "emergesFrom"), URIRef(key)))
        changeGraph.add((URIRef(key), createObject(hhtChange, "after"), URIRef(change["start"]["uri"])))
        changeGraph.add((URIRef(key), RDF.type, createObject(hhtChange, "FeatureChange")))
        changeGraph.add((URIRef(key), RDF.type, createObject(hhtChange, "Appearance")))
    for key in changes["disappearance"] :
        change=changes["disappearance"][key]
        changeGraph.add((URIRef(change["stop"]["uri"]), createObject(hhtChange, "goesThrough"), URIRef(key)))
        changeGraph.add((URIRef(key), createObject(hhtChange, "before"), URIRef(change["stop"]["uri"])))
        changeGraph.add((URIRef(key), RDF.type, createObject(hhtChange, "FeatureChange")))
        changeGraph.add((URIRef(key), RDF.type, createObject(hhtChange, "Disappearance")))
    print("Feature changes created...")
    finalChange=changes["change"]
    finalChange.update(changes["disappearance"])
    finalChange.update(changes["appearance"])
    found=set()
    compositeChanges=[]
    for k in finalChange :
        composite=[]
        toCheck=[k]
        change=finalChange[k]
        if ("GeometryChange" in change["nature"] or  "Disappearance" in change["nature"] or "Appearance" in change["nature"]) and k not in found :
            while len(toCheck)>0 :
                total=[]
                for j in toCheck :
                    total+=findNext(j, finalChange)
                toCheck=[]
                for r in total :
                    if r not in composite :
                        composite.append(r)
                        found.add(r)
                        toCheck.append(r)

            compositeChanges.append(composite)

    for compo in compositeChanges :
        if len(compo)>1 :
            changeID="http://www.semanticweb.org/melodi/data#ComplexChangeBasedOn_"+strafter(compo[0],"#")
            changeGraph.add((URIRef(changeID), RDF.type, createObject(hhtChange, "CompositeChange")))
            for feature in compo :
                changeGraph.add((URIRef(feature), createObject(hhtChange, "isPartOf"), URIRef(changeID)))
            before=0
            after=0
            inter=0
            for k in compo :
                if "start" in finalChange[k].keys() :
                    after+=1
                if "stop" in finalChange[k].keys() :
                    before+=1
                if "start" in finalChange[k].keys() and "stop" in finalChange[k].keys() :
                    inter+=1
            if after==1 and before>1 :
                changeGraph.add((URIRef(changeID), RDF.type, createObject(hhtChange, "Merge")))       
            elif after>1 and before==1 :
                changeGraph.add((URIRef(changeID), RDF.type, createObject(hhtChange, "Split")))       
            elif after>1 and before>1 :
                changeGraph.add((URIRef(changeID), RDF.type, createObject(hhtChange, "Redistribution")))     
            if (before>after and after==inter) or (after>=before and before==inter) :
                changeGraph.add((URIRef(changeID), RDF.type, createObject(hhtChange, "ContinuationChange")))
            elif inter==0 :
                changeGraph.add((URIRef(changeID), RDF.type, createObject(hhtChange, "DerivationChange")))

    print("Composite changes created...")
            
    changeGraph.serialize(destination=filename, format="turtle")
    print("Complete !")

if __name__ == '__main__':
    main()