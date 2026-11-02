import { useI18n } from "../i18n/I18nContext";

export default function GlobalLanguageSwitcher() {
  const { language, setLanguage, availableLanguages, t } = useI18n();
  return <label className="global-language-switcher" htmlFor="global-language"><span aria-hidden="true">🌐</span><span className="sr-only">{t("interfaceLanguage")}</span><select id="global-language" aria-label={t("interfaceLanguage")} value={language} onChange={(event) => setLanguage(event.target.value)}>{availableLanguages.map((item) => <option value={item.code} key={item.code}>{item.label}</option>)}</select></label>;
}
