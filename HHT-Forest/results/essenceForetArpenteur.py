from rdflib import Graph
import folium
from folium import plugins
from folium.plugins import MarkerCluster
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import matplotlib.pyplot as plt

g = Graph()
g.parse("Turtle/peuplementBoisement.ttl", format="ttl")

qres = g.query(
    """
    SELECT ?foret ?essence ?x ?y ?arpenteur
    WHERE {
        ?foret a <https://w3id.org/HHT/Forest#AfforestationVersion>.
        FILTER(STRENDS(STR(?foret), "V0")).
        ?foret <https://w3id.org/HHT/Forest#X> ?x.
        ?foret <https://w3id.org/HHT/Forest#Y> ?y.
        ?foret <https://w3id.org/HHT/Forest#hasStand> ?peup.
        ?peup <https://w3id.org/HHT/Forest#containsSpecies> ?essence.
        ?foret <https://w3id.org/HHT/Forest#isArpentedBy> ?arpenteur.

    }
    """
)

# On récupère les résultats de la requête
qres = [(row.foret, row.essence, row.x, row.y, row.arpenteur) for row in qres]

# On crée un DataFrame à partir des listes precedentes et des coordonnees des requetes, que l'on formate pour avoir des noms lisibles
df = pd.DataFrame(qres, columns=['bois', 'essence', 'x', 'y', 'arpenteur'])
df['bois'] = df['bois'].astype(str).apply(lambda x: x.replace("http://test.org/", "").replace("V0", ""))
df['essence'] = df['essence'].astype(str).apply(lambda x: x.replace("http://test.org/", ""))
df['arpenteur'] = df['arpenteur'].astype(str).apply(lambda x: x.replace("http://test.org/", ""))


#Transformer les points de coordonnées de lambert 93 en latitude longitude pour les afficher sur la carte
df['geometry'] = [Point(x, y) for x, y in zip(df['x'], df['y'])]
gdf = gpd.GeoDataFrame(df, geometry='geometry', crs='EPSG:2154')
gdf = gdf.to_crs('EPSG:4326')
gdf['latitude'] = gdf['geometry'].apply(lambda x: x.y)
gdf['longitude'] = gdf['geometry'].apply(lambda x: x.x)
gdf = gdf.drop(columns=['geometry'])

#Créer une carte centrée sur la france en utilisant la librairie folium
m = folium.Map(location=[46.603354, 1.888334], zoom_start=6)
arpenteurs = df['arpenteur'].unique()

#Pour chaque arpenteur, pn lui associe une couleur aleatoire pour les marqueurs
colors = {arpenteur: f"#{hex(0x0000FF + (int(0xFFFF/len(arpenteurs)) * i))[2:]}" for i, arpenteur in enumerate(arpenteurs)}

#On crée un layer pour chaque essence de bois
layers = {}
for essence in df['essence'].unique():
    layers[essence] = folium.FeatureGroup(name=essence, show=False)
    m.add_child(layers[essence])


# Pour chaque ligne du dataframe, on ajoute un marqueur sur la carte, avec une couleur differente pour chaque arpenteur, qui nous affiche les données voulues
for row in gdf.iterrows():
    row = row[1]
    folium.Marker(
        location=[row['latitude'], row['longitude']],
        popup=f"Bois : {row['bois']} - Arpenteur : {row['arpenteur']}",
        icon=folium.Icon(color='black',icon_color=colors[row['arpenteur']])
    ).add_to(layers[row['essence']])

#Ajouter un cluster de marqueurs à chaque layer correspondant à une essence de bois
for essence in df['essence'].unique():
    plugins.MarkerCluster().add_to(layers[essence])

# Désactive tous les layers par defaut
folium.LayerControl(collapsed=False).add_to(m)

# Sauvegarder la carte dans un fichier html
m.save('results/essenceForetArpenteur.html')
