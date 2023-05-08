# -*- coding: utf-8 -*-
"""
CensusVis.py

Author: Anderson Wong

Date: May 08, 2023

Description: This is a Python program that generates interactive data visualizations using
census linked data. The generated visualization is saved as an HTML file in your current
working directory and can be opened using any web browser. 
"""

import folium
import shapely.wkt
import pandas
import geojson
import sparql_dataframe
import CensusTools

from SPARQLWrapper import SPARQLWrapper, SPARQLWrapper2, JSON

# Set the SPARQL endpoint to the Canadian Census GraphDB
sparql = SPARQLWrapper("http://ec2-3-97-59-180.ca-central-1.compute.amazonaws.com:7200/repositories/CACensus")
sparql.setReturnFormat(JSON)
sparql2 = SPARQLWrapper2("http://ec2-3-97-59-180.ca-central-1.compute.amazonaws.com:7200/repositories/CACensus")
endpoint = "http://ec2-3-97-59-180.ca-central-1.compute.amazonaws.com:7200/repositories/CACensus"

# Initialize a GeoJSON variable
geoj = {"type": "FeatureCollection", "features": []}

# Print a welcome message for the user
print("Welcome! This Python program will generate an interactive map using data returned from a SPARQL query.")

# Prompt user to enter an administrative area. Prompt user to try again if input is invalid. 
while True:
    area = input("Please enter the class name of the administrative area to be visualized (Choose one of: CensusTract, Neighbourhood, Ward, PoliceDivision):")
    if area in ("CensusTract", "Neighbourhood", "Ward", "PoliceDivision"):
        break
    else:
        print("Sorry, your input is invalid.  Please enter 'CensusTract' or 'Neighbourhood' or 'Ward' or 'PoliceDivision' (case-sensitive)")
        continue
    
# Prompt user to enter a characteristic class name. Prompt user to try again if input is invalid. 
while True:
    characteristic = input("Please enter the class name of the characteristic to be visualized (e.g. LowIncomeMeasureAfterTax2016):")
    sparql.setQuery("PREFIX uoft: <http://ontology.eil.utoronto.ca/tove/cacensus#> ASK {uoft:" + characteristic + " rdfs:subClassOf uoft:Characteristic}")
    results = sparql.query().convert()
    if results["boolean"]:
        break
    else:
        print("Sorry, the class name you have entered is not in the graph database.  Please try again.")
        continue
    
# Prompt user to enter a display name for the characteristic.
indicator = input("Please enter the display name of the indicator (e.g. Number of low-income individuals) that is being visualized: ")

# Prompt user to enter a file name for the generated visualization HTML file.
filename = input("Please enter a file name for the visualization (e.g. entering 'map' would save the visualization as 'map.html'): ")

# Print "Generating visualization" to inform the user that the visualization is being generated
print("\nGenerating visualization...\n")

# SPARQL query to check whether the characteristic has values for male/female population
sparql.setQuery("PREFIX uoft: <http://ontology.eil.utoronto.ca/tove/cacensus#> PREFIX iso21972: <http://ontology.eil.utoronto.ca/ISO21972/iso21972#> PREFIX foaf: <http://xmlns.com/foaf/0.1/> ASK {uoft:Male" + characteristic + " rdfs:subClassOf foaf:Person}")
results = sparql.query().convert()

