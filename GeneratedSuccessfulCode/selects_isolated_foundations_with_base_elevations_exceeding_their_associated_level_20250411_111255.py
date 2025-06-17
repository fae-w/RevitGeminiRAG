# Purpose: This script selects isolated foundations with base elevations exceeding their associated level.

# Purpose: This script selects isolated foundations (structural footings) in Revit whose base elevation is above their associated level's elevation.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
clr.AddReference('System.Collections') # Required for List<T>
from System.Collections.Generic import List

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    ElementId,
    Level,
    FamilyInstance,
    BuiltInParameter,
    # ParameterType, # Removed this unused import causing the error
    StorageType,
    View # Needed for BoundingBox context if used, None gives model coords
)
from Autodesk.Revit.UI import Selection # Required for uidoc.Selection

# Access current document and UI document
# Assuming 'doc' and 'uidoc' are predefined.

# List to store IDs of foundations to select
foundations_to_select_ids = []
foundations_processed = 0
foundations_skipped_no_level = 0
foundations_skipped_no_elevation = 0
error_count = 0

# Collector for isolated foundations (structural footings)
# Ensure we are getting instances, not types
collector = FilteredElementCollector(doc)\
    .OfCategory(BuiltInCategory.OST_StructuralFoundation)\
    .WhereElementIsNotElementType()

# Iterate through foundations
for foundation in collector:
    foundations_processed += 1
    # Many foundations are FamilyInstances, but check just in case
    # if not isinstance(foundation, FamilyInstance):
    #     continue # Skip if not a family instance (though most foundations should be)

    try:
        # 1. Get the associated Level
        associated_level = None
        level_id = ElementId.InvalidElementId

        # Try common parameters for level association
        level_param = foundation.get_Parameter(BuiltInParameter.SCHEDULE_LEVEL_PARAM)
        if level_param is None or level_param.StorageType != StorageType.ElementId or level_param.AsElementId() == ElementId.InvalidElementId:
            level_param = foundation.get_Parameter(BuiltInParameter.INSTANCE_REFERENCE_LEVEL_PARAM)
            if level_param is None or level_param.StorageType != StorageType.ElementId or level_param.AsElementId() == ElementId.InvalidElementId:
                 level_param = foundation.get_Parameter(BuiltInParameter.FAMILY_LEVEL_PARAM) # Less common but possible

        if level_param and level_param.StorageType == StorageType.ElementId and level_param.AsElementId() != ElementId.InvalidElementId:
            level_id = level_param.AsElementId()
            level_element = doc.GetElement(level_id)
            if isinstance(level_element, Level):
                associated_level = level_element
            else:
                # print("# Debug: Found level ID {{level_id}} for foundation {{foundation.Id}}, but it's not a Level element.")
                pass # Will be handled by associated_level is None check below

        if associated_level:
            level_elevation = associated_level.ProjectElevation # Use ProjectElevation for consistency relative to Project Base Point

            # 2. Get the foundation's base elevation
            foundation_base_elevation = None

            # Try the specific parameter first: Elevation at Bottom relative to Project Base Point
            base_elevation_param = foundation.get_Parameter(BuiltInParameter.STRUCTURAL_FOUNDATION_ELEVATION_AT_BOTTOM)

            if base_elevation_param and base_elevation_param.HasValue:
                 if base_elevation_param.StorageType == StorageType.Double:
                       foundation_base_elevation = base_elevation_param.AsDouble()
                 else:
                       # print(f"# Debug: Parameter 'Elevation at Bottom' has unexpected storage type ({{base_elevation_param.StorageType}}) for foundation {{foundation.Id}}.")
                       pass # Continue to fallback if type is wrong
            else:
                # print(f"# Debug: Parameter 'Elevation at Bottom' not found or has no value for foundation {{foundation.Id}}. Trying BBox fallback.")
                pass # Continue to fallback

            # Fallback: Use Bounding Box Min Z if the specific parameter wasn't usable
            if foundation_base_elevation is None:
                # Get BoundingBox in model coordinates (pass None as view argument)
                bbox = foundation.get_BoundingBox(None)
                if bbox and bbox.Min:
                    foundation_base_elevation = bbox.Min.Z
                    # print(f"# Debug: Using BBox Min Z ({{foundation_base_elevation:.4f}}) for foundation {{foundation.Id}}.")
                else:
                    # print(f"# Debug: Cannot find 'Elevation at Bottom' parameter or valid BBox for foundation {{foundation.Id}}.")
                    foundations_skipped_no_elevation += 1
                    continue # Skip if no reliable elevation found

            # 3. Compare elevations
            if foundation_base_elevation is not None:
                 # Use a small tolerance for floating point comparison (e.g., 1/256 inch in feet)
                 tolerance = 1.0 / (256.0 * 12.0)
                 if foundation_base_elevation > (level_elevation + tolerance):
                     foundations_to_select_ids.append(foundation.Id)
                     # print(f"# Debug: Adding foundation {{foundation.Id}} (Base Elev: {{foundation_base_elevation:.4f}}) > Level {{associated_level.Name}} (Elev: {{level_elevation:.4f}})")
            else:
                 # This case should be caught by the 'continue' above, but double-check
                 foundations_skipped_no_elevation += 1

        else:
            # print(f"# Debug: Could not find associated Level for foundation {{foundation.Id}}.")
            foundations_skipped_no_level += 1

    except Exception as e:
        print("# Error processing foundation {0}: {1}".format(foundation.Id, str(e)))
        error_count += 1

# 4. Select the identified foundations
if foundations_to_select_ids:
    # Need to convert Python list to .NET List<ElementId>
    selection_list = List[ElementId](foundations_to_select_ids)
    try:
        # Ensure uidoc is available and has a Selection property
        if uidoc:
            uidoc.Selection.SetElementIds(selection_list)
            print("# Selected {0} isolated foundations whose base elevation is above their associated Level.".format(len(foundations_to_select_ids)))
        else:
             print("# Error: uidoc object is not available. Cannot set selection.")
             error_count += 1
    except Exception as sel_ex:
        print("# Error setting selection: {0}".format(str(sel_ex)))
        error_count += 1
elif foundations_processed > 0 and error_count == 0:
    print("# No isolated foundations found matching the criteria.")
elif foundations_processed == 0:
     print("# No isolated foundations found in the document.")

# Optional summary print statements (uncomment for debugging)
# print("# --- Summary ---")
# print("# Foundations processed: {0}".format(foundations_processed))
# print("# Foundations selected: {0}".format(len(foundations_to_select_ids)))
# print("# Skipped (no level found): {0}".format(foundations_skipped_no_level))
# print("# Skipped (no elevation data): {0}".format(foundations_skipped_no_elevation))
# print("# Errors encountered: {0}".format(error_count))