$ErrorActionPreference = "Stop"
$Deliverables = "c:\Users\arjun\Downloads\mini project\ProteinLens-OS\deliverables"
$DocxPath = Join-Path $Deliverables "ProteinLensOS_Mini_Project_Report.docx"
$ReportPdf = Join-Path $Deliverables "ProteinLensOS_Mini_Project_Report.pdf"
$PptxPath = Join-Path $Deliverables "ProteinLensOS_Defense_Presentation.pptx"
$PptPdf = Join-Path $Deliverables "ProteinLensOS_Defense_Presentation.pdf"

Write-Host "[1/2] Updating TOC fields & exporting IIITN Report PDF via MS Word..."
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
    $doc = $word.Documents.Open($DocxPath)
    $doc.Fields.Update() | Out-Null
    foreach ($toc in $doc.TablesOfContents) { $toc.Update() }
    $doc.Save()
    $doc.ExportAsFixedFormat($ReportPdf, 17) # 17 = wdExportFormatPDF
    $doc.Close()
} finally {
    $word.Quit()
}
Write-Host "Exported: $ReportPdf"

Write-Host "[2/2] Exporting 14-Slide Defense Presentation PDF via MS PowerPoint..."
$ppt = New-Object -ComObject PowerPoint.Application
try {
    $pres = $ppt.Presentations.Open($PptxPath, $true, $false, $false)
    $pres.SaveAs($PptPdf, 32) # 32 = ppSaveAsPDF
    $pres.Close()
} finally {
    $ppt.Quit()
}
Write-Host "Exported: $PptPdf"
