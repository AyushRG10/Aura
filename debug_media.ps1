$mediaType = [Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager, Windows.Media, ContentType=WindowsRuntime]
Write-Output "Type loaded: $mediaType"

$op = $mediaType::RequestAsync()
Write-Output "Operation Object Type: $($op.GetType().FullName)"

while ($op.Status -eq 'Started') { Start-Sleep -Milliseconds 50 }

Write-Output "Operation Status: $($op.Status)"
$manager = $op.GetResults()
Write-Output "Manager Object: $manager"
