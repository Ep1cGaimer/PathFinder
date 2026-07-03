import type { Coordinate, RoadReport, RouteResponse } from "./types";

export const API_URL = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

async function json<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(body.detail ?? `Request failed (${response.status})`);
  }
  return response.json();
}

export async function recommend(origin: Coordinate, destination: Coordinate): Promise<RouteResponse> {
  return json(await fetch(`${API_URL}/routes/recommend`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ origin, destination }),
  }));
}

export async function geocode(query: string): Promise<Coordinate> {
  return json(await fetch(`${API_URL}/places/geocode?q=${encodeURIComponent(query)}`));
}

export async function nearbyReports(bounds = { min_lat: 12.90, min_lng: 77.50, max_lat: 13.05, max_lng: 77.75 }): Promise<RoadReport[]> {
  const query = new URLSearchParams(Object.entries(bounds).map(([key, value]) => [key, String(value)]));
  return json<{ reports: RoadReport[] }>(await fetch(`${API_URL}/reports?${query}`)).then((data) => data.reports);
}

export async function myReports(token: string): Promise<RoadReport[]> {
  return json<{ reports: RoadReport[] }>(await fetch(`${API_URL}/reports/me`, { headers: { Authorization: `Bearer ${token}` } })).then((data) => data.reports);
}

export async function submitReport(data: FormData, token: string): Promise<RoadReport> {
  return json(await fetch(`${API_URL}/reports`, { method: "POST", headers: { Authorization: `Bearer ${token}` }, body: data }));
}
