import { useSyncExternalStore } from "react";

export type FavoriteWorkspace = { title: string; to: string };

const STORAGE_KEY = "statpro-favorite-workspaces";
const CHANGE_EVENT = "statpro-favorites-changed";
const maximumFavorites = 12;
let cachedSerialized: string | null = null;
let cachedFavorites: FavoriteWorkspace[] = [];

function readFavorites(): FavoriteWorkspace[] {
  try {
    const serialized = localStorage.getItem(STORAGE_KEY) ?? "[]";
    if (serialized === cachedSerialized) return cachedFavorites;
    const parsed: unknown = JSON.parse(serialized);
    cachedSerialized = serialized;
    cachedFavorites = !Array.isArray(parsed) ? [] : parsed.filter((item): item is FavoriteWorkspace => Boolean(
      item && typeof item === "object" && typeof (item as FavoriteWorkspace).title === "string"
        && typeof (item as FavoriteWorkspace).to === "string" && (item as FavoriteWorkspace).to.startsWith("/"),
    )).slice(0, maximumFavorites);
    return cachedFavorites;
  } catch {
    cachedSerialized = null;
    cachedFavorites = [];
    return cachedFavorites;
  }
}

function persistFavorites(favorites: FavoriteWorkspace[]) {
  const serialized = JSON.stringify(favorites.slice(0, maximumFavorites));
  localStorage.setItem(STORAGE_KEY, serialized);
  cachedSerialized = serialized;
  cachedFavorites = favorites.slice(0, maximumFavorites);
  window.dispatchEvent(new Event(CHANGE_EVENT));
}

export function isFavorite(to: string) {
  return readFavorites().some((favorite) => favorite.to === to);
}

export function toggleFavorite(workspace: FavoriteWorkspace) {
  const favorites = readFavorites();
  persistFavorites(favorites.some((favorite) => favorite.to === workspace.to)
    ? favorites.filter((favorite) => favorite.to !== workspace.to)
    : [workspace, ...favorites]);
}

export function removeFavorite(to: string) {
  persistFavorites(readFavorites().filter((favorite) => favorite.to !== to));
}

function subscribe(listener: () => void) {
  const onStorage = (event: StorageEvent) => { if (event.key === STORAGE_KEY) listener(); };
  window.addEventListener(CHANGE_EVENT, listener);
  window.addEventListener("storage", onStorage);
  return () => {
    window.removeEventListener(CHANGE_EVENT, listener);
    window.removeEventListener("storage", onStorage);
  };
}

export function useFavoriteWorkspaces() {
  return useSyncExternalStore(subscribe, readFavorites, () => []);
}
