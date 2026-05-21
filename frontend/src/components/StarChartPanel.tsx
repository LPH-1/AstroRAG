import { useMemo, useState } from 'react';

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
    width: '1400',
    height: '1800',
    mag_limit: magLimit.toFixed(1),
    show_dso: String(showDso),
    style: 'mobile',
    t: String(refreshKey),
  });

  return `/starchart?${params.toString()}`;
}

export default function StarChartPanel() {
  const [ra, setRa] = useState(310.0);
  const [dec, setDec] = useState(-17.0);
  const [fov, setFov] = useState(35);
  const [magLimit, setMagLimit] = useState(8.8);
  const [showDso, setShowDso] = useState(true);
  const [refreshKey, setRefreshKey] = useState(1);
  const [imageState, setImageState] = useState<'loading' | 'ready' | 'error'>('loading');

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

  return (
    <aside className="flex h-full min-h-0 flex-col border-t border-gray-800 bg-slate-950 lg:border-l lg:border-t-0">
      <div className="border-b border-slate-800 px-4 py-3">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h2 className="text-sm font-semibold text-slate-100">Star Chart</h2>
            <p className="text-xs text-slate-500">Local atlas renderer on port 8082</p>
          </div>
          <button
            type="button"
            onClick={refresh}
            className="rounded-md border border-cyan-700/70 px-3 py-1.5 text-xs font-medium text-cyan-200 transition-colors hover:border-cyan-500 hover:bg-cyan-950/50"
          >
            Render
          </button>
        </div>
      </div>

      <div className="grid gap-3 border-b border-slate-800 px-4 py-3">
        <div className="flex gap-2 overflow-x-auto pb-1">
          {TARGETS.map((target) => (
            <button
              key={target.name}
              type="button"
              onClick={() => applyTarget(target)}
              className="shrink-0 rounded-md bg-slate-900 px-3 py-1.5 text-xs text-slate-300 ring-1 ring-slate-700 transition-colors hover:bg-slate-800 hover:text-white"
            >
              {target.name}
            </button>
          ))}
        </div>

        <div className="grid grid-cols-2 gap-3">
          <label className="grid gap-1 text-xs text-slate-400">
            RA deg
            <input
              value={ra}
              onChange={(event) => setRa(clampNumber(event.target.value, ra, 0, 360))}
              className="rounded-md border border-slate-700 bg-slate-900 px-2 py-1.5 text-sm text-slate-100 outline-none focus:border-cyan-500"
              inputMode="decimal"
            />
          </label>
          <label className="grid gap-1 text-xs text-slate-400">
            Dec deg
            <input
              value={dec}
              onChange={(event) => setDec(clampNumber(event.target.value, dec, -89, 89))}
              className="rounded-md border border-slate-700 bg-slate-900 px-2 py-1.5 text-sm text-slate-100 outline-none focus:border-cyan-500"
              inputMode="decimal"
            />
          </label>
        </div>

        <label className="grid gap-1 text-xs text-slate-400">
          Field of view: {fov.toFixed(1)} deg
          <input
            type="range"
            min="2"
            max="60"
            step="0.5"
            value={fov}
            onChange={(event) => setFov(Number(event.target.value))}
            className="accent-cyan-500"
          />
        </label>

        <label className="grid gap-1 text-xs text-slate-400">
          Magnitude limit: {magLimit.toFixed(1)}
          <input
            type="range"
            min="4"
            max="10"
            step="0.1"
            value={magLimit}
            onChange={(event) => setMagLimit(Number(event.target.value))}
            className="accent-amber-400"
          />
        </label>

        <label className="flex items-center gap-2 text-xs text-slate-300">
          <input
            type="checkbox"
            checked={showDso}
            onChange={(event) => {
              setShowDso(event.target.checked);
              setImageState('loading');
              setRefreshKey((current) => current + 1);
            }}
            className="h-4 w-4 rounded border-slate-600 bg-slate-900 accent-cyan-500"
          />
          Show deep-sky objects
        </label>
      </div>

      <div className="relative min-h-0 flex-1 overflow-auto bg-black">
        {imageState === 'loading' && (
          <div className="absolute inset-0 z-10 grid place-items-center bg-black/50 text-xs text-slate-400">
            Rendering chart...
          </div>
        )}
        {imageState === 'error' && (
          <div className="absolute inset-0 z-20 grid place-items-center bg-slate-950 px-6 text-center text-sm text-slate-400">
            Start the star chart service at localhost:8082, then render again.
          </div>
        )}
        <img
          key={imageUrl}
          src={imageUrl}
          alt="Generated star chart"
          className="block h-full min-h-[420px] w-full object-contain"
          onLoad={() => setImageState('ready')}
          onError={() => setImageState('error')}
        />
      </div>
    </aside>
  );
}
