$path = 'D:\CascadeProjects\.streamlit\secrets.toml'
$content = Get-Content $path -Raw -ErrorAction SilentlyContinue
if ($content -notmatch 'GOOGLE_API_KEY') {
    $line = 'GOOGLE_API_KEY = "여기에_발급받은_API_키를_넣어주세요"'
    Add-Content $path -Value $line
    Write-Host "GOOGLE_API_KEY placeholder added to secrets.toml"
} else {
    Write-Host "GOOGLE_API_KEY already exists in secrets.toml"
}
