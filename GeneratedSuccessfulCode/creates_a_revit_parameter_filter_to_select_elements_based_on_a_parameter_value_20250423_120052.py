# Purpose: This script creates a Revit parameter filter to select elements based on a parameter value.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('System.Collections') # Required for List<T>
from System.Collections.Generic import List
from System import Exception as SystemException

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    BuiltInCategory,
    ElementId,
    ParameterFilterElement,
    ParameterFilterRuleFactory,
    FilterRule,
    BuiltInParameter,
    UnitUtils
)

# Attempt to import newer unit classes, handle fallback
try:
    from Autodesk.Revit.DB import ForgeTypeId
    from Autodesk.Revit.DB import UnitTypeId
    use_forge_type_id = True
except ImportError:
    from Autodesk.Revit.DB import DisplayUnitType
    use_forge_type_id = False

# --- Configuration ---
filter_name = "Low Walls"
height_threshold_mm = 1500.0
target_category = BuiltInCategory.OST_Walls
# Parameter: Unconnected Height (WALL_USER_HEIGHT_PARAM)
param_id = ElementId(BuiltInParameter.WALL_USER_HEIGHT_PARAM)

# --- Convert threshold value to internal units (feet) ---
threshold_internal_units = None
conversion_success = False
try:
    if use_forge_type_id:
        threshold_internal_units = UnitUtils.ConvertToInternalUnits(height_threshold_mm, UnitTypeId.Millimeters)
        conversion_success = True
    else:
        threshold_internal_units = UnitUtils.ConvertToInternalUnits(height_threshold_mm, DisplayUnitType.DUT_MILLIMETERS)
        conversion_success = True
except SystemException as conv_e:
    print("# Error converting threshold height {{{{}}}}mm to internal units: {{{{}}}}".format(height_threshold_mm, conv_e))
except AttributeError as attr_e:
    print("# Error accessing unit types: {{{{}}}}. Check API version compatibility.".format(attr_e))

if not conversion_success or threshold_internal_units is None:
    print("# Error: Unit conversion failed. Cannot proceed with filter creation.")
else:
    # --- Define Categories ---
    categories = List[ElementId]()
    categories.Add(ElementId(target_category))

    # --- Create Filter Rule ---
    filter_rule = None
    try:
        # Create a "less than" rule
        filter_rule = ParameterFilterRuleFactory.CreateLessRule(param_id, threshold_internal_units)
    except Exception as e:
        print("# Error creating filter rule for parameter ID {{{{}}}} and value {{{{:.4f}}}}: {{{{}}}}".format(param_id.IntegerValue, threshold_internal_units, e))

    if filter_rule:
        filter_rules = List[FilterRule]()
        filter_rules.Add(filter_rule)

        # --- Check if filter already exists ---
        existing_filter = None
        filter_collector = FilteredElementCollector(doc).OfClass(ParameterFilterElement)
        for f in filter_collector:
            if f.Name == filter_name:
                existing_filter = f
                break

        # --- Create Filter (Transaction handled externally) ---
        if existing_filter:
            print("# Filter named '{{}}' already exists with ID: {{}}".format(filter_name, existing_filter.Id))
            # Optional: Could add code here to update the existing filter's rules/categories if desired
            # try:
            #     existing_filter.SetCategories(categories)
            #     existing_filter.SetRules(filter_rules)
            #     print("# Updated existing filter '{{}}'".format(filter_name))
            # except Exception as update_e:
            #     print("# Error updating existing filter '{{}}': {{}}".format(filter_name, update_e))
        else:
            try:
                new_filter = ParameterFilterElement.Create(doc, filter_name, categories, filter_rules)
                print("# Successfully created Parameter Filter Element: '{}' with ID: {}".format(new_filter.Name, new_filter.Id))
                print("# Filter criteria: Walls with 'Unconnected Height' < {}mm ({:.4f} ft)".format(height_threshold_mm, threshold_internal_units))
            except SystemException as create_ex:
                print("# Error creating ParameterFilterElement '{}': {}".format(filter_name, create_ex.Message))
            except Exception as generic_ex: # Catch other potential exceptions during creation
                 print("# An unexpected error occurred during filter creation: {}".format(generic_ex))

    else:
        # Error message for rule creation failure already printed
        print("# Filter rule creation failed. Cannot create filter.")