# Purpose: This script hides text notes smaller than a specified size in the active Revit view.

﻿# Import necessary classes
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
clr.AddReference('System.Collections')
from System.Collections.Generic import List
from Autodesk.Revit.DB import (
    FilteredElementCollector,
    TextNote,
    TextNoteType,
    ElementId,
    UnitUtils,
    View,
    BuiltInParameter,
    Parameter,
    Element
)

# --- Configuration ---
# Threshold text size in millimeters
threshold_mm = 2.0

# --- Get Active View ---
# Assume 'doc' and 'uidoc' are pre-defined and available
active_view = None
try:
    active_view = doc.ActiveView
except Exception as e:
    print("# Error getting active view: {}".format(e))

if not active_view or not isinstance(active_view, View):
    print("# Error: No active valid project view found or view is inaccessible.")
    active_view = None # Prevent further processing
elif active_view.IsTemplate:
    print("# Error: The active view ('{}') is a view template. Cannot hide elements.".format(active_view.Name))
    active_view = None # Prevent further processing

# Proceed only if the view is valid
if active_view:
    # --- Convert Threshold to Internal Units (Feet) ---
    threshold_internal = None
    conversion_success = False

    # Try Revit 2021+ UnitTypeId method first
    try:
        from Autodesk.Revit.DB import UnitTypeId
        millimeters_type_id = UnitTypeId.Millimeters
        threshold_internal = UnitUtils.ConvertToInternalUnits(threshold_mm, millimeters_type_id)
        conversion_success = True
        # print("# DEBUG: Using UnitTypeId.Millimeters") # Optional Debug
    except ImportError:
        # Fallback for older API versions (pre-2021) using DisplayUnitType
        try:
            from Autodesk.Revit.DB import DisplayUnitType
            threshold_internal = UnitUtils.ConvertToInternalUnits(threshold_mm, DisplayUnitType.DUT_MILLIMETERS)
            conversion_success = True
            # print("# DEBUG: Using DisplayUnitType.DUT_MILLIMETERS") # Optional Debug
        except ImportError:
            print("# Error: Could not find suitable Unit classes (UnitTypeId or DisplayUnitType).")
            conversion_success = False
        except Exception as dut_e:
            print("# Error: Failed converting threshold units using DisplayUnitType: {}".format(dut_e))
            conversion_success = False
    except Exception as ut_e:
         # Handle potential errors during UnitTypeId conversion
         print("# Error converting threshold units using UnitTypeId: {}".format(ut_e))
         conversion_success = False
         # Attempt fallback to DisplayUnitType even if UnitTypeId exists but fails
         try:
             from Autodesk.Revit.DB import DisplayUnitType
             threshold_internal = UnitUtils.ConvertToInternalUnits(threshold_mm, DisplayUnitType.DUT_MILLIMETERS)
             conversion_success = True
             # print("# DEBUG: Using DisplayUnitType.DUT_MILLIMETERS (fallback)") # Optional Debug
         except ImportError:
             pass # Already handled ImportError for DisplayUnitType above
         except Exception as dut_e2:
             print("# Error: Failed converting threshold units using DisplayUnitType fallback: {}".format(dut_e2))
             conversion_success = False

    if not conversion_success or threshold_internal is None:
        print("# Error: Could not convert threshold ({} mm) to internal units. Cannot proceed.".format(threshold_mm))
    else:
        # --- Collect Text Notes in Active View ---
        collector = FilteredElementCollector(doc, active_view.Id).OfClass(TextNote)
        notes_to_hide = List[ElementId]()
        processed_count = 0
        hidden_count = 0

        for note in collector:
            # Ensure it's a TextNote element (redundant with OfClass but safe)
            if isinstance(note, TextNote):
                processed_count += 1
                try:
                    # Get the TextNoteType element associated with the note instance
                    note_type_id = note.GetTypeId()
                    note_type_element = doc.GetElement(note_type_id)

                    if isinstance(note_type_element, TextNoteType):
                        # Get the 'Text Size' parameter from the type
                        # This parameter value is stored in internal units (feet)
                        text_size_param = note_type_element.get_Parameter(BuiltInParameter.TEXT_SIZE)

                        if text_size_param and text_size_param.HasValue:
                            text_size_internal = text_size_param.AsDouble()

                            # Compare with the threshold (allowing for minor floating point inaccuracies)
                            tolerance = 0.00001 # Internal units tolerance (feet)
                            if (text_size_internal + tolerance) < threshold_internal:
                                # Check if the specific note is already hidden (optional, but good practice)
                                if not note.IsHidden(active_view):
                                     notes_to_hide.Add(note.Id)
                                     hidden_count += 1
                                # else:
                                    # print("# Note ID {} already hidden.".format(note.Id)) # Optional Debug
                        # else:
                        #     print("# Warning: Text Note Type ID {} has no Text Size parameter or value.".format(note_type_id)) # Optional Debug
                    # else:
                    #     print("# Warning: Could not retrieve valid TextNoteType for TextNote ID {} (Type ID: {}).".format(note.Id, note_type_id)) # Optional Debug

                except AttributeError as ae:
                    # Handle cases where expected properties/methods might be missing
                    print("# Error accessing properties for TextNote ID {}: {}".format(note.Id, ae))
                except Exception as e:
                    print("# Error processing TextNote ID {}: {}".format(note.Id, e))


        # --- Hide Collected Text Notes ---
        if notes_to_hide.Count > 0:
            try:
                # Hide the elements (Transaction managed externally)
                active_view.HideElements(notes_to_hide)
                print("# Attempted to hide {} text notes with text size smaller than {}mm in view '{}' (out of {} processed text notes).".format(hidden_count, threshold_mm, active_view.Name, processed_count))
            except Exception as hide_e:
                 # Provide more specific feedback if possible
                if "cannot be hidden in the view" in str(hide_e) or "Element cannot be hidden" in str(hide_e):
                     print("# Warning: Some text notes could not be hidden (perhaps already hidden, pinned, part of a group that prevents hiding, or view limitations). Processed {} notes, attempted to hide {}.".format(processed_count, hidden_count))
                else:
                    print("# Error occurred while hiding elements: {}".format(hide_e))
        else:
            if processed_count > 0:
                 print("# No text notes found with text size smaller than {}mm to hide in view '{}' ({} text notes processed).".format(threshold_mm, active_view.Name, processed_count))
            else:
                 print("# No text notes found in the active view '{}'.".format(active_view.Name))

# Else: Initial view check failed, message already printed.