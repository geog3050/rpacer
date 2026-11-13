"""Assignment 3: Spatial Overlays and Areal Interpolation.
Complete three functions using ArcPy and pathlib.Path. Prepare and project
copies before analysis; preserve inputs and avoid hardcoded paths or values.
Check input paths, geometry types, fields, coordinate systems, and output names.
Use try/except handling to catch and report errors.
Find and download census boundaries, a census/ACS numeric attribute, and roads (or another dataset with line geometry).
"""


def hawkid():
    return ["name", "hawkid"]


# Problem 1 (20 points)

#importing pathlib, arcpy and os
import arcpy
import os
from pathlib import Path 

def prepare_data(input_fc, output_geodatabase, out_coordinate_system,
join_table=None, join_field=None, value_field=None):

    try:
        #Check that the input feature class exists
        if not arcpy.Exists(input_fc):
            raise FileNotFoundError("Input feature class does not exist")
 
        #Create the output geodatabase if it does not exist
        if not arcpy.Exists(output_geodatabase):
            output_folder = str(Path(output_geodatabase).parent)
            gdb_name = Path(output_geodatabase).name
 
            arcpy.management.CreateFileGDB(output_folder, gdb_name)
 
        #Describe the input feature class
        desc = arcpy.Describe(input_fc)
 
        #Get the input feature class name
        output_name = desc.baseName
 
        #Create the output feature class path
        output_fc = str(Path(output_geodatabase) / output_name)
 
        #Check if the output feature class already exists
        if arcpy.Exists(output_fc):
            raise FileExistsError("Output feature class already exists")

        #Get the input spatial reference
        input_sr = desc.spatialReference
 
        #Check input coordinate system exists
        if input_sr.name == "Unknown":
            raise ValueError("Input feature class has an unknown coordinate system")

        #Project the input fc into the output gdb
        arcpy.management.Project(
            input_fc,
            output_fc,
            out_coordinate_system
        )

        #Check that all three join arguments are supplied together
        join_args = [join_table, join_field, value_field]
 
        if any(arg is not None for arg in join_args):
            if not all(arg is not None for arg in join_args):
                raise ValueError("All three join arguments must be supplied together")

        #Check that join table exists
        if not arcpy.Exists(join_table):
            raise FileNotFoundError("Join TABLE does not exist")

        #Import the join table into the output geodatabase
        table_name = Path(join_table).stem
        output_table = str(Path(output_geodatabase) / table_name)
 
        arcpy.conversion.TableToTable(
            join_table,
            output_geodatabase,
            table_name
        )

        #Joinfield to the polygons
        arcpy.management.JoinField(
            output_fc,
            join_field,
            output_table,
            join_field,
            [value_field]
        )

        #Get the field names from the polygon feature class
        polygon_fields = [field.name for field in arcpy.ListFields(output_fc)]
 
        #Get the field names from the CSV table
        table_fields = [field.name for field in arcpy.ListFields(output_table)]
 
        #Check that the join fields exist
        if join_field not in polygon_fields:
            raise ValueError("Join field does not exist in polygons")
        if join_field not in table_fields:
            raise ValueError("Join field does not exist in CSV table")
        #print(f"prepared feature class path: {output_fc}")
        return output_fc

    except Exception as e: 
        print(f"error preparing data: {e}")
        return None


#Testing the code 

#input_fc = Path(r"C:/Users/rpacer/3050_Assignment2/hw3_data/block_groups2.shp")
#output_geodatabase = Path(r"C:/Users/rpacer/3050_Assignment2/hw3.gdb")
#out_coordinate_system = arcpy.SpatialReference(26915)
#join_table = Path(r"C:/Users/rpacer/3050_Assignment2/hw3_data/population.csv")
#join_field = "GEOID"
#value_field = "POP_TOTAL"

#prepare_data(
  #  input_fc,
 #   output_geodatabase,
  #  out_coordinate_system,
  #  join_table, 
  #  join_field,
   # value_field
#)

#print(result)
 

# Problem 2 (40 points)
#importing pathlib, arcpy and os
import arcpy
import os
from pathlib import Path 

