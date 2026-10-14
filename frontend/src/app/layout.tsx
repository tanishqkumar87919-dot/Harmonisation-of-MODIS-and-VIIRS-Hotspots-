import type { Metadata } from 'next';
import './globals.css';
import { FixtureProvider } from '@/lib/fixtures/FixtureContext';
import { AppShell } from '@/components/layout/AppShell';

export const metadata: Metadata = {
  title: 'Harmonisation of MODIS and VIIRS Hotspots',
  description: 'Scientific Geospatial Workflow & Cross-Sensor Active-Fire Harmonisation Platform',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-slate-950 text-slate-100">
        <FixtureProvider>
          <AppShell>{children}</AppShell>
        </FixtureProvider>
      </body>
    </html>
  );
}
