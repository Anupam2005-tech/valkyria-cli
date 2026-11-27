"use client";

import { useSyncExternalStore } from "react";

export type CursorMode = "default" | "view" | "drag" | "copy" | "link";

export interface ScrollState {
  progress: number;
  section: number; // 0..6 (Hero .. Footer)
  velocity: number;
  scrollY: number;
  direction: "up" | "down";
  cursorMode: CursorMode;
  cursorLabel: string;
}

let state: ScrollState = {
  progress: 0,
  section: 0,
  velocity: 0,
  scrollY: 0,
  direction: "up",
  cursorMode: "default",
  cursorLabel: "",
};

const listeners = new Set<() => void>();

function emit() {
  listeners.forEach((l) => l());
}

export const scrollStore = {
  getState(): ScrollState {
    return state;
  },
  setState(partial: Partial<ScrollState>) {
    state = { ...state, ...partial };
    emit();
  },
  subscribe(listener: () => void) {
    listeners.add(listener);
    return () => {
      listeners.delete(listener);
    };
  },
};

export function useScrollStore<T = ScrollState>(
  selector: (s: ScrollState) => T = (s) => s as unknown as T
): T {
  const snapshot = useSyncExternalStore(
    scrollStore.subscribe,
    scrollStore.getState,
    scrollStore.getState
  );
  return selector(snapshot);
}