def estimatePopulationInZone(source_polygons, population_field, study_zone,
                             output_fc):
    try:
        #Check that input datasets exist
        if not arcpy.Exists(source_polygons):
            raise FileNotFoundError("Source polygons do not exist")
        if not arcpy.Exists(study_zone):
            raise FileNotFoundError("Study zone does not exist")

        #Describe input datasets
        source_desc = arcpy.Describe(source_polygons)
        zone_desc = arcpy.Describe(study_zone)

        #Check geometry types
        if source_desc.shapeType != "Polygon":
            raise ValueError("Source polygons must be polygon features")
        if zone_desc.shapeType != "Polygon":
            raise ValueError("Study zone must be polygon features")
            
        #Describe coordinate systems
        source_sr = source_desc.spatialReference
        zone_sr = zone_desc.spatialReference

        #Check that both coordinate systems are projected in meters
        if source_sr.type != "Projected" or source_sr.linearUnitName.lower() not in ["meter", "metre"]:
            raise ValueError("Source polygons must use a projected coordinate system in meters")
        if zone_sr.type != "Projected" or zone_sr.linearUnitName.lower() not in ["meter", "metre"]:
            raise ValueError("Study zone must use a projected coordinate system in meters")

        #Check that both datasets use the same coordinate system
        if source_sr.factoryCode != zone_sr.factoryCode:
            raise ValueError("Source polygons and study zone must use the same coordinate system")

        #Starting calculations, creating a temp copy of source
        temp_source = str(Path(output_fc).parent / "temp_source")

        arcpy.management.CopyFeatures(source_polygons, temp_source)

        #Add and calculate original polygon area
        arcpy.management.AddField(temp_source, "SRC_KM2", "DOUBLE")
        arcpy.management.CalculateGeometryAttributes(temp_source, [["SRC_KM2", "AREA"]], area_unit="SQUARE_KILOMETERS")


        #Dissolve study zone polygons
        dissolved_zone = str(Path(output_fc).parent / "dissolved_zone")
        arcpy.management.Dissolve(study_zone, dissolved_zone)

        #Intersect source polygons with dissolved study zone
        arcpy.analysis.Intersect([temp_source, dissolved_zone], output_fc, join_attributes="ALL")

        #Calculate intersected polygons 
        arcpy.management.AddField(output_fc, "PART_KM2", "DOUBLE") #adding field
        arcpy.management.CalculateGeometryAttributes(output_fc, [["PART_KM2", "AREA"]], area_unit="SQUARE_KILOMETERS")

        #Add estimated population field
        arcpy.management.AddField(output_fc, "EST_POP", "DOUBLE")
 
        # Calculate area-weighted population
        fields = [population_field, "SRC_KM2", "PART_KM2", "EST_POP"]
        with arcpy.da.UpdateCursor(output_fc, fields) as rows:
            for row in rows:
                population, source_area, part_area, _ = row
 
                if population is None or population < 0 or source_area <= 0:
                    raise ValueError("Population is zero or area is zero")
                    fraction = part_area / source_area
                    row[3] = population * fraction
                    rows.updateRow(row)

        #Calculate total estimated population
        total_population = 0 #start population estimate at zero
        with arcpy.da.SearchCursor(output_fc, ["EST_POP"]) as rows:
            for row in rows:
                total_population += row[0]
        print(f"Total estimated population: {total_population:,.0f}")
        return total_population
  
    except Exception as e:
        print(f"Error estimating population: {e}")
        return None
    
        
        
#Testing this code block 

# Define input datasets
#input_folder = Path(r"C:/Users/rpacer/3050_Assignment2/hw3_data")
#source_polygons = str(input_folder / "practice_polygons.shp")
#study_zone = str(input_folder / "practice_polygons.shp")
 
# Define population field
#population_field = "POP_TOTAL"
 
# Define output feature class
#output_fc = str(input_folder / "population_estimate")
 
# Run population estimation
#estimated_population = estimatePopulationInZone(
   # source_polygons,
  #  population_field,
   # study_zone,
   # output_fc
#)
 
