/**
 * Weighted Mode Utility Functions
 *
 * Provides information and context for weighted vs standard GEX views.
 * Helps beginners understand when to use each mode.
 */

/**
 * Represents the two GEX view modes
 */
export enum ViewMode {
    STANDARD = "STANDARD",
    WEIGHTED = "WEIGHTED"
}

/**
 * Get label for current view mode
 *
 * @param isWeightedMode - Whether weighted mode is active
 * @returns Human-readable mode label
 */
export function getModeLabel(isWeightedMode: boolean): string {
    return isWeightedMode ? "Volume-Weighted View" : "Standard GEX View";
}

/**
 * Get tooltip explanation for current mode
 *
 * Explains what data each mode displays
 *
 * @param isWeightedMode - Whether weighted mode is active
 * @returns Tooltip explanation string
 */
export function getModeTooltip(isWeightedMode: boolean): string {
    if (isWeightedMode) {
        return "Shows GEX weighted by trading volume - highlights current dealer activity and real-time positioning";
    }
    return "Shows raw GEX from open interest - reflects institutional positioning and long-term gamma levels";
}

/**
 * Get use case description for current mode
 *
 * Helps traders know when each mode is most useful
 *
 * @param isWeightedMode - Whether weighted mode is active
 * @returns Use case description string
 */
export function getModeUseCase(isWeightedMode: boolean): string {
    if (isWeightedMode) {
        return "Best for: Current dealer activity (intraday trading)";
    }
    return "Best for: Long-term levels (position management)";
}

/**
 * Get detailed description of what each mode measures
 *
 * @param isWeightedMode - Whether weighted mode is active
 * @returns Detailed explanation
 */
export function getModeDescription(isWeightedMode: boolean): string {
    if (isWeightedMode) {
        return "Volume-weighted GEX shows where dealers are actively hedging based on recent trading activity. Use this for intraday trading decisions.";
    }
    return "Standard GEX shows cumulative gamma from all open interest. Use this for identifying major structural support/resistance levels.";
}

/**
 * Get recommendation for when to switch modes
 *
 * @param isWeightedMode - Whether weighted mode is active
 * @returns Recommendation string
 */
export function getSwitchModeRecommendation(isWeightedMode: boolean): string {
    if (isWeightedMode) {
        return "Switch to Standard view to see major structural levels.";
    }
    return "Switch to Weighted view to see real-time dealer positioning.";
}

/**
 * Get color styling for mode indicator
 *
 * @param isWeightedMode - Whether weighted mode is active
 * @returns Tailwind color class
 */
export function getModeIndicatorColor(isWeightedMode: boolean): string {
    return isWeightedMode ? "text-indigo-400" : "text-muted-foreground";
}

/**
 * Get styling class for mode label
 *
 * @param isWeightedMode - Whether weighted mode is active
 * @returns Tailwind class string
 */
export function getModeLabelClass(isWeightedMode: boolean): string {
    return isWeightedMode ? "font-bold text-indigo-400" : "text-muted-foreground";
}

/**
 * Get border styling for mode card
 *
 * @param isWeightedMode - Whether weighted mode is active
 * @returns Tailwind class string
 */
export function getModeBorderClass(isWeightedMode: boolean): string {
    return isWeightedMode ? "border-l-4 border-l-indigo-500" : "border-l-4 border-l-slate-500";
}
