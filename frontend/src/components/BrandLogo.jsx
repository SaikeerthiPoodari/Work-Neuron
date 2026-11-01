import { brandConfig } from "../brand/brandConfig";

const sizes = {
  small: "brand-logo-small",
  compact: "brand-logo-compact",
  medium: "brand-logo-medium",
  large: "brand-logo-large",
};

export default function BrandLogo({ size = "medium", iconOnly = false, tagline = false, className = "" }) {
  const image = iconOnly ? brandConfig.assets.mark : brandConfig.assets.icon;

  return (
    <span className={`brand-logo ${sizes[size] || sizes.medium} ${className}`.trim()}>
      <img className={`brand-logo-icon${iconOnly ? " brand-logo-mark" : ""}`} src={image} alt={iconOnly ? brandConfig.name : ""} aria-hidden={iconOnly ? undefined : "true"} draggable="false" />
      {!iconOnly && (
        <span className="brand-logo-copy">
          <span className="brand-logo-wordmark" aria-label={brandConfig.name}>
            <span className="brand-word-work">Work</span>
            <span className="brand-word-neuron">Neuron</span>
          </span>
          {tagline && <span className="brand-logo-tagline">{brandConfig.tagline}</span>}
        </span>
      )}
    </span>
  );
}
