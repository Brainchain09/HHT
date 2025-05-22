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

maitrise_v0_colors = {
    "Comminges_(Saint-Gaudens)": "blue",
    "Quillan_(Quillan)": "orange",
    "Lauragais_(Castelnaudary)": "darkred",
    "Montpellier_(Montpellier)": "purple",
    "L'Isle-Jourdain_(L'Isle-Jourdain)": "green",
    "Toulouse_(Villemur)": "red",
    "Toulouse": "red",
    "Pamiers_(Pamiers": "darkblue",
    "Rodez_(Rodez)": "gray"
}

maitrise_v1_colors = {
    "L'Isle-Jourdain_(L'Isle-Jourdain)": "green",
    "Comminges_(Saint-Gaudens)": "blue",
    "St-Pons_(Saint-Pons)": "darkgreen",
    "Tarbes_(Tarbes)": "pink",
    "Quillan_(Quillan)": "orange",
    "Rodez_(Rodez)": "gray",
    "Villeneuve_de_Berg_(Villeneuve_de_Berg)": "lightblue",
    "Pamiers_(Pamiers": "darkblue",
    "Toulouse_(Villemur)": "red",
    "Lauragais_(Castelnaudary)": "darkred",
    "Montpellier_(Montpellier)": "purple"
}

qres = g.query(
    """
    SELECT ?bois ?foret ?x ?y ?maitrise
    WHERE {
        ?bois a <https://w3id.org/HHT/Forest#boisement>.
        ?bois hht:hasVersion ?foret.
        ?foret <https://w3id.org/HHT/Forest#X> ?x.
        ?foret <https://w3id.org/HHT/Forest#Y> ?y.

        ?foret hht:isMemberOf ?maitrise.
        FILTER(STRSTARTS(STR(?maitrise), "http://test.org/MaitriseParticuliere")).

    }
    """
)

qres = [row for row in qres if row.x != 0.0 and row.y != 0.0]

# On récupère les résultats de la requête, pour chaque boisement, je lui relie ses maitrises judiciaires V0 et V1
bois = list(set([row.bois for row in qres]))
bois_maitrises = {}
for i in range(len(bois)):
    bois_maitrises[bois[i]] = {"v0": "", "v1": ""}
for row in qres:
    if row.maitrise.endswith("V0"):
        bois_maitrises[row.bois]["v0"] = row.maitrise
    else:
        bois_maitrises[row.bois]["v1"] = row.maitrise


# Créer un DataFrame à partir des listes precedentes et des coordonnees des requetes, que l'on formate pour avoir des noms lisibles
df = pd.DataFrame(qres, columns=["bois","foret", "x", "y","maitrise"])
df["x"] = df["x"].astype(float)
df["y"] = df["y"].astype(float)
df['maitriseV0'] = df['bois'].apply(lambda x: bois_maitrises[x]["v0"])
df['maitriseV1'] = df['bois'].apply(lambda x: bois_maitrises[x]["v1"])
df['maitriseV0'] = df['maitriseV0'].astype(str).apply(lambda x: x.replace("http://test.org/MaitriseParticuliere", "").replace("V0", ""))
df['maitriseV1'] = df['maitriseV1'].astype(str).apply(lambda x: x.replace("http://test.org/MaitriseParticuliere", "").replace("V1", ""))
df['bois'] = df['bois'].astype(str).apply(lambda x: x.replace("http://test.org/", ""))
df = df.drop('foret', axis=1)
df = df.drop('maitrise', axis=1)
df = df.drop_duplicates()


# Transformer les points de coordonnées de lambert 93 en latitude longitude pour les afficher sur la carte
df['geometry'] = [Point(xy) for xy in zip(df.x, df.y)]
gdf = gpd.GeoDataFrame(df, geometry='geometry')
gdf.crs = {'init': 'epsg:2154'}
gdf = gdf.to_crs(epsg=4326)
gdf['latitude'] = gdf['geometry'].apply(lambda x: x.y)
gdf['longitude'] = gdf['geometry'].apply(lambda x: x.x)
gdf = gdf.drop('geometry', axis=1)
gdf = gdf.drop('x', axis=1)
gdf = gdf.drop('y', axis=1)
gdf = gdf.drop_duplicates()

# gdf2 et gdf3 sont des dataframes qui contiennent les boisements qui ont une maitrise V0 et V1 respectivement
gdf2 = gdf[gdf['maitriseV0'] != ""]
gdf2 = gdf2.drop('maitriseV1', axis=1)

gdf3 = gdf[gdf['maitriseV1'] != ""]

