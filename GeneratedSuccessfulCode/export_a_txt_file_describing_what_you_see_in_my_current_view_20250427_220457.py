# -*- coding: utf-8 -*-
import clr
import System
from System.Text import StringBuilder
from System import Environment

# Add References
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
clr.AddReference('System') # Required for StringBuilder, Environment

# Import necessary classes from Autodesk.Revit.DB
# Removed Parameter