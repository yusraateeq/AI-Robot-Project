const BAR_COUNT = 16;

/**
 * LiveLine
 * Ambient waveform that runs along the navbar, suggesting an
 * open call line that's always listening. Pure decoration with
 * intent — it's the one bold visual gesture on the page, kept
 * small and quiet everywhere else.
 */
export default function LiveLine() {
  return (
    <div className="flex h-4 items-center gap-[3px]" aria-hidden="true">
      {Array.from({ length: BAR_COUNT }).map((_, i) => (
        <span
          key={i}
          className="wave-bar w-[2px] rounded-full bg-signal/40"
          style={{
            height: "100%",
            animationDelay: `${(i % 8) * 0.12}s`,
          }}
        />
      ))}
    </div>
  );
}