# Fonction pour changer la couleur des markers en fonction du changement de maitrise
def change_marker_color(maitrise_v0, maitrise_v1):
    if maitrise_v0 == "":
        return 'purple'
    elif maitrise_v0 == maitrise_v1:
        return 'green'
    else:
        return 'red'
    
# Légende personnalisée
legend_html = """
<div style="position: fixed; bottom: 50px; right: 50px; z-index: 9999;">

    <div style="width: auto; height: auto; border: 2px solid grey; font-size: 14px; background-color: white; margin-bottom: 10px;">
        &nbsp;<b>Changement de maîtrise</b><br>
        &nbsp;<i class="fa fa-circle fa-1x" style="color:green"></i>&nbsp;Maitrise inchangée<br>
        &nbsp;<i class="fa fa-circle fa-1x" style="color:red"></i>&nbsp;Maitrise changée<br>
        &nbsp;<i class="fa fa-circle fa-1x" style="color:purple"></i>&nbsp;Maitrise inconnue avant réformation<br>
        &nbsp;<b>Maîtrises Judiciaires</b><br>
        &nbsp;<i class="fa fa-circle fa-1x" style="color:green"></i>&nbsp;L'Isle-Jourdain<br>
        &nbsp;<i class="fa fa-circle fa-1x" style="color:blue"></i>&nbsp;Saint-Gaudens<br>
        &nbsp;<i class="fa fa-circle fa-1x" style="color:darkgreen"></i>&nbsp;Saint-Pons<br>
        &nbsp;<i class="fa fa-circle fa-1x" style="color:pink"></i>&nbsp;Tarbes<br>
        &nbsp;<i class="fa fa-circle fa-1x" style="color:orange"></i>&nbsp;Quillan<br>
        &nbsp;<i class="fa fa-circle fa-1x" style="color:gray"></i>&nbsp;Rodez<br>
        &nbsp;<i class="fa fa-circle fa-1x" style="color:lightblue"></i>&nbsp;Villeneuve de Berg<br>
        &nbsp;<i class="fa fa-circle fa-1x" style="color:darkblue"></i>&nbsp;Pamiers<br>
        &nbsp;<i class="fa fa-circle fa-1x" style="color:red"></i>&nbsp;Toulouse-Villemur<br>
        &nbsp;<i class="fa fa-circle fa-1x" style="color:darkred"></i>&nbsp;Castelnaudary<br>
        &nbsp;<i class="fa fa-circle fa-1x" style="color:purple"></i>&nbsp;Montpellier<br>
    </div>

</div>
"""
# Créer une carte centrée sur la france en utilisant la librairie folium
m = folium.Map(location=[46.603354, 1.888334], zoom_start=6)


# Créer des groupes de marqueurs pour chaque type de maitrise
group_v0 = folium.FeatureGroup("Avant réformation").add_to(m)
group_v1 = folium.FeatureGroup("Après réformation").add_to(m)
group_change = folium.FeatureGroup("Changements de maîtrise").add_to(m)
folium.LayerControl().add_to(m)

# Ajouter les markers avec les couleurs initiales
for idx, row in gdf.iterrows():
    marker = folium.Marker(
        location=[row['latitude'], row['longitude']],  
        popup=f"Nom: {row['bois']}<br>Avant Réformation: {row['maitriseV0']}<br>Après Réformation: {row['maitriseV1']}",
        icon=folium.Icon(color=change_marker_color(row['maitriseV0'], row['maitriseV1']))
    )
    marker.add_to(group_change)

#ajouter les marqueurs pour gdf2 et 3 en liant les couleurs avec les maitrises
for idx, row in gdf2.iterrows():
    marker = folium.Marker(
        location=[row['latitude'], row['longitude']],
        popup=f"Nom: {row['bois']}<br>Avant Réformation: {row['maitriseV0']}",
        icon=folium.Icon(color=maitrise_v0_colors[row['maitriseV0']])
    )
    marker.add_to(group_v0)

for idx, row in gdf3.iterrows():
    marker = folium.Marker(
        location=[row['latitude'], row['longitude']],
        popup=f"Nom: {row['bois']}<br>Avant Réformation: {row['maitriseV0']}<br>Après Réformation: {row['maitriseV1']}",
        icon=folium.Icon(color=maitrise_v1_colors[row['maitriseV1']])
    )
    marker.add_to(group_v1)

# Ajouter la légende personnalisée à la carte
m.get_root().html.add_child(folium.Element(legend_html))
m.save('results/changementMaîtrisesJudiciaires.html')
