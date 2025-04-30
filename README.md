# RevitGeminiRAG

<p align="center">
  <img src="https://img.shields.io/badge/Revit-2025-blue.svg" alt="Revit Version">
  <img src="https://img.shields.io/badge/Platform-Windows-lightgrey.svg" alt="Platform">
  <img src="https://img.shields.io/badge/Status-Proof%20of%20Concept-yellow.svg" alt="Status">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
</p>

A Revit plugin that uses Retrieval-Augmented Generation (RAG) to enable natural language interaction with the Revit API.

## 📋 Project Status

> **Note:** This project is a proof of concept and is not actively maintained. It is being released to the community as a foundation for others to build upon. While functional, the codebase may contain rough edges.

## 🌟 Key Features

- **Natural Language Interaction**: Query your Revit model using plain English
- **Retrieval-Augmented Generation (RAG)**: Combines Revit API knowledge with Google's Gemini AI
- **Context-Aware Responses**: Get accurate answers about Revit API functionality specific to your model
- **Extensible Foundation**: Build your own AI-powered Revit tools on top of this framework

## 🔍 How It Works

RevitGeminiRAG creates a vector database of Revit API knowledge and combines it with Google's Gemini AI to provide context-aware responses to your queries. The RAG system enables any LLM to access and understand the Revit API in full, making it possible to interact with Revit using natural language.

When you ask a question, the system:
1. Searches the vector database for relevant Revit API information
2. Retrieves the most pertinent API documentation and examples
3. Combines this knowledge with the Gemini AI's capabilities
4. Generates a response that accurately addresses your query in the context of your model

## 🔧 Prerequisites

- Windows 10 or later
- Autodesk Revit 2025 (tested and confirmed working)
- Visual Studio 2019 or later with .NET Framework 4.8
- Google API Key for Gemini AI access
- Python 3.9+ (for the RAG system)

### Compatibility with Other Revit Versions

This plugin has been tested and confirmed working with Revit 2025. To use it with other Revit versions, you'll need to:

1. Download the Revit SDK for your specific Revit version
2. Clean and chunk the CHM documentation file
3. Convert the documentation to markdown format
4. Create a new RAG system database using the converted documentation

This process is necessary because the current RAG system database could not be uploaded to GitHub due to file size limits. Don't hesitate to ask an LLM (like ChatGPT or Claude) for help with these steps if you encounter any difficulties.

## ⚙️ Installation

1. Clone this repository:
   ```
   git clone https://github.com/ismail-seleit/RevitGeminiRAG.git
   ```

2. Open the solution in Visual Studio:
   ```
   RevitGeminiRAG.sln
   ```

3. Restore NuGet packages and build the solution

4. Set up your Google API Key as an environment variable:
   - Press Win + R, type `sysdm.cpl`, and press Enter
   - Go to the "Advanced" tab and click "Environment Variables"
   - Under "User variables", click "New"
   - Variable name: `GOOGLE_API_KEY`
   - Variable value: `your-api-key-here`
   - Click "OK" to save

5. Copy the built files to your Revit Addins folder:
   ```
   C:\Users\[YourUsername]\AppData\Roaming\Autodesk\Revit\Addins\[RevitVersion]\
   ```

## 📊 Large Files Notice

This repository does not include the large database files required for the RAG system to function. These files are:
- `python/revit_db/chroma.sqlite3` (approximately 375 MB)
- `python/revit_db/1ccb803a-3d67-4028-a8e8-35b549456170/data_level0.bin` (approximately 285 MB)

### Generating the Database Files

These files are automatically generated when you first run the plugin with a Revit model. The plugin will:
1. Extract relevant information from your Revit model
2. Create a vector database in the `python/revit_db` directory
3. Use this database for future RAG queries

The initial generation may take several minutes depending on your model complexity. The database files could not be included in this repository due to GitHub's file size limits, so this step must be completed after installation.

If you encounter any issues during database generation, don't hesitate to ask an LLM like ChatGPT or Claude for assistance. They can be particularly helpful in troubleshooting Python-related issues or understanding the RAG system's functionality.

### Hosting and Sharing the Database Files

If you want to share pre-built database files with your team or the community, here are the recommended options:

1. **GitHub Releases**: 
   - Go to your repository's Releases page
   - Create a new release with a version tag (e.g., v1.0.0-database)
   - Upload the database files as assets (GitHub allows up to 2GB per file in releases)
   - Add a link in your README pointing to the release

2. **Cloud Storage Services**:
   - Upload the files to Google Drive, Dropbox, OneDrive, or similar services
   - Create a public sharing link
   - Add the download link to your README
   - Consider using a service that doesn't require login for downloading

3. **Dedicated File Hosting**:
   - Services like MediaFire, Mega, or WeTransfer are designed for large files
   - They provide direct download links that can be added to your README
   - Some offer permanent links that won't expire

4. **Self-Hosted Solution**:
   - If you have access to a web server, you can host the files there
   - This gives you complete control over availability and bandwidth
   - Ensure your server can handle the file sizes and potential download traffic

When sharing database files, include information about which Revit version they were generated with and any specific models or content they contain. This helps users determine if the pre-built database will meet their needs.

Example README section for shared database files:
```markdown
## Pre-built Database Files

For convenience, you can download pre-built database files for Revit 2025:

- [Download RAG Database Files (660MB)](https://example.com/download/revit2025-rag-database.zip)

These files were generated using Revit 2025 with the standard API documentation. 
Extract the contents to the `python/revit_db` directory after installing the plugin.
```

## 🚀 Usage

1. Open Revit and load a model
2. Run the RevitGeminiRAG command from the Add-Ins tab
3. Enter your query in the prompt window (e.g., "How can I get all walls in this model?")
4. The plugin will use RAG to provide context-aware responses about your model and the Revit API

### Example Queries

- "How do I access all doors in this model?"
- "Show me how to create a new wall using the API"
- "What parameters are available for this selected element?"
- "How can I filter elements by their category?"

## ⚠️ Known Limitations

- The plugin requires an active internet connection to access Google's Gemini AI
- Initial database generation can be time-consuming for large models
- Some complex queries may require rephrasing for optimal results
- The codebase is provided as-is without extensive documentation
- Currently optimized for Revit 2025; adaptation required for other versions

## 🤝 Contributing

While this project is not actively maintained, contributions are welcome! This project is intended as a foundation for the community to build upon. Feel free to:

- Fork the repository
- Extend the functionality
- Fix bugs
- Improve documentation
- Submit pull requests

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

*This project is not affiliated with Autodesk or Google. Revit is a registered trademark of Autodesk, Inc. Gemini is a trademark of Google LLC.*
