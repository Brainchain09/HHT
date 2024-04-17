## New York City

This dataset details the expansion of the City of New York. As it uses the set operators to compute geometries it can not be analysed using the algorithm as of now. 
This dataset was built manually using informations found in :
MACY JR, Harry. Before the Five-Borough City: The Old Cities, Towns, and Villages That Came Together to Form ‘Greater New York.’. The New York Genealogical and Biographical Society, 1995, p. 3-10.
Available at : https://anthonywrobins.com/MASresources/Before.The.Five.Boroughs.Harry1.Macy.pdf

**NY.ttl is a description of the dataset using the previous geometry formalism of HHT, while NYV2.ttl uses the new formalism, which is significantly more expressive.**


For example, in NY.ttl, you can find :

    obaData:Yonkers_V0 a hht:UnitVersion;
        hht:validityPeriod oba:1788-1873;
        hht:isMemberOf oba:Town.
    
    obaData:Yonkers_V1 a hht:UnitVersion;
        hht:validityPeriod oba:1873-1998;
        hht:isMemberOf oba:Town.

The versions seem to be exactly the same, because the expressiveness of the ontology is not sufficient to express the evolution? In NYV2.ttl however, the description allows to see the change :

    obaData:Yonkers_V0 a hht:UnitVersion;
        hht:validityPeriod oba:1788-1873;
        hht:isMemberOf oba:Town;
        hht:hasSetGeometry [hht:hasComponent _:BB_Yonkers, _:BB_Kingsbridge;
        hht:operatorCardinality "2"].
        
    obaData:Yonkers_V1 a hht:UnitVersion;
        hht:validityPeriod oba:1873-1998;
        hht:isMemberOf oba:Town;
        hht:hasSetGeometry [hht:hasComponent _:BB_Yonkers;
        hht:operatorCardinality "1"].

**Time focus :** 1788-1998

|Level|Units  |Versions |
|---------|--| -- |
|  **City**       | 4  | 11 |
|  **Town**       | 27 | 35 |
|  Borough       | 5 | 6 |
|  Village      | 2 | 3 |
|  County     | 7  | 13 |
|  State     |1 | 1 |






