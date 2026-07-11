# Minimal relay server for Spotcast setup on Windows with Home Assistant OAuth flow

<#
Usage:

Default redirect URL (My Home Assistant cloud):
    iwr "https://raw.githubusercontent.com/Mincka/spotcast/main/scripts/relay_server.ps1" -UseBasicParsing | iex

Custom Home Assistant URL:
    $redirectUrl = "http://your-home-assistant.local:8123/auth/external/callback"
    iwr "https://raw.githubusercontent.com/Mincka/spotcast/main/scripts/relay_server.ps1" -UseBasicParsing | iex

Downloaded locally:
    .\relay_server.ps1 -r http://your-home-assistant.local:8123/auth/external/callback
    .\relay_server.ps1 --redirect-url http://your-home-assistant.local:8123/auth/external/callback
#>

Add-Type -AssemblyName System.Web

# Default redirect URL
if (-not (Get-Variable redirectUrl -Scope Script -ErrorAction SilentlyContinue)) {
    $redirectUrl = "https://my.home-assistant.io/redirect/oauth"
}

# Parse -r / --redirect-url command-line arguments
for ($i = 0; $i -lt $args.Length; $i++) {
    switch ($args[$i]) {
        '-r'             { if ($i + 1 -lt $args.Length) { $redirectUrl = $args[$i + 1]; $i++ } }
        '--redirect-url' { if ($i + 1 -lt $args.Length) { $redirectUrl = $args[$i + 1]; $i++ } }
    }
}

$LISTEN_PORT = 8080
$Listener    = $null

function Stop-RelayServer {
    if ($Listener) {
        try {
            if ($Listener.IsListening) { $Listener.Stop() }
            $Listener.Close()
        } catch { }
    }
}

# Ctrl+C handler: stop listener, allow PowerShell to continue default cancellation
$CtrlCHandler = [ConsoleCancelEventHandler]{
    param($sender, $eventArgs)
    Write-Host "`nCtrl+C detected. Shutting down relay server..."
    Stop-RelayServer
    # Do NOT set $eventArgs.Cancel = $true, so script stops and prompt returns
}
[Console]::add_CancelKeyPress($CtrlCHandler)

function Handle-Request {
    param([System.Net.HttpListenerContext]$Context)

    $Request  = $Context.Request
    $Response = $Context.Response

    if ($Request.Url.AbsolutePath -ne '/login') {
        $Response.StatusCode = 404
        $Response.Close()
        return
    }

    # Build redirect URL
    $QueryString = $Request.Url.Query
    if ($QueryString.StartsWith('?')) { $QueryString = $QueryString.Substring(1) }
    $RedirectUrl = if ([string]::IsNullOrEmpty($QueryString)) { $redirectUrl } else { "$redirectUrl`?$QueryString" }

    # Inform the user
    Write-Host ""
    Write-Host "Redirected to: $RedirectUrl"
    Write-Host ""
    Write-Host "Redirection complete. You can now finish the Spotcast integration setup in Home Assistant."
    Write-Host "You may close this window. The relay server is only needed for the initial setup."
    Write-Host ""

    # Send HTTP 302
    $Response.StatusCode       = 302
    $Response.RedirectLocation = $RedirectUrl
    $Response.ContentLength64  = 0
    $Response.Close()
}

try {
    # Start listener
    $Listener = [System.Net.HttpListener]::new()
    $Listener.Prefixes.Add("http://127.0.0.1:$LISTEN_PORT/")
    $Listener.Start()

    Write-Host ""
    Write-Host "Relay server running at http://127.0.0.1:$LISTEN_PORT/login"
    Write-Host "Target redirect URL: $redirectUrl"
    Write-Host "Open the Spotcast integration setup in Home Assistant."
    Write-Host "(Press Ctrl+C to cancel.)"
    Write-Host ""

    # Wait for first request
    while ($Listener.IsListening) {
        try {
            $Context = $Listener.GetContext()    # Blocks until a request arrives
            Handle-Request -Context $Context
            break                                # Stop after first successful /login
        } catch [System.Net.HttpListenerException] {
            break                                # Listener stopped
        } catch {
            Write-Error $_
        }
    }
}
finally {
    Stop-RelayServer
    if ($CtrlCHandler) { [Console]::remove_CancelKeyPress($CtrlCHandler) }
}
