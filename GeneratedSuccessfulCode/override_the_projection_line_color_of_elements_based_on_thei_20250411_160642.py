# Import necessary classes
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    OverrideGraphicSettings,
    Color,
    View,
    ElementId,
    BuiltInParameter,
    Element, # Included for completeness, though direct Element methods might not be used
    StorageType # Needed for parameter type check
)

# --- Configuration ---
# Define the mapping from Mark value to Color
# Mark 'A' -> Red, Mark 'B' -> Blue
# This map is case-sensitive. Use .upper() or .lower() on mark_value if case-insensitivity is needed.
mark_color_map = {
    "A": Color(255, 0, 0),    # Red
    "B": Color(0, 0, 255)     # Blue
    # Add more mappings here if needed, e.g., "C": Color(0, 255, 0) for Green
}

# --- Pre-create Override Settings for each color ---
# This avoids creating the same settings object multiple times inside the loop.
override_settings_map = {}
for mark_value, color in mark_color_map.items():
    ogs = OverrideGraphicSettings()
    ogs.SetProjectionLineColor(color)
    override_settings_map[mark_value] = ogs

# --- Get Active View ---
# Assumes 'doc' is pre-defined in the execution scope.
active_view = doc.ActiveView

# Proceed only if active_view is valid and allows overrides
if active_view and isinstance(active_view, View) and not active_view.IsTemplate and active_view.AreGraphicsOverridesAllowed():

    # --- Collect visible elements in the active view ---
    # Note: This collects *all* element instances visible in the view.
    # If performance is critical on very large models, consider filtering by category first.
    collector = FilteredElementCollector(doc, active_view.Id).WhereElementIsNotElementType()

    elements_overridden_count = 0
    # --- Iterate through elements and apply overrides based on Mark value ---
    # Using a general try-except block for robustness during iteration over the collector
    try:
        for element in collector:
            # Use a nested try-except block to handle errors for individual elements gracefully
            try:
                # Get the 'Mark' parameter using the specific BuiltInParameter
                mark_param = element.get_Parameter(BuiltInParameter.ALL_MODEL_MARK)

                # Check if the parameter exists, has a value, and is of type String
                if mark_param and mark_param.HasValue:
                    # Check storage type AFTER confirming HasValue to avoid potential errors on null params
                    if mark_param.StorageType == StorageType.String:
                        mark_value = mark_param.AsString()

                        # Ensure mark_value is not None or empty string before dictionary lookup
                        # Check if the retrieved mark value exists as a key in our predefined map
                        if mark_value and mark_value in override_settings_map:
                            # Get the pre-created override settings for this specific mark value
                            override_settings = override_settings_map[mark_value]

                            # Apply the override settings to the element in the active view
                            # This operation must happen within the external transaction context.
                            active_view.SetElementOverrides(element.Id, override_settings)
                            elements_overridden_count += 1
            except Exception as element_e:
                # Silently ignore elements that cause errors during parameter access or override application
                # This prevents one problematic element from stopping the script for others.
                # print("# Debug: Error processing element {}: {}".format(element.Id, element_e)) # Optional Debug line
                pass # Continue to the next element

    except Exception as loop_e:
         # Catch potential errors during the collector iteration itself (less common)
         # print("# Error during element collection or processing loop: {}".format(loop_e)) # Optional Debug line
         pass # Allow script to finish if possible, though results might be incomplete

    # Optional: Print summary of actions (commented out as per requirements)
    # print("# Applied projection line color overrides to {} elements based on 'Mark' value in view '{}'.".format(elements_overridden_count, active_view.Name))

# else:
    # Optional: Handle case where the view is not suitable (commented out)
    # This part will not execute if the active_view check fails.
    # print("# Error: Requires an active, non-template graphical view where overrides are allowed.")