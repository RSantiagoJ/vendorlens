import { createTheme, type CSSVariablesResolver } from "@mantine/core";

export const theme = createTheme({
  primaryColor: "umgreen",
  primaryShade: 6,
  cursorType: "pointer",
  colors: {
    umblue: [
      "#ebf5ff", "#d5e7fa", "#a4cdf7", "#72b2f6", "#4e9cf5",
      "#3b8ef5", "#3187f6", "#2674dc", "#1b67c4", "#0059ad",
    ],
    ummaroon: [
      "#ffecef", "#f7d8dd", "#ebaeb7", "#e08290", "#d75c6e",
      "#d24559", "#d0394e", "#b92b40", "#a62438", "#92192f",
    ],
    umgreen: [
      "#69E8D7", "#57E5D2", "#34DFC8", "#1FC7B0", "#19A391",
      "#148071", "#179281", "#19A391", "#1DB9A4", "#20CBB4",
    ],
    umyellow: [
      "#fff8e0", "#fff0ca", "#ffdf9a", "#fdcd64", "#fcbe38",
      "#fcb51b", "#fcb006", "#e19a00", "#c88900", "#ad7500",
    ],
    umpink: [
      "#ffeaf0", "#fdd5dd", "#f4a7b8", "#ec7891", "#e5506f",
      "#e1375a", "#e02850", "#c71a41", "#b21139", "#9e0230",
    ],
  },
});

export const resolver: CSSVariablesResolver = (t) => ({
  variables: {
    "--mantine-color-secondary": t.colors!.umblue![6],
  },
  light: {
    "--mantine-color-placeholder": t.colors!.gray![7],
    "--mantine-color-dimmed": t.colors!.gray![7],
  },
  dark: {},
});
