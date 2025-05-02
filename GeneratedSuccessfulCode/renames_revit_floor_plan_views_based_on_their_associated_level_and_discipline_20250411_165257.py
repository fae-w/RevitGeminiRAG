# Purpose: This script renames Revit floor plan views based on their associated level and discipline.

﻿# Mandatory Imports
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    ViewPlan,
    ViewType,
    Level,
    ElementId,
    BuiltInParameter,
    LabelUtils,
    View # Import View for isinstance check if needed, though OfClass(ViewPlan) should suffice
)
# No clr needed for LabelUtils, it's in Autodesk.Revit.DB

# --- Script Core Logic ---

# Collect Floor Plan views (non-templates)
collector = FilteredElementCollector(doc).OfClass(ViewPlan)

# Use a list comprehension for filtering
# Filter for FloorPlan type and ensure it's not a template
floor_plans = [v for v in collector if v.ViewType == ViewType.FloorPlan and not v.IsTemplate]

renamed_count = 0
skipped_no_level = 0
error_count = 0
already_correct_count = 0

# Iterate through the collected floor plan views
for view in floor_plans:
    level_name = "UNKNOWN_LEVEL"
    discipline_name = "UNKNOWN_DISCIPLINE"
    can_rename = True
    original_name = view.Name # Store original name for comparison and logging

    # 1. Get Level Name
    try:
        level_param = view.get_Parameter(BuiltInParameter.PLAN_VIEW_LEVEL)
        if level_param and level_param.HasValue:
            level_id = level_param.AsElementId()
            if level_id and level_id != ElementId.InvalidElementId:
                level = doc.GetElement(level_id)
                if isinstance(level, Level):
                    level_name = level.Name
                else:
                    # Failed to get Level element from valid ID
                    # print("# Warning: Could not find Level element for ID {} in view '{}'.".format(level_id, original_name)) # Debug
                    can_rename = False
                    skipped_no_level += 1
            else:
                # Invalid Level ID associated with the view
                # print("# Warning: View '{}' has invalid Level ID.".format(original_name)) # Debug
                can_rename = False
                skipped_no_level += 1
        else:
            # View doesn't have the Level parameter or it has no value
            # print("# Warning: View '{}' has no Level parameter value.".format(original_name)) # Debug
            can_rename = False
            skipped_no_level += 1
    except Exception as e_lvl:
        # print("# Error getting Level for view '{}': {}".format(original_name, e_lvl)) # Debug
        can_rename = False
        error_count += 1 # Count as error if exception occurs getting level

    # 2. Get Discipline Name (only proceed if level was determined)
    if can_rename:
        try:
            # Use the Discipline property (returns ForgeTypeId) and LabelUtils
            discipline_type_id = view.Discipline
            discipline_label = LabelUtils.GetLabelForDiscipline(discipline_type_id)

            if discipline_label:
                discipline_name = discipline_label
            else:
                # Fallback: Try reading the parameter directly as a string if LabelUtils fails
                discipline_param = view.get_Parameter(BuiltInParameter.VIEW_DISCIPLINE)
                if discipline_param:
                    discipline_name_from_param = discipline_param.AsValueString()
                    if discipline_name_from_param:
                         discipline_name = discipline_name_from_param
                    # else: Keep default "UNKNOWN_DISCIPLINE"

        except Exception as e_disc:
            # print("# Error getting Discipline for view '{}': {}".format(original_name, e_disc)) # Debug
            # Keep default "UNKNOWN_DISCIPLINE", but still attempt rename based on level
            error_count += 1

    # 3. Construct and Apply New Name (only if we identified the level)
    if can_rename:
        # Clean names: replace spaces with underscores for consistency
        clean_level_name = level_name.replace(" ", "_")
        clean_discipline_name = discipline_name.replace(" ", "_")

        # Construct the new name based on the pattern
        new_name = "FP_{}_{}".format(clean_level_name, clean_discipline_name)

        # Check if renaming is necessary
        if original_name != new_name:
            try:
                # Attempt to rename the view
                view.Name = new_name
                renamed_count += 1
                # print("# Renamed view '{}' (ID: {}) to '{}'".format(original_name, view.Id, new_name)) # Debug
            except Exception as e_rename:
                # Handle potential errors during renaming (e.g., duplicate names)
                # print("# Error renaming view '{}' (ID: {}) to '{}': {}".format(original_name, view.Id, new_name, e_rename)) # Debug
                error_count += 1
        else:
            # Name is already correct
            already_correct_count +=1
            # print("# View '{}' already has the correct name.".format(original_name)) # Debug


# Optional: Print summary to RevitPythonShell output (comment out if not desired)
# print("--- Floor Plan Renaming Summary ---")
# print("Successfully renamed: {}".format(renamed_count))
# print("Already had correct name: {}".format(already_correct_count))
# print("Skipped (No Associated Level Found): {}".format(skipped_no_level))
# print("Errors encountered: {}".format(error_count))
# print("Total Floor Plans Processed: {}".format(len(floor_plans)))