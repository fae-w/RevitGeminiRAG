# Purpose: This script creates or updates a Revit parameter filter based on a specified U-Value threshold for windows.

﻿# Import necessary Revit API classes and standard libraries
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
clr.AddReference('System.Collections')
from System.Collections.Generic import List
from System import String, Exception as SystemException, Double

import Autodesk.Revit.DB as DB

# Attempt to import newer unit/spec classes, handle fallback for older Revit/API versions
try:
    # Revit 2021+ API uses ForgeTypeId
    ForgeTypeId = DB.ForgeTypeId
    UnitTypeId = DB.UnitTypeId
    SpecTypeId = DB.SpecTypeId
    use_forge_type_id = True
except AttributeError:
    # Older Revit API uses DisplayUnitType
    DisplayUnitType = DB.DisplayUnitType
    use_forge_type_id = False

# --- Configuration ---
filter_name = "Inefficient Windows"
parameter_name = "U-Value"  # Case-sensitive name of the shared or project parameter
threshold_value_si = 1.8  # W/m²K (SI units)
target_category_bic = DB.BuiltInCategory.OST_Windows

# --- Helper Function to Find Parameter ---
def find_parameter_id_by_name(doc, name, category_bic):
    """
    Finds a filterable parameter ID by name for a given category.
    Checks if the parameter is numeric and applicable to the category.
    """
    target_category_id = DB.ElementId(category_bic)
    category_ids = List[DB.ElementId]()
    category_ids.Add(target_category_id)

    # Get parameters that are filterable for the specified category
    filterable_params = DB.ParameterFilterUtilities.GetFilterableParametersInCommon(doc, category_ids)

    param_id_found = DB.ElementId.InvalidElementId # Use InvalidElementId as default

    for p_id in filterable_params:
        param_elem = doc.GetElement(p_id)
        if param_elem is not None:
            # Check if the parameter name matches
            if param_elem.Name == name:
                # Check if it's a numerical type suitable for comparison
                # GetDefinition() is available on ParameterElement and SharedParameterElement
                definition = None
                if hasattr(param_elem, 'GetDefinition'):
                    definition = param_elem.GetDefinition()

                if definition:
                    # ParameterType.Number is common for simple numerical custom params.
                    # ParameterType.ThermalTransmittance or UFactor would be more specific.
                    # GetFilterableParametersInCommon should ideally only return suitable types.
                    # We prioritize finding by name and rely on rule creation to validate type implicitly.
                    # Check if it's a numeric type (Number, Integer, Angle, Length, Area, Volume, etc.)
                    # For U-Value, 'Number' or specific Thermal types are expected.
                    # ParameterType is an enum in DB namespace
                    if definition.ParameterType == DB.ParameterType.Number or \
                       definition.ParameterType == DB.ParameterType.Integer or \
                       definition.ParameterType == DB.ParameterType.ThermalTransmittance or \
                       definition.ParameterType == DB.ParameterType.UFactor:
                        param_id_found = p_id
                        break # Found the first matching filterable parameter by name

    if param_id_found == DB.ElementId.InvalidElementId:
        return None # Indicate parameter not found or not suitable
    else:
        return param_id_found


# --- Main Script ---
# Find the parameter ID
param_id = find_parameter_id_by_name(doc, parameter_name, target_category_bic)

if param_id is None:
    print("# Error: Parameter named '{}' not found, not filterable, or not applicable for category '{}'.".format(parameter_name, target_category_bic.ToString()))
