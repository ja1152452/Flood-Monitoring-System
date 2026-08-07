import { useQuery } from '@tanstack/react-query';
import { getLatestReading, getTrend, getReadingHistory, getRateOfRise } from '../api/readings';
import { getActiveAlerts } from '../api/alerts';
import { getSummary } from '../api/analytics';
import { getWeather } from '../api/weather';
import { WaterLevelChart } from '../components/dashboard/WaterLevelChart';
import { LiveCameraFeed } from '../components/dashboard/LiveCameraFeed';
import { SirenAlert } from '../components/dashboard/SirenAlert';
import { FloodBadge } from '../components/ui/Badge';
import { formatDateTime, formatTime, getFloodConfig } from '../utils/floodUtils';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { useReadingsSSE } from '../hooks/useReadingsSSE';
import { useThemeStore } from '../store/themeStore';

const CAMERA_ID = '3b7e2b66-d4d5-4ae9-be3f-1c7c31e5b03f';

function WeatherCard({ weather }) {
  if (!weather) {
    return (
      <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-5 shadow-sm dark:shadow-none h-full">
        <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">
          Weather — Lumban, Laguna
        </div>
        <div className="flex items-center justify-center h-32 text-slate-600 text-sm">
          Loading weather data...
        </div>
      </div>
    );
  }

  const ICON_MAP = {
    'Sunny': '☀️', 'Clear': '🌙', 'Partly cloudy': '⛅', 'Cloudy': '☁️',
    'Overcast': '☁️', 'Mist': '🌫️', 'Fog': '🌫️',
    'Light rain': '🌦️', 'Moderate rain': '🌧️', 'Heavy rain': '⛈️',
    'Thundery outbreaks': '⛈️', 'Patchy rain': '🌦️',
  };

  const icon = Object.entries(ICON_MAP).find(([k]) =>
    weather.description?.toLowerCase().includes(k.toLowerCase())
  )?.[1] || '🌤️';

  const uvLabel = weather.uv <= 2 ? 'Low'
    : weather.uv <= 5 ? 'Moderate'
    : weather.uv <= 7 ? 'High'
    : 'Very High';

  const weatherItems = [
    { icon: '💧', value: `${weather.humidity}%`,      label: 'Humidity' },
    { icon: '🌧',  value: `${weather.rain} mm`,        label: 'Rainfall' },
    { icon: '💨', value: `${weather.wind} kph`,        label: 'Wind Speed' },
    { icon: '🌡',  value: `UV ${weather.uv} · ${uvLabel}`, label: 'UV Index' },
  ];

  return (
    <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-5 shadow-sm dark:shadow-none h-full flex flex-col">
      <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">
        Weather — Lumban, Laguna
      </div>

      <div className="flex items-center gap-4 pb-4 mb-4 border-b border-slate-700">
        <span style={{ fontSize: 40 }}>{icon}</span>
        <div>
          <div className="text-4xl font-semibold text-white">{weather.temp}°C</div>
          <div className="text-sm text-slate-400 mt-1">
            {weather.description} · Feels {weather.feels_like}°C
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 flex-1">
        {weatherItems.map(item => (
          <div
            key={item.label}
            className="bg-slate-900 rounded-xl p-3 flex items-center justify-center gap-3">
            <span style={{ fontSize: 20, width: 24, textAlign: 'center' }}>{item.icon}</span>
            <div>
              <div className="text-sm font-medium text-white">{item.value}</div>
              <div className="text-xs text-slate-500 mt-0.5">{item.label}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function Dashboard() {
  useReadingsSSE(CAMERA_ID);

  const { data: reading } = useQuery({
    queryKey:        ['latest-reading'],
    queryFn:         () => getLatestReading(CAMERA_ID),
    refetchInterval: 5000,
    retry:           1,
  });

  const { data: trend } = useQuery({
    queryKey:        ['trend'],
    queryFn:         () => getTrend(CAMERA_ID),
    refetchInterval: 10000,
    retry:           1,
  });

  const { data: rate } = useQuery({
    queryKey:        ['rate-of-rise'],
    queryFn:         () => getRateOfRise(CAMERA_ID),
    refetchInterval: 10000,
    retry:           1,
  });

  const { data: alerts = [] } = useQuery({
    queryKey:       ['active-alerts'],
    queryFn:        getActiveAlerts,
    refetchInterval: 5000,
  });

  const { data: summary } = useQuery({
    queryKey:       ['summary'],
    queryFn:        getSummary,
    refetchInterval: 15000,
  });

  const { data: historyData } = useQuery({
    queryKey:       ['history', CAMERA_ID],
    queryFn:        () => getReadingHistory(CAMERA_ID, { limit: 48 }),
    refetchInterval: 30000,
  });

  const { data: weather } = useQuery({
    queryKey:       ['weather'],
    queryFn:        getWeather,
    refetchInterval: 300000,
    retry:          1,
  });

  const { isDark } = useThemeStore();
  const level    = reading?.flood_level || 'NORMAL';
  const config   = getFloodConfig(level);
  const wl       = parseFloat(reading?.water_level_m || 0);

  const SEVERITY = ['NORMAL', 'MONITOR', 'ALERT', 'EVACUATION', 'CRITICAL'];
  const activeAlert = alerts.length
    ? alerts.reduce((worst, a) =>
        SEVERITY.indexOf(a.flood_level) > SEVERITY.indexOf(worst.flood_level) ? a : worst
      )
    : null;

  const rateVal   = rate?.rate_per_hour || 0;
  const rateSign  = rateVal > 0 ? '+' : '';
  const rateTrend = rate?.trend || 'STABLE';
  const rateColor = rateTrend === 'RISING' ? 'text-red-400'
    : rateTrend === 'FALLING' ? 'text-green-400'
    : 'text-slate-400';

  const TrendIcon = trend?.trend === 'RISING'
    ? TrendingUp
    : trend?.trend === 'FALLING'
    ? TrendingDown
    : Minus;

  const trendColor = trend?.trend === 'RISING' ? 'text-red-400'
    : trend?.trend === 'FALLING' ? 'text-green-400'
    : 'text-slate-400';

  return (
    <div className="space-y-5">
      <div className="page-header flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-slate-400 text-sm mt-0.5">
            Pagsanjan–Lumban River — Real-time Monitoring
          </p>
        </div>
        <div className="text-xs text-slate-500">
          Last update: {formatDateTime(reading?.captured_at)}
        </div>
      </div>

      {activeAlert && <SirenAlert level={activeAlert.flood_level} />}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

        <div
          className="rounded-2xl p-5 border-2 flex flex-col justify-between"
          style={{
            borderColor:     config.color,
            background:      `linear-gradient(135deg, rgba(5,8,20,0.82) 0%, ${config.color}22 100%)`,
            backdropFilter:  'blur(20px)',
            WebkitBackdropFilter: 'blur(20px)',
            boxShadow:       `0 8px 32px rgba(0,0,0,0.5), 0 0 0 2px ${config.color}55`,
          }}>
          <div>
            <div className="flex items-center gap-2 mb-3">
              {activeAlert && (
                <span className="w-2.5 h-2.5 rounded-full bg-red-500 blink inline-block" />
              )}
              <span className="text-xs font-semibold text-slate-700 dark:text-slate-400 uppercase tracking-wider">
                Flood Status
              </span>
            </div>
            <div className="text-3xl font-bold mb-2" style={{ color: config.color }}>
              {config.label}
            </div>
            {activeAlert && (
              <div className="text-xs text-red-400 font-medium mt-1">
                ⚠ Siren Active — Alerts Dispatched
              </div>
            )}
          </div>
          <div className="mt-4 text-xs text-slate-700 dark:text-slate-500">
            📍 Lumban Bridge · CAM-LUMBAN-01
          </div>
        </div>

        <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-5 shadow-sm dark:shadow-none">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Water Level
            </span>
            <span className="text-xs text-slate-500">{formatTime(reading?.captured_at)}</span>
          </div>
          <div
            className="text-6xl font-bold mb-3"
            style={{ color: config.color }}>
            {wl.toFixed(2)}m
          </div>
          <div className="flex items-center gap-2 mb-3">
            <TrendIcon size={15} className={trendColor} />
            <span className={`text-sm font-medium ${trendColor}`}>
              {trend?.trend || 'STABLE'}
            </span>
            {trend?.delta_m != null && (
              <span className="text-xs text-slate-500">
                ({trend.delta_m > 0 ? '+' : ''}{trend.delta_m?.toFixed(3)}m)
              </span>
            )}
          </div>
          <div className="text-xs text-slate-500">
            Confidence: {reading?.confidence != null
              ? `${(reading.confidence * 100).toFixed(0)}%`
              : '--'}
          </div>
        </div>

        <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-5 shadow-sm dark:shadow-none">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">
            Quick Stats
          </div>
          <div className="grid grid-cols-2 gap-3 mb-3">
            <div className="bg-slate-900 rounded-xl p-3">
              <div className={`text-2xl font-bold ${rateColor}`}>
                {rateSign}{rateVal.toFixed(2)}
                <span className="text-sm font-normal ml-1">m/hr</span>
              </div>
              <div className="text-xs text-slate-500 mt-1">Rate of Rise</div>
            </div>
            <div className="bg-slate-900 rounded-xl p-3">
              <div className={`text-2xl font-bold ${alerts.length > 0 ? 'text-red-400' : 'text-green-400'}`}>
                {alerts.length}
              </div>
              <div className="text-xs text-slate-500 mt-1">Active Alerts</div>
            </div>
          </div>
          <div className="bg-slate-900 rounded-xl p-3 flex items-center justify-between">
            <div>
              <div className="text-sm font-medium text-white">
                {summary?.sos?.pending || 0} Pending SOS
              </div>
              <div className="text-xs text-slate-500 mt-0.5">
                {summary?.sos?.total || 0} total requests
              </div>
            </div>
            <span className="text-2xl">🆘</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2">
          <LiveCameraFeed cameraId={CAMERA_ID} />
        </div>
        <div className="lg:col-span-1">
          <WeatherCard weather={weather} />
        </div>
      </div>

      <WaterLevelChart data={historyData?.data || []} />

      {alerts.length > 0 && (
        <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-5 shadow-sm dark:shadow-none">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">
            Active Alerts
          </h3>
          <div className="space-y-3">
            {alerts.map(alert => {
              const acfg = getFloodConfig(alert.flood_level);
              return (
                <div
                  key={alert.id}
                  className="flex items-center justify-between p-4 rounded-xl border"
                  style={{
                    backgroundColor: acfg.color + '10',
                    borderColor:     acfg.color + '40',
                  }}>
                  <div className="flex items-center gap-3">
                    <span className="w-2 h-2 rounded-full blink" style={{ backgroundColor: acfg.color }} />
                    <div>
                      <div className="text-sm font-medium text-white">{alert.location_name}</div>
                      <div className="text-xs text-slate-500 mt-0.5">
                        {alert.barangay_name} · {formatDateTime(alert.triggered_at)}
                        {alert.siren_active && (
                          <span className="ml-2 text-red-400">🔊 Siren</span>
                        )}
                      </div>
                    </div>
                  </div>
                  <FloodBadge level={alert.flood_level} size="sm" />
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}