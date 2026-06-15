import Image from "next/image";
import institutionLogo from "./institution-logo.png";

interface Props {
  width?: number;
  className?: string;
}

export function Logo({ width = 60, ...props }: Props) {
  return (
    <Image
      src={institutionLogo}
      alt="Institution logo"
      width={width}
      priority
      {...props}
    />
  );
}
