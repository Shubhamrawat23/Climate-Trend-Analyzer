import { MapContainer, TileLayer, Marker, Popup, useMapEvents } from "react-leaflet";
import "leaflet/dist/leaflet.css";

function MapClickHandler({ onSelect }) {
  useMapEvents({
    click(event) {
      const { lat, lng } = event.latlng;
      onSelect([lat, lng]);
    },
  });

  return null;
}

export default function MapPicker({ position, onSelect }) {
  return (
    <div className="h-72 w-full overflow-hidden rounded-lg border border-gray-300">
      <MapContainer
        center={position || [20, 0]}
        zoom={position ? 8 : 2}
        style={{ height: "100%", width: "100%" }}
      >
        <TileLayer
          url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />

        <MapClickHandler onSelect={onSelect} />

        {position && (
          <Marker position={position}>
            <Popup>Selected location</Popup>
          </Marker>
        )}
      </MapContainer>
    </div>
  );
}