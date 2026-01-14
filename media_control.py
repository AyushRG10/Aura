import subprocess

def _run_media_script(action):
    # This PowerShell script connects to the Media Session Manager using embedded C#.
    # We use C# via Add-Type because direct PowerShell WinRT interaction often fails 
    # with "System.__ComObject" errors on older PowerShell versions (5.1).
    
    ps_script = f"""
    # Define assembly paths for WinRT and .NET Runtime
    $refs = @(
        "C:\\Windows\\System32\\WinMetadata\\Windows.Foundation.winmd",
        "C:\\Windows\\System32\\WinMetadata\\Windows.Media.winmd",
        "C:\\Windows\\Microsoft.NET\\Framework64\\v4.0.30319\\System.Runtime.WindowsRuntime.dll"
    )

    $code = @"
    using System;
    using System.Threading.Tasks;
    using Windows.Media.Control;
    using Windows.Foundation;
    
    public class MediaController {{
        public static string PerformAction(string action) {{
            try {{
                // Run the async logic synchronously
                return PerformActionAsync(action).GetAwaiter().GetResult();
            }} catch (Exception ex) {{
                return "Error: " + (ex.InnerException?.Message ?? ex.Message);
            }}
        }}

        private static async Task<string> PerformActionAsync(string action) {{
            // Request the SessionManager
            var manager = await GlobalSystemMediaTransportControlsSessionManager.RequestAsync();
            var session = manager.GetCurrentSession();
            
            if (session == null) return "No active media session found.";
            
            if (action == "GetInfo") {{
                var props = await session.TryGetMediaPropertiesAsync();
                var title = props.Title ?? "Unknown Title";
                var artist = props.Artist ?? "Unknown Artist";
                return "Playing: " + title + " by " + artist;
            }}
            
            bool success = false;
            if (action == "TogglePlayPause") success = await session.TryTogglePlayPauseAsync();
            else if (action == "SkipNext") success = await session.TrySkipNextAsync();
            else if (action == "SkipPrevious") success = await session.TrySkipPreviousAsync();
            
            return success ? "Command '" + action + "' executed." : "Command failed (not supported by app?)";
        }}
    }}
"@

    try {{
        # Compile the C# code 
        Add-Type -TypeDefinition $code -Language CSharp -ReferencedAssemblies $refs
        
        # Execute the static method
        [MediaController]::PerformAction("{action}")
    }} catch {{
        Write-Output "PowerShell Error: $_"
    }}
    """

    try:
        # Run the PowerShell command
        cmd = ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        output = result.stdout.strip()
        if not output and result.stderr:
            return f"Error: {result.stderr.strip()}"
            
        # Return success message or info
        return output if output else "Done."
    except Exception as e:
        # Handle Python-side errors (e.g., powershell not found)
        return f"System Error: {str(e)}"

# Wrapper functions for specific media actions

def play_pause():
    """Toggles play/pause on the active media session."""
    return _run_media_script("TogglePlayPause")

def skip_next():
    """Skips to the next track."""
    return _run_media_script("SkipNext")

def skip_previous():
    """Skips to the previous track."""
    return _run_media_script("SkipPrevious")

def get_media_info():
    """Retrieves current track title and artist."""
    return _run_media_script("GetInfo")
