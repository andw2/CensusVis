# -*- coding: utf-8 -*-
"""
CensusVis.py

Author: Anderson Wong

Date: August 3, 2023

Description: This is a Python program that generates interactive data visualizations using
census linked data from a SPARQL endpoint. The generated visualization is saved as an HTML 
file in your current working directory that can be opened using any web browser. 
"""
import folium
import shapely.wkt
import pandas
import geojson
import sparql_dataframe
import CensusTools
import sys
import os

from PyQt5.QtWidgets import QApplication, QWidget, QTabWidget, QLineEdit, QPushButton, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QComboBox
from PyQt5.QtCore import Qt
from PyQt5 import QtWebEngineWidgets
from SPARQLWrapper import SPARQLWrapper, SPARQLWrapper2, JSON

# Set the SPARQL endpoint to the Canadian Census GraphDB
sparql = SPARQLWrapper("http://ec2-3-97-59-180.ca-central-1.compute.amazonaws.com:7200/repositories/CACensus")
sparql.setReturnFormat(JSON)
sparql2 = SPARQLWrapper2("http://ec2-3-97-59-180.ca-central-1.compute.amazonaws.com:7200/repositories/CACensus")
endpoint = "http://ec2-3-97-59-180.ca-central-1.compute.amazonaws.com:7200/repositories/CACensus"

# Initialize a GeoJSON variable
geoj = {"type": "FeatureCollection", "features": []}

