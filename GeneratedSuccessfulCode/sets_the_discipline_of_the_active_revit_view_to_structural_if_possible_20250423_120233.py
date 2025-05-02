# Purpose: This script sets the discipline of the active Revit view to 'Structural', if possible.

﻿# Import necessary classes
from Autodesk.Revit.DB import View, ViewDiscipline
import System

# Get the current active view
current_view = uidoc.ActiveView

# Check if we have a valid view
if current_view is not None:
    # Define the target discipline
    target_discipline = ViewDiscipline.Structural

    try:
        # Check if the view has the Discipline property
        if current_view.HasViewDiscipline():
            # Check if the Discipline parameter can be modified (e.g., not controlled by a template)
            if current_view.CanModifyViewDiscipline():
                # Check if the current discipline is already the target discipline
                if current_view.Discipline != target_discipline:
                    # Set the Discipline parameter
                    current_view.Discipline = target_discipline
                    # print(f"# Successfully set Discipline for view '{current_view.Name}' to Structural.") # Optional print
                # else:
                    # print(f"# Discipline for view '{current_view.Name}' is already set to Structural.") # Optional print
            else:
                print("# Error: Cannot modify Discipline for view '{{0}}'. It might be controlled by a View Template.".format(current_view.Name))
        else:
            print("# Error: The current view '{{0}}' (Type: {{1}}) does not have a Discipline parameter.".format(current_view.Name, current_view.ViewType.ToString()))

    except System.Exception as e:
        print("# An error occurred while trying to set the Discipline for view '{{0}}': {{1}}".format(current_view.Name, e))
else:
    print("# Error: Could not get the current active view.")