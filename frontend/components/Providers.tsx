"use client";

import { MantineProvider } from "@mantine/core";
import { theme, resolver } from "@/lib/theme";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <MantineProvider theme={theme} cssVariablesResolver={resolver} forceColorScheme="light">
      {children}
    </MantineProvider>
  );
}
