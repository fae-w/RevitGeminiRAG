using Autodesk.Revit.Attributes;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using System;
using System.Windows.Forms;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Reflection;
using System.Threading.Tasks;
using System.Net.Http;
// Removed System.Net.Http.Headers as it wasn't explicitly used
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using IronPython.Hosting;
using Microsoft.Scripting.Hosting;
// Removed Microsoft.Scripting as direct usage isn't present after fixing ExceptionOperations
using System.Collections.Generic;
using System.Linq;
using Microsoft.Scripting;

// --- Assembly Binding Redirect Note ---
// If you encounter build warnings about assembly version conflicts (e.g., for System.Buffers,
// System.Memory, System.Runtime.CompilerServices.Unsafe, System.ValueTuple),
// these often arise from dependencies like Google Cloud libraries, gRPC, and IronPython
// requiring different versions than Revit or other libraries.
// The standard solution is to add assembly binding redirects to your project's App.config file
// to force the application to use a specific version of the conflicting assemblies.
// Example for System.Buffers in App.config:
/*
<configuration>
  <runtime>
    <assemblyBinding xmlns="urn:schemas-microsoft-com:asm.v1">
      <dependentAssembly>
        <assemblyIdentity name="System.Buffers" publicKeyToken="cc7b13ffcd2ddd51" culture="neutral" />
        <bindingRedirect oldVersion="0.0.0.0-4.0.3.0" newVersion="4.0.3.0" />
      </dependentAssembly>
      </assemblyBinding>
  </runtime>
</configuration>
*/
// Ensure the 'newVersion' matches the version you intend to use (often the higher version available).
// You might need to add an App.config file to your Visual Studio project if it doesn't exist.

namespace RevitGeminiRAG
{
    [Transaction(TransactionMode.Manual)]
    [Regeneration(RegenerationOption.Manual)]
    public class RunRAGCommand : IExternalCommand
    {
        // --- CONFIGURATION ---
        private const string GeminiModelId = "gemini-2.5-pro-exp-03-25"; // Using the latest model ID
        private const string GoogleApiKeyEnvVariable = "GOOGLE_API_KEY";
        private const int MaxOutputTokens = 8192;
        private const int MaxRetryAttempts = 5; // Max number of times to try fixing errors
        // --- END CONFIGURATION ---

