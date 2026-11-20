import { useEffect } from 'react'
import { CRS } from 'leaflet'
import {
  ImageOverlay,
  MapContainer,
  Rectangle,
  TileLayer,
  Tooltip,
  useMap,
} from 'react-leaflet'
import 'leaflet/dist/leaflet.css'

const colors = { low: '#78b95a', medium: '#28b4e6', high: '#3c4bed' }

function FitBounds({ bounds }) {
  const map = useMap()

  useEffect(() => {
    map.fitBounds(bounds, { padding: [12, 12] })
  }, [bounds, map])

  return null
}

function mapConfiguration(analysis) {
  const isGeographic = analysis.coordinate_system === 'geographic'
  const sourceBounds = analysis.geospatial?.bounds
  if (isGeographic && sourceBounds?.length === 4) {
    const [xMin, yMin, xMax, yMax] = sourceBounds
    return {
      bounds: [[yMin, xMin], [yMax, xMax]],
      simple: !/^EPSG:4326$/i.test(analysis.geospatial.crs || ''),
      note: analysis.geospatial.crs || 'Source CRS',
    }
  }

  return {
    bounds: [[0, 0], [analysis.image.height, analysis.image.width]],
    simple: true,
    note: 'Image pixels',
  }
}

function cellBounds(analysis, cell) {
  const bounds = cell.spatial_coordinates || cell.coordinates
  if (analysis.coordinate_system === 'image_pixels' && !cell.spatial_coordinates) {
    return [
      [analysis.image.height - bounds.y_max, bounds.x_min],
      [analysis.image.height - bounds.y_min, bounds.x_max],
    ]
  }
  return [[bounds.y_min, bounds.x_min], [bounds.y_max, bounds.x_max]]
}

export default function FieldMap({ analysis, imageUrl, onSelectCell }) {
  const configuration = mapConfiguration(analysis)
  const mapKey = `${analysis.coordinate_system}-${analysis.geospatial?.crs || 'pixels'}`

  return (
    <div className="gis-map-section">
      <div className="gis-map-heading">
        <div>
          <strong>Interactive GIS view</strong>
          <small>{configuration.note} · zoom, pan, and inspect cells</small>
        </div>
        <span>{analysis.statistics?.hotspot_count || 0} hotspots</span>
      </div>
      <MapContainer
        key={mapKey}
        className="field-map"
        bounds={configuration.bounds}
        crs={configuration.simple ? CRS.Simple : undefined}
        scrollWheelZoom
      >
        {!configuration.simple && (
          <TileLayer
            attribution="&copy; OpenStreetMap contributors"
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
        )}
        <ImageOverlay url={imageUrl} bounds={configuration.bounds} opacity={0.78} />
        <FitBounds bounds={configuration.bounds} />
        {analysis.grid.cells.map((cell) => (
          <Rectangle
            key={cell.id}
            bounds={cellBounds(analysis, cell)}
            pathOptions={{
              color: colors[cell.density_category],
              weight: 1,
              fillOpacity: 0.2,
            }}
            eventHandlers={{ click: () => onSelectCell(cell.id) }}
          >
            <Tooltip sticky>
              <strong>{cell.id}</strong>
              <br />
              {cell.weed_density_percent}% density · {cell.weed_instance_count} instances
            </Tooltip>
          </Rectangle>
        ))}
      </MapContainer>
    </div>
  )
}
