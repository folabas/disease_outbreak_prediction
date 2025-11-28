# Launch TensorBoard to view training metrics
# Run this script to start TensorBoard server

Write-Host "Starting TensorBoard..." -ForegroundColor Green
Write-Host "Logs directory: logs/fit" -ForegroundColor Cyan
Write-Host ""
Write-Host "Once TensorBoard starts, open your browser to:" -ForegroundColor Yellow
Write-Host "  http://localhost:6006" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C to stop TensorBoard" -ForegroundColor Gray
Write-Host ""

tensorboard --logdir logs/fit --port 6006