else:
    # --- Get Category ID ---
    category = DB.Category.GetCategory(doc, target_category_bic)
    if category is None:
        print("# Error: Category '{}' not found in the document.".format(target_category_bic.ToString()))
    else:
        category_ids = List[DB.ElementId]()
        category_ids.Add(category.Id)

        # --- Convert threshold value to internal units ---
        threshold_internal_units = None
        conversion_success = False
        internal_unit_type_name = "Unknown" # For logging

        try:
            param_def = doc.GetElement(param_id).GetDefinition()
            param_storage_type = param_def.ParameterType # Using ParameterType enum

            # --- Unit Conversion Logic ---
            if use_forge_type_id:
                si_unit = UnitTypeId.WattsPerSquareMeterKelvin
                internal_unit = None

                # Try getting units based on parameter's spec type if available (Revit 2022+)
                spec_type_id = None
                if hasattr(param_def, 'GetSpecTypeId') and param_def.GetSpecTypeId():
                     spec_type_id = param_def.GetSpecTypeId()
                elif param_storage_type == DB.ParameterType.ThermalTransmittance: # Check ParameterType enum value
                     spec_type_id = SpecTypeId.ThermalTransmittance
                # Add elif for other relevant spec types if needed

                if spec_type_id and spec_type_id.TypeId: # Check if a valid SpecTypeId was found
                    try:
                        format_options = doc.GetUnits().GetFormatOptions(spec_type_id)
                        internal_unit = format_options.GetUnitTypeId()
                        internal_unit_type_name = internal_unit.TypeId # Get string representation for logging
                    except SystemException as fmt_ex:
                         print("# Warning: Could not get FormatOptions for SpecTypeId '{}'. Trying fallback. Error: {}".format(spec_type_id.TypeId, fmt_ex.Message))

                if internal_unit is None:
                    # Fallback: Assume internal unit based on common practice if spec type fails
                    # For U-Value, Imperial is often BTU/(h·ft²·°F) internally
                    internal_unit = UnitTypeId.BritishThermalUnitsPerHourSquareFootFahrenheit
                    internal_unit_type_name = internal_unit.TypeId
                    print("# Warning: Using assumed internal unit '{}' for conversion.".format(internal_unit_type_name))

                # Perform the conversion
                threshold_internal_units = DB.UnitUtils.Convert(threshold_value_si, si_unit, internal_unit)
                conversion_success = True

            else: # Older Revit API using DisplayUnitType
                si_dut = DisplayUnitType.DUT_WATTS_PER_SQUARE_METER_KELVIN
                # Assume internal DUT for U-Value - typically Imperial in older versions
                internal_dut = DisplayUnitType.DUT_BTU_PER_HOUR_SQUARE_FOOT_FAHRENHEIT
                internal_unit_type_name = internal_dut.ToString()

                # Check if UnitUtils.Convert exists (might exist in some older versions)
                if hasattr(DB.UnitUtils, 'Convert'):
                    try:
                        threshold_internal_units = DB.UnitUtils.Convert(threshold_value_si, si_dut, internal_dut)
                        conversion_success = True
                    except SystemException as conv_e_old:
                        print("# Warning: UnitUtils.Convert failed (DUT: {} to {}). Trying ConvertToInternalUnits. Error: {}".format(si_dut, internal_dut, conv_e_old))
                        conversion_success = False # Reset flag

                # Fallback to ConvertToInternalUnits if Convert doesn't exist or failed
                if not conversion_success:
                     # ConvertToInternalUnits uses the parameter's data type implicit internal unit.
                     # We provide the value and the *display* unit it currently represents.
                     try:
                         # This might work if the parameter type implies the internal units correctly.
                         threshold_internal_units = DB.UnitUtils.ConvertToInternalUnits(threshold_value_si, si_dut)
                         conversion_success = True
                         print("# Info: Used ConvertToInternalUnits assuming target parameter type handles internal units.")
                     except SystemException as conv_e_internal:
                         print("# Error: Unit conversion failed using both Convert (if available) and ConvertToInternalUnits. Cannot proceed. Error: {}".format(conv_e_internal))
                         conversion_success = False


        except SystemException as conv_ex:
            print("# Error during unit conversion setup or execution: {}".format(conv_ex))
            conversion_success = False

        # Proceed only if conversion was successful
        if conversion_success and threshold_internal_units is not None:
            # --- Create Filter Rule ---
            try:
                # Using CreateGreaterRule for numerical comparison.
                # Ensure threshold_internal_units is Double type for the rule factory
                filter_rule = DB.ParameterFilterRuleFactory.CreateGreaterRule(param_id, float(threshold_internal_units))
                rules = List[DB.FilterRule]()
                rules.Add(filter_rule)

                # --- Create Element Filter ---
                # False means elements matching the rule *pass* the filter (i.e., are selected/affected)
                # True means elements matching the rule *fail* the filter (inverse logic)
                element_filter = DB.ElementParameterFilter(rules, False)

                # --- Find or Create Filter Element ---
                filter_element = None
                collector = DB.FilteredElementCollector(doc).OfClass(DB.ParameterFilterElement)
                for existing_filter in collector:
                    if existing_filter.Name == filter_name:
                        filter_element = existing_filter
                        break

                if filter_element is None:
                    # Create the ParameterFilterElement (Transaction managed externally)
                    try:
                        filter_element = DB.ParameterFilterElement.Create(
                            doc,
                            filter_name,
                            category_ids,
                            element_filter
                        )
                        print("# Filter '{}' created successfully. Criteria: '{}' > {} W/m²K ({} internal units - {} assumed/derived)".format(
                              filter_name, parameter_name, threshold_value_si, threshold_internal_units, internal_unit_type_name))
                    except SystemException as create_ex:
                         print("# Error creating filter '{}': {}".format(filter_name, create_ex.Message))
                else:
                    # Filter exists, update it
                    try:
                        # Update categories if changed (optional check, can just set)
                        filter_element.SetCategories(category_ids)
                        # Update the filter definition
                        filter_element.SetElementFilter(element_filter)
                        print("# Filter '{}' already existed and has been updated. Criteria: '{}' > {} W/m²K ({} internal units - {} assumed/derived)".format(
                              filter_name, parameter_name, threshold_value_si, threshold_internal_units, internal_unit_type_name))
                    except SystemException as update_ex:
                        print("# Error updating existing filter '{}': {}".format(filter_name, update_ex.Message))

            except SystemException as rule_ex:
                print("# Error creating filter rule or filter element for parameter '{}' (ID: {}): {}".format(parameter_name, param_id, rule_ex.Message))
                print("# This might indicate an issue with the parameter type, the converted value, or API limits.")
        else:
            print("# Error: Unit conversion failed for value {}. Cannot create filter rule.".format(threshold_value_si))