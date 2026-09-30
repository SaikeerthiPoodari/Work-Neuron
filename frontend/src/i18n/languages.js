export const languages = [
  { code: "en", label: "English", locale: "en-IN", voiceSearch: true }, { code: "te", label: "Telugu", locale: "te-IN", voiceSearch: true },
  { code: "hi", label: "Hindi", locale: "hi-IN", voiceSearch: true }, { code: "ta", label: "Tamil", locale: "ta-IN" },
  { code: "kn", label: "Kannada", locale: "kn-IN" }, { code: "ml", label: "Malayalam", locale: "ml-IN" },
  { code: "mr", label: "Marathi", locale: "mr-IN" }, { code: "bn", label: "Bengali", locale: "bn-IN" },
  { code: "gu", label: "Gujarati", locale: "gu-IN" }, { code: "pa", label: "Punjabi", locale: "pa-IN" },
  { code: "ur", label: "Urdu", locale: "ur-PK" }, { code: "or", label: "Odia", locale: "or-IN" },
  { code: "as", label: "Assamese", locale: "as-IN" }, { code: "ne", label: "Nepali", locale: "ne-NP" },
  { code: "kok", label: "Konkani", locale: "kok-IN" }, { code: "sa", label: "Sanskrit", locale: "sa-IN" },
  { code: "fr", label: "French", locale: "fr-FR" }, { code: "de", label: "German", locale: "de-DE" },
  { code: "es", label: "Spanish", locale: "es-ES" }, { code: "pt", label: "Portuguese", locale: "pt-PT" },
  { code: "ar", label: "Arabic", locale: "ar-SA" }, { code: "zh", label: "Chinese", locale: "zh-CN" },
  { code: "ja", label: "Japanese", locale: "ja-JP" }, { code: "ko", label: "Korean", locale: "ko-KR" },
  { code: "ru", label: "Russian", locale: "ru-RU" }, { code: "it", label: "Italian", locale: "it-IT" },
];

export const languageLabels = Object.fromEntries(languages.map(({ code, label }) => [code, label]));
