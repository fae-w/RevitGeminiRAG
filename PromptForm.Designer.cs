namespace RevitGeminiRAG
{
    partial class Gemini_RAG
    {
        /// <summary>
        /// Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        /// Clean up any resources being used.
        /// </summary>
        /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form Designer generated code

        /// <summary>
        /// Required method for Designer support - do not modify
        /// the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
            this.label1 = new System.Windows.Forms.Label();
            this.promptTextBox = new System.Windows.Forms.TextBox();
            this.button1 = new System.Windows.Forms.Button();
            this.SuspendLayout();
            // 
            // label1
            // 
            this.label1.AutoSize = true;
            this.label1.Font = new System.Drawing.Font("Artifakt Element Medium", 9F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.label1.Location = new System.Drawing.Point(22, 31);
            this.label1.Name = "label1";
            this.label1.Size = new System.Drawing.Size(413, 33);
            this.label1.TabIndex = 0;
            this.label1.Text = "Enter your Revit API question/task:";
            this.label1.Click += new System.EventHandler(this.label1_Click);
            // 
            // promptTextBox
            // 
            this.promptTextBox.AccessibleName = "promptTextBox";
            this.promptTextBox.Dock = System.Windows.Forms.DockStyle.Fill;
            this.promptTextBox.Font = new System.Drawing.Font("Artifakt Element Medium", 10.875F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.promptTextBox.Location = new System.Drawing.Point(0, 0);
            this.promptTextBox.Margin = new System.Windows.Forms.Padding(3, 4, 3, 4);
            this.promptTextBox.Multiline = true;
            this.promptTextBox.Name = "promptTextBox";
            this.promptTextBox.Size = new System.Drawing.Size(834, 329);
            this.promptTextBox.TabIndex = 1;
            // 
            // button1
            // 
            this.button1.AccessibleName = "submitButton";
            this.button1.BackColor = System.Drawing.SystemColors.ControlLight;
            this.button1.DialogResult = System.Windows.Forms.DialogResult.OK;
            this.button1.Dock = System.Windows.Forms.DockStyle.Bottom;
            this.button1.Font = new System.Drawing.Font("Artifakt Element Medium", 10.875F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.button1.Location = new System.Drawing.Point(0, 249);
            this.button1.Margin = new System.Windows.Forms.Padding(3, 4, 3, 4);
            this.button1.Name = "button1";
            this.button1.Size = new System.Drawing.Size(834, 80);
            this.button1.TabIndex = 2;
            this.button1.Text = "submit";
            this.button1.UseVisualStyleBackColor = false;
            // 
            // Gemini_RAG
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(6F, 16F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(834, 329);
            this.Controls.Add(this.button1);
            this.Controls.Add(this.promptTextBox);
            this.Controls.Add(this.label1);
            this.Font = new System.Drawing.Font("Artifakt Element Medium", 4.125F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.Margin = new System.Windows.Forms.Padding(3, 4, 3, 4);
            this.Name = "Gemini_RAG";
            this.Text = "Gemini RAG";
            this.Load += new System.EventHandler(this.PromptForm_Load);
            this.ResumeLayout(false);
            this.PerformLayout();

        }

        #endregion

        private System.Windows.Forms.Label label1;
        private System.Windows.Forms.TextBox promptTextBox;
        private System.Windows.Forms.Button button1;
    }
}