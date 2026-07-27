import { NextUIProvider } from '@nextui-org/react';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <NextUIProvider>
          <main className="dark bg-background text-foreground">
            {children}
          </main>
        </NextUIProvider>
      </body>
    </html>
  );
}
