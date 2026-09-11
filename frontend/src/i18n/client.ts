"use client";

import i18next from "i18next";
import { initReactI18next } from "react-i18next";
import { resources } from "./resources";

if (!i18next.isInitialized) {
  void i18next.use(initReactI18next).init({
    resources,
    lng: "en",
    fallbackLng: "en",
    interpolation: { escapeValue: false }
  });
}

export { i18next };
