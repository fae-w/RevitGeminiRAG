# Purpose: This script creates a Revit legend view displaying wall types.

﻿import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
import Autodesk.Revit.DB as DB
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ViewFamilyType,
    ViewFamily,
    WallType,
    ElementId,
    XYZ,
    BuiltInCategory,
    ElementTransformUtils,
    View,
    ViewType
    # LegendComponentType removed from here
)
# System import often useful, though not strictly needed here
# clr.AddReference('System')
# import System

# Define the name for the new legend view
legend_view_name = "Wall Types Legend"
view_exists = False
target_view = None

# --- Get the document ---
# doc is assumed to be pre-defined

# --- Check if the legend view already exists ---
existing_views = FilteredElementCollector(doc).OfClass(View).ToElements()
for v in existing_views:
    # Check by name and ViewType
    if v.Name == legend_view_name and v.ViewType == ViewType.Legend:
        target_view = v
        view_exists = True
        # print("# Legend view '{{}}' already exists. Will add components to it.".format(legend_view_name)) # Optional info
        break

# --- Find the Legend View Family Type ---
legend_vft_id = ElementId.InvalidElementId
vfts = FilteredElementCollector(doc).OfClass(ViewFamilyType).ToElements()
for vft in vfts:
    if vft.ViewFamily == ViewFamily.Legend:
        legend_vft_id = vft.Id
        break

if legend_vft_id == ElementId.InvalidElementId:
    print("# Error: Could not find a ViewFamilyType for Legends in the project.")
else:
    # --- Create the Legend View if it doesn't exist ---
    if not view_exists:
        try:
            # Use the fully qualified name for the static Create method
            # Note: Creating views requires a Transaction, handled by the C# wrapper
            target_view = DB.LegendView.Create(doc, legend_vft_id) # Use LegendView.Create for Revit 2022+
            target_view.Name = legend_view_name
            # print("# Created new Legend view: {{}}".format(legend_view_name)) # Optional info
        except AttributeError: # Fallback for older APIs that might not have LegendView.Create
            try:
                target_view = View.CreateLegend(doc, legend_vft_id) # Older method
                target_view.Name = legend_view_name
                # print("# Created new Legend view (using older API method): {{}}".format(legend_view_name)) # Optional info
            except Exception as create_ex_fallback:
                 print("# Error creating Legend view (both methods failed): {{}}".format(create_ex_fallback))
                 target_view = None # Ensure target_view is None if creation failed
        except Exception as create_ex:
            print("# Error creating Legend view: {{}}".format(create_ex))
            target_view = None # Ensure target_view is None if creation failed

    # --- Proceed only if the view exists or was created successfully ---
    if target_view:
        legend_view_id = target_view.Id

        # --- Collect Wall Types ---
        # Ensure we only get types, not instances, and they are actual WallTypes
        wall_types = FilteredElementCollector(doc).OfClass(WallType).WhereElementIsElementType().ToElements()

        # --- Define positioning variables ---
        current_pos = XYZ(0, 0, 0)
        # Adjust offset for typical legend scale (e.g., 1:50 or 1:100)
        # Use reasonable units (feet or meters depending on project units)
        vertical_offset = XYZ(0, -5.0, 0) # Place components 5 project units below each other vertically (use float, adjusted)
        added_count = 0

        # --- Iterate through Wall Types and create Legend Components ---
        # Use dictionary comprehension for uniqueness based on ElementId
        unique_wall_types = {wt.Id: wt for wt in wall_types if isinstance(wt, WallType)}

        for wall_type_id, wall_type in unique_wall_types.items():
            try:
                # Use the fully qualified name for LegendComponent create method
                # Note: Creating elements requires a Transaction, handled by the C# wrapper
                # Check if the type ID is valid before creating
                if wall_type_id != ElementId.InvalidElementId:
                    # Check if the wall type is valid for legend component creation
                    if DB.LegendComponent.IsAllowedForWallType(doc, wall_type_id):
                        lc = DB.LegendComponent.Create(doc, legend_view_id, wall_type_id)

                        # Set the component to display the wall's cut section
                        # Use ComponentType property which uses the LegendComponentType enum
                        # Use the fully qualified name DB.LegendComponentType
                        if hasattr(lc, "ComponentType"):
                            lc.ComponentType = DB.LegendComponentType.WallSection # FIXED: Use DB. prefix
                        # Some API versions might use ViewTypeOption (though less common for setting)
                        # elif hasattr(lc, "ViewTypeOption"):
                        #      lc.ViewTypeOption = DB.LegendComponentType.WallSection # FIXED: Use DB. prefix
                        else:
                            # print("# Warning: Could not set LegendComponent view type for '{{}}' (API inconsistency?). Using default.".format(wall_type.Name))
                            pass # Default might be sufficient

                        # Move the component to the calculated position
                        # Note: Modifying elements requires a Transaction, handled by C# wrapper
                        ElementTransformUtils.MoveElement(doc, lc.Id, current_pos)

                        # Update position for the next component
                        current_pos = current_pos.Add(vertical_offset)
                        added_count += 1
                    else:
                        # print("# Skipping Wall Type '{{}}' (ID: {{}}): Not allowed for legend components.".format(wall_type.Name, wall_type_id))
                        pass
                else:
                    # print("# Skipping invalid Wall Type ID.") # Optional info
                    pass

            except Exception as comp_ex:
                # Provide more specific error info if possible
                error_str = str(comp_ex)
                type_name = "Unknown"
                try:
                    type_name = wall_type.Name # Get name safely
                except:
                    pass

                if "cannot be used in a legend view" in error_str:
                     # print("# Skipping Wall Type '{{}}' (ID: {{}}): Cannot be used in a legend view.".format(type_name, wall_type_id)) # Optional info
                     pass # Skip this type gracefully
                elif "cannot find wall profile" in error_str or "cut graphics" in error_str:
                     # print("# Skipping Wall Type '{{}}' (ID: {{}}): Cannot find wall profile/graphics for legend.".format(type_name, wall_type_id)) # Optional info
                     pass # Skip this type gracefully
                else:
                    print("# Error processing Wall Type '{{}}' (ID: {{}}): {{}}".format(type_name, wall_type_id, comp_ex))

        if added_count > 0:
            print("# Added {} legend components to '{}'.".format(added_count, target_view.Name))
        elif not unique_wall_types: # Check the filtered unique list
             print("# No valid Wall Types found in the project.")
        else: # Only print this if wall types existed but none were added
             if added_count == 0: # Check specifically if nothing was added despite types existing
                 print("# No Wall Types could be added to the legend '{}'. Check if they are allowed in legends.".format(target_view.Name))

    # else: # Error handled when target_view is checked or creation failed
    #    if not view_exists: # Only print if creation failed
    #         print("# Could not create or find the target legend view.") # Combined message
    #    # No further action needed if target_view is None
    pass # This pass is harmless at the end