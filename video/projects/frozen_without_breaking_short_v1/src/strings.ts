import {localizedStringMaps} from './generated_locale_strings';

export type Locale = 'en' | 'es' | 'pt-BR' | 'ja';

export const en = {
  'brand.eyebrow': 'CAPITAL CHRONICLE · LABOR',
  'brand.slug': 'FROZEN WITHOUT BREAKING',
  'hook.jobs': 'JOBS FELL.',
  'hook.unemployment': 'UNEMPLOYMENT FELL.',
  'hook.question': 'How can both be true?',
  'paradox.payroll.label': 'PAYROLL EMPLOYMENT',
  'paradox.payroll.value': '−23K',
  'paradox.payroll.period': 'JULY 2026 · PRELIMINARY',
  'paradox.rate.label': 'UNEMPLOYMENT RATE',
  'paradox.rate.value': '4.1%',
  'paradox.rate.period': 'JULY 2026 · HOUSEHOLD SURVEY',
  'paradox.caveat': 'The one-month payroll move does not clear BLS’s usual 90% significance threshold.',
  'arithmetic.kicker': 'THE RATE’S ARITHMETIC',
  'arithmetic.subtitle.1': 'Three monthly estimates.',
  'arithmetic.subtitle.2': 'No story about motive.',
  'arithmetic.employment.label': 'HOUSEHOLD EMPLOYMENT',
  'arithmetic.employment.value': '−87K',
  'arithmetic.laborForce.label': 'LABOR FORCE',
  'arithmetic.laborForce.value': '−264K',
  'arithmetic.unemployed.label': 'UNEMPLOYED',
  'arithmetic.unemployed.value': '−178K',
  'arithmetic.result.before': 'THE RATE FELL',
  'arithmetic.result.after': 'WITHOUT MORE EMPLOYMENT',
  'arithmetic.caveat': 'Monthly CPS estimates are noisy. Stock changes do not identify individual motives or flows.',
  'doors.kicker': 'NOW WATCH THE DOORS',
  'doors.subtitle.1': 'Movement cooled on',
  'doors.subtitle.2': 'all three thresholds.',
  'doors.then': 'FEB 2020',
  'doors.now': 'JUN 2026',
  'doors.hires': 'HIRES',
  'doors.quits': 'QUITS',
  'doors.layoffs': 'LAYOFFS / DISCHARGES',
  'doors.hires.then': '3.9%',
  'doors.hires.now': '3.4%',
  'doors.quits.then': '2.3%',
  'doors.quits.now': '2.0%',
  'doors.layoffs.then': '1.3%',
  'doors.layoffs.now': '1.1%',
  'doors.thesis.1': 'LOW HIRE.',
  'doors.thesis.2': 'LOW QUIT.',
  'doors.thesis.3': 'LOW FIRE.',
  'doors.caveat': 'Low layoffs do not, by themselves, prove a healthy market.',
  'engine.kicker': 'THE ECONOMY STILL MOVED',
  'engine.demand.label': 'REAL FINAL SALES TO\nPRIVATE DOMESTIC PURCHASERS',
  'engine.demand.value': '+3.9%',
  'engine.demand.note': 'Q2 · ANNUALIZED · ADVANCE ESTIMATE',
  'engine.output.label': 'OUTPUT',
  'engine.output.value': '+2.5%',
  'engine.hours.label': 'HOURS',
  'engine.hours.value': '+0.2%',
  'engine.sector.label': 'NONFARM BUSINESS SECTOR',
  'engine.productivity.label': 'PRODUCTIVITY',
  'engine.productivity.value': '+2.2%',
  'engine.productivity.note': 'more output per hour',
  'engine.period': 'Q2 · YEAR OVER YEAR · PRELIMINARY',
  'engine.caveat': 'The data measure a gap. They do not prove AI caused it.',
  'resolve.motion': 'THE ECONOMY CAN KEEP MOVING',
  'resolve.stasis': 'WHILE WORKERS CAN’T.',
  'resolve.notBreak': 'NOT A BROAD LAYOFF COLLAPSE',
  'resolve.freeze': 'A LOW-HIRE · LOW-QUIT\nLOW-FIRE FREEZE',
  'resolve.watch': 'LESS ROOM FOR WHATEVER COMES NEXT',
  'source.bls.employment': 'BLS · EMPLOYMENT SITUATION · JULY 2026',
  'source.bls.cps': 'BLS · HOUSEHOLD SURVEY · JULY 2026',
  'source.bls.jolts': 'BLS JOLTS · JUNE 2026',
  'source.bls.productivity': 'BLS PRODUCTIVITY + BEA · Q2 2026',
  'source.illustrative': 'ILLUSTRATIVE FOOTAGE · NOT MEASURED WORKERS OR FACILITIES',
  'source.analysis': 'CAPITAL CHRONICLE ANALYSIS',
  'caption.01': 'How can jobs fall—and unemployment fall too?',
  'caption.02': 'July payrolls fell 23,000. That preliminary move is too small to clear BLS’s usual significance threshold.',
  'caption.03': 'The household survey gives the arithmetic: employment fell 87,000; the labor force, 264,000; the number unemployed, 178,000.',
  'caption.04': 'So the rate fell to 4.1 percent without more household employment.',
  'caption.05': 'Now watch the doors. June hiring, quitting, and layoffs and discharges were all below February 2020 rates: 3.4, 2.0, and 1.1 percent.',
  'caption.06': 'Low hire. Low quit. Low fire.',
  'caption.07': 'Yet real final sales to private domestic purchasers grew at a 3.9 percent annualized rate in the second quarter.',
  'caption.08': 'Nonfarm-business output rose 2.5 percent from a year earlier on just 0.2 percent more hours. Productivity rose 2.2 percent—preliminary, and not proof that AI caused it.',
  'caption.09': 'The economy can keep moving while workers can’t.',
  'caption.10': 'This isn’t a broad layoff collapse. It’s a freeze—with less room for whatever comes next.',
} as const;

export type StringKey = keyof typeof en;
export type StringMap = Record<StringKey, string>;

// Add governed translations here. English remains the safe fallback until each map is complete.
export const localeStrings: Partial<Record<Locale, StringMap>> = {
  en,
  ...localizedStringMaps,
};

export const localeLayout: Record<Locale, {
  fontScale: number;
  headlineWidth: number;
  captionWidth: number;
  lineHeight: number;
}> = {
  en: {fontScale: 1, headlineWidth: 900, captionWidth: 860, lineHeight: 1.02},
  es: {fontScale: 0.91, headlineWidth: 930, captionWidth: 900, lineHeight: 1.06},
  'pt-BR': {fontScale: 0.89, headlineWidth: 940, captionWidth: 900, lineHeight: 1.06},
  ja: {fontScale: 0.92, headlineWidth: 900, captionWidth: 880, lineHeight: 1.14},
};

export const stringsFor = (locale: Locale): StringMap => localeStrings[locale] ?? en;
