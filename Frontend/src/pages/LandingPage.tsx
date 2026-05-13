import { Link } from "react-router-dom"

export function LandingPage() {
  return (
    <section
      // Fills the viewport below the fixed header (pt-24 = 6rem on <main>).
      className="relative flex h-full flex-col items-center justify-center px-4 text-center"
    >
      <h1 className="text-4xl sm:text-5xl md:text-6xl 2xl:md:text-7xl font-bold tracking-tight text-brand-text leading-[1.05]">
        Your Entire Garage,
        <br />
        <span className="bg-gradient-to-b from-brand-text to-brand-text/55 bg-clip-text text-transparent">
          Digitized.
        </span>
      </h1>

      {/* Decorative divider between hero and subhead:
          horizontal gradient line + three centred dots (the middle one glows). */}
      <div
        aria-hidden="true"
        className="mt-16 mb-14 2xl:mt-16 2xl:mb-12 flex items-center justify-center gap-4"
      >
        <span className="h-px w-20 bg-gradient-to-r from-transparent to-brand-accent/40 sm:w-32" />
        <span className="flex items-center gap-1.5">
          <span className="h-1 w-1 rounded-full bg-brand-accent/40" />
          <span className="h-2 w-2 rounded-full bg-brand-accent shadow-[0_0_12px_rgba(34,197,94,0.8)]" />
          <span className="h-1 w-1 rounded-full bg-brand-accent/40" />
        </span>
        <span className="h-px w-20 bg-gradient-to-l from-transparent to-brand-accent/40 sm:w-32" />
      </div>

      <p className="max-w-2xl text-sm sm:text-base 2xl:text-xl text-brand-text-muted">
        Identify parts with a photo, find your dream car, and access
        step-by-step guides for any make or model. The world&apos;s first truly
        complete AI car companion.
      </p>

      <div className="mt-12 2xl:mt-10 flex flex-col items-center gap-4">
        <Link
          to="/chat"
          // Diagonal-sweep fill on hover, bottom-left → top-right:
          //   - parent: larger, less-round white slab, dark text, overflow-hidden so the overlay clips to the rounded edges
          //   - overlay: brand-accent rectangle, parked OFF the bottom-left corner via (-X, +Y) translate, lightly skewed for character
          //   - on group-hover the overlay slides to (0, 0) — diagonal motion sweeps the fill from bottom-left to top-right
          //   - label: lifted via z-10; colour flips to white on hover
          className="group relative inline-flex items-center justify-center overflow-hidden 2xl:rounded-xl bg-white px-6 py-3 rounded-lg text-sm 2xl:px-8 2xl:py-4 2xl:text-base font-bold text-brand-bg shadow-sm"
        >
          {/* Massive overlay (-inset-32) so the overlay's corners are far outside the button
              at every point in the animation — the user only ever sees a flat skewed SIDE
              sweeping diagonally, never a pointy corner.                                      */}
          <span
            aria-hidden="true"
            className="pointer-events-none absolute -inset-16 -translate-x-full translate-y-full rotate-45 bg-brand-accent transition-transform duration-600 ease-[cubic-bezier(.4,0,.2,1)] group-hover:translate-x-0 group-hover:translate-y-0"
          />
          <span className="relative z-10 transition-colors duration-600 ease-[cubic-bezier(.4,0,.2,1)] group-hover:text-white">
            Explore Features
          </span>
        </Link>
      </div>
    </section>
  )
}
