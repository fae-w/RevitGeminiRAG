using System;
// Make sure System.Windows.Forms is referenced in your project
// and included here. Visual Studio usually adds this automatically
// when you add a Form.
using System.Windows.Forms;

namespace RevitGeminiRAG
{
    // The 'partial' keyword means the other part of this class definition
    // is in PromptForm.Designer.cs (where InitializeComponent and control definitions live)
    public partial class Gemini_RAG : Form
    {
        // Constructor - called when you create an instance of the form
        public Gemini_RAG()
        {
            // This method is defined in PromptForm.Designer.cs
            // and sets up all the controls you added in the visual designer.
            InitializeComponent();

            // Optional: Set initial focus to the text box when the form loads
            this.Load += (s, e) => { promptTextBox.Focus(); };
        }

        /// <summary>
        /// Public property to safely get the text entered by the user
        /// into the promptTextBox control.
        /// </summary>
        public string UserPrompt
        {
            // The 'get' accessor returns the current value of the Text property
            // of the control named 'promptTextBox'.
            // Make sure the TextBox control on your form is actually named "promptTextBox"
            // in the Properties window of the designer.
            get { return promptTextBox.Text; }

            // You could add a 'set' accessor if you wanted to pre-fill the box,
            // but it's not needed for just retrieving the user's input.
            // set { promptTextBox.Text = value; }
        }

        // --- Optional Event Handlers ---

        // This handler likely got created if you double-clicked the label in the designer.
        // If it's empty, you can safely remove it (and remove the linkage
        // in PromptForm.Designer.cs if you're comfortable doing that, otherwise leave it).
        private void label1_Click(object sender, EventArgs e)
        {
            // Nothing needed here typically for a static label.
        }

        // This handler runs when the form first loads.
        private void PromptForm_Load(object sender, EventArgs e)
        {
            // This is a good place for setup code that needs to run
            // after InitializeComponent(), like setting focus as shown
            // in the constructor example above, or perhaps loading saved settings.
        }

        // Example of handling the Submit button click for validation (Optional)
        // You would need to connect this method to the Submit button's Click event
        // in the form designer's Properties window (Events section - lightning bolt icon).
        // Note: Setting the button's DialogResult property often handles closing automatically.
        /*
        private void submitButton_Click(object sender, EventArgs e)
        {
            if (string.IsNullOrWhiteSpace(promptTextBox.Text))
            {
                MessageBox.Show("Please enter a prompt before submitting.",
                                "Input Required",
                                MessageBoxButtons.OK,
                                MessageBoxIcon.Warning);
                // Important: Prevent the form from closing if validation fails
                // when DialogResult is set on the button.
                this.DialogResult = DialogResult.None;
            }
            else
            {
                // Ensure DialogResult is set correctly if validation passes
                // (especially if you overrode it with DialogResult.None above)
                // This assumes the button's DialogResult property was set to OK in the designer.
                 if(this.DialogResult == DialogResult.None) // Only set if validation previously failed
                 {
                    this.DialogResult = DialogResult.OK;
                 }
                // No need to call this.Close() explicitly if DialogResult is set correctly.
            }
        }
        */
    }
}
