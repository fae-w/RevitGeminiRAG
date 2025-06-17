using Autodesk.Revit.UI;
using System;
using System.Reflection; // Needed for finding assembly location

namespace RevitGeminiRAG
{
    public class App : IExternalApplication
    {
        // Static variable to store the path to this assembly
        static string AddInPath = typeof(App).Assembly.Location;

        public Result OnStartup(UIControlledApplication application)
        {
            // 1. Create Ribbon Tab
            string tabName = "Gemini RAG";
            try
            {
                application.CreateRibbonTab(tabName);
            }
            catch (Exception)
            {
                // Tab might already exist
            }

            // 2. Create Ribbon Panel
            RibbonPanel ribbonPanel = application.CreateRibbonPanel(tabName, "Commands");

            // 3. Create Button Data
            // We'll link this to our command class in the next step
            string commandClassName = typeof(RunRAGCommand).FullName; // Get the full class name

            PushButtonData buttonData = new PushButtonData(
                "RunRAGButton",        // Internal name
                "Run Gemini\nRAG",     // Text displayed on the button
                AddInPath,             // Path to the assembly containing the command
                commandClassName       // Full class name of the command
            );

            // Optional: Set tooltip and icon
            buttonData.ToolTip = "Generates and runs Python code via Gemini RAG workflow.";
            // buttonData.LargeImage = new System.Windows.Media.Imaging.BitmapImage(new Uri("path/to/your/icon.png")); // Add an icon later

            // 4. Add Button to Panel
            PushButton pushButton = ribbonPanel.AddItem(buttonData) as PushButton;

            return Result.Succeeded;
        }

        public Result OnShutdown(UIControlledApplication application)
        {
            // Clean up resources if needed
            return Result.Succeeded;
        }
    }
}