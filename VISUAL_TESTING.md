# Visual Regression Testing Guide

This document provides guidelines for testing the visual appearance of the GEX Tool dashboard after making changes to the UI or upgrading dependencies.

## Overview

The GEX Tool dashboard uses a custom dark theme with glassmorphism effects, gradients, and interactive visualizations. Visual regression testing ensures that UI changes don't inadvertently break the appearance or user experience.

## Manual Testing Checklist

### 1. Initial State Testing
Run the app without calculating GEX first:

```bash
streamlit run streamlit_app.py
```

**Verify:**
- [ ] Welcome screen displays correctly with gradient header
- [ ] Four feature cards (Call Walls, Put Walls, Zero Gamma, Heatmaps) are visible
- [ ] Sidebar controls are properly styled with dark theme
- [ ] No layout issues or overlapping elements

### 2. Symbol Selection Testing
Test with different symbols and configurations:

**Test Cases:**
- [ ] SPY with 30 DTE (default)
- [ ] QQQ with 60 DTE (maximum)
- [ ] Custom symbol (e.g., AAPL)
- [ ] Different strike ranges (5%, 20%, 50%)

**For each test case, verify:**
- [ ] Symbol badge displays correctly in gradient style
- [ ] Metric cards show proper values with appropriate colors
- [ ] Charts render without errors
- [ ] Hover effects work on all interactive elements

### 3. Chart Visualization Testing

**GEX Profile Chart:**
- [ ] Gradient fills for positive (green) and negative (red) bars
- [ ] Spot price line (cyan) with annotation box
- [ ] Zero gamma line (yellow) with annotation box
- [ ] Call wall marker (green) if present
- [ ] Put wall marker (red/pink) if present
- [ ] Chart title formatting with symbol and DTE info
- [ ] Hover tooltips display correctly

**Call vs Put Breakdown Chart:**
- [ ] Stacked bars with correct colors
- [ ] Vertical markers match main chart
- [ ] Legend displays properly
- [ ] Hover effects work

**Heatmap by Expiration:**
- [ ] Color scale from red (negative) to green (positive)
- [ ] Strike labels on Y-axis
- [ ] Date labels on X-axis (rotated 45°)
- [ ] Hover tooltips show strike, date, and GEX value

### 4. Metric Cards Testing

**Primary Metrics Row (5 cards):**
- [ ] Spot Price (neutral/cyan border)
- [ ] Total Net GEX (green/red based on value)
- [ ] Zero Gamma (neutral, with "Flip level" subtitle)
- [ ] Call Wall (green, with "Resistance" subtitle)
- [ ] Put Wall (red, with "Support" subtitle)

**Secondary Metrics Row (3 cards):**
- [ ] Call Gamma (green)
- [ ] Put Gamma (red)
- [ ] Net at Spot (color based on value, "Interpolated" subtitle)

**For all cards, verify:**
- [ ] Glassmorphism effect (semi-transparent with blur)
- [ ] Hover animation (lift up 2px)
- [ ] Glow effect on hover (cyan shadow)
- [ ] Text colors and font sizes
- [ ] Border colors match card type

### 5. Responsive Layout Testing

Test at different viewport sizes:
- [ ] Desktop (1920x1080)
- [ ] Laptop (1366x768)
- [ ] Tablet landscape (1024x768)
- [ ] Tablet portrait (768x1024)

**Verify:**
- [ ] Columns wrap appropriately
- [ ] No horizontal scrolling
- [ ] Charts resize properly
- [ ] Sidebar remains functional

### 6. Dark Theme Components

**General styling:**
- [ ] Background gradient (dark blue-black)
- [ ] Sidebar dark theme with border
- [ ] Section headers with bottom border
- [ ] Dividers (gradient line)
- [ ] Buttons (gradient cyan-purple)
- [ ] Expanders (dark card style)
- [ ] Radio buttons (dark background)
- [ ] Text inputs (dark with proper contrast)

### 7. Browser-Specific Testing

Test in multiple browsers (see Browser Compatibility in README.md):
- [ ] Chrome/Edge 76+ (full support)
- [ ] Firefox 103+ (full support)
- [ ] Safari 9+ (WebKit prefix support)
- [ ] Older browser (fallback to solid backgrounds)

**Verify per browser:**
- [ ] Backdrop-filter blur effect works (or fallback is acceptable)
- [ ] CSS gradients render correctly
- [ ] Text gradients display (or fallback to solid color)
- [ ] Font rendering is clear and readable

