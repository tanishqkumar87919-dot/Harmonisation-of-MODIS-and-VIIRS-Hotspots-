'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';

interface FixtureContextType {
  isFixtureMode: boolean;
  toggleFixtureMode: () => void;
  setFixtureMode: (value: boolean) => void;
}

const FixtureContext = createContext<FixtureContextType>({
  isFixtureMode: false,
  toggleFixtureMode: () => {},
  setFixtureMode: () => {},
});

export function FixtureProvider({ children }: { children: React.ReactNode }) {
  const [isFixtureMode, setIsFixtureMode] = useState<boolean>(false);

  useEffect(() => {
    // Check localStorage if available
    try {
      const stored = localStorage.getItem('modis_viirs_fixture_mode');
      if (stored === 'true') {
        setIsFixtureMode(true);
      }
    } catch {
      // storage disabled
    }
  }, []);

  const toggleFixtureMode = () => {
    setIsFixtureMode((prev) => {
      const next = !prev;
      try {
        localStorage.setItem('modis_viirs_fixture_mode', String(next));
      } catch {
        // storage disabled
      }
      return next;
    });
  };

  const setFixtureMode = (value: boolean) => {
    setIsFixtureMode(value);
    try {
      localStorage.setItem('modis_viirs_fixture_mode', String(value));
    } catch {
      // storage disabled
    }
  };

  return (
    <FixtureContext.Provider value={{ isFixtureMode, toggleFixtureMode, setFixtureMode }}>
      {children}
    </FixtureContext.Provider>
  );
}

export function useFixtureMode() {
  return useContext(FixtureContext);
}
