'use client';

import React, { createContext, useContext, useState, useCallback } from 'react';
import { Locale, defaultLocale, formatMessage } from './config';

interface I18nContextType {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: string) => string;
}

const I18nContext = createContext<I18nContextType | undefined>(undefined);

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(defaultLocale);

  const setLocale = useCallback((newLocale: Locale) => {
    setLocaleState(newLocale);
    // Persist to localStorage
    if (typeof window !== 'undefined') {
      localStorage.setItem('muset-locale', newLocale);
    }
  }, []);

  const t = useCallback(
    (key: string) => {
      return formatMessage(locale, key);
    },
    [locale]
  );

  // Load locale from localStorage on mount
  React.useEffect(() => {
    if (typeof window !== 'undefined') {
      const savedLocale = localStorage.getItem('muset-locale') as Locale;
      if (savedLocale && (savedLocale === 'zh' || savedLocale === 'en')) {
        setLocaleState(savedLocale);
      }
    }
  }, []);

  return (
    <I18nContext.Provider value={{ locale, setLocale, t }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n() {
  const context = useContext(I18nContext);
  if (!context) {
    throw new Error('useI18n must be used within I18nProvider');
  }
  return context;
}
