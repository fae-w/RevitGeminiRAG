# Purpose: This script groups Revit views in the Project Browser based on a custom parameter and optionally by family and type.

﻿# Import necessary .NET libraries
import clr
clr.AddReference('System.Collections')
from System.Collections.Generic import List
import System # Required for specific Exception types like ArgumentException

# Add Revit API references
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')

# Import Revit API namespaces
import Autodesk.Revit.DB as DB
import Autodesk.Revit.UI as UI # Often useful, even if not explicitly used everywhere
from Autodesk.Revit.DB import BuiltInParameter # Explicit import for BuiltInParameter
# Import Revit Exceptions specifically (using the DB alias)
from Autodesk.Revit.Exceptions import InvalidOperationException, ArgumentException as RevitArgumentException

# --- Configuration ---
custom_param_name = "Level Group" # The exact name of the custom parameter to group by first
use_family_type_grouping = True   # Include 'Family and Type' as the second grouping level
clear_existing_sorting = False     # Set to True to remove existing sorting rules
clear_existing_filters = False    # Set to True to remove existing filters

# --- Helper Function to Find Parameter Element ---
def find_parameter_element_by_name(doc_param, param_name):
    """Finds a ParameterElement by its name."""
    collector = DB.FilteredElementCollector(doc_param).OfClass(DB.ParameterElement)
    param_elem = None
    for p in collector:
        if p is None:
            continue
        try:
             definition = p.GetDefinition()
             if definition is not None and definition.Name == param_name:
                 param_elem = p
                 break
        except Exception:
             # Ignore elements where definition cannot be retrieved or compared
             pass
    return param_elem

# --- Main Logic ---
error_occurred = False
level_group_param_id = DB.ElementId.InvalidElementId
family_type_param_id = DB.ElementId.InvalidElementId
current_view_org = None

# Use the pre-defined 'doc' variable
# 1. Find Custom Parameter Element
level_group_param_elem = find_parameter_element_by_name(doc, custom_param_name)
if not level_group_param_elem:
    print("# Error: Custom parameter named '{}' not found.".format(custom_param_name))
    error_occurred = True
else:
    level_group_param_id = level_group_param_elem.Id
    if level_group_param_id == DB.ElementId.InvalidElementId:
         print("# Error: Found parameter '{}' but its ID is InvalidElementId.".format(custom_param_name))
         error_occurred = True
    else:
        print("# Found custom parameter '{}' (ID: {}).".format(custom_param_name, level_group_param_id))

# 2. Get Family and Type Parameter ID (if needed)
if use_family_type_grouping:
    # Use the ElementId corresponding to the BuiltInParameter
    # CORRECTED: Use explicitly imported BuiltInParameter
    try:
        # Use BuiltInParameter enum directly to get its ElementId representation
        family_type_param_id = DB.ElementId(BuiltInParameter.VIEW_FAMILY_AND_TYPE)
        if family_type_param_id == DB.ElementId.InvalidElementId:
             print("# Warning: Could not get a valid ElementId for BuiltInParameter.VIEW_FAMILY_AND_TYPE. Skipping this grouping level.")
             use_family_type_grouping = False # Disable if ID is invalid
        else:
            print("# Found Family and Type parameter (BIP ID: {}).".format(family_type_param_id))
    except AttributeError as attr_err:
        print("# Error accessing BuiltInParameter.VIEW_FAMILY_AND_TYPE: {}. Make sure Revit API is correctly loaded. Skipping this grouping level.".format(attr_err))
        use_family_type_grouping = False # Disable if not found
    except Exception as bip_err:
         print("# Error getting ElementId for BuiltInParameter.VIEW_FAMILY_AND_TYPE: {}. Skipping this grouping level.".format(bip_err))
         use_family_type_grouping = False # Disable if error


# 3. Get Current View Browser Organization
if not error_occurred:
    try:
        current_view_org = DB.BrowserOrganization.GetCurrentBrowserOrganizationForViews(doc)
        if not current_view_org:
            print("# Error: Could not get the current Browser Organization for Views. Is one active in the Project Browser settings?")
            error_occurred = True
        elif current_view_org.IsReadOnly:
             print("# Error: The current Browser Organization '{}' is read-only and cannot be modified.".format(current_view_org.Name))
             error_occurred = True
        else:
             print("# Info: Operating on current view organization: '{}'".format(current_view_org.Name))
    except Exception as e:
         print("# Error getting current browser organization: {}".format(e))
         error_occurred = True

