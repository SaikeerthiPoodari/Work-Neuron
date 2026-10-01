// Interface languages supported by WorkNeuron. Keep this list limited to
// Indian languages and retain each language's native script for the selector.
export const languages = [
  { code: "en", label: "English", locale: "en-IN" },
  { code: "te", label: "తెలుగు", locale: "te-IN" },
  { code: "hi", label: "हिन्दी", locale: "hi-IN" },
  { code: "kn", label: "ಕನ್ನಡ", locale: "kn-IN" },
  { code: "ta", label: "தமிழ்", locale: "ta-IN" },
  { code: "ml", label: "മലയാളം", locale: "ml-IN" },
  { code: "mr", label: "मराठी", locale: "mr-IN" },
  { code: "bn", label: "বাংলা", locale: "bn-IN" },
  { code: "gu", label: "ગુજરાતી", locale: "gu-IN" },
  { code: "pa", label: "ਪੰਜਾਬੀ", locale: "pa-IN" },
  { code: "or", label: "ଓଡ଼ିଆ", locale: "or-IN" },
  { code: "as", label: "অসমীয়া", locale: "as-IN" },
  { code: "ur", label: "اُردُو", locale: "ur-IN" },
  { code: "sa", label: "संस्कृतम्", locale: "sa-IN" },
  { code: "ne", label: "नेपाली", locale: "ne-IN" },
  { code: "kok", label: "कोंकणी", locale: "kok-IN" },
  { code: "ks", label: "کٲشُر", locale: "ks-IN" },
  { code: "sd", label: "سنڌي", locale: "sd-IN" },
  { code: "mai", label: "मैथिली", locale: "mai-IN" },
  { code: "doi", label: "डोगरी", locale: "doi-IN" },
  { code: "mni", label: "ꯃꯩꯇꯩꯂꯣꯟ", locale: "mni-IN" },
  { code: "brx", label: "बर’", locale: "brx-IN" },
  { code: "sat", label: "ᱥᱟᱱᱛᱟᱲᱤ", locale: "sat-IN" },
];

export const languageLabels = Object.fromEntries(languages.map(({ code, label }) => [code, label]));
