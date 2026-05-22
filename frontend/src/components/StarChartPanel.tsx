import { useMemo, useState, useCallback } from 'react';

interface ChartTarget {
  name: string;
  ra: number;
  dec: number;
  fov: number;
  magLimit: number;
}

const TARGETS: ChartTarget[] = [
  { name: 'Mars / Capricorn', ra: 310.0, dec: -17.0, fov: 35, magLimit: 8.8 },
  { name: 'Orion', ra: 83.82, dec: -5.39, fov: 18, magLimit: 8 },
  { name: 'M31', ra: 10.68, dec: 41.27, fov: 10, magLimit: 8 },
  { name: 'Pleiades', ra: 56.75, dec: 24.12, fov: 8, magLimit: 8.2 },
  { name: 'Cygnus', ra: 305.0, dec: 40.0, fov: 24, magLimit: 8 },
  { name: 'Galactic Center', ra: 266.4, dec: -29.0, fov: 22, magLimit: 8.5 },
];

function clampNumber(value: string, fallback: number, min: number, max: number) {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return fallback;
  return Math.min(max, Math.max(min, parsed));
}

function buildChartUrl(
  ra: number,
  dec: number,
  fov: number,
  magLimit: number,
  showDso: boolean,
  refreshKey: number,
) {
  const params = new URLSearchParams({
    ra: ra.toFixed(4),
    dec: dec.toFixed(4),
    fov: fov.toFixed(1),
    width: '1800',
    height: '2200',
    mag_limit: magLimit.toFixed(1),
    show_dso: String(showDso),
    style: 'mobile',
    t: String(refreshKey),
  });

  return `/starchart?${params.toString()}`;
}

function Spinner() {
  return (
    <div className="flex flex-col items-center gap-3">
      <svg className="animate-spin h-8 w-8 text-indigo-400" viewBox="0 0 24 24" fill="none">
        <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" strokeDasharray="8 4" opacity="0.3" />
        <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" strokeDasharray="31.4 31.4" opacity="0.7">
          <animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="2s" repeatCount="indefinite" />
        </circle>
      </svg>
      <span className="text-xs text-gray-400">Generating star chart...</span>
    </div>
  );
}