# Proceed only if setup was successful so far
if not error_occurred:
    # 4. Get existing settings or create new ones
    existing_settings = None
    try:
        # Use InvalidElementId for the root folder settings
        retrieved_settings = current_view_org.GetFolderItems(DB.ElementId.InvalidElementId)
        if retrieved_settings is None:
            print("# Info: No existing settings found for the root folder of '{}'. Creating new settings.".format(current_view_org.Name))
            existing_settings = DB.BrowserOrganizationSettings()
        else:
            print("# Info: Retrieved existing settings for '{}'.".format(current_view_org.Name))
            # Create a new modifiable instance and copy properties from the retrieved one
            existing_settings = DB.BrowserOrganizationSettings()
            existing_settings.Filter = retrieved_settings.Filter # Keep existing filter unless cleared later
            # Copy Sorting rules if they exist
            if retrieved_settings.Sorting is not None:
                existing_settings.Sorting = List[DB.BrowserSetting](retrieved_settings.Sorting)
            else:
                existing_settings.Sorting = List[DB.BrowserSetting]()
            # Start grouping fresh - will be populated below
            existing_settings.Grouping = List[DB.BrowserSetting]()
            print("# Info: Copied existing settings to a modifiable instance.")

    except Exception as e:
        print("# Error getting/copying existing folder items for '{}': {}. Attempting to proceed with new settings.".format(current_view_org.Name, e))
        existing_settings = DB.BrowserOrganizationSettings() # Fallback to new settings

    # 5. Create the new list of Grouping Settings
    new_grouping_settings = List[DB.BrowserSetting]()

    # Add custom parameter grouping
    try:
        if level_group_param_id != DB.ElementId.InvalidElementId:
            # Validate if the parameter can be used for grouping views
            can_group = DB.BrowserOrganization.CanViewGroupByParameter(doc, level_group_param_id)
            if can_group:
                grouping_1 = DB.BrowserSetting(level_group_param_id)
                grouping_1.SortOrder = DB.SortOrder.Ascending
                new_grouping_settings.Add(grouping_1)
                print("# Prepared grouping by: '{}' (ID: {})".format(custom_param_name, level_group_param_id))
            else:
                print("# Error: Custom parameter '{}' (ID: {}) cannot be used for grouping views.".format(custom_param_name, level_group_param_id))
                error_occurred = True # Stop processing if primary grouping fails
        else:
             print("# Error: Cannot add grouping for '{}' due to invalid parameter ID.".format(custom_param_name))
             error_occurred = True # Stop processing if primary grouping fails
    except RevitArgumentException as arg_ex:
        print("# Error: Failed to create BrowserSetting for custom parameter '{}'. API Message: {}".format(custom_param_name, arg_ex.Message))
        error_occurred = True
    except System.Exception as e:
        print("# Error creating BrowserSetting for custom parameter '{}': {}".format(custom_param_name, e))
        error_occurred = True

    # Add Family and Type grouping (if enabled and no errors so far)
    if use_family_type_grouping and not error_occurred:
         try:
            if family_type_param_id != DB.ElementId.InvalidElementId:
                can_group = DB.BrowserOrganization.CanViewGroupByParameter(doc, family_type_param_id)
                if can_group:
                    grouping_2 = DB.BrowserSetting(family_type_param_id)
                    grouping_2.SortOrder = DB.SortOrder.Ascending
                    new_grouping_settings.Add(grouping_2)
                    print("# Prepared grouping by: Family and Type (BIP ID: {})".format(family_type_param_id))
                else:
                    # It's unexpected that VIEW_FAMILY_AND_TYPE couldn't be used, but handle it.
                    print("# Warning: Could not create BrowserSetting for Family and Type (BIP ID: {}). Parameter cannot be used for grouping.".format(family_type_param_id))
            else:
                print("# Info: Skipping Family and Type grouping due to previously identified invalid ID.")
         except RevitArgumentException as arg_ex:
             print("# Warning: Could not create BrowserSetting for Family and Type (BIP ID: {}). API Message: {}".format(family_type_param_id, arg_ex.Message))
         except System.Exception as e:
             print("# Warning: Failed to create BrowserSetting for Family and Type (BIP ID: {}): {}".format(family_type_param_id, e))

# Final application step if no critical errors occurred
if not error_occurred:
    # 6. Assign the new grouping settings
    existing_settings.Grouping = new_grouping_settings

    # 7. Handle existing Sorting and Filtering based on configuration
    if clear_existing_sorting:
        if existing_settings.Sorting is not None and existing_settings.Sorting.Count > 0:
            print("# Info: Clearing existing sorting rules.")
            existing_settings.Sorting = List[DB.BrowserSetting]()
    # else: print("# Info: Preserving existing sorting rules.")

    if clear_existing_filters:
        if existing_settings.Filter is not None:
            print("# Info: Clearing existing filters.")
            existing_settings.Filter = None
    # else: print("# Info: Preserving existing filters.")


    # 8. Apply the modified settings back to the Browser Organization
    # IMPORTANT: This operation requires an active transaction, handled externally.
    try:
        # Use InvalidElementId for the root folder settings
        current_view_org.SetFolderItems(DB.ElementId.InvalidElementId, existing_settings)
        print("# Successfully applied new settings to Browser Organization: '{}'".format(current_view_org.Name))
        print("# Please check the Project Browser to confirm the changes.")
    except RevitArgumentException as arg_ex:
        print("# Error applying settings to '{}'. Possible invalid parameter ID used. API Message: {}".format(current_view_org.Name, arg_ex.Message))
    except InvalidOperationException as inv_op_ex:
        print("# Error applying settings to '{}'. Invalid operation. API Message: {}".format(current_view_org.Name, inv_op_ex.Message))
    except System.Exception as e:
        print("# Unexpected error applying settings to Browser Organization '{}': {}".format(current_view_org.Name, e))

# Final status message (optional, commented out per instructions)
# if error_occurred:
#      print("# Script finished with errors.")
# else:
#      print("# Script finished.")