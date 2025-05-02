# Purpose: This script duplicates a Revit view as dependent for each scope box, assigning the scope box and renaming the new view.

﻿# Import necessary classes
import clr
clr.AddReference('System.Collections')
from System.Collections.Generic import List

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    View,
    ViewPlan,
    ElementId,
    ViewDuplicateOption,
    BuiltInCategory,
    Parameter,
    BuiltInParameter
)
import System # Required for Exception handling

# --- Configuration ---
primary_view_name = "L1 - Block 43" # Name of the primary Floor Plan view to duplicate

# --- Helper Function to Find View ---
def find_view_by_name(doc_param, view_name):
    """Finds a View element by its exact name."""
    collector = FilteredElementCollector(doc_param).OfClass(View)
    for view in collector:
        # Ensure it's not a template and matches the name
        if not view.IsTemplate and view.Name == view_name:
            # Check if it's a suitable type (e.g., FloorPlan, CeilingPlan)
            # Although scope boxes can apply to sections/elevations, duplicating as dependent usually applies to plans.
            if isinstance(view, ViewPlan): # Check if it's a ViewPlan
                 # Check if it's already a dependent view
                 if view.GetPrimaryViewId() == ElementId.InvalidElementId:
                     return view
                 else:
                     print("# Error: View '{{}}' is already a dependent view.".format(view_name))
                     return None
            else:
                # Allow other view types but warn if not ViewPlan as Scope Box application might differ
                # print("# Warning: View '{{}}' is not a Floor Plan, but proceeding.".format(view_name))
                if view.GetPrimaryViewId() == ElementId.InvalidElementId:
                     return view
                else:
                     print("# Error: View '{{}}' is already a dependent view.".format(view_name))
                     return None

    print("# Error: Primary view named '{{}}' not found or is not a valid primary view.".format(view_name))
    return None

# --- Find the Primary View ---
primary_view = find_view_by_name(doc, primary_view_name)

# --- Proceed only if Primary View is found ---
if primary_view:
    # --- Find all Scope Boxes in the project ---
    scope_box_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_ScopeBoxes).WhereElementIsNotElementType()
    scope_boxes = list(scope_box_collector)

    if not scope_boxes:
        print("# Error: No Scope Boxes found in the project.")
    else:
        created_count = 0
        failed_count = 0
        print("# Found {{}} Scope Boxes. Attempting to create dependent views for primary view '{{}}' (ID: {{}})...".format(len(scope_boxes), primary_view.Name, primary_view.Id))

        for scope_box in scope_boxes:
            scope_box_name = scope_box.Name
            scope_box_id = scope_box.Id
            new_view_name = "{} - {}".format(primary_view_name, scope_box_name) # Proposed name
            new_view_id = ElementId.InvalidElementId

            try:
                # 1. Duplicate the primary view as dependent
                if primary_view.CanViewBeDuplicated(ViewDuplicateOption.AsDependent):
                    new_view_id = primary_view.Duplicate(ViewDuplicateOption.AsDependent)
                else:
                    print("# Error: Primary view '{{}}' cannot be duplicated as dependent.".format(primary_view_name))
                    failed_count += 1
                    continue # Skip to next scope box

                if new_view_id == ElementId.InvalidElementId:
                    print("# Error: Failed to duplicate primary view for Scope Box '{{}}'.".format(scope_box_name))
                    failed_count += 1
                    continue # Skip to next scope box

                new_view = doc.GetElement(new_view_id)
                if not new_view:
                     print("# Error: Could not retrieve newly created dependent view element for Scope Box '{{}}'.".format(scope_box_name))
                     failed_count += 1
                     # Attempt to delete potentially orphaned view element if possible/needed? API Limitations might prevent easy cleanup here.
                     continue

                # 2. Assign the Scope Box to the new dependent view
                scope_box_param = new_view.get_Parameter(BuiltInParameter.VIEWER_VOLUME_OF_INTEREST_CROP)
                if scope_box_param and not scope_box_param.IsReadOnly:
                    try:
                        scope_box_param.Set(scope_box_id)
                        # print("# Info: Assigned Scope Box '{{}}' to new view ID {{}}.".format(scope_box_name, new_view_id)) # Optional Debug
                    except Exception as set_sb_ex:
                         print("# Warning: Failed to assign Scope Box '{{}}' to new view '{{}}' (ID: {{}}). Error: {{}}".format(
                            scope_box_name, new_view.Name, new_view_id, str(set_sb_ex)
                         ))
                         # Proceeding with renaming anyway, but crop might be wrong.
                else:
                    print("# Warning: Could not find or set the Scope Box parameter for the new view '{{}}' (ID: {{}}). Crop region may not match Scope Box '{{}}'.".format(
                        new_view.Name, new_view_id, scope_box_name
                    ))

                # 3. Rename the new dependent view
                try:
                    # Basic check for existing name (might need more robust unique naming)
                    existing_names = [v.Name for v in FilteredElementCollector(doc, primary_view.Id).OfClass(View)] # Check dependents of primary
                    final_new_name = new_view_name
                    counter = 1
                    while final_new_name in existing_names:
                        final_new_name = "{} ({})".format(new_view_name, counter)
                        counter += 1

                    if new_view.Name != final_new_name:
                        new_view.Name = final_new_name
                        print("# Successfully created and renamed dependent view: '{}' (ID: {}) linked to Scope Box: '{}'".format(
                            final_new_name, new_view_id.IntegerValue, scope_box_name
                        ))
                    else:
                         print("# Successfully created dependent view: '{}' (ID: {}) linked to Scope Box: '{}' (already named correctly)".format(
                            new_view.Name, new_view_id.IntegerValue, scope_box_name
                        ))

                    created_count += 1

                except Exception as rename_ex:
                    print("# Error: Failed to rename new view (ID: {{}}) for Scope Box '{{}}'. Original name: '{{}}'. Error: {{}}".format(
                        new_view_id, scope_box_name, new_view.Name, str(rename_ex)
                    ))
                    failed_count += 1
                    # The view was created but not renamed/scope box potentially not set correctly.

            except System.Exception as general_ex:
                print("# Error processing Scope Box '{{}}': {{}}".format(scope_box_name, str(general_ex)))
                failed_count += 1
                # Clean up the potentially created view if ID is known?
                # This is tricky without transactions managed here. C# wrapper should handle rollback on failure.
                # if new_view_id != ElementId.InvalidElementId:
                #     try:
                #         doc.Delete(new_view_id) # Risky if transaction state is unknown
                #     except:
                #         pass # Ignore delete error

        print("# --- Summary ---")
        print("# Successfully created: {}".format(created_count))
        print("# Failed attempts:    {}".format(failed_count))

else:
    print("# Operation cancelled: Primary view '{{}}' could not be found or is not suitable.".format(primary_view_name))