### 8. Interaction Testing

**User interactions:**
- [ ] Symbol dropdown works correctly
- [ ] Custom symbol input validates properly
- [ ] DTE slider updates value display
- [ ] Strike range slider updates value display
- [ ] "Calculate GEX" button shows loading spinner
- [ ] Chart view radio buttons switch between Net and Breakdown
- [ ] "View Raw Data" expander opens and closes
- [ ] "How to Interpret GEX" expander opens and closes
- [ ] CSV download button works

### 9. Error State Testing

**Test error handling:**
- [ ] Invalid symbol displays error message styled correctly
- [ ] Missing credentials shows styled error
- [ ] API errors display with proper formatting
- [ ] No major gamma levels shows styled empty state

### 10. Performance Testing

**Check for visual performance issues:**
- [ ] Animations are smooth (no jank)
- [ ] Charts render in reasonable time (< 2 seconds)
- [ ] No layout shift during loading
- [ ] Hover effects are responsive
- [ ] Page scrolling is smooth

## Screenshot Documentation

### Recommended Screenshots to Capture

After major UI changes, capture screenshots of:

1. **Initial welcome screen**
   - Full page view showing gradient header and feature cards

2. **Dashboard with SPY data**
   - Metric cards section
   - Main GEX profile chart with markers
   - Call vs Put breakdown chart
   - Major gamma levels table and heatmap side-by-side

3. **Sidebar controls**
   - Symbol selection
   - Sliders
   - Advanced settings expanded

4. **Different symbols**
   - At least one comparison (e.g., SPY vs QQQ) to verify consistency

5. **Hover states**
   - Metric card with hover effect
   - Chart with tooltip visible

### Screenshot Naming Convention

Use descriptive names:
```
gex-dashboard-{component}-{date}.png

Examples:
gex-dashboard-welcome-2025-12-08.png
gex-dashboard-spy-metrics-2025-12-08.png
gex-dashboard-gex-chart-2025-12-08.png
```

### Storage Location

Store screenshots in a `screenshots/` directory (not tracked in git due to .gitignore):
```
screenshots/
├── baseline/          # Reference images from last stable version
├── current/           # Latest screenshots
└── comparison/        # Diff images if using automated tools
```

## Automated Visual Regression Testing (Optional)

For more rigorous testing, consider implementing automated visual regression tests using tools like:

### Option 1: Playwright + Streamlit
```python
# Example test structure
from playwright.sync_api import sync_playwright

def test_dashboard_visual():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("http://localhost:8501")
        page.screenshot(path="screenshot.png")
        # Compare with baseline
        browser.close()
```

### Option 2: Percy (Visual Testing Platform)
- Integrates with CI/CD
- Automatic screenshot comparison
- Provides visual diffs

### Option 3: Selenium + Image Comparison
- Use Selenium to navigate
- Capture screenshots
- Compare using PIL or OpenCV

## Testing After Streamlit Upgrades

When upgrading Streamlit, follow these steps:

1. **Before upgrade:**
   - Capture baseline screenshots of all key views
   - Document current Streamlit version in `assets/dark_theme.css` header

2. **After upgrade:**
   - Update version comment in `streamlit_app.py` (line 54)
   - Update version comment in `assets/dark_theme.css` header
   - Run through entire manual testing checklist
   - Capture new screenshots and compare with baseline
   - Pay special attention to:
     - `data-testid` selectors (may change)
     - Component styling (Streamlit may change default styles)
     - Layout behavior (columns, containers)

3. **If issues found:**
   - Check Streamlit release notes for breaking changes
   - Update CSS selectors if needed
   - Adjust styling to compensate for Streamlit changes
   - Re-test

4. **Document changes:**
   - Update this file with any new known issues
   - Note any CSS adjustments made
   - Update browser compatibility if needed

## Known Visual Issues

### Current Version (Streamlit 1.40.0)
- None currently documented

### Historical Issues
- *Document any issues found during testing here for future reference*

## Reporting Visual Bugs

When reporting a visual bug, include:
1. **Screenshot** showing the issue
2. **Browser** name and version
3. **Streamlit version** (`pip show streamlit`)
4. **Steps to reproduce**
5. **Expected vs actual** behavior
6. **Screen resolution** and zoom level

## Contributing

When making visual changes:
1. Update this document if adding new components to test
2. Run through the full checklist before creating a PR
3. Include before/after screenshots in PR description
4. Note any browser compatibility concerns
