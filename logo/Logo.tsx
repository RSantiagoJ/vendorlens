import Image from "next/image";
import umassLogo from "./umass-logo.png";

interface Props {
  width?: number;
  className?: string;
}

export function Logo({ width = 60, ...props }: Props) {
  return (
    <Image
      src={umassLogo}
      alt="University of Massachusetts logo"
      width={width}
      priority
      {...props}
    />
  );
}