# If CensusTract was selected as the administrative area, use one of the following 2 SPARQL queries.
if area == "CensusTract":    
    if results["boolean"]:
        """
        If values for male/female population exist, query for:
            ?areaname: Name of the administrative area
            ?areawkt: The polygon coordinates for the administrative area in WKT format
            ?sumvalue: The value of the characteristic for the total population
            ?sumvaluemale: The value of the characteristic for the male population
            ?sumvaluefemale: The value of the characteristic for the female population
        """
        
        q = """
        PREFIX uoft: <http://ontology.eil.utoronto.ca/tove/cacensus#>
        PREFIX toronto: <http://ontology.eil.utoronto.ca/Toronto/Toronto#>
        PREFIX iso21972: <http://ontology.eil.utoronto.ca/ISO21972/iso21972#> 
        PREFIX iso50871: <http://ontology.eil.utoronto.ca/5087/1/SpatialLoc/>
        PREFIX iso5087m: <http://ontology.eil.utoronto.ca/5087/1/Mereology/>
        PREFIX geo: <http://www.opengis.net/ont/geosparql#>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        SELECT DISTINCT ?areaname
        ?sumvalue
        ?areawkt
        ?sumvaluemale
        ?sumvaluefemale
        
        WHERE{
        ?area a toronto:""" + area + """;
        rdfs:comment ?areaname;
        iso50871:hasLocation ?location. 
       
        ?location geo:asWKT ?areawkt.
        
        ?limat a uoft:""" + characteristic + """; 
        uoft:hasLocation ?area; 
        iso21972:cardinality_of ?population; 
        iso21972:value ?measure.
        
        ?measure iso21972:numerical_value ?sumvalue. 
    
        ?population a ?populationclass. 
        ?populationclass iso21972:defined_by uoft:Person""" + characteristic + """.
        
        ?limatmale a uoft:""" + characteristic + """; 
        uoft:hasLocation ?area; 
        iso21972:cardinality_of ?populationmale; 
        iso21972:value ?measuremale.
            
        ?measuremale iso21972:numerical_value ?sumvaluemale. 
        
        ?populationmale a ?populationclassmale. 
        ?populationclassmale iso21972:defined_by uoft:Male""" + characteristic + """.
        
        ?limatfemale a uoft:""" + characteristic + """; 
        uoft:hasLocation ?area; 
        iso21972:cardinality_of ?populationfemale; 
        iso21972:value ?measurefemale.
            
        ?measurefemale iso21972:numerical_value ?sumvaluefemale. 
    
        ?populationfemale a ?populationclassfemale. 
        ?populationclassfemale iso21972:defined_by uoft:Female""" + characteristic + """.
        } 
        """
    
        # Converts SPARQL query results into a Pandas DataFrame
        df = sparql_dataframe.get(endpoint, q)
        
        # Adds the data in the DataFrame to the geoj GeoJSON variable
        for index, row in df.iterrows():
            geoj["features"].append(geojson.Feature(geometry=shapely.wkt.loads(row['areawkt']), properties={"areaname": row["areaname"], "sumvalue": row["sumvalue"], "sumvaluemale": row["sumvaluemale"], "sumvaluefemale": row["sumvaluefemale"]}))
    
    else:
        """
        Else, query for:
            ?areaname: Name of the administrative area
            ?areawkt: The polygon coordinates for the administrative area in WKT format
            ?sumvalue: The value of the characteristic for the total population
        """
        
        q = """
        PREFIX uoft: <http://ontology.eil.utoronto.ca/tove/cacensus#>
        PREFIX toronto: <http://ontology.eil.utoronto.ca/Toronto/Toronto#>
        PREFIX iso21972: <http://ontology.eil.utoronto.ca/ISO21972/iso21972#> 
        PREFIX iso50871: <http://ontology.eil.utoronto.ca/5087/1/SpatialLoc/>
        PREFIX iso5087m: <http://ontology.eil.utoronto.ca/5087/1/Mereology/>
        PREFIX geo: <http://www.opengis.net/ont/geosparql#>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        SELECT DISTINCT ?areaname
        ?areawkt
        ?sumvalue
        FROM <http://www.ontotext.com/explicit>
        WHERE{
        ?area a toronto:""" + area + """;
        rdfs:comment ?areaname;
        iso50871:hasLocation ?location. 
       
        ?location geo:asWKT ?areawkt.
        
        ?limat a uoft:""" + characteristic + """; 
        uoft:hasLocation ?area; 
        iso21972:value ?measure.
        
        ?measure iso21972:numerical_value ?sumvalue. 
        } 
        """
    
        # Converts SPARQL query results into a Pandas DataFrame
        df = sparql_dataframe.get(endpoint, q)
        
        # Adds the data in the DataFrame to the geoj GeoJSON variable
        for index, row in df.iterrows():
            geoj["features"].append(geojson.Feature(geometry=shapely.wkt.loads(row['areawkt']), properties={"areaname": row["areaname"], "sumvalue": row["sumvalue"]}))
        
