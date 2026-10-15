import { ProductSelectionRecord } from '@/types/harmonisation';

export const AUTHORITATIVE_PRODUCT_RECORDS: ProductSelectionRecord[] = [
  {
    sensor: 'MODIS',
    product_short_name: 'MOD14 / MYD14 / MCD14ML',
    satellite_platform: 'Terra (10:30 AM/PM local equator crossing) & Aqua (1:30 PM/AM)',
    product_collection_version: 'Collection 6.1 (C6.1)',
    temporal_coverage: '2000-present (Terra), 2002-present (Aqua)',
    data_format: 'CSV (NASA FIRMS / NRT), HDF4 (Standard Science Products)',
    source_download_endpoint: 'https://firms.modaps.eosdis.nasa.gov / NASA LAADS DAAC',
    required_credentials_note: 'NASA Earthdata Login & FIRMS API Map Key for direct streaming',
    quality_fields_interpretation: 'confidence (0-100% continuous probability heuristic), scan & track footprint expansion',
    licence_usage_conditions: 'NASA Open Data Policy (Acknowledge NASA FIRMS & MODIS Science Team)',
  },
  {
    sensor: 'VIIRS',
    product_short_name: 'VNP14IMGTDL / VJ114IMGTDL',
    satellite_platform: 'Suomi-NPP (1:30 PM/AM crossing) & NOAA-20 / JPSS-1 (1:30 PM/AM shifted)',
    product_collection_version: 'Collection 1 (C1) / Collection 2 (C2)',
    temporal_coverage: '2012-present (Suomi-NPP), 2018-present (NOAA-20)',
    data_format: 'CSV (NASA FIRMS / NRT), NetCDF4 / HDF5 (Standard Science Products)',
    source_download_endpoint: 'https://firms.modaps.eosdis.nasa.gov / NASA LANCE / LP DAAC',
    required_credentials_note: 'NASA Earthdata Login & FIRMS API Map Key for direct streaming',
    quality_fields_interpretation: 'confidence categorical flag ("low", "nominal", "high") based on 375m I-band context',
    licence_usage_conditions: 'NASA Open Data Policy (Acknowledge NASA FIRMS & VIIRS Land Science Team)',
  },
];
