# Mandatory Imports
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    OverrideGraphicSettings,
    View,
    ElementId,
    BuiltInParameter,
    Parameter # To check parameter existence
)
import System # For exception handling

# --- Configuration ---
# Specify the username to match (case-sensitive)
target_username = "SpecificUser" # Replace with the actual username

# --- Get Active View ---
active_view = doc.ActiveView
if not active_view or not isinstance(active_view, View) or active_view.IsTemplate:
    print("# Error: Requires an active, non-template graphical view to apply overrides.")
    # Exit script cleanly if no suitable view
    import sys
    sys.exit()

if not active_view.AreGraphicsOverridesAllowed():
     print("# Error: The active view '{{}}' does not support element overrides.".format(active_view.Name))
     import sys
     sys.exit()

# --- Create Override Settings ---
override_settings = OverrideGraphicSettings()
override_settings.SetHalftone(True)

# --- Find Elements Created By Target User ---
elements_to_override_ids = []
collector = FilteredElementCollector(doc, active_view.Id).WhereElementIsNotElementType()

for element in collector:
    try:
        # Get the 'Created By' parameter
        created_by_param = element.get_Parameter(BuiltInParameter.CREATED_BY)

        # Check if the parameter exists and its value matches the target username
        if created_by_param and created_by_param.HasValue:
            param_value = created_by_param.AsString() # Use AsString() for string parameters
            if param_value == target_username:
                elements_to_override_ids.append(element.Id)
    except Exception as e:
        # print("# Skipping Element ID {{}} - Error accessing 'Created By' parameter: {{}}".format(element.Id, e.Message)) # Debug
        pass # Silently skip elements where the parameter cannot be accessed

# --- Apply Overrides ---
applied_count = 0
error_count = 0

if not elements_to_override_ids:
    print("# No elements found in the active view created by '{}'.".format(target_username))
else:
    print("# Found {{}} elements created by '{}' in view '{{}}'. Applying halftone override...".format(len(elements_to_override_ids), target_username, active_view.Name))
    for element_id in elements_to_override_ids:
        try:
            # Check if element still exists (might have been deleted)
            element = doc.GetElement(element_id)
            if element is not None:
                 # Re-check if override can be applied (optional but safe)
                 if active_view.CanApplyElementOverrides(element_id):
                      active_view.SetElementOverrides(element_id, override_settings)
                      applied_count += 1
                 else:
                      # Optionally log elements that cannot have overrides applied in this view
                      # print("# Skipping Element ID {{}} - Cannot apply override in this view.".format(element_id))
                      error_count += 1 # Count as an error/skip if needed
            else:
                # Optionally log elements that no longer exist
                # print("# Skipping Element ID {{}} - Element not found.".format(element_id))
                error_count += 1 # Count as an error/skip
        except System.Exception as e:
            # print("# Error applying override to Element ID {{}}: {{}}".format(element_id, e.Message)) # Optional detailed error message
            error_count += 1

# --- Final Summary ---
if applied_count > 0:
    print("# Successfully applied halftone override to {{}} elements created by '{}' in view '{{}}'.".format(applied_count, target_username, active_view.Name))
if error_count > 0:
    print("# Encountered {{}} issues (element not found, not visible, or other error) while applying overrides.".format(error_count))
if applied_count == 0 and len(elements_to_override_ids) > 0:
     print("# No overrides were successfully applied, though matching elements were identified. Check view visibility or specific element issues.")