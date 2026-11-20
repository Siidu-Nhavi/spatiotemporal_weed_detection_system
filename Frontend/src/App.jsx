import { useMemo, useRef, useState } from 'react'
import { analyzeImage, exportAnalysis } from './services/api'
import FieldMap from './components/FieldMap'
import './App.css'

const initialSettings = { rows: 8, columns: 12, lowThreshold: 10, highThreshold: 30 }

function StatCard({ label, value, tone = '' }) {
  return (
    <article className={`stat-card ${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  )
}

function App() {
  const inputRef = useRef(null)
  const [file, setFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState('')
  const [analysis, setAnalysis] = useState(null)
  const [view, setView] = useState('heatmap')
  const [settings, setSettings] = useState(initialSettings)
  const [dragging, setDragging] = useState(false)
  const [loading, setLoading] = useState(false)
  const [exporting, setExporting] = useState('')
  const [error, setError] = useState('')
  const [selectedCell, setSelectedCell] = useState(null)

  const cellsByCategory = analysis?.statistics || {}
  const hottest = analysis?.statistics?.highest_density_region
  const selectedRender = analysis?.renders?.[view]
  const selectedCellDetails = useMemo(
    () => analysis?.grid.cells.find((cell) => cell.id === selectedCell) || null,
    [analysis, selectedCell],
  )

  function acceptFile(nextFile) {
    if (!nextFile) return
    if (!['image/jpeg', 'image/png', 'image/tiff', 'image/x-tiff'].includes(nextFile.type) && !/\.(tif|tiff)$/i.test(nextFile.name)) {
      setError('Please choose a JPG, JPEG, PNG, or GeoTIFF image.')
      return
    }
    if (nextFile.size > 15 * 1024 * 1024) {
      setError('Images must be 15 MB or smaller.')
      return
    }
    setError('')
    setFile(nextFile)
    setPreviewUrl(URL.createObjectURL(nextFile))
    setAnalysis(null)
  }

  async function runAnalysis() {
    if (!file) return
    setLoading(true)
    setError('')
    try {
      const result = await analyzeImage(file, settings)
      setAnalysis(result)
      setView('heatmap')
      setSelectedCell(null)
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setLoading(false)
    }

  }

  async function downloadExport(format) {
    if (!file || !analysis) return
    setExporting(format)
    setError('')
    try {
      const blob = await exportAnalysis(file, settings, format)
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `weed-analysis-${format === 'geotiff' ? 'mask.tif' : `grid.${format === 'geojson' ? 'geojson' : 'png'}`}`
      link.click()
      URL.revokeObjectURL(url)
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setExporting('')
    }
  }

  function updateSetting(name, value) {
    setSettings((current) => ({ ...current, [name]: Number(value) }))
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">✦</div>
          <div>
            <strong>FieldSight</strong>
            <span>Precision agriculture intelligence</span>
          </div>
        </div>
        <div className="status-pill"><i /> System ready</div>
      </header>

      <section className="intro">
        <div>
          <p className="eyebrow">WEED STATE ESTIMATION · PHASE 01</p>
          <h1>See the field<br /><em>between the rows.</em></h1>
          <p className="intro-copy">Transform field imagery into a spatial weed-density baseline for smarter, more targeted decisions.</p>
        </div>
        <div className="coordinate-note">
          <span className="note-icon">◎</span>
          <div><strong>Image-coordinate analysis</strong><small>GPS georeferencing ready for a future phase</small></div>
        </div>
      </section>

      <section className="workspace">
        <aside className="control-panel">
          <div className="section-heading"><span className="step">01</span><div><h2>Field image</h2><p>Upload an image to begin</p></div></div>
          <div
            className={`drop-zone ${dragging ? 'dragging' : ''} ${file ? 'has-file' : ''}`}
            onClick={() => inputRef.current?.click()}
            onDragOver={(event) => { event.preventDefault(); setDragging(true) }}
            onDragLeave={() => setDragging(false)}
            onDrop={(event) => { event.preventDefault(); setDragging(false); acceptFile(event.dataTransfer.files[0]) }}
          >
            <input ref={inputRef} type="file" accept=".jpg,.jpeg,.png,.tif,.tiff,image/jpeg,image/png,image/tiff" onChange={(event) => acceptFile(event.target.files[0])} />
            {file ? <>{file.type === 'image/tiff' || /\.(tif|tiff)$/i.test(file.name) ? <div className="upload-icon success">◎</div> : <img className="upload-preview" src={previewUrl} alt="Uploaded field preview" />}<strong>{file.name}</strong><small>{(file.size / 1024 / 1024).toFixed(2)} MB · Ready to analyze</small></> : <><div className="upload-icon">↑</div><strong>Drop field image here</strong><small>or click to browse · JPG, PNG, GeoTIFF up to 15 MB</small></>}
          </div>
          <div className="control-section">
            <div className="section-heading compact"><span className="step">02</span><div><h2>Spatial grid</h2><p>Configure analysis resolution</p></div></div>
            <div className="grid-inputs">
              <label>Rows<input type="number" min="1" max="32" value={settings.rows} onChange={(event) => updateSetting('rows', event.target.value)} /></label>
              <span>×</span>
              <label>Columns<input type="number" min="1" max="32" value={settings.columns} onChange={(event) => updateSetting('columns', event.target.value)} /></label>
            </div>
            <div className="thresholds">
              <label>Low / medium boundary<input type="number" min="0" max="99" value={settings.lowThreshold} onChange={(event) => updateSetting('lowThreshold', event.target.value)} /><b>%</b></label>
              <label>Medium / high boundary<input type="number" min="1" max="100" value={settings.highThreshold} onChange={(event) => updateSetting('highThreshold', event.target.value)} /><b>%</b></label>
            </div>
          </div>
          <button className="analyze-button" disabled={!file || loading} onClick={runAnalysis}>{loading ? 'Analyzing field…' : 'Analyze field'} <span>↗</span></button>
          {error && <p className="error-message">{error}</p>}
          <p className="disclaimer">Analysis is based on the configured model. Without a trained agricultural model, results are clearly marked as demonstration mode.</p>
        </aside>

        <section className="results-panel">
          {!analysis ? <div className="empty-state"><div className="empty-orbit">✦</div><h2>Your field map will appear here</h2><p>Upload an image and run analysis to generate segmentation, density zones, and field statistics.</p></div> : <>
            <div className="results-header"><div><p className="eyebrow">ANALYSIS RESULT</p><h2>Field density map</h2></div><div className="result-actions"><button onClick={() => downloadExport('geojson')} disabled={Boolean(exporting)}>Export GeoJSON</button><button onClick={() => downloadExport('png')} disabled={Boolean(exporting)}>Export mask PNG</button>{analysis.coordinate_system === 'geographic' && <button onClick={() => downloadExport('geotiff')} disabled={Boolean(exporting)}>Export GeoTIFF</button>}<div className={`mode-badge ${analysis.detection.mode}`}>{analysis.detection.mode === 'demo' ? 'DEMO MODE' : 'CUSTOM MODEL'} <span>●</span></div></div></div>
            <div className="map-toolbar"><div className="view-tabs">{[['heatmap', 'Density map'], ['overlay', 'Segmentation'], ['original', 'Original'], ['mask', 'Mask']].map(([key, label]) => <button key={key} className={view === key ? 'active' : ''} onClick={() => setView(key)}>{label}</button>)}</div><span className="zoom-hint">Scroll to inspect · click a cell</span></div>
            <div className="map-frame">
              <img src={selectedRender} alt={`${view} analysis`} />
              {view === 'heatmap' && <div className="cell-picker">{analysis.grid.cells.map((cell) => <button key={cell.id} title={`${cell.id}: ${cell.weed_density_percent}%`} className={cell.density_category} style={{ left: `${cell.coordinates.x_min / analysis.image.width * 100}%`, top: `${cell.coordinates.y_min / analysis.image.height * 100}%`, width: `${(cell.coordinates.x_max - cell.coordinates.x_min) / analysis.image.width * 100}%`, height: `${(cell.coordinates.y_max - cell.coordinates.y_min) / analysis.image.height * 100}%` }} onClick={() => setSelectedCell(cell.id)} />)}</div>}
              <div className="map-badge">↗ {analysis.image.width} × {analysis.image.height} px</div>
            </div>
            <FieldMap analysis={analysis} imageUrl={selectedRender} onSelectCell={setSelectedCell} />
            <div className="map-footer"><div className="legend"><span>Density</span><i className="low" /> Low <i className="medium" /> Medium <i className="high" /> High</div>{selectedCellDetails && <div className="cell-detail"><strong>{selectedCellDetails.id}</strong> {selectedCellDetails.weed_density_percent}% · {selectedCellDetails.weed_instance_count} instances</div>}</div>
            <div className="stats-grid">
              <StatCard label="Weed coverage" value={`${analysis.detection.weed_coverage_percent}%`} tone="accent" />
              <StatCard label="Detected instances" value={analysis.detection.instance_count} />
              <StatCard label="Avg. confidence" value={analysis.detection.average_confidence ? `${(analysis.detection.average_confidence * 100).toFixed(0)}%` : '—'} />
              <StatCard label="Peak cell" value={hottest ? `${hottest.weed_density_percent}%` : '—'} tone="warm" />
            </div>
            <div className="category-row"><span><i className="low" /> {cellsByCategory.low_density_cells} low-density cells</span><span><i className="medium" /> {cellsByCategory.medium_density_cells} medium-density cells</span><span><i className="high" /> {cellsByCategory.high_density_cells} high-density cells</span></div>
            <p className="model-note">{analysis.detection.note}</p>
          </>}
        </section>
      </section>
      <footer><span>FieldSight · Closed-loop spatiotemporal weed intelligence</span><span>v0.1 · Image coordinate system</span></footer>
    </main>
  )
}

export default App
