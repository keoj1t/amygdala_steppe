type GoldenSpiralProps = {
  className?: string;
  stroke?: string;
  opacity?: number;
};

export function GoldenSpiral({ className, stroke = "#CC5500", opacity = 0.6 }: GoldenSpiralProps) {
  return (
    <svg aria-hidden="true" className={className} viewBox="0 0 1000 618" fill="none" preserveAspectRatio="xMidYMid meet">
      <rect x="1" y="1" width="998" height="616" rx="2" stroke={stroke} strokeWidth="2" opacity={opacity * 0.7} />
      <path d="M618 1V617M618 235H999M382 235V617M382 381H618M528 381V527M528 471H618M472 471V527M472 501H528" stroke={stroke} strokeWidth="2" opacity={opacity * 0.38} />
      <path d="M0 618A618 618 0 0 1 618 0A382 382 0 0 1 1000 382A236 236 0 0 1 764 618A146 146 0 0 1 618 472A90 90 0 0 1 708 382A56 56 0 0 1 764 438" stroke={stroke} strokeWidth="7" strokeLinecap="round" opacity={opacity} />
    </svg>
  );
}