export default function StarChartPanel() {
  const [ra, setRa] = useState(310.0);
  const [dec, setDec] = useState(-17.0);
  const [fov, setFov] = useState(35);
  const [magLimit, setMagLimit] = useState(8.8);
  const [showDso, setShowDso] = useState(true);
  const [refreshKey, setRefreshKey] = useState(1);
  const [imageState, setImageState] = useState<'loading' | 'ready' | 'error'>('loading');
  const [zoomed, setZoomed] = useState(false);

  const imageUrl = useMemo(
    () => buildChartUrl(ra, dec, fov, magLimit, showDso, refreshKey),
    [ra, dec, fov, magLimit, showDso, refreshKey],
  );

  const applyTarget = (target: ChartTarget) => {
    setRa(target.ra);
    setDec(target.dec);
    setFov(target.fov);
    setMagLimit(target.magLimit);
    setImageState('loading');
    setRefreshKey((current) => current + 1);
  };

  const refresh = () => {
    setImageState('loading');
    setRefreshKey((current) => current + 1);
  };

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Escape') setZoomed(false);
  }, []);

  return (
    <>
      <aside className="flex h-full min-h-0 flex-col border-t border-gray-800 bg-gray-950 lg:border-l lg:border-t-0">
        <div className="border-b border-gray-800 px-4 py-3">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="text-sm font-semibold text-gray-100 flex items-center gap-2">
                <span className="text-base">✨</span> Star Chart
              </h2>
              <p className="text-xs text-gray-500 mt-0.5">Local atlas · port 8082</p>
            </div>
            <button
              type="button"
              onClick={refresh}
              className="rounded-lg border border-indigo-700/60 px-3 py-1.5 text-xs font-medium text-indigo-200 transition-all hover:border-indigo-500 hover:bg-indigo-950/40 hover:text-indigo-100 active:scale-95"
            >
              Render
            </button>
          </div>
        </div>

        <div className="space-y-3 border-b border-gray-800 px-4 py-3">
          <div className="flex gap-1.5 overflow-x-auto pb-0.5 scrollbar-none">
            {TARGETS.map((target) => (
              <button
                key={target.name}
                type="button"
                onClick={() => applyTarget(target)}
                className="shrink-0 rounded-md bg-gray-900 px-2.5 py-1.5 text-xs text-gray-400 ring-1 ring-gray-800 transition-all hover:bg-gray-800 hover:text-gray-100 hover:ring-gray-700"
              >
                {target.name}
              </button>
            ))}
          </div>

          <div className="grid grid-cols-2 gap-2">
            <label className="grid gap-1 text-xs text-gray-500">
              RA (deg)
              <input
                value={ra}
                onChange={(event) => setRa(clampNumber(event.target.value, ra, 0, 360))}
                className="rounded-lg border border-gray-800 bg-gray-900 px-2.5 py-1.5 text-sm text-gray-100 outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/30 transition-all font-mono"
                inputMode="decimal"
              />
            </label>
            <label className="grid gap-1 text-xs text-gray-500">
              Dec (deg)
              <input
                value={dec}
                onChange={(event) => setDec(clampNumber(event.target.value, dec, -89, 89))}
                className="rounded-lg border border-gray-800 bg-gray-900 px-2.5 py-1.5 text-sm text-gray-100 outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/30 transition-all font-mono"
                inputMode="decimal"
              />
            </label>
          </div>

          <label className="grid gap-1.5 text-xs text-gray-500">
            <span>Field of view: <span className="text-gray-300 font-mono">{fov.toFixed(1)}°</span></span>
            <input
              type="range"
              min="2"
              max="60"
              step="0.5"
              value={fov}
              onChange={(event) => setFov(Number(event.target.value))}
              className="accent-indigo-500 h-1.5"
            />
          </label>

          <label className="grid gap-1.5 text-xs text-gray-500">
            <span>Mag limit: <span className="text-gray-300 font-mono">{magLimit.toFixed(1)}</span></span>
            <input
              type="range"
              min="4"
              max="10"
              step="0.1"
              value={magLimit}
              onChange={(event) => setMagLimit(Number(event.target.value))}
              className="accent-amber-400 h-1.5"
            />
          </label>

          <label className="flex items-center gap-2 text-xs text-gray-400 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={showDso}
              onChange={(event) => {
                setShowDso(event.target.checked);
                setImageState('loading');
                setRefreshKey((current) => current + 1);
              }}
              className="h-4 w-4 rounded border-gray-700 bg-gray-900 accent-indigo-500 cursor-pointer"
            />
            Show deep-sky objects
          </label>
        </div>

        <div className="relative min-h-0 flex-1 bg-black overflow-hidden group">
          {imageState === 'loading' && (
            <div className="absolute inset-0 z-10 flex items-center justify-center bg-gray-950/70 backdrop-blur-sm">
              <Spinner />
            </div>
          )}
          {imageState === 'error' && (
            <div className="absolute inset-0 z-20 flex flex-col items-center justify-center bg-gray-950 px-8 text-center gap-3">
              <span className="text-3xl">🔭</span>
              <p className="text-sm text-gray-400">Star chart service not available</p>
              <p className="text-xs text-gray-600">Start the service at <code className="text-indigo-400 bg-gray-900 px-1 py-0.5 rounded">localhost:8082</code></p>
              <button
                onClick={refresh}
                className="mt-1 px-4 py-2 text-xs rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white transition-colors"
              >
                Retry
              </button>
            </div>
          )}
          <img
            key={imageUrl}
            src={imageUrl}
            alt="Star chart"
            className={`block h-full w-full object-contain cursor-zoom-in transition-opacity duration-300 ${imageState === 'ready' ? 'opacity-100' : 'opacity-0'}`}
            onLoad={() => setImageState('ready')}
            onError={() => setImageState('error')}
            onClick={() => imageState === 'ready' && setZoomed(true)}
          />
          {imageState === 'ready' && (
            <div className="absolute bottom-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
              <span className="text-[10px] text-gray-500 bg-gray-950/80 px-2 py-1 rounded">Click to zoom</span>
            </div>
          )}
        </div>
      </aside>

      {zoomed && (
        <div
          className="fixed inset-0 z-50 bg-black/90 backdrop-blur-md flex items-center justify-center p-4 animate-fadeIn"
          onClick={() => setZoomed(false)}
          onKeyDown={handleKeyDown}
          tabIndex={0}
        >
          <button
            className="absolute top-4 right-4 text-gray-400 hover:text-white text-2xl transition-colors w-10 h-10 flex items-center justify-center rounded-full bg-gray-900/50 hover:bg-gray-800"
            onClick={() => setZoomed(false)}
          >
            ×
          </button>
          <img
            src={imageUrl}
            alt="Star chart (zoomed)"
            className="max-h-[95vh] max-w-[95vw] object-contain rounded-lg shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          />
          <p className="absolute bottom-4 text-xs text-gray-600">Click anywhere to close · Scroll to zoom (browser native)</p>
        </div>
      )}
    </>
  );
}