        public Result Execute(
      ExternalCommandData commandData,
      ref string message,
      ElementSet elements)
        {
            UIApplication uiapp = commandData.Application;
            UIDocument uidoc = uiapp.ActiveUIDocument;
            Document doc = uidoc.Document;
            string userPrompt = string.Empty;
            string initialRagPrompt = string.Empty;

            // --- Step 1: Get User Prompt ---
            try
            {
                // Assuming PromptForm is a custom WinForms Form you have defined elsewhere
                using (Gemini_RAG promptForm = new Gemini_RAG())
                {
#if REVIT
                    // Set owner window for Revit environment if possible
                    try
                    {
                        System.Windows.Interop.WindowInteropHelper helper = new System.Windows.Interop.WindowInteropHelper(promptForm);
                        helper.Owner = uiapp.MainWindowHandle;
                    }
                    catch (Exception ex)
                    {
                        System.Diagnostics.Debug.WriteLine($"Warning: Could not set owner window for PromptForm: {ex.Message}");
                    }
#endif

                    if (promptForm.ShowDialog() == DialogResult.OK)
                    {
                        userPrompt = promptForm.UserPrompt;
                        if (string.IsNullOrWhiteSpace(userPrompt))
                        {
                            TaskDialog.Show("Input Error", "Prompt cannot be empty.");
                            return Result.Failed;
                        }
                    }
                    else
                    {
                        return Result.Cancelled; // User cancelled the prompt form
                    }
                }
            }
            catch (Exception ex)
            {
                message = $"Error displaying prompt form: {ex.Message}";
                TaskDialog.Show("UI Error", message);
                System.Diagnostics.Debug.WriteLine($"Prompt Form Exception: {ex}");
                return Result.Failed;
            }

            // --- Step 2: Generate *Initial* LLM Prompt (via RAG) ---
            try
            {
                System.Diagnostics.Debug.WriteLine("Generating initial LLM prompt via Python RAG script...");
                initialRagPrompt = GenerateLlmPromptViaPython(userQuery: userPrompt); // Pass userPrompt here
                if (string.IsNullOrWhiteSpace(initialRagPrompt))
                {
                    message = "Failed to generate initial LLM prompt via Python script (returned empty). Check Python script logs/errors in Debug Output.";
                    TaskDialog.Show("Python Execution Error", message);
                    return Result.Failed;
                }
                System.Diagnostics.Debug.WriteLine($"--- Initial RAG Prompt (Length: {initialRagPrompt.Length}) ---");
            }
            catch (Exception ex)
            {
                message = $"Error running Python RAG script: {ex.Message}";
                if (ex.InnerException != null) message += $"\nInner Exception: {ex.InnerException.Message}";
                message += "\n\nCheck Debug Output for detailed Python errors (PY_STDERR).";
                TaskDialog.Show("Python Execution Error", message);
                System.Diagnostics.Debug.WriteLine($"Python Execution Exception: {ex}");
                return Result.Failed;
            }


            // --- Step 3 & 4: Feedback Loop (Call API, Execute Code, Retry on Error) ---
            bool overallSuccess = false;
            string lastErrorMessage = string.Empty;
            string lastScriptOutput = string.Empty;
            string currentCodeToExecute = string.Empty;
            string lastFailedCode = string.Empty;
            string finalCodeToShowUser = string.Empty;

            for (int attempt = 1; attempt <= MaxRetryAttempts; attempt++)
            {
                System.Diagnostics.Debug.WriteLine($"--- Attempt {attempt} of {MaxRetryAttempts} ---");
                string promptToSend = string.Empty;
                string apiResponse = string.Empty;
                currentCodeToExecute = string.Empty;

                // 3a. Determine the prompt for this attempt
                if (attempt == 1)
                {
                    promptToSend = initialRagPrompt;
                    System.Diagnostics.Debug.WriteLine("Using initial RAG prompt for first API call.");
                }
                else
                {
                    System.Diagnostics.Debug.WriteLine("Constructing 'fix-it' prompt for retry.");
                    promptToSend = ConstructFixItPrompt(userPrompt, lastFailedCode, lastErrorMessage);
                    if (string.IsNullOrWhiteSpace(promptToSend))
                    {
                        message = "Failed to construct a valid 'fix-it' prompt. Aborting retries.";
                        System.Diagnostics.Debug.WriteLine($"Error: {message}");
                        lastErrorMessage = message;
                        break; // Exit the loop
                    }
                }

                // 3b. Call Gemini API
                try
                {
                    System.Diagnostics.Debug.WriteLine($"Sending prompt to Gemini (Attempt {attempt})...");
                    // Use .Result on the async method call (blocks the thread - consider making Execute async if possible in future)
                    apiResponse = CallGeminiApiAsync(promptToSend).Result;

                    if (string.IsNullOrWhiteSpace(apiResponse))
                    {
                        throw new InvalidOperationException("API returned an empty or null response body.");
                    }

                    System.Diagnostics.Debug.WriteLine($"--- Raw Response Body from Gemini (Attempt {attempt}) ---");
                    // System.Diagnostics.Debug.WriteLine(apiResponse); // Uncomment for full response debugging
                    System.Diagnostics.Debug.WriteLine($"--- End Raw Response Body (Attempt {attempt}) ---");

                    string extractedContent = ParseGeminiResponse(apiResponse);
                    if (string.IsNullOrWhiteSpace(extractedContent))
                    {
                        throw new InvalidOperationException("Failed to extract valid content from Gemini response JSON.");
                    }

                    string extractedCode = ExtractPythonCode(extractedContent);
                    // Use the extracted code if found, otherwise use the full content as a fallback
                    currentCodeToExecute = !string.IsNullOrWhiteSpace(extractedCode) ? extractedCode : extractedContent;
                    if (string.IsNullOrWhiteSpace(extractedCode))
                    {
                        System.Diagnostics.Debug.WriteLine("WARNING: Could not extract fenced Python code. Using full extracted content as potential code.");
                    }

                    finalCodeToShowUser = currentCodeToExecute;
                    System.Diagnostics.Debug.WriteLine($"--- Generated/Corrected Code (Attempt {attempt}) ---\n{currentCodeToExecute}\n--- End Code ---");
                }
                catch (AggregateException aggEx) // Catches exceptions from awaited tasks when using .Result
                {
                    // Extract the most relevant inner exception
                    Exception relevantEx = aggEx.InnerExceptions.FirstOrDefault() ?? aggEx;
                    System.Diagnostics.Debug.WriteLine($"Gemini API Call or Processing Failed (Attempt {attempt}): {relevantEx}");
                    lastErrorMessage = $"Attempt {attempt}: Error calling Gemini API or processing its response: {relevantEx.Message}";
                    lastFailedCode = string.IsNullOrEmpty(currentCodeToExecute) ? lastFailedCode : currentCodeToExecute;
                    finalCodeToShowUser = lastFailedCode;

                    if (relevantEx is HttpRequestException httpEx)
                    {
                        if (httpEx.Data.Contains("ResponseBody")) lastErrorMessage += $"\nResponse Body:\n{httpEx.Data["ResponseBody"]}";
                        if (httpEx.Data.Contains("StatusCode")) lastErrorMessage += $"\nStatus Code: {httpEx.Data["StatusCode"]}";
                    }

                    if (attempt == MaxRetryAttempts && string.IsNullOrEmpty(message))
                    {
                        message = lastErrorMessage + "\n\nCould not get a valid response from the AI after multiple attempts.";
                    }
                    continue; // Go to the next attempt
                }
                catch (Exception apiEx) // Catch other potential exceptions
                {
                    System.Diagnostics.Debug.WriteLine($"Gemini API Call or Processing Failed (Attempt {attempt}): {apiEx}");
                    lastErrorMessage = $"Attempt {attempt}: Error calling Gemini API or processing its response: {apiEx.Message}";
                    lastFailedCode = string.IsNullOrEmpty(currentCodeToExecute) ? lastFailedCode : currentCodeToExecute;
                    finalCodeToShowUser = lastFailedCode;

                    if (apiEx is HttpRequestException httpEx)
                    {
                        if (httpEx.Data.Contains("ResponseBody")) lastErrorMessage += $"\nResponse Body:\n{httpEx.Data["ResponseBody"]}";
                        if (httpEx.Data.Contains("StatusCode")) lastErrorMessage += $"\nStatus Code: {httpEx.Data["StatusCode"]}";
                    }

                    if (attempt == MaxRetryAttempts && string.IsNullOrEmpty(message))
                    {
                        message = lastErrorMessage + "\n\nCould not get a valid response from the AI after multiple attempts.";
                    }
                    continue; // Go to the next attempt
                }


                // 4a. Offer to Execute the code
                TaskDialog codeDialog = new TaskDialog("Review Code")
                {
                    MainInstruction = $"Review Code (Attempt {attempt}/{MaxRetryAttempts})",
                    MainContent = "Gemini generated the following Python code based on your request.\nReview carefully before executing.",
                    ExpandedContent = currentCodeToExecute.Length > 1000 ? currentCodeToExecute.Substring(0, 1000) + "\n\n[... Code truncated for preview ...]" : currentCodeToExecute,
                    VerificationText = "Execute this code? USE WITH EXTREME CAUTION! Ensure it does what you expect.",
                    // AllowCancel property removed as it doesn't exist
                    CommonButtons = TaskDialogCommonButtons.Cancel // Provides Cancel button
                };
                // Add command links for user choices
                codeDialog.AddCommandLink(TaskDialogCommandLinkId.CommandLink1, "Execute this code (Inside Transaction)");
                codeDialog.AddCommandLink(TaskDialogCommandLinkId.CommandLink2, "Copy code to Clipboard and Cancel");
                // Setting default button might also be useful depending on API version
                // codeDialog.DefaultButton = TaskDialogResult.Cancel;

                TaskDialogResult tdr = codeDialog.Show();

                if (tdr == TaskDialogResult.CommandLink1) // User chose Execute
                {
                    string scriptOutput = string.Empty;
                    string scriptError = string.Empty;
                    bool currentAttemptSuccess = false;

                    using (Transaction pyTransaction = new Transaction(doc, $"Execute Gemini Python Code Attempt {attempt}"))
                    {
                        try
                        {
                            pyTransaction.Start();
                            System.Diagnostics.Debug.WriteLine($"Attempting to execute code (Attempt {attempt}) inside a transaction...");
                            currentAttemptSuccess = ExecuteGeneratedPythonCode(currentCodeToExecute, doc, uidoc, uiapp, out scriptOutput, out scriptError);

                            lastScriptOutput = scriptOutput;

                            if (currentAttemptSuccess)
                            {
                                pyTransaction.Commit();
                                uidoc.RefreshActiveView();
                                System.Diagnostics.Debug.WriteLine($"Attempt {attempt} SUCCEEDED. Transaction committed.");
                                overallSuccess = true;
                            }
                            else
                            {
                                pyTransaction.RollBack();
                                System.Diagnostics.Debug.WriteLine($"Attempt {attempt} FAILED. Transaction rolled back. Error: {scriptError}");
                                lastErrorMessage = scriptError;
                                lastFailedCode = currentCodeToExecute;
                            }
                        }
                        catch (Autodesk.Revit.Exceptions.OperationCanceledException)
                        {
                            System.Diagnostics.Debug.WriteLine($"Transaction cancelled by user during attempt {attempt}.");
                            if (pyTransaction.GetStatus() == TransactionStatus.Started) { try { pyTransaction.RollBack(); } catch { } }
                            message = "Python code execution cancelled by user during Revit operation.";
                            lastErrorMessage = message;
                            overallSuccess = false;
                            goto EndLoop; // Jump out of loop
                        }
                        catch (Exception ex)
                        {
                            System.Diagnostics.Debug.WriteLine($"Critical error during Python execution transaction management (Attempt {attempt}): {ex}");
                            if (pyTransaction.GetStatus() == TransactionStatus.Started) { try { pyTransaction.RollBack(); } catch { } }
                            lastErrorMessage = $"Attempt {attempt}: Critical error executing Python code wrapper: {ex.Message}";
                            lastFailedCode = currentCodeToExecute;
                            overallSuccess = false;
                            message = lastErrorMessage;
                            goto EndLoop; // Jump out of loop
                        }
                    } // End Transaction using

                    if (overallSuccess) break; // Exit loop on success
                }
                else if (tdr == TaskDialogResult.CommandLink2) // User chose Copy and Cancel
                {
                    try { Clipboard.SetText(currentCodeToExecute); TaskDialog.Show("Clipboard", "Code copied to clipboard. Operation cancelled."); }
                    catch (Exception clipEx) { TaskDialog.Show("Clipboard Error", $"Could not copy code to clipboard: {clipEx.Message}"); }
                    message = "Operation cancelled by user after copying code.";
                    overallSuccess = false;
                    goto EndLoop; // Exit loop
                }
                else // User clicked Cancel or closed the dialog (tdr == TaskDialogResult.Cancel)
                {
                    message = "Operation cancelled by user during code review.";
                    overallSuccess = false;
                    goto EndLoop; // Exit loop
                }

            } // End For Loop (Attempts)

        EndLoop:; // Label for goto jump

            // --- Step 5: Final Reporting ---
            if (overallSuccess)
            {
                TaskDialog.Show("Execution Succeeded", $"Python code executed successfully.\n\nFinal Output:\n{lastScriptOutput}");
                return Result.Succeeded;
            }
            else
            {
                if (string.IsNullOrWhiteSpace(message))
                {
                    message = $"Code execution failed after {MaxRetryAttempts} attempts or was aborted.\n\nLast Error:\n{lastErrorMessage}\n\nOutput before last error (if any):\n{lastScriptOutput}";
                }

                TaskDialog failureDialog = new TaskDialog("Execution Failed or Cancelled")
                {
                    MainInstruction = "Code Execution Failed or Cancelled",
                    MainContent = message,
                    ExpandedContent = $"Last code attempted or generated:\n\n{finalCodeToShowUser}",
                    // AllowCancel removed
                    CommonButtons = TaskDialogCommonButtons.Close
                };
                failureDialog.Show();

                System.Diagnostics.Debug.WriteLine($"Execution failed or cancelled. Final message: {message}");
                return message.ToLowerInvariant().Contains("cancel") ? Result.Cancelled : Result.Failed;
            }

        } // End Execute Method


