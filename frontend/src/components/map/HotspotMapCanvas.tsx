'use client';

import React, { useEffect, useMemo, useRef, useState } from 'react';
import { HarmonisedRecord, MatchStatus, SensorType } from '@/types/harmonisation';
import { MATCH_STATUS_CONFIGS, SENSOR_CONFIGS } from '@/lib/constants/design';
import {
  Compass,
  Crosshair,
  Maximize2,
  Minus,
  Navigation,
  Plus,
  RotateCcw,
} from 'lucide-react';
import clsx from 'clsx';

interface HotspotMapCanvasProps {
  records: HarmonisedRecord[];
  activeLayers: Record<string, boolean>;
  onSelectRecord: (record: HarmonisedRecord) => void;
  selectedRecordId?: string | null;
  className?: string;
}

export function HotspotMapCanvas({
  records,
  activeLayers,
  onSelectRecord,
  selectedRecordId,
  className,
}: HotspotMapCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  // Default coordinate viewport centered around Northern India / Indo-Gangetic Basin
  const [center, setCenter] = useState<{ lon: number; lat: number }>({ lon: 77.2, lat: 29.3 });
  const [zoom, setZoom] = useState<number>(8); // zoom level 1 to 16

  // Mouse interaction state
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [dragStart, setDragStart] = useState<{ x: number; y: number } | null>(null);
  const [cursorCoords, setCursorCoords] = useState<{ lon: number; lat: number } | null>(null);
  const [hoveredRecord, setHoveredRecord] = useState<HarmonisedRecord | null>(null);

  // Canvas dimensions
  const [dimensions, setDimensions] = useState<{ width: number; height: number }>({
    width: 800,
    height: 500,
  });

  useEffect(() => {
    const updateSize = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.clientWidth || 800,
          height: containerRef.current.clientHeight || 500,
        });
      }
    };
    updateSize();
    window.addEventListener('resize', updateSize);
    return () => window.removeEventListener('resize', updateSize);
  }, []);

  // Compute bounding box from records if available to auto-center on initial load
  useEffect(() => {
    if (records.length > 0) {
      let minLon = 180;
      let maxLon = -180;
      let minLat = 90;
      let maxLat = -90;
      let count = 0;

      records.forEach((rec) => {
        const obs = rec.modis_observation || rec.viirs_observation;
        if (obs) {
          if (obs.longitude < minLon) minLon = obs.longitude;
          if (obs.longitude > maxLon) maxLon = obs.longitude;
          if (obs.latitude < minLat) minLat = obs.latitude;
          if (obs.latitude > maxLat) maxLat = obs.latitude;
          count++;
        }
      });

      if (count > 0 && minLon <= maxLon && minLat <= maxLat) {
        setCenter({
          lon: (minLon + maxLon) / 2,
          lat: (minLat + maxLat) / 2,
        });
      }
    }
  }, [records]);

  // Coordinate Projection formulas: WGS84 (EPSG:4326) to Screen Coordinates
  // 1 degree longitude at zoom Z corresponds to scale pixels
  const pixelsPerDegree = useMemo(() => {
    return (Math.pow(2, zoom) * 256) / 360;
  }, [zoom]);

  const projectToScreen = (lon: number, lat: number) => {
    const x = dimensions.width / 2 + (lon - center.lon) * pixelsPerDegree;
    // Invert Y for screen coordinates (latitude increases upwards)
    const latRad = (lat * Math.PI) / 180;
    const centerLatRad = (center.lat * Math.PI) / 180;
    const y = dimensions.height / 2 - (lat - center.lat) * pixelsPerDegree * Math.cos(centerLatRad);
    return { x, y };
  };

  const unprojectFromScreen = (x: number, y: number) => {
    const centerLatRad = (center.lat * Math.PI) / 180;
    const lon = center.lon + (x - dimensions.width / 2) / pixelsPerDegree;
    const lat = center.lat - (y - dimensions.height / 2) / (pixelsPerDegree * Math.cos(centerLatRad));
    return { lon, lat };
  };

  // Mouse Handlers for Pan
  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX, y: e.clientY });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    const rect = containerRef.current?.getBoundingClientRect();
    if (rect) {
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;
      const coords = unprojectFromScreen(mouseX, mouseY);
      setCursorCoords(coords);
    }

    if (isDragging && dragStart) {
      const dx = e.clientX - dragStart.x;
      const dy = e.clientY - dragStart.y;
      const centerLatRad = (center.lat * Math.PI) / 180;

      const dLon = -dx / pixelsPerDegree;
      const dLat = dy / (pixelsPerDegree * Math.cos(centerLatRad));

      setCenter((prev) => ({
        lon: prev.lon + dLon,
        lat: Math.max(-85, Math.min(85, prev.lat + dLat)),
      }));
      setDragStart({ x: e.clientX, y: e.clientY });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
    setDragStart(null);
  };

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    if (e.deltaY < 0) {
      setZoom((prev) => Math.min(14, prev + 0.3));
    } else {
      setZoom((prev) => Math.max(3, prev - 0.3));
    }
  };

  // Metric Scale Bar calculation (approx km at current latitude & zoom)
  const metricScale = useMemo(() => {
    const centerLatRad = (center.lat * Math.PI) / 180;
    // 1 pixel in metres
    const metersPerPixel = (111320 * Math.cos(centerLatRad)) / pixelsPerDegree;
    const targetPixelWidth = 100;
    const rawMeters = targetPixelWidth * metersPerPixel;

    let displayKm = 10;
    if (rawMeters < 1000) {
      return { label: `${Math.round(rawMeters)} m`, pixelWidth: targetPixelWidth };
    }
    const km = rawMeters / 1000;
    if (km < 2) displayKm = 1;
    else if (km < 5) displayKm = 2;
    else if (km < 10) displayKm = 5;
    else if (km < 25) displayKm = 10;
    else if (km < 50) displayKm = 25;
    else if (km < 100) displayKm = 50;
    else displayKm = 100;

    const actualWidth = (displayKm * 1000) / metersPerPixel;
    return { label: `${displayKm} km`, pixelWidth: actualWidth };
  }, [center.lat, pixelsPerDegree]);

  // Filter records by active layers
  const visibleRecords = useMemo(() => {
    return records.filter((rec) => {
      if (rec.match_status === 'matched' && !activeLayers.matched) return false;
      if (rec.match_status === 'unmatched_modis' && !activeLayers.unmatched_modis) return false;
      if (rec.match_status === 'unmatched_viirs' && !activeLayers.unmatched_viirs) return false;
      if (rec.match_status === 'ambiguous' && !activeLayers.ambiguous) return false;
      return true;
    });
  }, [records, activeLayers]);

  // Clustering logic: if zoom is low (zoom <= 6) or total records > 500, cluster points by grid cell
  const clusters = useMemo(() => {
    if (zoom > 7 && visibleRecords.length <= 500) {
      return null; // render individual points
    }

    const gridSize = 40; // pixel distance threshold
    const buckets: Array<{
      x: number;
      y: number;
      count: number;
      items: HarmonisedRecord[];
    }> = [];

    visibleRecords.forEach((rec) => {
      const obs = rec.modis_observation || rec.viirs_observation;
      if (!obs) return;
      const screenPos = projectToScreen(obs.longitude, obs.latitude);
      if (
        screenPos.x < -50 ||
        screenPos.x > dimensions.width + 50 ||
        screenPos.y < -50 ||
        screenPos.y > dimensions.height + 50
      ) {
        return;
      }

      const existing = buckets.find(
        (b) => Math.hypot(b.x - screenPos.x, b.y - screenPos.y) < gridSize
      );

      if (existing) {
        existing.count += 1;
        existing.items.push(rec);
      } else {
        buckets.push({
          x: screenPos.x,
          y: screenPos.y,
          count: 1,
          items: [rec],
        });
      }
    });

    return buckets;
  }, [visibleRecords, zoom, dimensions, center, pixelsPerDegree]);

  return (
    <div
      ref={containerRef}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      onWheel={handleWheel}
      className={clsx(
        'relative w-full h-full bg-slate-950 overflow-hidden select-none cursor-grab active:cursor-grabbing border border-slate-800 rounded-lg',
        className
      )}
    >
      {/* Background Geospatial Coordinate Grid Lines */}
      <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-20">
        <defs>
          <pattern id="geo-grid" width="60" height="60" patternUnits="userSpaceOnUse">
            <path d="M 60 0 L 0 0 0 60" fill="none" stroke="#38bdf8" strokeWidth="0.5" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#geo-grid)" />
      </svg>

      {/* SVG Vector Layer for Hotspot Geometries & Connector Lines */}
      <svg className="absolute inset-0 w-full h-full z-10 pointer-events-auto">
        {/* Render Matched & Ambiguous Connector Lines */}
        {zoom > 6 &&
          visibleRecords.map((rec) => {
            if (!rec.modis_observation || !rec.viirs_observation) return null;
            const pModis = projectToScreen(rec.modis_observation.longitude, rec.modis_observation.latitude);
            const pViirs = projectToScreen(rec.viirs_observation.longitude, rec.viirs_observation.latitude);

            const isSelected = selectedRecordId === rec.harmonisation_id;

            return (
              <g key={`line-${rec.harmonisation_id}`}>
                <line
                  x1={pModis.x}
                  y1={pModis.y}
                  x2={pViirs.x}
                  y2={pViirs.y}
                  stroke={
                    rec.match_status === 'matched'
                      ? MATCH_STATUS_CONFIGS.matched.color
                      : MATCH_STATUS_CONFIGS.ambiguous.color
                  }
                  strokeWidth={isSelected ? 2.5 : 1.5}
                  strokeDasharray="4 3"
                  opacity={isSelected ? 1 : 0.75}
                />
              </g>
            );
          })}

        {/* Render Point Clusters when active */}
        {clusters &&
          clusters.map((cl, idx) => (
            <g
              key={`cluster-${idx}`}
              transform={`translate(${cl.x}, ${cl.y})`}
              className="cursor-pointer"
              onClick={(e) => {
                e.stopPropagation();
                setCenter(unprojectFromScreen(cl.x, cl.y));
                setZoom((prev) => Math.min(13, prev + 2));
              }}
            >
              <circle
                r={Math.min(28, 14 + Math.log2(cl.count) * 3)}
                fill="#087F5B"
                fillOpacity="0.35"
                stroke="#63E6BE"
                strokeWidth="2"
              />
              <circle
                r={Math.min(22, 10 + Math.log2(cl.count) * 3)}
                fill="#087F5B"
                fillOpacity="0.85"
              />
              <text
                textAnchor="middle"
                dy="4"
                fill="#FFFFFF"
                fontSize="11"
                fontFamily="ui-monospace, monospace"
                fontWeight="bold"
              >
                {cl.count}
              </text>
            </g>
          ))}

        {/* Render Individual Points when not clustered */}
        {!clusters &&
          visibleRecords.map((rec) => {
            const isSelected = selectedRecordId === rec.harmonisation_id;
            const isHovered = hoveredRecord?.harmonisation_id === rec.harmonisation_id;

            // Render MODIS point if present
            const modisPoint = rec.modis_observation ? (
              <g
                key={`modis-${rec.harmonisation_id}`}
                transform={`translate(${projectToScreen(rec.modis_observation.longitude, rec.modis_observation.latitude).x}, ${
                  projectToScreen(rec.modis_observation.longitude, rec.modis_observation.latitude).y
                })`}
                className="cursor-pointer"
                onMouseEnter={() => setHoveredRecord(rec)}
                onMouseLeave={() => setHoveredRecord(null)}
                onClick={(e) => {
                  e.stopPropagation();
                  onSelectRecord(rec);
                }}
              >
                {/* Square Marker for MODIS */}
                <rect
                  x="-6"
                  y="-6"
                  width="12"
                  height="12"
                  rx="2"
                  fill={SENSOR_CONFIGS.MODIS.color}
                  stroke={isSelected || isHovered ? '#FFFFFF' : '#FFE8CC'}
                  strokeWidth={isSelected || isHovered ? '2.5' : '1'}
                />
              </g>
            ) : null;

            // Render VIIRS point if present
            const viirsPoint = rec.viirs_observation ? (
              <g
                key={`viirs-${rec.harmonisation_id}`}
                transform={`translate(${projectToScreen(rec.viirs_observation.longitude, rec.viirs_observation.latitude).x}, ${
                  projectToScreen(rec.viirs_observation.longitude, rec.viirs_observation.latitude).y
                })`}
                className="cursor-pointer"
                onMouseEnter={() => setHoveredRecord(rec)}
                onMouseLeave={() => setHoveredRecord(null)}
                onClick={(e) => {
                  e.stopPropagation();
                  onSelectRecord(rec);
                }}
              >
                {/* Triangle Marker for VIIRS */}
                <polygon
                  points="0,-7 7,5 -7,5"
                  fill={SENSOR_CONFIGS.VIIRS.color}
                  stroke={isSelected || isHovered ? '#FFFFFF' : '#E3FAFC'}
                  strokeWidth={isSelected || isHovered ? '2.5' : '1'}
                />
              </g>
            ) : null;

            return (
              <g key={`rec-${rec.harmonisation_id}`}>
                {modisPoint}
                {viirsPoint}
              </g>
            );
          })}
      </svg>

      {/* Floating Hover Tooltip */}
      {hoveredRecord && (
        <div
          className="absolute top-4 left-4 z-30 p-2.5 rounded bg-slate-950/90 border border-slate-700 text-[11px] font-mono text-slate-200 shadow-2xl pointer-events-none space-y-1"
        >
          <div className="flex items-center gap-1.5 font-bold text-slate-100">
            <span
              className="w-2 h-2 rounded-full"
              style={{ backgroundColor: MATCH_STATUS_CONFIGS[hoveredRecord.match_status].color }}
            />
            <span>{MATCH_STATUS_CONFIGS[hoveredRecord.match_status].label}</span>
            <span className="text-slate-400 font-normal">({hoveredRecord.harmonisation_id})</span>
          </div>
          {hoveredRecord.spatial_distance_m !== null && (
            <div>Distance: {hoveredRecord.spatial_distance_m.toFixed(1)} m</div>
          )}
          {hoveredRecord.time_difference_s !== null && (
            <div>Time Delta: {Math.round(hoveredRecord.time_difference_s / 60)} mins</div>
          )}
          {hoveredRecord.modis_observation && (
            <div className="text-amber-300">
              MODIS FRP: {hoveredRecord.modis_observation.frp_raw} MW (Conf: {String(hoveredRecord.modis_observation.confidence_raw)}%)
            </div>
          )}
          {hoveredRecord.viirs_observation && (
            <div className="text-cyan-300">
              VIIRS FRP: {hoveredRecord.viirs_observation.frp_raw} MW (Conf: {String(hoveredRecord.viirs_observation.confidence_raw)})
            </div>
          )}
        </div>
      )}

      {/* Map Controls: Top-Right Zoom & Reset */}
      <div className="absolute top-4 right-4 z-20 flex flex-col gap-1.5 bg-slate-900/90 border border-slate-800 rounded-lg p-1 shadow-lg backdrop-blur">
        <button
          type="button"
          onClick={() => setZoom((prev) => Math.min(14, prev + 1))}
          className="p-1.5 rounded hover:bg-slate-800 text-slate-300 hover:text-white transition-colors"
          title="Zoom In"
        >
          <Plus className="w-4 h-4" />
        </button>
        <button
          type="button"
          onClick={() => setZoom((prev) => Math.max(3, prev - 1))}
          className="p-1.5 rounded hover:bg-slate-800 text-slate-300 hover:text-white transition-colors"
          title="Zoom Out"
        >
          <Minus className="w-4 h-4" />
        </button>
        <button
          type="button"
          onClick={() => {
            setCenter({ lon: 77.2, lat: 29.3 });
            setZoom(8);
          }}
          className="p-1.5 rounded hover:bg-slate-800 text-slate-300 hover:text-white transition-colors"
          title="Reset to Study Area Center"
        >
          <Crosshair className="w-4 h-4" />
        </button>
      </div>

      {/* Map Footer Overlays: Bottom-Right Lat/Lon & CRS Badge */}
      <div className="absolute bottom-4 right-4 z-20 flex items-center gap-2 text-[10px] font-mono bg-slate-950/85 border border-slate-800 px-3 py-1.5 rounded shadow-lg backdrop-blur text-slate-300">
        <Compass className="w-3.5 h-3.5 text-cyan-400" />
        <span>
          {cursorCoords
            ? `${cursorCoords.lat.toFixed(5)}°N, ${cursorCoords.lon.toFixed(5)}°E`
            : `${center.lat.toFixed(5)}°N, ${center.lon.toFixed(5)}°E`}
        </span>
        <span className="text-slate-600">|</span>
        <span className="text-cyan-400 font-bold uppercase">
          CRS: EPSG:4326 (WGS 84)
        </span>
      </div>

      {/* Metric Scale Bar: Bottom-Left (08_UI_UX_DESIGN.md Section 2.4) */}
      <div className="absolute bottom-4 left-72 z-20 hidden sm:flex flex-col items-center text-[10px] font-mono text-slate-300 bg-slate-950/80 px-2 py-1 rounded border border-slate-800">
        <span>{metricScale.label}</span>
        <div
          className="h-1 bg-slate-200 border-x border-slate-900 mt-0.5"
          style={{ width: `${metricScale.pixelWidth}px` }}
        />
      </div>
    </div>
  );
}
