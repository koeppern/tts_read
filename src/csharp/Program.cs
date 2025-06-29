using System;
using System.IO;
using System.Windows.Forms;

namespace TtsRead;

static class Program
{
    /// <summary>
    ///  The main entry point for the application.
    /// </summary>
    [STAThread]
    static void Main()
    {
        // Enable visual styles
        Application.EnableVisualStyles();
        Application.SetCompatibleTextRenderingDefault(false);
        
        // Create debug log file
        string logPath = Path.Combine(AppContext.BaseDirectory, "debug.log");
        
        try
        {
            File.AppendAllText(logPath, $"[{DateTime.Now}] TtsRead starting...\n");
            
            // To customize application configuration such as set high DPI settings or default font,
            // see https://aka.ms/applicationconfiguration.
            var form = new Form1();
            File.AppendAllText(logPath, $"[{DateTime.Now}] Form1 created successfully\n");
            
            Application.Run(form);
            File.AppendAllText(logPath, $"[{DateTime.Now}] Application.Run completed\n");
        }
        catch (Exception ex)
        {
            File.AppendAllText(logPath, $"[{DateTime.Now}] CRITICAL ERROR: {ex.Message}\n");
            File.AppendAllText(logPath, $"[{DateTime.Now}] Stack trace: {ex.StackTrace}\n");
            
            MessageBox.Show(
                $"TtsRead startup error:\n\n{ex.Message}\n\nCheck debug.log for details.",
                "TtsRead Error",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error
            );
        }
    }    
}