        /// <summary>
        /// Constructs a prompt asking the LLM to fix previously failed Python code.
        /// </summary>
        private string ConstructFixItPrompt(string originalUserRequest, string failedCode, string errorMessage)
        {
            if (string.IsNullOrWhiteSpace(failedCode)) failedCode = "# No previous code was available or execution failed before code generation.";
            if (string.IsNullOrWhiteSpace(errorMessage)) errorMessage = "# No specific error message was captured, but the previous attempt failed.";

            // Basic escaping for braces
            string escapedErrorMessage = errorMessage.Replace("{", "{{").Replace("}", "}}");
            string escapedFailedCode = failedCode.Replace("{", "{{").Replace("}", "}}");
            string escapedOriginalRequest = originalUserRequest.Replace("{", "{{").Replace("}", "}}");

            // Using verbatim string literal and interpolation
            string fixPromptTemplate = $@"ROLE: You are an expert Revit API assistant generating Python code using IronPython for Autodesk Revit.

TASK: Your previous attempt to generate Python code resulted in an error when executed within the Revit environment using IronPython. Analyze the error message and the failed code provided below. Your goal is to provide a corrected Python script ONLY that addresses the error and fulfills the original user request.

ORIGINAL USER REQUEST:
---
{escapedOriginalRequest}
---

FAILED PYTHON CODE (Executed via IronPython):
```python
{escapedFailedCode}
```

ERROR MESSAGE RECEIVED FROM IRONPYTHON/REVIT:
---
{escapedErrorMessage}
---

RESPONSE FORMAT & CONSTRAINTS (VERY IMPORTANT - FOLLOW EXACTLY):
1.  Output ONLY the corrected Python code.
2.  Start the response DIRECTLY with the Python code (e.g., `import clr` or the first functional line).
3.  Do NOT include the markdown fence (\`\`\`python or \`\`\`) around your code.
4.  Do NOT include ANY introductory text, explanations, apologies, or concluding remarks.
5.  Do NOT manage Revit Transactions (NO `Transaction()`, `t.Start()`, `t.Commit()`). The C# wrapper handles this.
6.  Assume the following variables are pre-defined and available in the script's scope:
    * `doc`: The current Revit Document (Autodesk.Revit.DB.Document)
    * `uidoc`: The current Revit UIDocument (Autodesk.Revit.UI.UIDocument)
    * `app`: The Revit Application object (Autodesk.Revit.ApplicationServices.Application)
    * `uiapp`: The Revit UIApplication object (Autodesk.Revit.UI.UIApplication)
    * `__revit__`: Often used as a reference to `uiapp` in some contexts.
7.  Ensure all necessary Revit API namespaces are imported via `clr.AddReference()` and `import ...` statements (e.g., `clr.AddReference('RevitAPI')`, `from Autodesk.Revit.DB import *`).
8.  If the error cannot be fixed based on the provided information, or if the original request is impossible within the Revit API/IronPython constraints, output ONLY a single Python comment line explaining why (e.g., `# Error: Cannot fix the previous error because [specific reason].` or `# Error: The original request cannot be fulfilled because [specific reason].`).

CORRECTED PYTHON SCRIPT (or single comment line if unfixable):
"; // End of template string

            return fixPromptTemplate;
        }


        /// <summary>
        /// Executes an external Python script to generate the initial prompt for the LLM.
        /// </summary>
        private string GenerateLlmPromptViaPython(string userQuery)
        {
            string assemblyLocation = Assembly.GetExecutingAssembly().Location;
            string pluginDirectory = Path.GetDirectoryName(assemblyLocation);
            string pythonWorkingDir = Path.Combine(pluginDirectory, "Python");
            string scriptPath = Path.Combine(pythonWorkingDir, "generate_rag_prompt.py");
            // IMPORTANT: Verify this path or make it configurable (e.g., via environment variable or config file)
            string pythonExePath = @"C:\Users\isele\anaconda3\envs\revit_rag_env\python.exe";

            if (!Directory.Exists(pythonWorkingDir)) throw new DirectoryNotFoundException($"Python working directory not found: {pythonWorkingDir}");
            if (!File.Exists(scriptPath)) throw new FileNotFoundException($"Python RAG script not found: {scriptPath}");
            if (!File.Exists(pythonExePath)) throw new FileNotFoundException($"Python executable not found. Please check the path: {pythonExePath}");

            System.Diagnostics.Debug.WriteLine($"DEBUG: Using Python executable: [{pythonExePath}]");
            System.Diagnostics.Debug.WriteLine($"DEBUG: Running Python script: [{scriptPath}]");
            System.Diagnostics.Debug.WriteLine($"DEBUG: Setting Python Working Directory: [{pythonWorkingDir}]");
            System.Diagnostics.Debug.WriteLine($"DEBUG: Passing query to Python: [{userQuery}]");

            ProcessStartInfo startInfo = new ProcessStartInfo
            {
                FileName = pythonExePath,
                Arguments = $"{EscapeArgument(scriptPath)} {EscapeArgument(userQuery)}",
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                StandardOutputEncoding = Encoding.UTF8,
                StandardErrorEncoding = Encoding.UTF8,
                CreateNoWindow = true,
                WorkingDirectory = pythonWorkingDir
            };

            StringBuilder outputBuilder = new StringBuilder();
            StringBuilder errorBuilder = new StringBuilder();
            int timeoutMilliseconds = 120000; // 2 minutes timeout

            using (Process process = new Process { StartInfo = startInfo })
            {
                // Use anonymous methods for event handlers
                process.OutputDataReceived += (sender, args) => { if (args.Data != null) outputBuilder.AppendLine(args.Data); };
                process.ErrorDataReceived += (sender, args) => { if (args.Data != null) { errorBuilder.AppendLine(args.Data); System.Diagnostics.Debug.WriteLine($"PY_STDERR: {args.Data}"); } };

                process.Start();
                System.Diagnostics.Debug.WriteLine($"DEBUG: Started Python process (ID: {process.Id}). Waiting for exit (Timeout: {timeoutMilliseconds / 1000}s)...");
                process.BeginOutputReadLine();
                process.BeginErrorReadLine();

                bool exited = process.WaitForExit(timeoutMilliseconds);
                string errors = errorBuilder.ToString().Trim();
                string output = outputBuilder.ToString().Trim();

                if (!exited)
                {
                    System.Diagnostics.Debug.WriteLine($"ERROR: Python process timed out...");
                    try { if (!process.HasExited) process.Kill(); } catch (Exception kex) { System.Diagnostics.Debug.WriteLine($"ERROR: Failed to kill Python process: {kex.Message}"); }
                    throw new TimeoutException($"Python RAG script execution timed out after {timeoutMilliseconds / 1000} seconds. Captured STDERR (if any):\n{errors}");
                }

                System.Diagnostics.Debug.WriteLine($"DEBUG: Python process (ID: {process.Id}) exited with code {process.ExitCode}.");
                if (process.ExitCode != 0)
                {
                    throw new Exception($"Python script failed with Exit Code: {process.ExitCode}.\n--- STDERR ---\n{errors}\n--- STDOUT ---\n{output}");
                }
                if (!string.IsNullOrEmpty(errors))
                {
                    System.Diagnostics.Debug.WriteLine($"--- Python Script Finished (Exit Code 0) but produced STDERR Output ---");
                    // Consider if stderr output should always be treated as an error
                }
                if (string.IsNullOrWhiteSpace(output))
                {
                    System.Diagnostics.Debug.WriteLine("WARNING: Python script exited successfully (Code 0) but produced no output to STDOUT.");
                }
                return output;
            }
        }


        /// <summary>
        /// Calls the Google Gemini API asynchronously.
        /// </summary>
        private async Task<string> CallGeminiApiAsync(string ragPrompt)
        {
            string apiKey = Environment.GetEnvironmentVariable(GoogleApiKeyEnvVariable);
            if (string.IsNullOrWhiteSpace(apiKey))
            {
                throw new InvalidOperationException($"Google API key not found. Please set the '{GoogleApiKeyEnvVariable}' environment variable.");
            }

            string endpoint = $"https://generativelanguage.googleapis.com/v1beta/models/{GeminiModelId}:generateContent?key={apiKey}";
            System.Diagnostics.Debug.WriteLine($"DEBUG: Gemini API Endpoint: {endpoint}");

            using (HttpClient client = new HttpClient())
            {
                client.Timeout = TimeSpan.FromSeconds(180); // 3 minutes timeout
                var requestBody = new
                {
                    contents = new[] { new { role = "user", parts = new[] { new { text = ragPrompt } } } },
                    generationConfig = new { maxOutputTokens = MaxOutputTokens },
                    safetySettings = new[] {
            new { category = "HARM_CATEGORY_HARASSMENT", threshold = "BLOCK_MEDIUM_AND_ABOVE" },
            new { category = "HARM_CATEGORY_HATE_SPEECH", threshold = "BLOCK_MEDIUM_AND_ABOVE" },
            new { category = "HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold = "BLOCK_MEDIUM_AND_ABOVE" },
            new { category = "HARM_CATEGORY_DANGEROUS_CONTENT", threshold = "BLOCK_MEDIUM_AND_ABOVE" }
          }
                };
                string jsonRequestBody = JsonConvert.SerializeObject(requestBody, Formatting.None);
                using (StringContent content = new StringContent(jsonRequestBody, Encoding.UTF8, "application/json"))
                {
                    // Use ConfigureAwait(false) to avoid potential deadlocks in UI/Revit context
                    HttpResponseMessage response = await client.PostAsync(endpoint, content).ConfigureAwait(false);
                    string responseBody = await response.Content.ReadAsStringAsync().ConfigureAwait(false);

                    System.Diagnostics.Debug.WriteLine($"--- Received Response from Gemini (Status: {response.StatusCode}) ---");
                    if (!response.IsSuccessStatusCode)
                    {
                        string errorDetails = responseBody;
                        try { JObject errorJson = JObject.Parse(responseBody); errorDetails = errorJson?["error"]?["message"]?.ToString() ?? errorDetails; } catch (JsonException) { }
                        string exceptionMessage = $"Gemini API request failed.\nStatus Code: {response.StatusCode} ({(int)response.StatusCode})\nDetails: {errorDetails}";
                        var ex = new HttpRequestException(exceptionMessage);
                        ex.Data.Add("ResponseBody", responseBody);
                        ex.Data.Add("StatusCode", response.StatusCode);
                        throw ex;
                    }
                    return responseBody;
                }
            }
        }


        /// <summary>
        /// Parses the JSON response from the Gemini API.
        /// </summary>
        private string ParseGeminiResponse(string responseBody)
        {
            if (string.IsNullOrWhiteSpace(responseBody)) { System.Diagnostics.Debug.WriteLine("ERROR: ParseGeminiResponse received null or empty input."); return null; }
            try
            {
                JObject jsonResponse = JObject.Parse(responseBody);
                var promptFeedback = jsonResponse["promptFeedback"];
                string blockReason = promptFeedback?["blockReason"]?.ToString();
                if (!string.IsNullOrWhiteSpace(blockReason))
                {
                    string blockDetails = promptFeedback?["blockReasonMessage"]?.ToString();
                    string safetyRatings = promptFeedback?["safetyRatings"]?.ToString(Formatting.None);
                    string errorMessage = $"Gemini blocked the prompt. Reason: {blockReason}";
                    if (!string.IsNullOrWhiteSpace(blockDetails)) errorMessage += $" - Details: {blockDetails}";
                    System.Diagnostics.Debug.WriteLine($"ERROR: {errorMessage}. Safety Ratings: {safetyRatings}");
                    throw new Exception(errorMessage);
                }

                JToken candidate = jsonResponse["candidates"]?[0];
                if (candidate == null) { System.Diagnostics.Debug.WriteLine("ERROR: Gemini response parsed, but 'candidates' array is missing or empty."); return null; }

                string finishReason = candidate["finishReason"]?.ToString();
                System.Diagnostics.Debug.WriteLine($"Gemini Finish Reason: {finishReason}");
                switch (finishReason)
                {
                    case "STOP": break; // Expected
                    case "SAFETY": System.Diagnostics.Debug.WriteLine("WARNING: Gemini response potentially altered/blocked due to SAFETY."); break;
                    case "MAX_TOKENS": System.Diagnostics.Debug.WriteLine("WARNING: Gemini response may have been cut short due to max tokens limit."); break;
                    case "RECITATION": System.Diagnostics.Debug.WriteLine("ERROR: Gemini response blocked due to recitation policy."); throw new Exception("Gemini response generation stopped due to recitation policy.");
                    case null: System.Diagnostics.Debug.WriteLine("WARNING: Gemini response candidate missing 'finishReason'."); break;
                    default: System.Diagnostics.Debug.WriteLine($"WARNING: Gemini response generation finished with unexpected reason: {finishReason}."); break;
                }

                string generatedText = candidate?["content"]?["parts"]?[0]?["text"]?.ToString();
                if (!string.IsNullOrWhiteSpace(generatedText))
                {
                    System.Diagnostics.Debug.WriteLine("Successfully extracted text content from Gemini response.");
                    return generatedText;
                }
                else
                {
                    System.Diagnostics.Debug.WriteLine("WARNING: Gemini response parsed, but did not contain expected text content.");
                    return null;
                }
            }
            catch (JsonException jsonEx)
            {
                System.Diagnostics.Debug.WriteLine($"ERROR: Failed to parse Gemini JSON response: {jsonEx.Message}");
                System.Diagnostics.Debug.WriteLine($"--- Response Body Start ---\n{responseBody}\n--- Response Body End ---");
                throw;
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"ERROR: Unexpected error processing Gemini response content: {ex.Message}");
                throw;
            }
        }


        /// <summary>
        /// Executes the provided Python code string using IronPython.
        /// </summary>
        private bool ExecuteGeneratedPythonCode(
      string pythonCode,
      Document doc,
      UIDocument uidoc,
      UIApplication uiapp,
      out string output,
      out string errorMessage)
        {
            output = string.Empty;
            errorMessage = string.Empty;
            ScriptEngine engine = null;
            ScriptScope scope = null;
            MemoryStream outputStream = null;
            StreamWriter outputWriter = null;
            StreamReader outputReader = null;

            try
            {
                System.Diagnostics.Debug.WriteLine("--- Setting up IronPython Engine ---");
                engine = Python.CreateEngine();
                scope = engine.CreateScope();

                System.Diagnostics.Debug.WriteLine("Loading Revit API and standard assemblies into IronPython...");
                try
                {
                    Assembly apiAssembly = typeof(Document).Assembly;
                    Assembly uiAssembly = typeof(TaskDialog).Assembly;
                    if (apiAssembly != null) engine.Runtime.LoadAssembly(apiAssembly); else System.Diagnostics.Debug.WriteLine("Warning: Could not load RevitAPI assembly.");
                    if (uiAssembly != null) engine.Runtime.LoadAssembly(uiAssembly); else System.Diagnostics.Debug.WriteLine("Warning: Could not load RevitAPIUI assembly.");

                    engine.Runtime.LoadAssembly(typeof(List<>).Assembly);
                    engine.Runtime.LoadAssembly(typeof(System.Linq.Enumerable).Assembly);
                    engine.Runtime.LoadAssembly(typeof(Path).Assembly);
                    // Explicitly qualify System.Windows.Forms.Form to resolve ambiguity
                    engine.Runtime.LoadAssembly(typeof(System.Windows.Forms.Form).Assembly);
                }
                catch (Exception asmEx)
                {
                    errorMessage = $"Fatal Error: Failed to load required assemblies into IronPython: {asmEx.Message}";
                    System.Diagnostics.Debug.WriteLine(errorMessage);
                    return false;
                }
                System.Diagnostics.Debug.WriteLine("Finished loading assemblies.");

                scope.SetVariable("doc", doc);
                scope.SetVariable("uidoc", uidoc);
                scope.SetVariable("app", uiapp.Application);
                scope.SetVariable("uiapp", uiapp);
                scope.SetVariable("__revit__", uiapp);

                outputStream = new MemoryStream();
                outputWriter = new StreamWriter(outputStream, Encoding.UTF8, 1024, leaveOpen: true);
                engine.Runtime.IO.SetOutput(outputStream, outputWriter);
                engine.Runtime.IO.SetErrorOutput(outputStream, outputWriter);

                System.Diagnostics.Debug.WriteLine("--- Executing Generated Python Code ---");
                ScriptSource source = engine.CreateScriptSourceFromString(pythonCode, SourceCodeKind.Statements);
                source.Execute(scope);
                System.Diagnostics.Debug.WriteLine("--- Python Execution Attempt Finished (No Exceptions Thrown by IronPython Engine) ---");

                outputWriter.Flush();
                outputStream.Position = 0;
                outputReader = new StreamReader(outputStream, Encoding.UTF8, true, 1024, leaveOpen: true);
                output = outputReader.ReadToEnd();
                System.Diagnostics.Debug.WriteLine($"--- Python Script Output ---\n{output}\n---------------------");
                return true;
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"!!! IronPython Execution Error Captured: {ex.GetType().Name} !!!");
                // Corrected: GetService<ExceptionOperations>() is directly under Hosting
                var exceptionOperations = engine?.GetService<ExceptionOperations>();
                string formattedException = (exceptionOperations != null) ? exceptionOperations.FormatException(ex) : ex.ToString();
                errorMessage = $"Python Execution Error:\n{formattedException}";
                System.Diagnostics.Debug.WriteLine($"Formatted Error:\n{errorMessage}");

                try
                {
                    if (outputWriter != null) outputWriter.Flush();
                    if (outputStream != null && outputStream.CanRead && outputStream.CanSeek)
                    {
                        outputStream.Position = 0;
                        using (var errorReader = new StreamReader(outputStream, Encoding.UTF8, true, 1024, leaveOpen: true))
                        {
                            output = errorReader.ReadToEnd();
                        }
                        System.Diagnostics.Debug.WriteLine($"--- Script Output (Partial, Captured Before/During Error) ---\n{output}\n---------------------");
                    }
                }
                catch (Exception readEx)
                {
                    System.Diagnostics.Debug.WriteLine($"Error reading partial output stream after Python exception: {readEx.Message}");
                    errorMessage += $"\n\n(Additionally, failed to read script output after error: {readEx.Message})";
                }
                return false;
            }
            finally
            {
                // Dispose streams safely
                outputWriter?.Dispose();
                outputReader?.Dispose();
                outputStream?.Dispose();
                System.Diagnostics.Debug.WriteLine("--- IronPython Streams Disposed ---");
            }
        }


