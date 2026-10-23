# FuelWatch Lanka — Prototype

Standalone React + Vite + Tailwind app for the `fuelwatch_lanka_prototype.tsx`
prototype (real-time petrol station tank monitoring dashboard for Sri Lanka).

It is intentionally self-contained and does **not** touch the Russian
translator app in `../frontend` or `../backend`.

## Run

```bash
cd fuelwatch
npm install          # offline-friendly: all deps are in the npm cache
npm run dev
```

Open: http://127.0.0.1:5174/

Production build / preview:

```bash
npm run build
npm run preview      # serves ./dist
```

## Structure

| Path | Purpose |
| --- | --- |
| `src/App.tsx` | The prototype (copied verbatim from `fuelwatch_lanka_prototype.tsx`) |
| `src/main.tsx` | React entry point |
| `src/index.css` | Tailwind base + slim scrollbars |
| `tailwind.config.js` | Tailwind config, adds the `animate-fadeIn` keyframe the prototype uses |

## The four perspectives

Switch roles from the top nav bar:

1. **Public Driver App** — station list, live tank percentages, EN/SI/TA language switch.
2. **Station Office Monitor** — per-tank gauges, dispenser pump lock, simulation
   controls (sales dispense, bowser delivery, theft/sudden-drop alert) and the event log.
3. **Dealer & Business** — subscription tiers and the 3-year revenue scenario simulator.
4. **National Dashboard** — provincial stock breakdown and emergency allocation directives.

All data is mocked in-component (`initialStations`); there is no backend call.
