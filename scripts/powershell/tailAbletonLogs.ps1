KillProcess (GetProcessFromNameOrTitle "*logs terminal*") -force
$host.ui.RawUI.WindowTitle = "logs terminal"

$version = $Env:abletonVersion

$logFile = "$env:userprofile\AppData\Roaming\Ableton\Live $version\Preferences\Log.txt"
$startSize = 70
$processLogFile = $true
$debug = $false
$showDateTime = $true
$global:write_next_n_lines = 0

$host.ui.RawUI.WindowTitle = 'logs terminal'
Get-Process -Id $pid | Set-WindowState -State SHOWMAXIMIZED

function FocusLogs()
{
    python.exe "$p0\scripts\python\focus_window.py" "logs terminal"
}

function Get-LogColor
{
    Param([Parameter(Position = 0)]
        [String]$LogEntry)

    process {
        if ( $LogEntry.Contains("P0 -"))
        {
            if ( $LogEntry.Contains("P0 - dev"))
            {
                Return "Yellow"
            }
            elseif ($LogEntry.Contains("P0 - debug"))
            {
                Return "Gray"
            }
            elseif ( $LogEntry.Contains("P0 - info"))
            {
                Return "Green"
            }
            elseif ($LogEntry.Contains("P0 - notice"))
            {
                Return "Blue"
            }
            elseif ($LogEntry.Contains("P0 - warning"))
            {
                Return "Magenta"
            }
            else
            {
                Return "Red"
                FocusLogs
                #                Return "White"
            }
        }

        if ($LogEntry -like ("*error*") -or $LogEntry -like ("*exception*"))
        {
            Return "Red"
            FocusLogs
        }

        Return "DarkGray"
    }
}
function Format-LogLine
{
    Param([Parameter(Position = 0)]
        [String]$LogEntry)

    process {
        # remove Protocol 0 log prefix
        if ($debug)
        {
            Write-Host $LogEntry
        }
        $LogEntry = $LogEntry -replace "P0 - (\w+:)?"

        # remove unecessary remote script log info
        $LogEntry = $LogEntry -replace "Python: INFO:root:\d* - "
        $LogEntry = $LogEntry -replace "(info|debug):\s?"
        $LogEntry = $LogEntry -replace "RemoteScriptError: "

        # Simplify date
        $timestampReg = "^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{6}:"
        if ($LogEntry -match $timestampReg)
        {
            $parts = [regex]::split($LogEntry, '\s+')
            if (-not$parts[2])  # allow printing empty lines
            {
                return ""
            }

            $parts = $LogEntry.Split(" ")  # keeping indentation
            if ($showDateTime)
            {
                $date = [datetime]::parseexact($parts[0], 'yyyy-MM-ddTHH:mm:ss.ffffff:', $null)
                $logEntry = (Get-Date -Date $date -Format "HH:mm:ss.fff") + " " + $parts[1].TrimStart() + ($parts[2..($parts.Count - 1)] -join " ")
            }
            else
            {
                $logEntry = $parts[1..($parts.Count - 1)] -join " "
            }
        }

        Return $LogEntry
    }
}
function Select-Log-Line
{
    Param([Parameter(Position = 0)]
        [String]$LogEntry)

    if ($debug)
    {
        return $true
    }

    if ( $LogEntry.Contains("(Protocol0) Initializing"))
    {
        Clear-Host
    }

    $Filters = "P0", "ArgumentError", "RemoteScriptError"

    foreach ($Filter in $Filters)
    {
        if ( $LogEntry.Contains($Filter))
        {
            if ( $LogEntry.Contains("ArgumentError") -or $LogEntry.Contains("Pythonargument"))
            {
                $global:write_next_n_lines = 3

            }
            return $LogEntry
            Write-Host -ForegroundColor (Get-LogColor $LogEntry) (Format-LogLine($LogEntry))
        }
    }

    if ($write_next_n_lines -ne 0)
    {
        $global:write_next_n_lines -= 1
        return $LogEntry
    }

    return $null
}
function Write-Log-Line
{
    Param([Parameter(Position = 0)]
        [String]$LogEntry)

    if (Select-Log-Line($LogEntry))
    {
        Write-Host -ForegroundColor (Get-LogColor $LogEntry) (Format-LogLine($LogEntry))
    }
}

if ($processLogFile)
{
    Get-Content -Tail $startSize -wait $logFile | ForEach-Object { Write-Log-Line($_) }
}
else
{
    Get-Content -Tail $startSize -wait $logFile
}