# Else, use one of the following 2 SPARQL queries.      
else:
    if results["boolean"]:
        """
        If values for male/female population exist, query for:
            ?areaname: Name of the administrative area
            ?areawkt: The polygon coordinates for the administrative area in WKT format
            ?censuswkt: The polygon coordinates for a census tract located in the administrative area in WKT format
            ?sumvalue: The value of the characteristic for the total population in the census tract
            ?sumvaluemale: The value of the characteristic for the male population in the census tract
            ?sumvaluefemale: The value of the characteristic for the female population in the census tract
        """
        
        sparql2.setQuery("""
        PREFIX uoft: <http://ontology.eil.utoronto.ca/tove/cacensus#>
        PREFIX toronto: <http://ontology.eil.utoronto.ca/Toronto/Toronto#>
        PREFIX iso21972: <http://ontology.eil.utoronto.ca/ISO21972/iso21972#> 
        PREFIX iso50871: <http://ontology.eil.utoronto.ca/5087/1/SpatialLoc/>
        PREFIX iso5087m: <http://ontology.eil.utoronto.ca/5087/1/Mereology/>
        PREFIX geo: <http://www.opengis.net/ont/geosparql#>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        SELECT DISTINCT ?areaname
        ?areawkt
        ?censuswkt
        ?value
        ?valuemale
        ?valuefemale
    
        WHERE{
        ?area a toronto:""" + area + """;
        iso50871:hasLocation ?location;
        rdfs:comment ?areaname;
        toronto:hasCensusTract ?censustract.
           
        ?location geo:asWKT ?areawkt.
        
        ?censustract iso50871:hasLocation ?censuslocation.
        
        ?censuslocation geo:asWKT ?censuswkt.
            
        ?limat a uoft:""" + characteristic + """; 
        uoft:hasLocation ?censustract; 
        iso21972:cardinality_of ?population; 
        iso21972:value ?measure.
            
        ?measure iso21972:numerical_value ?value. 
    
        ?population a ?populationclass. 
        ?populationclass iso21972:defined_by uoft:Person""" + characteristic + """.
        
        ?limatmale a uoft:""" + characteristic + """; 
        uoft:hasLocation ?censustract; 
        iso21972:cardinality_of ?populationmale; 
        iso21972:value ?measuremale.
            
        ?measuremale iso21972:numerical_value ?valuemale. 
    
        ?populationmale a ?populationclassmale. 
        ?populationclassmale iso21972:defined_by uoft:Male""" + characteristic + """.
        
        ?limatfemale a uoft:""" + characteristic + """; 
        uoft:hasLocation ?censustract; 
        iso21972:cardinality_of ?populationfemale; 
        iso21972:value ?measurefemale.
            
        ?measurefemale iso21972:numerical_value ?valuefemale. 
    
        ?populationfemale a ?populationclassfemale. 
        ?populationclassfemale iso21972:defined_by uoft:Female""" + characteristic + """.
        } 
        """)
        
        # Initializes a dictionary variable for storing the results of the query
        dic = {}
        
        # Initializes a dictionary variable that will be converted to a Pandas DataFrame
        dfdic = {"areaname": [], "wkt": [], "sumvalue": [], "sumvaluemale": [], "sumvaluefemale": []}
        
        # Iterates through each SPARQL query result
        for result in sparql2.query().bindings:
            """
            Creates a key:value pair in the dic dictionary to store data for the administrative area 
            if it does not already exist.  Each administrative area has its own dictionary containing:
                areaname: The name of the administrative area
                wkt: The polygon coordinates for the administrative area in WKT format
                sumvalue: The value of the characteristic for the total population in the administrative area
                sumvaluemale: The value of the characteristic for the male population in the administrative area
                sumvaluefemale: The value of the characteristic for the female population in the administrative area
            """
            if not(str(result["areaname"].value) in dic):
                dic[str(result["areaname"].value)] = {"areaname": str(result["areaname"].value), "wkt": str(result["areawkt"].value), "sumvalue": 0, "sumvaluemale": 0, "sumvaluefemale": 0}
            
            # Get the total, male, female values of the characteristic from the query result
            try: 
                value = float(result["value"].value)
                valuemale = float(result["valuemale"].value)
                valuefemale = float(result["valuefemale"].value)
            # If there's an error (due to no data), set values to 0
            except:
                value = 0
                valuemale = 0
                valuefemale = 0
            
            # Uses the wktintersect function from the CensusTools module to calculate how much
            # of the census tract overlaps with the administrative area
            multiplier = CensusTools.wktintersect(str(result["censuswkt"].value), str(result["areawkt"].value))
            
            # Multiply the result by the total, male, female values
            mvalue = multiplier * value
            mvaluemale = multiplier * valuemale
            mvaluefemale = multiplier * valuefemale
            
            # Add the calculated total, male, female values to the administrative 
            # area's sumvalue, sumvaluemale, sumvaluefemale, respectively
            dic[str(result["areaname"].value)]["sumvalue"] += mvalue
            dic[str(result["areaname"].value)]["sumvaluemale"] += mvaluemale
            dic[str(result["areaname"].value)]["sumvaluefemale"] += mvaluefemale
        
        # Iterates through the dic dictionary and converts the data into GeoJSON and Pandas DataFrame format
        for key in dic:
            # Round sumvalue, sumvaluemale, sumvaluefemale to the nearest whole number
            sumvalue = round(dic[key]["sumvalue"])
            sumvaluemale = round(dic[key]["sumvaluemale"])
            sumvaluefemale = round(dic[key]["sumvaluefemale"])
            
            # Converts data to GeoJson
            geoj["features"].append(geojson.Feature(geometry=shapely.wkt.loads(dic[key]['wkt']), properties={"areaname": dic[key]["areaname"], "sumvalue": sumvalue, "sumvaluemale": sumvaluemale, "sumvaluefemale": sumvaluefemale}))
            
            # Converts data to a dictionary that is compatible with Pandas DataFrame
            dfdic["areaname"].append(dic[key]["areaname"])
            dfdic["wkt"].append(dic[key]["wkt"])
            dfdic["sumvalue"].append(sumvalue)
            dfdic["sumvaluemale"].append(sumvaluemale)
            dfdic["sumvaluefemale"].append(sumvaluefemale)
        
        # Converts the dfdic dictionary into a Pandas DataFrame
        df = pandas.DataFrame(dfdic)
    else:
        """
        Else, query for:
            ?areaname: Name of the administrative area
            ?areawkt: The polygon coordinates for the administrative area in WKT format
            ?censuswkt: The polygon coordinates for a census tract located in the administrative area in WKT format
            ?sumvalue: The value of the characteristic for the total population in the census tract
        """
        
        sparql2.setQuery("""
        PREFIX uoft: <http://ontology.eil.utoronto.ca/tove/cacensus#>
        PREFIX toronto: <http://ontology.eil.utoronto.ca/Toronto/Toronto#>
        PREFIX iso21972: <http://ontology.eil.utoronto.ca/ISO21972/iso21972#> 
        PREFIX iso50871: <http://ontology.eil.utoronto.ca/5087/1/SpatialLoc/>
        PREFIX iso5087m: <http://ontology.eil.utoronto.ca/5087/1/Mereology/>
        PREFIX geo: <http://www.opengis.net/ont/geosparql#>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        SELECT DISTINCT ?areaname
        ?areawkt
        ?censuswkt
        ?value
        
        FROM <http://www.ontotext.com/explicit>
        
        WHERE{
        ?area a toronto:""" + area + """;
        iso50871:hasLocation ?location;
        rdfs:comment ?areaname;
        toronto:hasCensusTract ?censustract.
           
        ?location geo:asWKT ?areawkt.
        
        ?censustract iso50871:hasLocation ?censuslocation.
        
        ?censuslocation geo:asWKT ?censuswkt.
            
        ?limat a uoft:""" + characteristic + """; 
        uoft:hasLocation ?censustract; 
        iso21972:value ?measure.
            
        ?measure iso21972:numerical_value ?value. 
        } 
        """)
        
        # Initializes a dictionary variable for storing the results of the query
        dic = {}
        
        # Initializes a dictionary variable that will be converted to a Pandas DataFrame
        dfdic = {"areaname": [], "wkt": [], "sumvalue": []}
        
        # Iterates through each SPARQL query result
        for result in sparql2.query().bindings:
            """
            Creates a key:value pair in the dic dictionary to store data for the administrative area 
            if it does not already exist.  Each administrative area has its own dictionary containing:
                areaname: The name of the administrative area
                wkt: The polygon coordinates for the administrative area in WKT format
                sumvalue: The value of the characteristic for the total population in the administrative area
            """
            if not(str(result["areaname"].value) in dic):
                dic[str(result["areaname"].value)] = {"areaname": str(result["areaname"].value), "wkt": str(result["areawkt"].value), "sumvalue": 0}
            
            # Get the value of the characteristic from the query result
            try: 
                value = float(result["value"].value)
            # If there's an error (due to no data), set value to 0
            except:
                value = 0
            
            # Uses the wktintersect function from the CensusTools module to calculate how much
            # of the census tract overlaps with the administrative area
            multiplier = CensusTools.wktintersect(str(result["censuswkt"].value), str(result["areawkt"].value))
            
            # Multiply the result by the values
            mvalue = multiplier * value
            
            # Add the calculated value to the administrative area's sumvalue
            dic[str(result["areaname"].value)]["sumvalue"] += mvalue
        
        # Iterates through the dic dictionary and converts the data into GeoJSON and Pandas DataFrame format
        for key in dic:
            # Round sumvalue to the nearest whole number
            sumvalue = round(dic[key]["sumvalue"])
            
            # Converts data to GeoJson
            geoj["features"].append(geojson.Feature(geometry=shapely.wkt.loads(dic[key]['wkt']), properties={"areaname": dic[key]["areaname"], "sumvalue": sumvalue}))
            
            # Converts data to a dictionary that is compatible with Pandas DataFrame
            dfdic["areaname"].append(dic[key]["areaname"])
            dfdic["wkt"].append(dic[key]["wkt"])
            dfdic["sumvalue"].append(sumvalue)
        
        # Converts the dfdic dictionary into a Pandas DataFrame
        df = pandas.DataFrame(dfdic)