        /// <summary>
        /// Attempts to extract Python code blocks from raw LLM content.
        /// </summary>
        private static string ExtractPythonCode(string rawContent)
        {
            // (Implementation unchanged from previous version, assuming it works as intended)
            if (string.IsNullOrWhiteSpace(rawContent)) return string.Empty;
            string code = rawContent.Trim();
            string lowerCode = code.ToLowerInvariant();
            const string pythonFenceStart = "```python";
            const string genericFenceStart = "```";
            const string fenceEnd = "```";
            int startCodePos = -1;
            int endCodePos = -1;
            int pythonFenceStartPos = lowerCode.IndexOf(pythonFenceStart);
            if (pythonFenceStartPos != -1)
            {
                startCodePos = pythonFenceStartPos + pythonFenceStart.Length;
                if (startCodePos < code.Length) { if (code[startCodePos] == '\r' && startCodePos + 1 < code.Length && code[startCodePos + 1] == '\n') startCodePos += 2; else if (code[startCodePos] == '\n') startCodePos++; }
                endCodePos = code.IndexOf(fenceEnd, startCodePos);
            }
            if (startCodePos == -1)
            {
                int genericFenceStartPos = lowerCode.IndexOf(genericFenceStart);
                if (genericFenceStartPos != -1)
                {
                    startCodePos = genericFenceStartPos + genericFenceStart.Length;
                    if (startCodePos < code.Length) { if (code[startCodePos] == '\r' && startCodePos + 1 < code.Length && code[startCodePos + 1] == '\n') startCodePos += 2; else if (code[startCodePos] == '\n') startCodePos++; }
                    endCodePos = code.IndexOf(fenceEnd, startCodePos);
                }
            }
            if (startCodePos != -1)
            {
                if (endCodePos != -1) { return code.Substring(startCodePos, endCodePos - startCodePos).Trim(); }
                else { System.Diagnostics.Debug.WriteLine("Warning: Found opening code fence but no closing fence. Extracting from opening fence to end."); return code.Substring(startCodePos).Trim(); }
            }
            System.Diagnostics.Debug.WriteLine("No code fences found. Attempting heuristic check for code content.");
            string[] lines = code.Split(new[] { '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries);
            if (lines.Length > 0)
            {
                string firstLineTrimmed = lines[0].Trim();
                var codeIndicators = new HashSet<string> { "import ", "from ", "clr.", "def ", "class ", "try:", "with ", "for ", "while ", "#", "t = Transaction", "Transaction(", "doc.", "uidoc.", "app.", "uiapp.", "__revit__." };
                if (codeIndicators.Any(indicator => firstLineTrimmed.StartsWith(indicator)) || firstLineTrimmed.Contains("="))
                {
                    System.Diagnostics.Debug.WriteLine("Heuristic check suggests content might be code. Returning entire trimmed content.");
                    return code;
                }
            }
            System.Diagnostics.Debug.WriteLine("No code fences found and heuristic check failed. Returning original content.");
            return rawContent; // Return original if no better option
        }


        /// <summary>
        /// Escapes command-line arguments safely.
        /// </summary>
        private static string EscapeArgument(string arg)
        {
            if (string.IsNullOrEmpty(arg)) return "\"\"";
            // Ensure backslashes are escaped, then escape quotes, then wrap in quotes
            string escaped = arg.Replace("\\", "\\\\").Replace("\"", "\\\"");
            return "\"" + escaped + "\"";
        }

    } // End Command Class
} // End Namespace