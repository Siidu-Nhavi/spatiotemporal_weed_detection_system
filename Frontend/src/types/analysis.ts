export type DensityCategory = 'low' | 'medium' | 'high'

export interface DensityCell {
  id: string
  row: number
  column: number
  coordinates: { x_min: number; y_min: number; x_max: number; y_max: number }
  spatial_coordinates?: { x_min: number; y_min: number; x_max: number; y_max: number }
  valid_field_area_square_units?: number
  weed_density_percent: number
  density_category: DensityCategory
  weed_instance_count: number
  average_detection_confidence: number
}

export interface AnalysisResult {
  schema_version: string
  coordinate_system: 'image_pixels' | 'geographic'
  image: { width: number; height: number; channels: number }
  geospatial?: {
    available: boolean
    crs: string | null
    transform?: number[]
    bounds?: number[]
    nodata?: number | null
    area_unit?: string | null
    note?: string
  }
  detection: {
    mode: 'demo' | 'custom_model'
    model_name: string | null
    instance_count: number
    weed_coverage_percent: number
    average_confidence: number
    note: string
  }
  grid: { rows: number; columns: number; cells: DensityCell[] }
  renders: { original: string; mask: string; overlay: string; heatmap: string }
  statistics: {
    low_density_cells: number
    medium_density_cells: number
    high_density_cells: number
    hotspot_count: number
    hotspot_cells: DensityCell[]
    highest_density_region: DensityCell | null
  }
}