# Create a folium map centered at the location specified by the coordinates
m = folium.Map(location=[43.6581,-79.3845], zoom_start=12)

# Create a colour scale based on the characteristic values from the data in the Pandas DataFrame
custom_scale = (df["sumvalue"].quantile((0,0.2,0.4,0.6,0.8,1))).tolist()

# Create a choropleth layer using the data in the GeoJSON and Pandas DataFrame and add it to the folium map
choro = folium.Choropleth(
    # Use geo data from the geoj GeoJSON variable for the choropleth layer
    geo_data=geoj,
    # Use the display name entered by the user as the name of the choropleth layer
    name=indicator,
    # Use data from the df Pandas DataFrame for the choropleth layer
    data=df,
    # Create polygons of the administrative areas and color them according to their sumvalue
    columns=["areaname", "sumvalue"],
    key_on="feature.properties.areaname",
    # Use the custom_scale color scale for coloring the visualization
    threshold_scale=custom_scale, 
    # Color the visualization using yellow, orange, and red
    fill_color='YlOrRd',
    # Use the color white if the value of the characteristic is 0
    nan_fill_color="White",
    # Set the opacity of the polygons
    fill_opacity=0.7,
    # Set the opacity of the polygon outlines
    line_opacity=0.2,
    # Use the display name entered by the user for the color legend in the top right of the visualization
    legend_name=indicator,
    # Highlight if polygon is selected
    highlight=True,
    # Set polygon outline color to black
    line_color='black'
    ).add_to(m)

