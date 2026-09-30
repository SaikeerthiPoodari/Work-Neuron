import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { useEffect, useMemo, useRef } from "react";
import { MapContainer, Marker, Popup, TileLayer, useMap } from "react-leaflet";
import { Link } from "react-router-dom";
import { useI18n } from "../i18n/I18nContext";

const jobIcon = L.divIcon({
  className: "job-marker",
  html: '<span aria-hidden="true" style="display:block;width:18px;height:18px;border-radius:50%;background:#2563eb;border:3px solid #fff;box-shadow:0 1px 6px #0f172a88"></span>',
  iconSize: [24, 24],
  iconAnchor: [12, 12],
});
const workerIcon = L.divIcon({
  className: "worker-marker",
  html: '<span aria-hidden="true" style="display:block;width:20px;height:20px;border-radius:50%;background:#f97316;border:4px solid #fff;box-shadow:0 1px 7px #0f172a99"></span>',
  iconSize: [28, 28],
  iconAnchor: [14, 14],
});

export const hasCoordinates = (item) => {
  if (item?.latitude == null || item?.longitude == null || item.latitude === "" || item.longitude === "") return false;
  const latitude = Number(item.latitude);
  const longitude = Number(item.longitude);
  return Number.isFinite(latitude) && Number.isFinite(longitude) && Math.abs(latitude) <= 90 && Math.abs(longitude) <= 180;
};

function MapViewport({ jobs, workerPosition, selectedJob, markerRefs }) {
  const map = useMap();
  const selectedKey = selectedJob?.id;
  useEffect(() => {
    if (selectedJob && hasCoordinates(selectedJob)) {
      const point = [Number(selectedJob.latitude), Number(selectedJob.longitude)];
      map.flyTo(point, Math.max(map.getZoom(), 13), { duration: 0.35 });
      markerRefs.current[selectedJob.id]?.openPopup();
      return;
    }
    const points = jobs.filter(hasCoordinates).map((job) => [Number(job.latitude), Number(job.longitude)]);
    if (workerPosition && hasCoordinates({ latitude: workerPosition[0], longitude: workerPosition[1] })) points.push(workerPosition);
    if (points.length > 1) map.fitBounds(L.latLngBounds(points), { padding: [36, 36], maxZoom: 14 });
    else if (points.length === 1) map.setView(points[0], 13);
  }, [jobs, workerPosition, selectedKey, map, markerRefs]);
  return null;
}

export default function JobMap({ jobs, center, selectedJobId, onSelect }) {
  const { t } = useI18n();
  const markerRefs = useRef({});
  const markers = useMemo(() => jobs.filter(hasCoordinates), [jobs]);
  const unavailable = useMemo(() => jobs.filter((job) => !hasCoordinates(job)), [jobs]);
  const workerPosition = hasCoordinates({ latitude: center?.[0], longitude: center?.[1] })
    ? [Number(center[0]), Number(center[1])]
    : null;
  const selected = markers.find((job) => job.id === selectedJobId);
  const mapCenter = workerPosition || (markers[0] ? [Number(markers[0].latitude), Number(markers[0].longitude)] : null);

  if (!mapCenter) return <div className="flex h-80 items-center justify-center rounded-2xl bg-slate-100 p-6 text-center text-sm text-slate-500">{t("noMapJobs")}</div>;
  return <div className="space-y-4">
    <div className="relative overflow-hidden rounded-2xl ring-1 ring-slate-200">
      <MapContainer center={mapCenter} zoom={12} scrollWheelZoom className="h-[28rem] w-full sm:h-[34rem]">
        <TileLayer attribution='&copy; OpenStreetMap contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        {workerPosition && <Marker position={workerPosition} icon={workerIcon} zIndexOffset={1000}><Popup><strong>{t("yourLocation")}</strong></Popup></Marker>}
        {markers.map((job) => <Marker
          key={`job-${job.id}`}
          position={[Number(job.latitude), Number(job.longitude)]}
          icon={jobIcon}
          ref={(marker) => { if (marker) markerRefs.current[job.id] = marker; else delete markerRefs.current[job.id]; }}
          eventHandlers={{ click: () => onSelect(job.id) }}
        ><Popup eventHandlers={{ remove: () => {} }}><div className="min-w-[220px] space-y-1 text-sm">
          <p className="font-black text-slate-900">{job.title}</p>
          <p className="text-slate-600">{t("clientLabel")}: {job.client_name || job.owner_email || t("clientLabel")}</p>
          <p className="text-slate-600">{job.location || job.location_city || t("localJob")}</p>
          {job.distance_km != null && <p className="text-slate-600">{job.distance_km} km {t("away")}</p>}
          <p className="text-slate-600">{job.job_type?.replaceAll("_", " ")}{job.category ? ` · ${job.category}` : ""}</p>
          {job.budget != null && <p className="font-bold text-emerald-700">₹{job.budget}</p>}
          <Link className="mt-2 inline-block rounded-lg bg-blue-600 px-3 py-2 font-bold text-white" to={`/tasks/${job.id}`}>{t("viewDetails")}</Link>
          <a className="ml-2 inline-block font-bold text-brand" target="_blank" rel="noreferrer" href={`https://www.google.com/maps/dir/?api=1&destination=${Number(job.latitude)},${Number(job.longitude)}`}>{t("directions")}</a>
        </div></Popup></Marker>)}
        <MapViewport jobs={markers} workerPosition={workerPosition} selectedJob={selected} markerRefs={markerRefs} />
      </MapContainer>
      <div className="absolute bottom-3 left-3 z-[1000] flex gap-3 rounded-lg bg-white/95 px-3 py-2 text-xs font-semibold shadow" aria-label={t("mapLegend")}>
        <span className="flex items-center gap-2"><i className="h-3 w-3 rounded-full bg-orange-500" />{t("yourLocation")}</span>
        <span className="flex items-center gap-2"><i className="h-3 w-3 rounded-full bg-blue-600" />{t("jobLocation")}</span>
      </div>
    </div>
    {unavailable.length > 0 && <section className="rounded-2xl border border-amber-200 bg-amber-50 p-4" aria-labelledby="unmapped-jobs-heading">
      <h3 id="unmapped-jobs-heading" className="font-bold text-amber-950">{t("locationUnavailableJobs")} ({unavailable.length})</h3>
      <ul className="mt-2 divide-y divide-amber-200">{unavailable.map((job) => <li key={`unmapped-${job.id}`} className={`flex flex-wrap items-center justify-between gap-2 py-3 ${selectedJobId === job.id ? "font-semibold" : ""}`}>
        <button className="text-left text-slate-900 hover:text-brand" onClick={() => onSelect(job.id)}>{job.title}<span className="ml-2 text-sm text-slate-600">· {job.owner_email || t("client")}</span></button>
        <span className="text-sm text-amber-900">{t("locationUnavailable")}</span>
      </li>)}</ul>
    </section>}
  </div>;
}