#print(estimated_population)
        



# Problem 3 (40 points)
#importing pathlib, arcpy and os
import arcpy
import os
from pathlib import Path 




def summarizeLineLength(lines, polygons, polygon_id_field, output_fc):
    try:
        #Check that input datasets exist
        if not arcpy.Exists(lines):
            raise FileNotFoundError("Line features do not exist")
        if not arcpy.Exists(polygons):
            raise FileNotFoundError("Polygon features do not exist")
        #Describe input datasets
        lines_desc = arcpy.Describe(lines)
        polygons_desc = arcpy.Describe(polygons)
 
        #Check geometry types
        if lines_desc.shapeType != "Polyline":
            raise ValueError("Input lines must be polyline features.")
        if polygons_desc.shapeType != "Polygon":
            raise ValueError("Input polygons must be polygon features.")

        #Describe coordinate systems
        lines_sr = lines_desc.spatialReference
        polygons_sr = polygons_desc.spatialReference
 
        # Check that both coordinate systems are projected in meters
        if lines_sr.type != "Projected" or lines_sr.linearUnitName.lower() not in ["meter", "metre"]:
            raise ValueError("Lines must be in meters")
        if polygons_sr.type != "Projected" or polygons_sr.linearUnitName.lower() not in ["meter", "metre"]:
            raise ValueError("Polygons must be in meters")
 
        #Check that both datasets use the same coordinate system
        if lines_sr.factoryCode != polygons_sr.factoryCode:
            raise ValueError("Lines and polygons must use the same coordinate system")
 
        #Check that polygon ID field exists
        fields = [field.name for field in arcpy.ListFields(polygons)]
        if polygon_id_field not in fields:
            raise ValueError("Polygon ID field does not exist")

        #Create a copy of the original polygons
        arcpy.management.CopyFeatures(polygons, output_fc)
 
        #Create intersected line fc
        intersect_fc = str(Path(output_fc).parent / "intersect_lines")
 
        arcpy.analysis.Intersect(
            [lines, polygons],
            intersect_fc,
            join_attributes="ALL"
        )

        #Add and calculate line length in kM
        arcpy.management.AddField(intersect_fc, "LINE_KM", "DOUBLE")
        arcpy.management.CalculateGeometryAttributes(
            intersect_fc,
            [["LINE_KM", "LENGTH"]],
            length_unit="KILOMETERS"
        )

        #Summarize line lengths by polygon ID
        summary_table = str(Path(output_fc).parent / "line_summary")
 
        arcpy.analysis.Statistics(
            intersect_fc,
            summary_table,
            [["LINE_KM", "SUM"]],
            polygon_id_field
        )

          #Join summarized lengths to polygons
        arcpy.management.JoinField(
            output_fc,
            polygon_id_field,
            summary_table,
            polygon_id_field,
            ["SUM_LINE_KM"]
        )
 
        #Rename summarized field to LINE_KM
        arcpy.management.AlterField(
            output_fc,
            "SUM_LINE_KM",
            "LINE_KM",
            "LINE_KM"
        )
 
        #Replace null values with zero
        arcpy.management.CalculateField(
            output_fc,
            "LINE_KM",
            "0 if !LINE_KM! is None else !LINE_KM!",
            "PYTHON3"
        )
        print(f"output_fc: {output_fc}")
        return output_fc

    except Exception as e:
        print(f"Error summarizing line length: {e}")
        return None


#Testing 
#input_folder = Path(r"C:/Users/rpacer/3050_Assignment2/hw3_data")
#lines = str(input_folder / "practice_lines.shp")
#polygons = str(input_folder / "block_groups2.shp")
 
#polygon_id_field = "GEOID"
 
#output_gdb = Path(r"C:/Users/rpacer/3050_Assignment2/hw3.gdb")
#output_fc = str(output_gdb / "line_length")

    


######################################################################
# MAKE NO CHANGES BEYOND THIS POINT.
######################################################################
if __name__ == "__main__" and hawkid()[1] == "hawkid":
    print("### Error: YOU MUST provide your HawkID in the hawkid() function.")