# If values for male/female population exist, create a GeoJSON object containing popup boxes 
# that show the administrative area name and the total, male, female values for the characteristic
if results["boolean"]:
    folium.features.GeoJson(
        # Use data from the geoj GeoJSON variable for the popup boxes
        data=geoj,
        # Use the display name entered by the user as the name for the GeoJSON object
        name=indicator,
        # Set smooth factor to 2. More means better performance and smoother look, and less means more accurate representation.
        smooth_factor=2,
        # Set the color, fill color to transparent and stroke width (weight) to 0.5 
        style_function=lambda x: {'color':'transparent','fillColor':'transparent','weight':0.5},
        # Create popup boxes that show the administrative area name and the total, male, female values for the characteristic
        tooltip=folium.features.GeoJsonTooltip(
            # Use areaname, sumvalue, sumvaluemale, sumvaluefemale from geoj as values for the popup box
            fields=['areaname',
                    'sumvalue',
                    'sumvaluemale',
                    'sumvaluefemale'
                    ],
            # Use the administrative area type and the display name entered by the user as labels for the above values
            aliases=[area,
                     indicator + " (Total)",
                     indicator + " (Male)",
                     indicator + " (Female)"
                     ], 
            # Use JavaScript’s .toLocaleString() to format values (i.e. comma separators, float truncation)
            localize=True,
            # Use to set whether the popup box follows the mouse cursor
            sticky=False,
            # Use to toggle whether to show the labels and values
            labels=True,
            # Set max width of the popup box
            max_width=800,)
        ).add_to(choro)
