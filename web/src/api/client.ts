import type { EvidenceResponse, MatchPresentation, NarrativeUpdate, ReplayMessage, ScenarioCatalog } from "./types";

async function readJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status} ${response.statusText}`);
  }
  return (await response.json()) as T;
}

export async function fetchPresentation(scenario: string): Promise<MatchPresentation> {
  return readJson<MatchPresentation>(
    await fetch(`/api/matches/${encodeURIComponent(scenario)}/presentation`),
  );
}

export async function fetchTimeline(scenario: string): Promise<ReplayMessage[]> {
  return readJson<ReplayMessage[]>(
    await fetch(`/api/matches/${encodeURIComponent(scenario)}/timeline`),
  );
}

export async function fetchScenarios(): Promise<string[]> {
  const result = await readJson<ScenarioCatalog>(await fetch("/api/scenarios"));
  return result.scenarios;
}

export async function fetchEvidence(
  scenario: string,
  insightId: string,
): Promise<EvidenceResponse> {
  const path = `/api/matches/${encodeURIComponent(scenario)}/evidence/${encodeURIComponent(
    insightId,
  )}`;
  return readJson<EvidenceResponse>(await fetch(path));
}

export interface ReplayStreamHandlers {
  onMessage: (message: ReplayMessage) => void;
  onComplete: () => void;
  onError: (message: string) => void;
}

export function openReplayStream(
  scenario: string,
  speed: number,
  handlers: ReplayStreamHandlers,
): () => void {
  const source = new EventSource(
    `/api/matches/${encodeURIComponent(scenario)}/stream?speed=${speed}`,
  );

  const consume = (event: MessageEvent<string>) => {
    try {
      handlers.onMessage(JSON.parse(event.data) as ReplayMessage);
    } catch {
      handlers.onError("The replay stream returned an invalid message.");
      source.close();
    }
  };

  source.addEventListener("match_event", consume as EventListener);
  source.addEventListener("tactical_insight", consume as EventListener);
  source.addEventListener("replay_complete", () => {
    handlers.onComplete();
    source.close();
  });
  source.onerror = () => {
    if (source.readyState === EventSource.CLOSED) {
      return;
    }
    handlers.onError("Live replay connection interrupted.");
  };

  return () => source.close();
}

export function openNarrativeStream(
  scenario: string,
  audience: NarrativeUpdate["audience"],
  handlers: {
    onNarrative: (message: NarrativeUpdate) => void;
    onError: (message: string) => void;
  },
): () => void {
  const source = new EventSource(
    `/api/matches/${encodeURIComponent(scenario)}/narratives/stream?audience=${encodeURIComponent(audience)}`,
  );
  let active = true;
  source.addEventListener("narrative_update", (event: MessageEvent<string>) => {
    if (!active) return;
    try {
      const message = JSON.parse(event.data) as NarrativeUpdate;
      if (message.audience !== audience || !message.insight_id || !message.text) {
        throw new Error("Invalid narrative update");
      }
      handlers.onNarrative(message);
    } catch {
      handlers.onError("The narrative stream returned an invalid message.");
      source.close();
    }
  });
  source.addEventListener("narrative_complete", () => source.close());
  source.onerror = () => {
    if (active && source.readyState !== EventSource.CLOSED) {
      handlers.onError("Narrative stream interrupted; factual replay is unaffected.");
    }
  };
  return () => {
    active = false;
    source.close();
  };
}