# Create a QtWindow
class Window(QWidget):
    def __init__(self):
        super().__init__()
        
        # Set window title to "CensusVis"
        self.setWindowTitle("CensusVis")
        
        # Set layout as vertical box layout
        mainlayout = QVBoxLayout()
        self.setLayout(mainlayout)
        
        # Create 2 tabs (1 for visualization, 1 for search) for the window
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tabs.addTab(self.tab2,"Indicator Search")
        self.tabs.addTab(self.tab1,"Visualization Generator")
        mainlayout.addWidget(self.tabs)
        
        # Set layout for visualization tab as vertical box layout
        layout = QVBoxLayout()
        self.tab1.setLayout(layout)
      
        # Print title
        widget = QLabel("Visualization Generator")
        font = widget.font()
        font.setPointSize(20)
        widget.setFont(font)
        widget.setTextInteractionFlags(Qt.TextSelectableByMouse)
        widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(widget)
        
        # Print prompt for administrative area
        widget = QLabel("Type of administrative area to be visualized")
        font = widget.font()
        font.setPointSize(10)
        widget.setFont(font)
        widget.setTextInteractionFlags(Qt.TextSelectableByMouse)
        widget.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(widget)
        
        # Create combo box for administrative area input
        q = """
        PREFIX iso50872: <http://ontology.eil.utoronto.ca/5087/2/City/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT DISTINCT ?area
        FROM <http://www.ontotext.com/explicit>
        WHERE{
        ?area rdfs:subClassOf iso50872:CityAdministrativeArea;
        } 
        """
    
        # Converts SPARQL query results into a Pandas DataFrame
        df = sparql_dataframe.get(endpoint, q)
        
        self.combobox1 = QComboBox()
        # Adds the data in the DataFrame to the geoj GeoJSON variable
        for index, row in df.iterrows():
            if row["area"] != "http://ontology.eil.utoronto.ca/Toronto/Toronto#BusinessImprovementArea":
                self.combobox1.addItem(row["area"].replace("http://ontology.eil.utoronto.ca/Toronto/Toronto#", ""))
        self.combobox1.setFixedWidth(500)
        layout.addWidget(self.combobox1)
        
        # Print prompt for indicator URI
        widget = QLabel("URI of the indicator to be visualized (e.g. http://ontology.eil.utoronto.ca/tove/cacensus#LowIncomeMeasureAfterTax2016).")
        font = widget.font()
        font.setPointSize(10)
        widget.setFont(font)
        widget.setTextInteractionFlags(Qt.TextSelectableByMouse)
        widget.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(widget)
        
        # Create text box for indicator URI input
        self.charainput = QLineEdit()
        self.charainput.setFixedWidth(500)
        layout.addWidget(self.charainput, alignment=Qt.AlignmentFlag.AlignLeft)
        
        # Print prompt for display name
        widget = QLabel("Display name of the indicator (e.g. Number of low-income individuals)")
        font = widget.font()
        font.setPointSize(10)
        widget.setFont(font)
        widget.setTextInteractionFlags(Qt.TextSelectableByMouse)
        widget.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(widget)
        
        # Create text box for display name input
        self.displayinput = QLineEdit()
        self.displayinput.setFixedWidth(500)
        layout.addWidget(self.displayinput, alignment=Qt.AlignmentFlag.AlignLeft)
 
        # Print prompt for file name
        widget = QLabel("File name for the visualization (saved as FileName.html)")
        font = widget.font()
        font.setPointSize(10)
        widget.setFont(font)
        widget.setTextInteractionFlags(Qt.TextSelectableByMouse)
        widget.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(widget)
        
        # Create text box for file name input
        self.fileinput = QLineEdit()
        self.fileinput.setFixedWidth(500)
        layout.addWidget(self.fileinput, alignment=Qt.AlignmentFlag.AlignLeft)   
        
        # Create button to generate the visualization
        button = QPushButton("Generate Visualization")
        button.clicked.connect(self.generate)
        layout.addWidget(button)
        
        # Create a QLabel for the finished message
        self.output = QLabel()
        font = self.output.font()
        font.setPointSize(10)
        self.output.setFont(font)
        self.output.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.output.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.output)       
        
        # Create a web engine widget to show the HTML visualization
        self.webEngineView = QtWebEngineWidgets.QWebEngineView()
        layout.addWidget(self.webEngineView)
        
        # Set layout for search tab as vertical box layout
        layout2 = QVBoxLayout()
        self.tab2.setLayout(layout2)
        
        # Print title
        widget = QLabel("Indicator Search")
        font = widget.font()
        font.setPointSize(20)
        widget.setFont(font)
        widget.setTextInteractionFlags(Qt.TextSelectableByMouse)
        widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout2.addWidget(widget)
        
        # Print welcome message
        widget = QLabel("Welcome! This Python program will generate an interactive map using data returned from a SPARQL query.\n")
        font = widget.font()
        font.setPointSize(10)
        widget.setFont(font)
        widget.setTextInteractionFlags(Qt.TextSelectableByMouse)
        widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout2.addWidget(widget)
        
        # Print search prompt
        widget = QLabel("To begin, please search for an indicator using key words.")
        font = widget.font()
        font.setPointSize(10)
        widget.setFont(font)
        widget.setTextInteractionFlags(Qt.TextSelectableByMouse)
        widget.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout2.addWidget(widget)
        
        # Create text box for search input
        self.searchinput = QLineEdit()
        self.searchinput.setFixedWidth(500)
        layout2.addWidget(self.searchinput, alignment=Qt.AlignmentFlag.AlignLeft)
        
        # Create search button
        button2 = QPushButton("Search")
        button2.clicked.connect(self.search)
        layout2.addWidget(button2)
        
        # Create a QLabel for the finished search message
        self.output2 = QLabel()
        font = self.output2.font()
        font.setPointSize(10)
        self.output2.setFont(font)
        self.output2.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.output2.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout2.addWidget(self.output2)
        
        # Create a table widget to output search results
        self.tableWidget = QTableWidget()
        self.tableWidget.setColumnCount(2)
        self.tableWidget.setColumnWidth(0, 250)
        self.tableWidget.setColumnWidth(1, 600)
        self.tableWidget.setHorizontalHeaderLabels(['Indicator URI', 'Description'])
        self.tableWidget.cellDoubleClicked.connect(self.cell_select)
        layout2.addWidget(self.tableWidget)
    
    # Function that auto fills text fields in the Visualization Generator tab using a selected search result
    def cell_select(self):
        # Get the row number of the selected cell
        row = self.tableWidget.currentItem().row()
        
        # Get the indicator URI
        cell1 = self.tableWidget.item(row, 0).text()
        # Get the indicator description
        cell2 = self.tableWidget.item(row, 1).text()
        
        # Enter the indicator URI into the indicator URI input box
        self.charainput.setText(cell1)
        # Enter the indicator description into the display name input box
        self.displayinput.setText(cell2)
        # Set the default file name as "visualization"
        self.fileinput.setText("Visualization")
        
        # Switch to the Visualization Generator tab 
        self.tabs.setCurrentIndex(1)
        
    
    # Indicator search function    
    def search(self):
        search = self.searchinput.text()
        
        # SPARQL query that returns the indicators that match the user's search terms
        q = """
        PREFIX iso21972: <http://ontology.eil.utoronto.ca/ISO21972/iso21972#> 
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        
        SELECT DISTINCT ?class ?comment
        
        WHERE{
            ?class rdfs:subClassOf iso21972:Indicator;
            rdfs:comment ?comment
            FILTER CONTAINS(lcase(?comment), lcase(\"""" + search + """\")) 
        }
        """
        df = sparql_dataframe.get(endpoint, q)
        
        # Convert results from SPARQL query into a list
        results = []
        for index, row in df.iterrows():
            results.append([row["class"], row["comment"]])
        
        # Output search results as a table
        self.tableWidget.setRowCount(len(results))
        row = 0
        for item in results:
            self.tableWidget.setItem(row, 0, QTableWidgetItem(item[0]))
            self.tableWidget.setItem(row, 1, QTableWidgetItem(item[1]))
            row += 1
        
        self.tableWidget.resizeRowsToContents()
        # Print search result message
        self.output2.setText("Here are the search results for \"" + search + "\".\nDouble clicking on a search result will auto-fill the Visualization Generation tab using the selected indicator.")
        
    # Visualization generator function 
    def generate(self):
        area = self.combobox1.currentText()
        characteristic = self.charainput.text()
        indicator = self.displayinput.text()
        filename = self.fileinput.text()
        
        # Check if indicator URI input is valid
        sparql.setQuery("PREFIX iso21972: <http://ontology.eil.utoronto.ca/ISO21972/iso21972#>  ASK {<" + characteristic + "> rdfs:subClassOf iso21972:Indicator}")
        valid = sparql.query().convert()
        
        if valid["boolean"] == False:
            self.output.setText("Sorry, your Indicator URI input is invalid.")
            return
        
        person = characteristic.replace("http://ontology.eil.utoronto.ca/tove/cacensus#", "http://ontology.eil.utoronto.ca/tove/cacensus#" + "Person")
        male = characteristic.replace("http://ontology.eil.utoronto.ca/tove/cacensus#", "http://ontology.eil.utoronto.ca/tove/cacensus#" + "Male")
        female = characteristic.replace("http://ontology.eil.utoronto.ca/tove/cacensus#", "http://ontology.eil.utoronto.ca/tove/cacensus#" + "Female")
        # SPARQL query to check whether the characteristic has values for male/female population
        sparql.setQuery("PREFIX uoft: <http://ontology.eil.utoronto.ca/tove/cacensus#> PREFIX iso21972: <http://ontology.eil.utoronto.ca/ISO21972/iso21972#> PREFIX foaf: <http://xmlns.com/foaf/0.1/> ASK {<" + male + "> rdfs:subClassOf foaf:Person}")
        results = sparql.query().convert()
        
        # SPARQL query to check if the administrative area of the indicator is the same as the administrative area for the visualization
        sparql.setQuery( """
        PREFIX uoft: <http://ontology.eil.utoronto.ca/tove/cacensus#>
        PREFIX toronto: <http://ontology.eil.utoronto.ca/Toronto/Toronto#>
        PREFIX iso50872: <http://ontology.eil.utoronto.ca/5087/2/City/>
     
        ASK{
        ?area2 a iso50872:CityAdministrativeArea.
        ?limat a <""" + characteristic + """>;
        ?p ?area2.
        ?area2 a toronto:""" + area + """
        }
        """)
        results2 = sparql.query().convert()
        
        # SPARQL query to check if the administrative area of the indicator is a properPartOf the administrative area for the visualization
        sparql.setQuery( """
        PREFIX uoft: <http://ontology.eil.utoronto.ca/tove/cacensus#>
        PREFIX toronto: <http://ontology.eil.utoronto.ca/Toronto/Toronto#>
        PREFIX iso50872: <http://ontology.eil.utoronto.ca/5087/2/City/>
        PREFIX iso5087m: <http://ontology.eil.utoronto.ca/5087/1/Mereology/>
        
        ASK{
        ?area a toronto:""" + area + """.
        ?area2 a iso50872:CityAdministrativeArea.
        ?limat a <""" + characteristic + """>;
        ?p ?area2.
        ?area2 iso5087m:properPartOf ?area
        }
        """)
        results3 = sparql.query().convert()
        
        print(results, results2, results3)
        
        # If the selected administrative area is the same as the indicator's administrative area, use one of the following 2 SPARQL queries.
        if results2["boolean"]:    
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
                
                ?limat a <""" + characteristic + """>; 
                uoft:hasLocation ?area; 
                iso21972:cardinality_of ?population; 
                iso21972:value ?measure.
                
                ?measure iso21972:numerical_value ?sumvalue. 
            
                ?population a ?populationclass. 
                ?populationclass iso21972:defined_by <""" + person + """>.
                
                ?limatmale a <""" + characteristic + """>; 
                uoft:hasLocation ?area; 
                iso21972:cardinality_of ?populationmale; 
                iso21972:value ?measuremale.
                    
                ?measuremale iso21972:numerical_value ?sumvaluemale. 
                
                ?populationmale a ?populationclassmale. 
                ?populationclassmale iso21972:defined_by <""" + male + """>.
                
                ?limatfemale a <""" + characteristic + """>; 
                uoft:hasLocation ?area; 
                iso21972:cardinality_of ?populationfemale; 
                iso21972:value ?measurefemale.
                    
                ?measurefemale iso21972:numerical_value ?sumvaluefemale. 
            
                ?populationfemale a ?populationclassfemale. 
                ?populationclassfemale iso21972:defined_by <""" + female + """>.
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
                
                ?limat a <""" + characteristic + """>; 
                ?p ?area; 
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
                ?areaname2
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
                
                ?censustract rdfs:comment ?areaname2;
                iso50871:hasLocation ?censuslocation.
                
                ?censuslocation geo:asWKT ?censuswkt.
                    
                ?limat a <""" + characteristic + """>; 
                uoft:hasLocation ?censustract; 
                iso21972:cardinality_of ?population; 
                iso21972:value ?measure.
                    
                ?measure iso21972:numerical_value ?value. 
            
                ?population a ?populationclass. 
                ?populationclass iso21972:defined_by <""" + person + """>.
                
                ?limatmale a <""" + characteristic + """>; 
                uoft:hasLocation ?censustract; 
                iso21972:cardinality_of ?populationmale; 
                iso21972:value ?measuremale.
                    
                ?measuremale iso21972:numerical_value ?valuemale. 
            
                ?populationmale a ?populationclassmale. 
                ?populationclassmale iso21972:defined_by <""" + male + """>.
                
                ?limatfemale a <""" + characteristic + """>; 
                uoft:hasLocation ?censustract; 
                iso21972:cardinality_of ?populationfemale; 
                iso21972:value ?measurefemale.
                    
                ?measurefemale iso21972:numerical_value ?valuefemale. 
            
                ?populationfemale a ?populationclassfemale. 
                ?populationclassfemale iso21972:defined_by <""" + female + """>.
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
                        dic[str(result["areaname"].value)] = {"areaname": str(result["areaname"].value) + "<br> <br>", "wkt": str(result["areawkt"].value), "sumvalue": 0, "sumvaluemale": 0, "sumvaluefemale": 0, "multiplier": ""}
                    
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
                    dic[str(result["areaname"].value)]["multiplier"] +="<br>" + result["areaname2"].value + ": " + str(round(multiplier*100, 1)) 
                # Iterates through the dic dictionary and converts the data into GeoJSON and Pandas DataFrame format
                for key in dic:
                    # Round sumvalue, sumvaluemale, sumvaluefemale to the nearest whole number
                    sumvalue = round(dic[key]["sumvalue"])
                    sumvaluemale = round(dic[key]["sumvaluemale"])
                    sumvaluefemale = round(dic[key]["sumvaluefemale"])
                    
                    # Converts data to GeoJson
                    geoj["features"].append(geojson.Feature(geometry=shapely.wkt.loads(dic[key]['wkt']), properties={"areaname": dic[key]["areaname"], "sumvalue": sumvalue, "sumvaluemale": sumvaluemale, "sumvaluefemale": sumvaluefemale, "multiplier": dic[key]["multiplier"]}))
                    
                    # Converts data to a dictionary that is compatible with Pandas DataFrame
                    dfdic["areaname"].append(dic[key]["areaname"])
                    dfdic["wkt"].append(dic[key]["wkt"])
                    dfdic["sumvalue"].append(sumvalue)
                    dfdic["sumvaluemale"].append(sumvaluemale)
                    dfdic["sumvaluefemale"].append(sumvaluefemale)
                
                # Converts the dfdic dictionary into a Pandas DataFrame
                df = pandas.DataFrame(dfdic)
            
            else:
                if results3["boolean"]:
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
                    ?areaname2
                    ?areawkt
                    ?censuswkt
                    ?value
                    
                    
                    WHERE{
                    ?area a toronto:""" + area + """;
                    iso50871:hasLocation ?location;
                    rdfs:comment ?areaname;
                    iso5087m:hasProperPart ?censustract.
                       
                    ?location geo:asWKT ?areawkt.
                    
                    ?censustract rdfs:comment ?areaname2;
                    iso50871:hasLocation ?censuslocation.
                    
                    ?censuslocation geo:asWKT ?censuswkt.
                        
                    ?limat a <""" + characteristic + """>; 
                    ?p ?censustract; 
                    iso21972:value ?measure.
                        
                    ?measure iso21972:numerical_value ?value. 
                    } 
                    """)

                    
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
                    ?areaname2
                    ?areawkt
                    ?censuswkt
                    ?value
                    
                    
                    WHERE{
                    ?area a toronto:""" + area + """;
                    iso50871:hasLocation ?location;
                    rdfs:comment ?areaname;
                    iso5087m:properPartOf ?censustract.
                       
                    ?location geo:asWKT ?areawkt.
                    
                    ?censustract rdfs:comment ?areaname2;
                    iso50871:hasLocation ?censuslocation.
                    
                    ?censuslocation geo:asWKT ?censuswkt.
                        
                    ?limat a <""" + characteristic + """>; 
                    ?p ?censustract; 
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
                        dic[str(result["areaname"].value)] = {"areaname": str(result["areaname"].value) + "<br> <br>", "wkt": str(result["areawkt"].value), "sumvalue": 0, "multiplier": ""}
                        
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
                    dic[str(result["areaname"].value)]["multiplier"] += "<br>" + result["areaname2"].value + ": " + str(round(multiplier*100, 1)) 
                
                # Iterates through the dic dictionary and converts the data into GeoJSON and Pandas DataFrame format
                for key in dic:
                    # Round sumvalue to the nearest whole number
                    sumvalue = round(dic[key]["sumvalue"])
                    
                    # Converts data to GeoJson
                    geoj["features"].append(geojson.Feature(geometry=shapely.wkt.loads(dic[key]['wkt']), properties={"areaname": dic[key]["areaname"], "sumvalue": sumvalue, "multiplier": dic[key]["multiplier"]}))
                    
                    # Converts data to a dictionary that is compatible with Pandas DataFrame
                    dfdic["areaname"].append(dic[key]["areaname"])
                    dfdic["wkt"].append(dic[key]["wkt"])
                    dfdic["sumvalue"].append(sumvalue)
                
                # Converts the dfdic dictionary into a Pandas DataFrame
                df = pandas.DataFrame(dfdic)
                
                    
            

        # Create a folium map centered at the location specified by the coordinates
        m = folium.Map(location=[43.6581,-79.3845], zoom_start=12)

        # Create a colour scale based on the indicator values from the data in the Pandas DataFrame
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
            # Use the color white if the value of the indicator is 0
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
        # that show the administrative area name and the total, male, female values for the indicator
        if results["boolean"]:
            if results2["boolean"]:
                folium.features.GeoJson(
                    # Use data from the geoj GeoJSON variable for the popup boxes
                    data=geoj,
                    # Use the display name entered by the user as the name for the GeoJSON object
                    name=indicator,
                    # Set smooth factor to 2. More means better performance and smoother look, and less means more accurate representation.
                    smooth_factor=2,
                    # Set the color, fill color to transparent and stroke width (weight) to 0.5 
                    style_function=lambda x: {'color':'transparent','fillColor':'transparent','weight':0.5},
                    # Create popup boxes that show the administrative area name and the total, male, female values for the indicator
                    tooltip=folium.features.GeoJsonTooltip(
                        # Use areaname, sumvalue, sumvaluemale, sumvaluefemale from geoj as values for the popup box
                        fields=['areaname',
                                'sumvalue',
                                'sumvaluemale',
                                'sumvaluefemale',
                                ],
                        # Use the administrative area type and the display name entered by the user as labels for the above values
                        aliases=[area,
                                 indicator + " (Total)",
                                 indicator + " (Male)",
                                 indicator + " (Female)",
                                 ], 
                        # Use JavaScript’s .toLocaleString() to format values (i.e. comma separators, float truncation)
                        localize=True,
                        # Use to set whether the popup box follows the mouse cursor
                        sticky=False,
                        # Use to toggle whether to show the labels and values
                        labels=True,
                        # Set max width of the popup box
                        max_width=300)
                    ).add_to(choro)
            else:
                folium.features.GeoJson(
                    # Use data from the geoj GeoJSON variable for the popup boxes
                    data=geoj,
                    # Use the display name entered by the user as the name for the GeoJSON object
                    name=indicator,
                    # Set smooth factor to 2. More means better performance and smoother look, and less means more accurate representation.
                    smooth_factor=2,
                    # Set the color, fill color to transparent and stroke width (weight) to 0.5 
                    style_function=lambda x: {'color':'transparent','fillColor':'transparent','weight':0.5},
                    # Create popup boxes that show the administrative area name and the total, male, female values for the indicator
                    tooltip=folium.features.GeoJsonTooltip(
                        # Use areaname, sumvalue, sumvaluemale, sumvaluefemale from geoj as values for the popup box
                        fields=['areaname',
                                'sumvalue',
                                'sumvaluemale',
                                'sumvaluefemale',
                                'multiplier'
                                ],
                        # Use the administrative area type and the display name entered by the user as labels for the above values
                        aliases=[area + "<br> <br>",
                                 indicator + " (Total)",
                                 indicator + " (Male)",
                                 indicator + " (Female)",
                                 "Administrative areas used for calculation"
                                 ], 
                        # Use JavaScript’s .toLocaleString() to format values (i.e. comma separators, float truncation)
                        localize=True,
                        # Use to set whether the popup box follows the mouse cursor
                        sticky=False,
                        # Use to toggle whether to show the labels and values
                        labels=True,
                        # Set max width of the popup box
                        max_width=300)
                    ).add_to(choro)
        # Else, create a GeoJSON object containing popup boxes showing the administrative area name and the value for the indicator
        else:
            if results2["boolean"]:
                folium.features.GeoJson(
                    # Use data from the geoj GeoJSON variable for the popup boxes
                    data=geoj,
                    # Use the display name entered by the user as the name for the GeoJSON object
                    name= indicator,
                    # Set smooth factor to 2. More means better performance and smoother look, and less means more accurate representation.
                    smooth_factor=2,
                    # Set the color, fill color to transparent and stroke width (weight) to 0.5 
                    style_function=lambda x: {'color':'transparent','fillColor':'transparent','weight':0.5},
                    # Create popup boxes that show the administrative area name and the value for the indicator
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
                        max_width=300)
                    ).add_to(choro)
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
                    # Create popup boxes that show the administrative area name and the value for the indicator
                    tooltip=folium.features.GeoJsonTooltip(
                        # Use areaname, sumvalue from geoj as values for the popup box
                        fields=['areaname',
                                'sumvalue',
                                'multiplier'
                                ],
                        # Use the administrative area type and the display name entered by the user as labels for the above values
                        aliases=[area + "<br> <br>",
                                 indicator,
                                 "Administrative areas used for calculation"
                                 ], 
                        # Use JavaScript’s .toLocaleString() to format values (i.e. comma separators, float truncation)
                        localize=True,
                        # Use to set whether the popup box follows the mouse cursor
                        sticky=False,
                        # Use to toggle whether to show the labels and values
                        labels=True,
                        # Set max width of the popup box
                        max_width=300)
                    ).add_to(choro)
                

        # Add a LayerControl to the map which adds a toggle for showing/hiding the choropleth layer
        folium.LayerControl().add_to(m)

        # Save the visualization map using the file name specified by the user
        m.save(filename + ".html")
        
        # Open the generated HTML visualization using webEngineView
        with open(os.path.join(os.getcwd(), filename + ".html"), 'r') as f:
            html = f.read()
            self.webEngineView.setHtml(html)
        
        # Print finished message
        self.output.setText("Done! Your visualization has been saved as " + filename + ".html in your current working directory.")
        del df
# Show the QtWindow
app = QApplication(sys.argv)
window = Window()
window.show()
sys.exit(app.exec())
