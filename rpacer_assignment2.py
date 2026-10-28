###################################################################### 
# Edit the following function definition, replacing the words
# 'name' with your name and 'hawkid' with your hawkid.
# 
# Note: Your hawkid is the login name you use to access ICON, and not
# your firsname-lastname@uiowa.edu email address.
# 
# def hawkid():
#     return(["Caglar Koylu", "ckoylu"])
###################################################################### 
def hawkid():
    return(["Riley Pacer", "rpacer"])

###################################################################### 
# Problem 1 (10 Points)
#
# This function reads all the feature classes in a workspace (folder or geodatabase) and
# prints the name of each feature class and the geometry type of that feature class in the following format:
# 'states is a point feature class'

###################################################################### 
import arcpy
import os

#defining the function 
def printFeatureClassNames(workspace):
    arcpy.env.workspace = workspace

    #Get the feature classes in the gdb
    feature_classes = arcpy.ListFeatureClasses()

    #check if feature classes are present and print an error message if none are found
    try: 
        if not feature_classes: 
            print("No feature classes within input geodatabase")

    #list and describe feature classes
        for fc in feature_classes: 
            geometry_type = arcpy.Describe(fc).shapeType
            print(f"{fc} is a {geometry_type.lower()} feature class")

    except Exception as e:
        print(f"Error: {e}")

       
#Testing with blank gdb
#printFeatureClassNames(r"C:/Users/rpacer/3050_Assignment2/empty.gdb")

###################################################################### 
# Problem 2 (20 Points)
#
# This function reads all the attribute names in a feature class or shape file and
# prints the name of each attribute name and its type (e.g., integer, float, double)
# only if it is a numerical type

###################################################################### 
def printNumericalFieldNames(inputFc, workspace):
    arcpy.env.workspace = workspace

    #read attribute names 
    fields = arcpy.ListFields(inputFc)

    #print fields and types if they are numerical 
    for field in fields: 
        if field.type in ["SmallInteger", "Integer", "Big Integer" "Single", "Double", "Short", "Long", "OID"]: 
            print(f"{field.name} is a {field.type}")

#Testing
#printNumericalFieldNames("parks", "C:/Users/rpacer/3050_Assignment2/hw2.gdb")

###################################################################### 
# Problem 3 (30 Points)
#
# Given a geodatabase with feature classes, and shape type (point, line or polygon) and an output geodatabase:
# this function creates a new geodatabase and copying only the feature classes with the given shape type into the new geodatabase

###################################################################### 
def exportFeatureClassesByShapeType(input_geodatabase, shapeType, output_geodatabase):
    arcpy.env.workspace = input_geodatabase

    #Get the feature classes in the gdb
    feature_classes = arcpy.ListFeatureClasses()

    #check if feature classes are present and print an error message if none are found
    try: 
        if not feature_classes: 
            print("No feature classes within input geodatabase")

    #Create output gdb
        if not arcpy.Exists(output_geodatabase): 
            output_folder = os.path.dirname(output_geodatabase)
            output_name = os.path.basename(output_geodatabase)

            arcpy.management.CreateFileGDB(output_folder, output_name)

    #Check feature classes
        for fc in feature_classes: 
            shape_Type = arcpy.Describe(fc).shapeType

 #only select desired shape type
            if shape_Type.lower() == shapeType.lower(): 
                output_fc = os.path.join(output_geodatabase, fc)
                arcpy.management.CopyFeatures(fc, output_fc)

                print(f"{fc} copied to new gdb")
    except Exception as e:
        print(f"Error: {e}")

#Testing with blank gdb
#exportFeatureClassesByShapeType("C:/Users/rpacer/3050_Assignment2/empty.gdb", "polyline", "C:/Users/rpacer/3050_Assignment2/polygon2.gdb")

###################################################################### 
# Problem 4 (40 Points)
#
# Given an input feature class or a shape file and a table in a geodatabase or a folder workspace,
# join the table to the feature class using one-to-one and export to a new feature class.
# Print the results of the joined output to show how many records matched and unmatched in the join operation. 

###################################################################### 
def exportAttributeJoin(inputFc, idFieldInputFc, inputTable, idFieldTable, workspace):

    arcpy.env.workspace = workspace

    #Check that the input feature class and table exist
    if not arcpy.Exists(inputFc):
        print(f"Error: Input feature class {inputFc} does not exist.")
        return

    if not arcpy.Exists(inputTable):
        print(f"Error: Join table {inputTable} does not exist.")
        return

    #Check that the join fields exist, try and except
    try:
        input_fields = [f.name for f in arcpy.ListFields(inputFc)]
        table_fields = [f.name for f in arcpy.ListFields(inputTable)]

        if idFieldInputFc not in input_fields:
            raise ValueError(f"Field '{idFieldInputFc}' not found in input feature class.")

        if idFieldTable not in table_fields:
            raise ValueError(f"Field '{idFieldTable}' not found in join table.")

    except ValueError as e:
        print(f"Join field error: {e}")
        return

    #Create output featureclass
    out_fc = os.path.join(workspace, "block_groups_join_output")

    #Join Fields and run try and except statements on errors
    try:
        arcpy.management.JoinField(inputFc, idFieldInputFc, inputTable, idFieldTable)

        #Export joined feature class
        arcpy.management.CopyFeatures(inputFc, out_fc)
        #Print result
        print(f"Joined feature class exported to: {out_fc}")

    except arcpy.ExecuteError:
        print(arcpy.GetMessages(2))

   #Checking how many records match 
    with arcpy.da.SearchCursor(inputFc, [idFieldInputFc]) as rows:
        Fc_ids = [row[0] for row in rows]

    with arcpy.da.SearchCursor(inputTable, [idFieldTable]) as rows:
        T_ids = {row[0] for row in rows if row[0] is not None}

    #Print results
    print("Matched records:", sum(1 for value in Fc_ids if value is not None and value in T_ids))
    print("Unmatched records:", len(Fc_ids) - sum(1 for value in Fc_ids if value is not None and value in T_ids))

#Testing with block groups and table 
#exportAttributeJoin("block_groups", "FIPS", "mytable", "FIPS", "C:/Users/rpacer/3050_Assignment2/hw2.gdb")


######################################################################
# MAKE NO CHANGES BEYOND THIS POINT.
######################################################################
if __name__ == '__main__' and hawkid()[1] == "hawkid":
    print('### Error: YOU MUST provide your hawkid in the hawkid() function.')
