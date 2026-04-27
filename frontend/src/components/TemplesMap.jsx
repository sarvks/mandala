import { useEffect, useRef } from "react";

// India bounding box for initial view
const INDIA_CENTER = [22.9, 80.9];
const INDIA_ZOOM = 5;

export default function TemplesMap({ temples, deityMap = {}, onTempleClick }) {
  const containerRef = useRef(null);
  const mapRef = useRef(null);
  const markerLayerRef = useRef(null);

  // Mount the map once
  useEffect(() => {
    const L = window.L;
    if (!L || !containerRef.current) return;
    if (mapRef.current) return;
    const map = L.map(containerRef.current, {
      center: INDIA_CENTER,
      zoom: INDIA_ZOOM,
      scrollWheelZoom: false,
      zoomControl: true,
      attributionControl: true,
    });
    L.tileLayer(
      "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
      {
        maxZoom: 18,
        attribution:
          '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
      }
    ).addTo(map);
    mapRef.current = map;
    markerLayerRef.current = L.layerGroup().addTo(map);

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Re-render markers whenever temples change
  useEffect(() => {
    const L = window.L;
    const map = mapRef.current;
    const layer = markerLayerRef.current;
    if (!L || !map || !layer) return;
    layer.clearLayers();

    // Group by state
    const byState = {};
    temples
      .filter((t) => typeof t.lat === "number" && typeof t.lng === "number")
      .forEach((t) => {
        (byState[t.state] ||= []).push(t);
      });

    const allBounds = [];

    Object.entries(byState).forEach(([state, group]) => {
      // If multiple temples in same state -> cluster marker at their centroid
      if (group.length > 1) {
        const lat =
          group.reduce((s, t) => s + t.lat, 0) / group.length;
        const lng =
          group.reduce((s, t) => s + t.lng, 0) / group.length;
        const count = group.length;
        const icon = L.divIcon({
          className: "mandala-cluster",
          html: `<div class="mcluster-inner"><span>${count}</span></div>`,
          iconSize: [44, 44],
          iconAnchor: [22, 22],
        });
        const marker = L.marker([lat, lng], { icon });
        const listHtml = group
          .map((t) => {
            const d = deityMap[t.deity_ids?.[0]];
            return `
            <li>
              <button data-temple-id="${t.id}" class="mcluster-item">
                <span class="mcluster-name">${t.name}</span>
                <span class="mcluster-city">${t.city}${d ? " · " + d.name : ""}</span>
              </button>
            </li>`;
          })
          .join("");
        marker.bindPopup(
          `<div class="mcluster-popup">
            <div class="mcluster-title">${state}</div>
            <div class="mcluster-sub">${count} temples</div>
            <ul>${listHtml}</ul>
           </div>`,
          { maxWidth: 320 }
        );
        marker.on("popupopen", (e) => {
          const el = e.popup.getElement();
          if (!el) return;
          el.querySelectorAll(".mcluster-item").forEach((btn) => {
            btn.addEventListener("click", () => {
              const id = btn.getAttribute("data-temple-id");
              const temple = group.find((g) => g.id === id);
              if (temple && onTempleClick) onTempleClick(temple);
            });
          });
        });
        marker.addTo(layer);
        allBounds.push([lat, lng]);
      } else {
        const t = group[0];
        const d = deityMap[t.deity_ids?.[0]];
        const icon = L.divIcon({
          className: "mandala-pin",
          html: `<div class="mpin-inner"></div>`,
          iconSize: [22, 22],
          iconAnchor: [11, 11],
        });
        const marker = L.marker([t.lat, t.lng], { icon });
        marker.bindPopup(
          `<div class="mpin-popup">
             <div class="mpin-name">${t.name}</div>
             <div class="mpin-city">${t.city}, ${t.state}</div>
             ${d ? `<div class="mpin-deity">${d.name}</div>` : ""}
             <button data-temple-id="${t.id}" class="mpin-cta">Open details</button>
           </div>`,
          { maxWidth: 260 }
        );
        marker.on("popupopen", (e) => {
          const el = e.popup.getElement();
          if (!el) return;
          const btn = el.querySelector(".mpin-cta");
          if (btn)
            btn.addEventListener("click", () => onTempleClick && onTempleClick(t));
        });
        marker.addTo(layer);
        allBounds.push([t.lat, t.lng]);
      }
    });

    if (allBounds.length) {
      try {
        map.fitBounds(allBounds, { padding: [40, 40], maxZoom: 7 });
      } catch (_) {}
    }
  }, [temples, deityMap, onTempleClick]);

  return (
    <div
      data-testid="temples-map-container"
      ref={containerRef}
      className="h-[560px] w-full overflow-hidden rounded-2xl border border-stone-200 bg-white"
    />
  );
}
