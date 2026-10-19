import type { SourceActionDetails } from "../domain/sourceActionDetails";

interface SourceActionDetailsPanelProps {
  details: SourceActionDetails;
  onClose: () => void;
}

export function SourceActionDetailsPanel({ details, onClose }: SourceActionDetailsPanelProps) {
  return (
    <section className="key-moment-details" aria-label="Recorded event analysis">
      <div className="key-moment-details-header">
        <div>
          <span className="key-moment-details-eyebrow">Evidence · recorded event</span>
          <h3>{details.heading}</h3>
        </div>
        <button
          className="key-moment-details-close"
          type="button"
          onClick={onClose}
          aria-label="Close recorded event analysis"
        >
          ×
        </button>
      </div>
      <dl className="key-moment-fact-list">
        {details.facts.map((fact) => (
          <div className="key-moment-fact" key={fact.label}>
            <dt>{fact.label}</dt>
            <dd>{fact.value}</dd>
          </div>
        ))}
      </dl>
      <p className="key-moment-details-note">{details.qualification}</p>
    </section>
  );
}
