# HHT
HHT (Hierarchical Historical Territories) is an ontology designed to describe multiple-hierarchy evolving territories in an historical context. This ontology relies on a discrete geometry description using building blocks. It is provided with an algorithm implemented with SHACL-Rules to detect and categorize changes inside a knowledge graph relying on HHT. 

## HHT Ontology

The file **HHT.ttl** contains the HHT ontology description (IRI : https://w3id.org/HHT).

## HHT Change computation algorithm

The HHT Algorithm is implemented in the **HHT-Algo-Python.py** file.

To run the script one can use the following command :

    python HHT-Algo-Python.py <endpoint> <startDate> <endDate> <resultFileName.ttl>

Where <endpoint>, <startDate>, <endDate> and <resultFileName.ttl> should be replaced with the endpoint is located, the start and end years of the focus of the graph and the name the result file shoud take.

## Datasets

Examples of knowledge graphs using HHT are provided. They are located in the folders :

 - Communes
 - FranceRegions
 - NewYork
 - NUTS
 - Third Republic
 - ThirdRepublicEvolutionCommunes

Every dataset folder contains one or several **.ttl** file containing the initial knowledge graph. For most, the result of the algorithm is located in (**resultAlgo.ttl**). A dataset description regarding the number of entities in both the dataset and the results of the algorithm are provided. Finally, in the case of Communes, several scripts are added to document the process of creating the dataset. Note that these scripts were complemented with some manual editions.

## Competency Questions

We detail in this section the competency questions that are relevant to the HHT ontology. For each question, we provide a SPAQRL query which answers the question.

### What are the characteristics of a territory and how does it interact with other territories?

This question is adressed through the following competency question.
**CQ-1.1:** What hierarchical criterion does a level $L depend on?
		SELECT ?h where {
			<$L$> hht:hasVersion ?lv.
			?h hht:hasLevel ?lv.
		}
**CQ-1.2:** What is the level of a territory $X?

		SELECT ?l where {
			<$X> hht:hasVersion ?v.
			?v hht:isMemberOf ?lv.
			?l hht:hasVersion ?lv.
		}

**CQ-1.3:** What are the hierarchical levels that are directly subordinated to a level $L?

		SELECT ?l where {
			<$L> hht:hasVersion ?v.
			?v hht:hasSubLevel ?lv.
			?l hht:hasVersion ?lv.
		}

**CQ-1.4:** Which hierarchical levels take part in the hierarchy defined by criterion $C?

		SELECT ?l where {
			<$C> hht:hasMember ?lv.
			?l hht:hasVersion ?lv.
		}

**CQ-1.5:** Which territories are simultaneously included in territories $X$ and $Y$? 

	SELECT ?unit WHERE {
		?unit hht:hasVersion ?v.
		<$X> hht:hasVersion ?vx.
		<$Y> hht:hasVersion ?vy.
		?vx hht:contains ?v.
		?vy hht:contains ?v.
	}

### Which evolution occurred in territories?

This question is adressed through the following competency question.
**CQ-2.1:** What is the name of territory $X at time $t ?
		SELECT ?label WHERE {
			<$X> hht:hasVersion ?v
			?v rdfs:label ?l.
			?v hht:validityPeriod ?p.
			?p time:hasBeginning ?b.
			?b time:inXSDgYear ?bY.
			?p time:hasEnd ?e.
			?e time:inXSDgYear ?eY.
			FILTER (t>=?by && t<eY)

		}
**CQ-2.2:** Does territory $X exist at time $t ?

		ASK {
			<$X> hht:hasVersion ?v.
			?v hht:validityPeriod ?p.
			?p time:hasBeginning ?b.
			?b time:inXSDgYear ?bY.
			?p time:hasEnd ?e.
			?e time:inXSDgYear ?eY.
			FILTER (t>=?by && t<eY)
		}


**CQ-2.3:** Which territories appear/disappear during a period [$b, $e]?

		SELECT ?t WHERE {
			?d a hhtC:Disappearance.
			?d hht:before ?tv.
			?t hht:hasVersion ?tv.
			?tv hht:validityPeriod ?i.
			?i time:hasEnd ?e.
			?e time:inXSDgYear ?eY.
			FILTER (?eY>=$b && ?eY<=$e)
		}

**CQ-2.4:** Is there a common meaning for the changes occurring in territories $X and $Y at time $t?

		ASK {
			<$X> hht:hasVersion ?v.
			?v hht:validityPeriod ?p.
			?p time:hasEnd ?e.
			?e time:inXSDgYear $t.
			?change hhtC:before ?v.
			<$Y> hht:hasVersion ?v2.
			?v2 hht:validityPeriod ?p2.
			?p2 time:hasEnd ?e.
			?change2 hhtC:before ?v2.
			?change2 hhtC:isPartOf ?r.
			?change hhtC:isPartOf ?r.
		}

### What is the geometry of a territory?

**CQ-3.1:** What is the geometry of $T at time $y ?

		SELECT DISTINCT ?unitApres WHERE {
					?unit hht:hasVersion ?target.
				?target hht:validityPeriod ?interval.
				?interval time:hasBeginning ?start.
						?start time:inXSDgYear ?b.
				?interval time:hasEnd ?stop.
						?stop time:inXSDgYear ?e.
				FILTER ($t>=b && $t<e)
						{?target  hht:contains ?subApres.
				?subApres hht:isMemberOf ?level.
				?level a hht:ElementaryLevelVersion.} UNION {?niveau a hht:ElementaryLevelVersion. BIND (?target AS ?subApres)}
				{FILTER NOT EXISTS {?subApres hht:contains ?x.}
						FILTER NOT EXISTS {?subApres hht:hasGeometry ?y.}
				?unitApres hht:hasVersion ?subApres.} UNION {FILTER NOT EXISTS {?subApres hht:contains ?x.}
				?subApres hht:hasGeometry ?unitApres.} UNION
						{?subApres hht:contains+ ?x.
				FILTER NOT EXISTS {?x hht:contains ?y.}
						FILTER NOT EXISTS {?x hht:hasGeometry ?y.}
				?unitApres hht:hasVersion ?x.}
						UNION 
						{?subApres hht:contains+ ?x.
				FILTER NOT EXISTS {?x hht:contains ?y.}
				?x hht:hasGeometry ?unitApres.}

		}

**CQ-3.2:** Is $T1 contained in $T2 at time $t?

**CQ-3.3:**  Does $T1 overlap with $T2 at time $t ?

**CQ-3.4:** Do we know if the geometry description of territory $X is exhaustive at time $t  ?
	ASK {
		<$X> hht:hasVersion ?target.
		?target hht:validityPeriod ?interval.
		?interval time:hasBeginning ?start.
        ?start time:inXSDgYear ?b.
		?interval time:hasEnd ?stop.
        ?stop time:inXSDgYear ?e.
		FILTER ($t>=b && $t<e)
		{?target hht:operativeContent ?u} UNION {?target hht:hasSetGeometry ?u}
	
}



## Querying

We provide example of SPARQL queries that can be used in order to query the knowledge graph and the result of the algorithm.

 1. Count the territories described and their version by level : 

	    SELECT DISTINCT ?Level (COUNT(DISTINCT ?version) AS ?versionCount) (COUNT(DISTINCT ?unit) AS ?unitCount) 
	    WHERE{
	        ?version hht:isMemberOf ?Level.
	        ?unit hht:hasVersion ?version.
	    } GROUP BY ?Level

 2. Count feature changes occurring per year  :
 

	    SELECT DISTINCT ?year (COUNT(DISTINCT ?change) AS ?changeCount) WHERE{
    	    {
    		    ?change a hht:FeatureChange.
    		     ?change hht:before ?version.
    		    ?version hht:validityPeriod ?interval.
    		    ?interval <http://www.w3.org/2006/time#hasEnd> ?start.
    		    ?start <http://www.w3.org/2006/time#inXSDgYear> ?year.
    		} UNION {
    		    ?change a hht:Appearance.
    		    ?change hht:after ?version.
    		    ?version hht:validityPeriod ?interval.
    		    ?interval <http://www.w3.org/2006/time#hasBeginning> ?start.
    		    ?start <http://www.w3.org/2006/time#inXSDgYear> ?year.
    	    }
        } GROUP BY ?year ORDER BY ?year

 3. Count composite changes occurring per year  :

	    SELECT ?year (COUNT(DISTINCT ?change) AS ?changeCount)WHERE{
	    	?change a hht:CompositeChange.
	    	?changeF hht:isPartOf ?change.
	    	?changeF hht:before ?version.
	    	?version hht:validityPeriod ?interval.
	    	?interval time:hasEnd ?start.
	    	?start <http://www.w3.org/2006/time#inXSDgYear> ?year.
	    } GROUP BY ?year ORDER BY ?year

## Querying : comparison with TSN (http://purl.org/net/tsn)

Some queries can be carried out in HHT and not in TSN. Here are some examples :

1. Identify levels taking part in several hierarchies :

		SELECT DISTINCT ?level WHERE {
			{SELECT ?level (COUNT(DISTINCT ?hierarchy) AS ?nbHierarchies) {
				?level a hht:Level.
				?level hht:hasVersion ?v.
				?v hht:isLevelOf ?hierarchy.	
			} GROUP BY ?level.}
			FILTER (?hierarchy > 1).	
		}

2. Identify Units that are part of given territories from different hierarchies :

		SELECT DISTINCT ?unit WHERE {
			?unit a hht:Unit.
			?unit hht:hasUnitVersion ?v.
			?v hht:isMemberOf ?levelV.
			oba:Paroisse hht:hasLevelVersion ?levelV.
			oba:Generalite000007v1 hht:contains ?v.
			oba:Diaconne000106v1 hht:contains ?v.	
		}
		
Some queries easily written in TSN get extremely verbose with HHT. For example if we want to get all the units being part of oba:Generalite000007 at the same time as oba:Paroisse015267, it will be written in TSN : 

		SELECT DISTINCT ?unit WHERE {
			?unit a tsn:Unit.
			?unit tsn:hasVersion ?v.
			?v tsn:isMemberOf ?levelV.
			?levelV tsn:isDivisionOf ?nomenclature.
			oba:Generalite000007 tsn:hasVersion ?generalV.
			oba:Paroisse015267 tsn:hasVersion ?vParoisse.
			?generalV tsn:hasSubFeature ?vParoisse.
			?generalV tsn:hasSubFeature ?v.
		}
It is much more verbose in HHT :

		SELECT DISTINCT ?unit WHERE {
			?unit a hht:Unit.
			?unit hht:hasUnitVersion ?v.
			oba:Generalite000007 hht:hasUnitVersion ?generalV.
			?generalV hht:hasSubUnit ?v.
			{SELECT ?datestart ?dateend WHERE{
				oba:Paroisse015267 hht:hasVersion ?vParoisse.
				?generalV hht:hasSubUnit ?vParoisse.
				?generalV hht:validityPeriod ?gInterval.
				?gInterval time:hasBeginning ?gBegin.
				?gBegin time:inXSDgYear ?gBeginYear.
				?gInterval time:hasEnd ?gEnd.
				?gEnd time:inXSDgYear ?gEndYear.
				?vParoisse hht:validityPeriod ?pInterval.
				?pInterval time:hasBeginning ?pBegin.
				?pBegin time:inXSDgYear ?pBeginYear.
				?pInterval time:hasEnd ?pEnd.
				?pEnd time:inXSDgYear ?pEndYear.
				BIND(IF(?pBeginYear < ?gBeginYear, ?gBeginYear, ?pBeginYear) AS ?datestart)
				BIND(IF(?pEndYear > ?gEndYear, ?gEndYear, ?pENdYear) AS ?dateend)		
			}
			{SELECT ?datestartV ?dateendV WHERE{
				?generalV hht:validityPeriod ?gInterval.
				?gInterval time:hasBeginning ?gBegin.
				?gBegin time:inXSDgYear ?gBeginYear.
				?gInterval time:hasEnd ?gEnd.
				?gEnd time:inXSDgYear ?gEndYear.
				?v hht:validityPeriod ?pInterval.
				?pInterval time:hasBeginning ?pBegin.
				?pBegin time:inXSDgYear ?pBeginYear.
				?pInterval time:hasEnd ?pEnd.
				?pEnd time:inXSDgYear ?pEndYear.
				BIND(IF(?pBeginYear < ?gBeginYear, ?gBeginYear, ?pBeginYear) AS ?datestartV)
				BIND(IF(?pEndYear > ?gEndYear, ?gEndYear, ?pENdYear) AS ?dateendV)		
			}
			FILTER((?datestartV >= ?datestart && ?datestartV <= ?dateend) ||(?dateendV >= ?datestart && ?dateendV <= ?dateend)
		}

Still, the opposite is true for some queries. If we want to query for a list of all the actual changes occuring at a specific date, in TSN it will be written :

		SELECT DISTINCT ?date WHERE {
			oba:versionA tsn:isMemberOf ?levelV.
			?levelV tsn:isDivisionOf ?nomenclatureV.
			oba:versionA tsn:isVersionOf ?A.
			?nomenclatureV tsn:referencePeriod ?intervalA.
			?intervalA time:hasEnd ?endA.
			?endA time:inXSDgYear ?endDateA.
			?nomenclatureV tsn:isVersionOf ?nomenclature.
			?nomenclature tsn:hasVersion ?otherV.
			?otherV tsn:referencePeriod ?intervalOther.
			?intervalOther time:hasBeginning ?beginOther.
			?beginOther time:inXSDgYear ?date.
			FILTER (?date >= ?endDateA)
			?A tsn:hasVersion ?aV.
			?aV tsn:isMemberOf ?levelaV.
			?levelaV tsn:isDivisionOf ?otherV.
			oba:versionA tsn:hasGeometry ?geoA.
			?aV tsn:hasGeometry ?geoAv.
			FILTER(?aV != ?geoAv).
			oba:versionA tsn:hasName ?nameA.
			?aV tsn:hasName ?nameAv.
			FILTER(?nameA != ?nameAv).
		} ORDER BY ?date LIMIT 1

While in HHT it can be expressed as :


		SELECT DISTINCT ?date WHERE {
			oba:versionA hht:hasNextVersion ?nV.
			oba:versionA hht:validityPeriod ?Interval.
			?Interval time:hasEnd ?end.
			?end time:inXSDgYear ?date.
		}

## Alignment with fundational ontologies

We are working on aligning our ontology with DOLCE and BFO. As of now, we are considering the following super classes for our concepts. These alignments will be added to the ontology's specification after they are discussed with specialists of foundational ontology.

|HHT Class| BFO Super Class| DOLCE Super Class|
|--|--|--|
| Territory  | Fiat Object Part | Non-Agentive Physical Object|
| Version | Occurent | State|
| Level | Generally Dependent Continuant | Non-Agentive Social Object |
| Hierarchical Criterion | Generally Dependent Continuant | Non-Agentive Social Object |