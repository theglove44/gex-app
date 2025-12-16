"use client";

import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from "@/components/ui/sheet";
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { AlertCircle, Lightbulb, TrendingUp, TrendingDown, Zap, Anchor, Target } from "lucide-react";

interface HelpPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

export function HelpPanel({ isOpen, onClose }: HelpPanelProps) {
  return (
    <Sheet open={isOpen} onOpenChange={onClose}>
      <SheetContent side="right" className="w-full sm:w-[600px] overflow-y-auto bg-background border-border">
        <SheetHeader className="space-y-3 mb-6">
          <SheetTitle className="text-2xl font-bold">Trading Guide</SheetTitle>
          <SheetDescription className="text-base">
            Learn how to interpret GEX signals and make better trading decisions
          </SheetDescription>
        </SheetHeader>

        <Accordion type="multiple" className="w-full space-y-4">
          {/* Quick Start Section */}
          <AccordionItem value="quick-start" className="border border-border rounded-lg px-4">
            <AccordionTrigger className="hover:no-underline py-4">
              <div className="flex items-center gap-2">
                <Lightbulb className="h-5 w-5 text-amber-500" />
                <span className="font-semibold">Quick Start</span>
                <Badge variant="secondary" className="ml-2">START HERE</Badge>
              </div>
            </AccordionTrigger>
            <AccordionContent className="space-y-4 text-sm leading-relaxed pb-4">
              <p className="font-semibold text-foreground">3-Step Beginner Workflow:</p>

              <div className="space-y-3">
                <div className="flex gap-3">
                  <div className="flex-shrink-0 w-6 h-6 bg-emerald-500 rounded-full flex items-center justify-center text-white text-xs font-bold">1</div>
                  <div>
                    <p className="font-semibold">Check Market Regime</p>
                    <p className="text-xs text-muted-foreground mt-1">Look at the "Market Regime" card. It tells you if volatility will be HIGH or LOW today.</p>
                  </div>
                </div>

                <div className="flex gap-3">
                  <div className="flex-shrink-0 w-6 h-6 bg-emerald-500 rounded-full flex items-center justify-center text-white text-xs font-bold">2</div>
                  <div>
                    <p className="font-semibold">Read the Strategy Signal</p>
                    <p className="text-xs text-muted-foreground mt-1">If a strategy card appears (MEAN_REVERSION, ACCELERATION, or MAGNET_PIN), read the "Trading Approach" section to know what to do.</p>
                  </div>
                </div>

                <div className="flex gap-3">
                  <div className="flex-shrink-0 w-6 h-6 bg-emerald-500 rounded-full flex items-center justify-center text-white text-xs font-bold">3</div>
                  <div>
                    <p className="font-semibold">Identify Key Levels</p>
                    <p className="text-xs text-muted-foreground mt-1">Look at the chart. The green zone shows where price is expected to stay. Red zones are breakout areas.</p>
                  </div>
                </div>
              </div>

              <div className="bg-blue-500/10 border border-blue-500/30 rounded p-3 mt-4">
                <p className="text-xs text-blue-100"><strong>💡 Tip:</strong> Use the Call Wall and Put Wall prices as your support/resistance targets for the day.</p>
              </div>
            </AccordionContent>
          </AccordionItem>

          {/* Understanding GEX Section */}
          <AccordionItem value="understanding-gex" className="border border-border rounded-lg px-4">
            <AccordionTrigger className="hover:no-underline py-4">
              <div className="flex items-center gap-2">
                <Target className="h-5 w-5 text-emerald-500" />
                <span className="font-semibold">Understanding GEX</span>
              </div>
            </AccordionTrigger>
            <AccordionContent className="space-y-4 text-sm leading-relaxed pb-4">
              <div>
                <p className="font-semibold text-foreground mb-2">What is Gamma Exposure?</p>
                <p className="text-xs text-muted-foreground">
                  Gamma Exposure (GEX) measures how much dealers' hedging activity will push the market in a specific direction. When dealers are short gamma (negative GEX), they have to sell into rallies and buy into dips, which amplifies price moves. When dealers are long gamma (positive GEX), they do the opposite, which calms volatility.
                </p>
              </div>

              <div>
                <p className="font-semibold text-foreground mb-2">How Do Dealers Hedge?</p>
                <p className="text-xs text-muted-foreground mb-2">
                  When options traders buy call options, dealers sell them and need to hedge by buying stock. If the stock drops, dealers have to sell their hedge, pushing the price down further. This creates "gamma pressure" that can turn support/resistance levels into magnetic price targets.
                </p>
              </div>

              <div>
                <p className="font-semibold text-foreground mb-2">Why GEX Predicts Price Action</p>
                <p className="text-xs text-muted-foreground">
                  <span className="text-emerald-400">Positive GEX:</span> Price is "sticky" - market makers resist big moves, expect mean reversion.<br/>
                  <span className="text-rose-400">Negative GEX:</span> Price is "slippery" - market makers amplify moves, expect trending behavior.<br/>
                  <span className="text-amber-400">Zero Gamma:</span> The flip point where behavior changes dramatically.
                </p>
              </div>

              <div className="bg-emerald-500/10 border border-emerald-500/30 rounded p-3">
                <p className="text-xs text-emerald-100"><strong>Key Insight:</strong> High positive GEX at resistance = strong support that's hard to break. High negative GEX = price will accelerate through that level.</p>
              </div>
            </AccordionContent>
          </AccordionItem>

          {/* Strategy Signals Section */}
          <AccordionItem value="strategy-signals" className="border border-border rounded-lg px-4">
            <AccordionTrigger className="hover:no-underline py-4">
              <div className="flex items-center gap-2">
                <Zap className="h-5 w-5 text-amber-500" />
                <span className="font-semibold">Strategy Signals</span>
              </div>
            </AccordionTrigger>
            <AccordionContent className="space-y-4 text-sm leading-relaxed pb-4">
              <div className="space-y-4">
                {/* Mean Reversion */}
                <div className="border border-border/50 rounded p-3 space-y-2">
                  <div className="flex items-center gap-2">
                    <div className="h-3 w-3 rounded-full bg-emerald-500"></div>
                    <p className="font-semibold">MEAN REVERSION</p>
                  </div>
                  <p className="text-xs text-muted-foreground mb-2">
                    The market has high positive gamma. Price is confined to a range between the Call Wall (resistance) and Put Wall (support).
                  </p>
                  <div className="space-y-1 text-xs">
                    <p><strong className="text-foreground">What to Do:</strong> Fade breakouts. Sell call spreads at resistance, put spreads at support. Target the midpoint.</p>
                    <p><strong className="text-foreground">Risk Level:</strong> Low - Range is well-defined. Watch for overnight gaps.</p>
                    <p><strong className="text-foreground">Time Horizon:</strong> Intraday to 1-3 days</p>
                  </div>
                </div>

                {/* Acceleration */}
                <div className="border border-border/50 rounded p-3 space-y-2">
                  <div className="flex items-center gap-2">
                    <Zap className="h-3 w-3 text-amber-500" />
                    <p className="font-semibold">ACCELERATION</p>
                  </div>
                  <p className="text-xs text-muted-foreground mb-2">
                    High negative gamma environment. Price will accelerate through levels. Volatility is elevated and directional.
                  </p>
                  <div className="space-y-1 text-xs">
                    <p><strong className="text-foreground">What to Do:</strong> Trade breakouts. Buy straddles/strangles if you expect a big move. Use wide stops.</p>
                    <p><strong className="text-foreground">Risk Level:</strong> High - Volatility can be extreme. Use smaller position sizes.</p>
                    <p><strong className="text-foreground">Time Horizon:</strong> Same day - momentum exhaustion can be rapid</p>
                  </div>
                </div>

                {/* Magnet Pin */}
                <div className="border border-border/50 rounded p-3 space-y-2">
                  <div className="flex items-center gap-2">
                    <Anchor className="h-3 w-3 text-blue-500" />
                    <p className="font-semibold">MAGNET PIN</p>
                  </div>
                  <p className="text-xs text-muted-foreground mb-2">
                    Price is attracted to a major gamma level (wall). Expect consolidation around that strike price into market close.
                  </p>
                  <div className="space-y-1 text-xs">
                    <p><strong className="text-foreground">What to Do:</strong> Sell theta (short options). Avoid directional trades. Target midday/close consolidation.</p>
                    <p><strong className="text-foreground">Risk Level:</strong> Medium - Risk of late-day volatility if the wall breaks.</p>
                    <p><strong className="text-foreground">Time Horizon:</strong> Into market close (typically after 2 PM)</p>
                  </div>
                </div>
              </div>

              <div className="bg-amber-500/10 border border-amber-500/30 rounded p-3">
                <p className="text-xs text-amber-100"><strong>Important:</strong> These signals are based on current gamma structure. If the market rallies or sells off significantly, the levels and signals will change. Always refresh your data.</p>
              </div>
            </AccordionContent>
          </AccordionItem>

          {/* Major Levels Guide */}
          <AccordionItem value="major-levels" className="border border-border rounded-lg px-4">
            <AccordionTrigger className="hover:no-underline py-4">
              <div className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-emerald-500" />
                <span className="font-semibold">Major Levels</span>
              </div>
            </AccordionTrigger>
            <AccordionContent className="space-y-4 text-sm leading-relaxed pb-4">
              <div className="space-y-3">
                <div>
                  <p className="font-semibold text-emerald-400 mb-1">Call Wall (Resistance)</p>
                  <p className="text-xs text-muted-foreground">
                    The strike with the highest positive GEX. This is where dealers have the most resistance to price going higher. It acts like a magnet pulling price toward it. Expect price to struggle or consolidate here.
                  </p>
                </div>

                <div>
                  <p className="font-semibold text-rose-400 mb-1">Put Wall (Support)</p>
                  <p className="text-xs text-muted-foreground">
                    The strike with the most negative GEX (lowest value). Dealers resist price going lower. It acts like a magnet at the bottom. Expect buyers to step in or consolidation here.
                  </p>
                </div>

                <div>
                  <p className="font-semibold text-amber-400 mb-1">Zero Gamma Level (Flip Point)</p>
                  <p className="text-xs text-muted-foreground">
                    The price where total GEX equals zero - where positive gamma (above) meets negative gamma (below). This is a critical inflection point. If price crosses this level, the entire market behavior changes. Above = mean reversion, Below = trend continuation.
                  </p>
                </div>

                <div className="bg-rose-500/10 border border-rose-500/30 rounded p-3">
                  <p className="text-xs text-rose-100"><strong>⚠️ Watch Out:</strong> If price approaches a major level, it will often bounce or consolidate there first. Breaking through a major wall is significant and often marks the start of a new trend.</p>
                </div>
              </div>
            </AccordionContent>
          </AccordionItem>

          {/* Chart Interpretation */}
          <AccordionItem value="chart-reading" className="border border-border rounded-lg px-4">
            <AccordionTrigger className="hover:no-underline py-4">
              <div className="flex items-center gap-2">
                <Target className="h-5 w-5 text-blue-500" />
                <span className="font-semibold">Chart Interpretation</span>
              </div>
            </AccordionTrigger>
            <AccordionContent className="space-y-4 text-sm leading-relaxed pb-4">
              <div className="space-y-3">
                <div>
                  <p className="font-semibold text-foreground mb-2">Reading the Bars</p>
                  <p className="text-xs text-muted-foreground mb-2">
                    <span className="text-emerald-400">Green bars (right side):</span> Positive GEX from call options. Higher = more resistance to price going up.<br/>
                    <span className="text-rose-400">Red bars (left side):</span> Negative GEX from put options. Lower = more pressure for price to go down.<br/>
                    <span className="text-muted-foreground">Longer bars = more significant gamma at that strike.</span>
                  </p>
                </div>

                <div>
                  <p className="font-semibold text-foreground mb-2">Understanding Reference Lines</p>
                  <p className="text-xs text-muted-foreground mb-2">
                    <span className="text-yellow-400">Gold line (Spot Price):</span> Where the market is trading right now.<br/>
                    <span className="text-emerald-400">Green dashed line (Call Wall):</span> Resistance - price struggles to go higher.<br/>
                    <span className="text-rose-400">Red dashed line (Put Wall):</span> Support - price struggles to go lower.<br/>
                    <span className="text-amber-400">Amber dotted line (Zero Gamma):</span> The inflection point where behavior flips.
                  </p>
                </div>

                <div>
                  <p className="font-semibold text-foreground mb-2">Identifying Key Zones</p>
                  <p className="text-xs text-muted-foreground mb-2">
                    <span className="text-emerald-400">Green highlighted zone:</span> Expected trading range. Price is expected to stay here today.<br/>
                    <span className="text-rose-400">Red highlighted zones:</span> Breakout areas. If price reaches here, expect acceleration.<br/>
                    <span className="text-amber-400">Amber zone near Zero Gamma:</span> Transition zone. Price behavior changes here.
                  </p>
                </div>

                <div className="bg-blue-500/10 border border-blue-500/30 rounded p-3">
                  <p className="text-xs text-blue-100"><strong>Pro Tip:</strong> Most of the day, price stays in the green zone (between the walls). Break above the Call Wall or below the Put Wall is a significant event worth paying attention to.</p>
                </div>
              </div>
            </AccordionContent>
          </AccordionItem>

          {/* Weighted Mode */}
          <AccordionItem value="weighted-mode" className="border border-border rounded-lg px-4">
            <AccordionTrigger className="hover:no-underline py-4">
              <div className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-indigo-500" />
                <span className="font-semibold">Weighted Mode</span>
              </div>
            </AccordionTrigger>
            <AccordionContent className="space-y-4 text-sm leading-relaxed pb-4">
              <div>
                <p className="font-semibold text-foreground mb-2">What is Volume Weighting?</p>
                <p className="text-xs text-muted-foreground mb-3">
                  GEX can be shown in two ways:
                </p>
                <div className="space-y-2 text-xs mb-3">
                  <p><strong className="text-emerald-400">Standard GEX:</strong> Total gamma at each strike, regardless of volume.</p>
                  <p><strong className="text-indigo-400">Volume-Weighted GEX:</strong> GEX adjusted by how much trading is happening at that strike.</p>
                </div>
              </div>

              <div>
                <p className="font-semibold text-foreground mb-2">When to Use Each Mode</p>
                <p className="text-xs text-muted-foreground mb-2">
                  <strong className="text-emerald-400">Use Standard Mode for:</strong> Long-term support/resistance, end-of-day analysis, institutional positioning.
                </p>
                <p className="text-xs text-muted-foreground mb-2">
                  <strong className="text-indigo-400">Use Weighted Mode for:</strong> Intraday trading, finding where traders are actively positioned RIGHT NOW, identifying surprises.
                </p>
              </div>

              <div>
                <p className="font-semibold text-foreground mb-2">Interpretation Differences</p>
                <p className="text-xs text-muted-foreground">
                  In standard mode, a level might have huge GEX but low volume (old positioning). In weighted mode, it will appear less important. Weighted mode helps you find what traders actually care about TODAY.
                </p>
              </div>

              <div className="bg-indigo-500/10 border border-indigo-500/30 rounded p-3">
                <p className="text-xs text-indigo-100"><strong>Recommendation:</strong> Start with Standard mode to learn. Switch to Weighted mode intraday if the market is doing something unexpected.</p>
              </div>
            </AccordionContent>
          </AccordionItem>

          {/* Market Regime */}
          <AccordionItem value="market-regime" className="border border-border rounded-lg px-4">
            <AccordionTrigger className="hover:no-underline py-4">
              <div className="flex items-center gap-2">
                <AlertCircle className="h-5 w-5 text-purple-500" />
                <span className="font-semibold">Market Regime</span>
              </div>
            </AccordionTrigger>
            <AccordionContent className="space-y-4 text-sm leading-relaxed pb-4">
              <div className="space-y-3">
                <div>
                  <p className="font-semibold text-emerald-400 mb-1">POSITIVE GAMMA Environment</p>
                  <p className="text-xs text-muted-foreground mb-2">
                    Total GEX is high and positive (above $1 billion).
                  </p>
                  <div className="text-xs space-y-1 bg-emerald-500/5 p-2 rounded border border-emerald-500/20">
                    <p><strong>Characteristics:</strong></p>
                    <ul className="list-disc list-inside space-y-1">
                      <li>Volatility is suppressed - big moves are hard</li>
                      <li>Mean reversion is strong - price bounces off walls</li>
                      <li>Safe environment for selling options</li>
                      <li>Breakouts often fail</li>
                    </ul>
                  </div>
                </div>

                <div>
                  <p className="font-semibold text-rose-400 mb-1">NEGATIVE GAMMA Environment</p>
                  <p className="text-xs text-muted-foreground mb-2">
                    Total GEX is negative or very low.
                  </p>
                  <div className="text-xs space-y-1 bg-rose-500/5 p-2 rounded border border-rose-500/20">
                    <p><strong>Characteristics:</strong></p>
                    <ul className="list-disc list-inside space-y-1">
                      <li>Volatility is elevated - big moves happen fast</li>
                      <li>Momentum persists - price accelerates through levels</li>
                      <li>Risky environment for selling options</li>
                      <li>Breakouts are often successful</li>
                    </ul>
                  </div>
                </div>

                <div>
                  <p className="font-semibold text-amber-400 mb-1">TRANSITIONAL States</p>
                  <p className="text-xs text-muted-foreground">
                    When GEX is near zero or changing sign rapidly. This is when the market structure is shifting. Be extra careful as old support/resistance levels may no longer work.
                  </p>
                </div>

                <div className="bg-purple-500/10 border border-purple-500/30 rounded p-3">
                  <p className="text-xs text-purple-100"><strong>Key Takeaway:</strong> Positive gamma = fade breakouts. Negative gamma = trade breakouts. Always know what regime you're in!</p>
                </div>
              </div>
            </AccordionContent>
          </AccordionItem>
        </Accordion>

        <div className="mt-8 p-4 bg-muted rounded-lg border border-border">
          <p className="text-xs text-muted-foreground">
            <strong>Need help?</strong> Each section in this guide can be expanded by clicking on it. Keep this panel open while you trade to reference quickly!
          </p>
        </div>
      </SheetContent>
    </Sheet>
  );
}