# Else, create a GeoJSON object containing popup boxes showing the administrative area name and the value for the characteristic
else:
    folium.features.GeoJson(
        # Use data from the geoj GeoJSON variable for the popup boxes
        data=geoj,
        # Use the display name entered by the user as the name for the GeoJSON object
        name= indicator,
        # Set smooth factor to 2. More means better performance and smoother look, and less means more accurate representation.
        smooth_factor=2,
        # Set the color, fill color to transparent and stroke width (weight) to 0.5 
        style_function=lambda x: {'color':'transparent','fillColor':'transparent','weight':0.5},
        # Create popup boxes that show the administrative area name and the value for the characteristic
        tooltip=folium.features.GeoJsonTooltip(
            # Use areaname, sumvalue from geoj as values for the popup box
            fields=['areaname',
                    'sumvalue',
                    ],
            # Use the administrative area type and the display name entered by the user as labels for the above values
            aliases=[area,
                     indicator
                     ], 
            # Use JavaScript’s .toLocaleString() to format values (i.e. comma separators, float truncation)
            localize=True,
            # Use to set whether the popup box follows the mouse cursor
            sticky=False,
            # Use to toggle whether to show the labels and values
            labels=True,
            # Set max width of the popup box
            max_width=800,)
        ).add_to(choro)

# Add a LayerControl to the map which adds a toggle for showing/hiding the choropleth layer
folium.LayerControl().add_to(m)

# Save the visualization map using the file name specified by the user
m.save(filename + ".html")

# Print completion message
print("Done! Your visualization has been saved as " + filename + ".html in your current working directory.")

