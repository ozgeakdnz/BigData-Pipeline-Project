$NetworkName = "bigdata-net"
$existing = docker network ls --filter "name=$NetworkName" --format "{{.Name}}" 2>$null
if ($existing -eq $NetworkName) {
    Write-Host "Docker network '$NetworkName' already exists - nothing to do."
} else {
    docker network create $NetworkName
    Write-Host "OK: Docker network '$NetworkName' created."
}