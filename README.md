# RevitGeminiRAG

A Revit plugin that uses Retrieval-Augmented Generation (RAG) to enhance Revit workflows.

## Description

This plugin integrates Google's Gemini AI with Revit, providing intelligent assistance for Revit users through a RAG (Retrieval-Augmented Generation) system that can understand and respond to queries about Revit models.

## Installation

1. Clone this repository
2. Build the solution in Visual Studio
3. Copy the built files to your Revit Addins folder

## Large Files Notice

This repository does not include the large database files required for the RAG system to function. These files are:
- `python/revit_db/chroma.sqlite3` (approximately 375 MB)
- `python/revit_db/1ccb803a-3d67-4028-a8e8-35b549456170/data_level0.bin` (approximately 285 MB)

### Generating the Database Files

These files are automatically generated when you first run the plugin with a Revit model. The plugin will:
1. Extract relevant information from your Revit model
2. Create a vector database in the `python/revit_db` directory
3. Use this database for future RAG queries

Alternatively, you can download pre-built database files for common Revit elements from [our releases page](https://github.com/ismail-seleit/RevitGeminiRAG/releases).

## Usage

1. Open Revit
2. Run the RevitGeminiRAG command
3. Enter your query in the prompt window
4. The plugin will use RAG to provide context-aware responses about your Revit model

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
